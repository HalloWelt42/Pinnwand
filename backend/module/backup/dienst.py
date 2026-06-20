"""Snapshot-Erzeugung, Vorschau und Wiederherstellung.

Ein Snapshot ist eine ZIP-Datei mit fester Struktur:
  manifest.json          - Version, Zeit, Art, Schema, Zähler
  db/pinnwand.db         - konsistente Online-Kopie der Datenbank
  berichte/<dateien>     - das unveränderliche Berichts-Archiv
  konfig/<dateien>       - Konfigurationsvorlage (und vorhandene .env)

Die Datenbank wird über die SQLite-Online-Backup-Schnittstelle kopiert, damit
der Snapshot auch bei parallelen Schreibzugriffen in sich konsistent ist. Beim
Wiederherstellen wird zuerst automatisch ein Sicherheits-Snapshot des aktuellen
Standes erzeugt, dann werden Datenbank und Archiv ersetzt.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.config import VERSION, einstellungen
from app.db import DB_PFAD, verbindung

from . import persistence as db

_PROJEKT_WURZEL = Path(__file__).resolve().parents[3]
_BERICHTE = Path(__file__).resolve().parents[2] / "data" / "berichte"
_MANIFEST = "manifest.json"


# --- Bestandsaufnahme des aktuellen Standes -------------------------------------------------


def _schema(conn: sqlite3.Connection) -> list[dict]:
    tabellen = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    ergebnis: list[dict] = []
    for t in tabellen:
        spalten = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")').fetchall()]
        ergebnis.append({"tabelle": t, "spalten": spalten})
    return ergebnis


def _zaehler(conn: sqlite3.Connection) -> dict[str, int]:
    zahlen: dict[str, int] = {}
    for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        name = r[0]
        try:
            zahlen[name] = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        except sqlite3.Error:
            zahlen[name] = -1
    return zahlen


def _berichte_dateien() -> list[Path]:
    if not _BERICHTE.is_dir():
        return []
    return [p for p in sorted(_BERICHTE.glob("*")) if p.is_file()]


def aktueller_zustand() -> dict:
    with verbindung() as conn:
        zaehler = _zaehler(conn)
    return {"version": VERSION, "zaehler": zaehler, "berichte": len(_berichte_dateien())}


def aktuelles_schema() -> list[dict]:
    with verbindung() as conn:
        return _schema(conn)


# --- Snapshot erzeugen ----------------------------------------------------------------------


def _kopiere_db(ziel: Path) -> None:
    """Konsistente Kopie der Datenbank über die Online-Backup-Schnittstelle."""
    quelle = sqlite3.connect(DB_PFAD)
    senke = sqlite3.connect(ziel)
    try:
        quelle.backup(senke)
    finally:
        senke.close()
        quelle.close()


def _konfig_dateien() -> list[tuple[Path, str]]:
    """Nur die Konfigurationsvorlage sichern, niemals die echte .env.

    Ein Snapshot kann heruntergeladen und weitergegeben werden; Geheimnisse
    (Token, Schlüssel) gehören daher bewusst nicht hinein. Die Datei .env bleibt
    ohnehin lokal im Projekt und wird nicht versioniert.
    """
    paare: list[tuple[Path, str]] = []
    p = _PROJEKT_WURZEL / ".env.muster"
    if p.is_file():
        paare.append((p, "konfig/.env.muster"))
    return paare


def erzeuge(art: str = "manuell", notiz: str = "") -> dict:
    """Erzeugt einen Snapshot und gibt dessen Metadaten zurück."""
    sid = "s_" + uuid4().hex[:10]
    jetzt = datetime.now()
    stempel = jetzt.strftime("%Y%m%d_%H%M%S")
    # Die ID gehört in den Dateinamen, sonst kollidieren mehrere Snapshots derselben Sekunde.
    dateiname = f"pinnwand_{stempel}_{art}_{sid}.zip"
    db.DATEN.mkdir(parents=True, exist_ok=True)
    ziel = db.DATEN / dateiname

    with verbindung() as conn:
        schema = _schema(conn)
        zaehler = _zaehler(conn)

    manifest = {
        "id": sid,
        "version": VERSION,
        "erstellt_am": jetzt.isoformat(timespec="seconds"),
        "art": art,
        "notiz": notiz,
        "schema": schema,
        "zaehler": zaehler,
        "berichte": len(_berichte_dateien()),
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_db = Path(tmp) / "pinnwand.db"
        _kopiere_db(tmp_db)
        with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(_MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
            zf.write(tmp_db, "db/pinnwand.db")
            for p in _berichte_dateien():
                zf.write(p, f"berichte/{p.name}")
            for pfad, eintrag in _konfig_dateien():
                zf.write(pfad, eintrag)

    groesse = ziel.stat().st_size
    info = {
        "id": sid,
        "dateiname": dateiname,
        "erstellt_am": manifest["erstellt_am"],
        "groesse": groesse,
        "version": VERSION,
        "art": art,
        "notiz": notiz,
    }
    db.speichere_meta(info)
    _raeume_automatische_auf()
    return info


def _raeume_automatische_auf() -> None:
    """Begrenzt die Zahl automatischer Snapshots (Aufbewahrung aus der Konfiguration)."""
    for alt in db.automatische_aelter_als(einstellungen.backup_behalten):
        _loesche_datei(alt["dateiname"])
        db.loesche_meta(alt["id"])


def synchronisiere_index() -> None:
    """Gleicht die Metadaten-Tabelle mit den tatsächlich vorhandenen Snapshot-Dateien ab.

    Nötig, weil eine Wiederherstellung die Datenbank (und damit auch diese Tabelle)
    zurücksetzt: Snapshots, die nach dem wiederhergestellten Stand entstanden sind
    (etwa der Sicherheits-Snapshot), liegen dann zwar als Datei vor, haben aber keinen
    Eintrag mehr. Der Abgleich liest jede Datei aus ihrem Manifest neu ein.
    """
    if not db.DATEN.is_dir():
        return
    bekannt = {r["id"]: r for r in db.liste()}
    for zpfad in sorted(db.DATEN.glob("*.zip")):
        try:
            m = _lies_manifest(zpfad)
        except Exception:
            continue
        sid = m.get("id")
        if not sid or sid in bekannt:
            continue
        db.speichere_meta(
            {
                "id": sid,
                "dateiname": zpfad.name,
                "erstellt_am": m.get("erstellt_am", ""),
                "groesse": zpfad.stat().st_size,
                "version": m.get("version", "?"),
                "art": m.get("art", "manuell"),
                "notiz": m.get("notiz", ""),
            }
        )
    # Verwaiste Einträge (Datei fehlt) entfernen.
    for sid, r in bekannt.items():
        if not (db.DATEN / r["dateiname"]).is_file():
            db.loesche_meta(sid)


def _bereit_fuer_snapshot() -> bool:
    """Sicherung: erst sichern, wenn die Kerntabellen wirklich existieren.

    Verhindert einen leeren automatischen Snapshot, falls die Funktion je vor der
    Initialisierung der anderen Module aufgerufen würde.
    """
    with verbindung() as conn:
        tabellen = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    return "karte" in tabellen and "person" in tabellen


def auto_wenn_faellig() -> None:
    """Erzeugt beim Start einen automatischen Snapshot, falls aktiviert und der letzte älter als 24 Stunden ist."""
    if not einstellungen.backup_auto:
        return
    if not _bereit_fuer_snapshot():
        return
    letzter = db.letzter_automatischer()
    if letzter:
        try:
            wann = datetime.fromisoformat(letzter["erstellt_am"])
        except ValueError:
            wann = None
        if wann and (datetime.now() - wann) < timedelta(hours=24):
            return
    try:
        erzeuge(art="automatisch")
    except Exception:
        # Eine fehlgeschlagene automatische Sicherung darf den Start nie verhindern.
        pass


# --- Vorschau -------------------------------------------------------------------------------


def _lies_manifest(pfad: Path) -> dict:
    with zipfile.ZipFile(pfad, "r") as zf:
        return json.loads(zf.read(_MANIFEST).decode("utf-8"))


def vorschau(sid: str) -> dict | None:
    meta = db.hole_meta(sid)
    if meta is None:
        return None
    pfad = db.DATEN / meta["dateiname"]
    if not pfad.is_file():
        return None
    manifest = _lies_manifest(pfad)
    aktuell = aktueller_zustand()

    warnungen: list[str] = []
    if manifest.get("version") != VERSION:
        warnungen.append(
            f"Snapshot stammt aus Version {manifest.get('version')}, aktuell ist {VERSION}."
        )
    snap_tabellen = {t["tabelle"]: set(t.get("spalten", [])) for t in manifest.get("schema", [])}
    akt_tabellen = {t["tabelle"]: set(t["spalten"]) for t in aktuelles_schema()}
    fehlend = sorted(set(akt_tabellen) - set(snap_tabellen))
    if fehlend:
        warnungen.append("Im Snapshot fehlen Tabellen: " + ", ".join(fehlend))
    for t in sorted(set(snap_tabellen) & set(akt_tabellen)):
        neue_spalten = sorted(akt_tabellen[t] - snap_tabellen[t])
        if neue_spalten:
            warnungen.append(f"Tabelle {t}: neuere Spalten fehlen im Snapshot ({', '.join(neue_spalten)}).")

    return {
        "info": meta,
        "snapshot": {
            "version": manifest.get("version", "?"),
            "zaehler": manifest.get("zaehler", {}),
            "berichte": manifest.get("berichte", 0),
        },
        "aktuell": aktuell,
        "schema": manifest.get("schema", []),
        "warnungen": warnungen,
    }


# --- Wiederherstellung ----------------------------------------------------------------------


def _loesche_datei(dateiname: str) -> None:
    pfad = db.DATEN / dateiname
    if pfad.is_file():
        pfad.unlink()


def hole_datei(sid: str) -> tuple[Path, str] | None:
    meta = db.hole_meta(sid)
    if meta is None:
        return None
    pfad = db.DATEN / meta["dateiname"]
    if not pfad.is_file():
        return None
    return pfad, meta["dateiname"]


def loesche(sid: str) -> bool:
    meta = db.hole_meta(sid)
    if meta is None:
        return False
    _loesche_datei(meta["dateiname"])
    db.loesche_meta(meta["id"])
    return True


def _pruefe_db(pfad: Path) -> None:
    """Stellt sicher, dass die entpackte Datei eine intakte SQLite-Datenbank ist."""
    conn = sqlite3.connect(pfad)
    try:
        ergebnis = conn.execute("PRAGMA integrity_check").fetchone()
        if not ergebnis or ergebnis[0] != "ok":
            raise ValueError("Datenbank im Snapshot ist beschädigt.")
    finally:
        conn.close()


def wiederherstellen(sid: str) -> dict | None:
    meta = db.hole_meta(sid)
    if meta is None:
        return None
    pfad = db.DATEN / meta["dateiname"]
    if not pfad.is_file():
        return None

    # Sicherheitsnetz: aktuellen Stand vorher sichern.
    sicherung = erzeuge(art="vor_wiederherstellung", notiz="automatisch vor Wiederherstellung")

    with zipfile.ZipFile(pfad, "r") as zf:
        namen = set(zf.namelist())
        if "db/pinnwand.db" not in namen:
            raise ValueError("Snapshot enthält keine Datenbank.")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = Path(tmp) / "pinnwand.db"
            tmp_db.write_bytes(zf.read("db/pinnwand.db"))
            _pruefe_db(tmp_db)

            # Datenbank ersetzen. Verbindungen sind kurzlebig (pro Anfrage),
            # daher ist ein Austausch zwischen Anfragen gefahrlos.
            shutil.copyfile(tmp_db, DB_PFAD)
            for nebendatei in ("-wal", "-shm"):
                neben = Path(str(DB_PFAD) + nebendatei)
                if neben.exists():
                    neben.unlink()

            # Berichts-Archiv ersetzen.
            _BERICHTE.mkdir(parents=True, exist_ok=True)
            for vorhanden in _berichte_dateien():
                vorhanden.unlink()
            for name in namen:
                if name.startswith("berichte/") and not name.endswith("/"):
                    ziel = _BERICHTE / Path(name).name
                    ziel.write_bytes(zf.read(name))

    # Die wiederhergestellte DB hat die Snapshot-Liste mit zurückgesetzt; aus den
    # vorhandenen Dateien wieder vervollständigen (inklusive Sicherheits-Snapshot).
    synchronisiere_index()
    return {"ok": True, "vorher_gesichert": sicherung["id"], "wiederhergestellt": aktueller_zustand()}


def _leeren() -> None:
    """Entfernt die Inhaltsdaten. Konfiguration, ein leeres Board und die Snapshots bleiben."""
    daten_tabellen = (
        "karte", "zeiteintrag", "urlaub", "feiertag", "serie",
        "person", "bericht_archiv", "agent_audit", "agent_idempotenz",
        "dokument", "wochen_override", "termin_serie", "termin_instanz",
    )
    with verbindung() as conn:
        vorhanden = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for t in daten_tabellen:
            if t in vorhanden:
                conn.execute(f"DELETE FROM {t}")
    if _BERICHTE.is_dir():
        for p in _BERICHTE.glob("*"):
            if p.is_file():
                p.unlink()


def zuruecksetzen(modus: str = "beispiel") -> dict:
    """Setzt die Daten zurück. Vorher wird automatisch ein Sicherheits-Snapshot erstellt.

    modus 'beispiel': alle Daten löschen und die Beispieldaten neu anlegen (Auslieferungszustand).
    modus 'leer': zusätzlich die Beispiel-Inhalte entfernen (leeres Board, keine Personen/Karten).
    """
    sicherung = erzeuge(art="vor_reset", notiz="automatisch vor Zurücksetzen")
    from app.modul_registry import init_fuer, lade_manifeste

    with verbindung() as conn:
        tabellen = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        for t in tabellen:
            conn.execute(f'DROP TABLE IF EXISTS "{t}"')
    # Alle Module neu initialisieren (Schema + Seed). backup baut dabei seinen
    # Snapshot-Index aus den vorhandenen Dateien neu auf, der Sicherheits-Snapshot bleibt erhalten.
    for manifest in lade_manifeste():
        init_fuer(manifest)
    if modus == "leer":
        _leeren()
    return {"ok": True, "modus": modus, "vorher_gesichert": sicherung["id"], "zustand": aktueller_zustand()}


@asynccontextmanager
async def lebenszyklus():
    """Läuft erst, nachdem alle Module initialisiert und geseedet sind.

    Erst dann ist ein automatischer Snapshot vollständig (alle Tabellen + Daten).
    """
    auto_wenn_faellig()
    yield
