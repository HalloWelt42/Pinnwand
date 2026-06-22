"""Vorbuchung: erzeugt aus Serien die kommenden Karten-Instanzen.

Idempotent: pro Serie und Datum entsteht höchstens eine Karte (Markierung an
der Karte). Die Instanzen sind normale Karten - mit Fälligkeit, geplanter Zeit
(Soll) und damit Timer-fähig.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db import verbindung
from module.kanban_kern import persistence as k

from . import persistence as db, wiederholung


def _zielspalte(serie: dict) -> str | None:
    if serie.get("spalte_id"):
        return serie["spalte_id"]
    with verbindung() as conn:
        r = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge LIMIT 1", (serie["board_id"],)
        ).fetchone()
    return r["id"] if r else None


def _feiertage(von: date, bis: date) -> set[str]:
    """Feiertags-Datumswerte im Bereich (zum Ueberspringen in Serien)."""
    with verbindung() as conn:
        try:
            rows = conn.execute(
                "SELECT DISTINCT datum FROM feiertag WHERE datum >= ? AND datum <= ?",
                (von.isoformat(), bis.isoformat()),
            ).fetchall()
        except Exception:
            return set()
    return {r["datum"] for r in rows}


def _urlaubstage(kuerzel: str | None, von: date, bis: date) -> set[str]:
    """Urlaubs-Datumswerte der zustaendigen Person im Bereich (zum Ueberspringen). Defensiv."""
    if not kuerzel:
        return set()
    try:
        from module.planung import persistence as pdb
        pid = next((p["id"] for p in pdb.liste_personen() if p.get("kuerzel") == kuerzel), None)
        if not pid:
            return set()
        return {u["datum"] for u in pdb.liste_urlaub(pid, von.isoformat(), bis.isoformat())}
    except Exception:
        return set()


def materialisiere(serie: dict, heute: date | None = None) -> int:
    """Legt fehlende Instanzen der Serie im Vorlauf-Zeitraum an. Gibt die Anzahl zurück."""
    if not serie.get("aktiv"):
        return 0
    heute = heute or date.today()
    # 0 ist ein gueltiger Wert (nur heute) - daher kein "or 14", das 0 verschlucken wuerde.
    vorlauf = serie.get("vorlauf_tage")
    vorlauf = 14 if vorlauf is None else int(vorlauf)
    bis = heute + timedelta(days=max(0, vorlauf))
    spalte = _zielspalte(serie)
    if not spalte:
        return 0
    feiertage = _feiertage(heute, bis) if serie.get("feiertage_ueberspringen") else None
    urlaub = _urlaubstage(serie.get("zustaendig"), heute, bis)
    erzeugt = 0
    for d in wiederholung.termine(serie, heute, bis, feiertage):
        iso = d.isoformat()
        if iso in urlaub:
            continue
        if k.serien_instanz_existiert(serie["id"], iso):
            continue
        titel = serie["titel"]
        if serie.get("uhrzeit"):
            titel = f"{serie['uhrzeit']} {titel}"
        karte = k.erstelle_karte(
            karte_id="k_" + uuid4().hex[:8], board_id=serie["board_id"], spalte=spalte,
            titel=titel, beschreibung=serie.get("beschreibung"), labels=serie.get("labels") or [],
            prioritaet=None, cover=None, start=None, faellig=iso, zustaendig=serie.get("zustaendig"),
        )
        if serie.get("dauer_min"):
            k.aktualisiere_karte(karte.id, {"schaetzung_min": serie["dauer_min"]})
        try:
            k.markiere_serie(karte.id, serie["id"], iso)
        except Exception:
            # Paralleler Lauf hat dieselbe Instanz bereits angelegt (UNIQUE-Index)
            # -> die eben erzeugte Doppel-Karte wieder verwerfen.
            k.loesche_karte(karte.id)
            continue
        erzeugt += 1
    return erzeugt


def materialisiere_alle(heute: date | None = None) -> int:
    return sum(materialisiere(s, heute) for s in db.liste())


def loesche(sid: str) -> bool:
    """Loescht die Serie und raeumt ihre Instanzen auf.

    Karten ohne erfasste Zeit (reine Vorbuchungen) werden geloescht; Karten mit
    erfasster Zeit bleiben als Verlauf erhalten, werden aber von der Serie
    geloest (serie_id/serie_datum entfernt). So entstehen beim Loeschen oder
    Ersetzen einer Serie keine verwaisten Doppel-Karten.
    """
    with verbindung() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM karte WHERE serie_id = ?", (sid,)).fetchall()]
    for kid in ids:
        with verbindung() as conn:
            hat_zeit = conn.execute(
                "SELECT 1 FROM zeiteintrag WHERE karte_id = ? LIMIT 1", (kid,)
            ).fetchone()
        if hat_zeit:
            with verbindung() as conn:
                conn.execute("UPDATE karte SET serie_id = NULL, serie_datum = NULL WHERE id = ?", (kid,))
        else:
            k.loesche_karte(kid)
    return db.loesche(sid)


def offene_nachtraege(heute: date | None = None) -> list[dict]:
    """Serien-Karten vergangener Tage, die nicht erfasst und nicht erledigt sind.

    Das sind die Vorkommen, die der Nutzer ignoriert hat - dafuer wird am
    Folgetag gefragt, ob die Stunden nachgetragen werden sollen.
    """
    heute = heute or date.today()
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT k.id, k.schluessel, k.titel, k.faellig, s.titel AS serie_titel, s.dauer_min "
            "FROM karte k "
            "JOIN serie s ON s.id = k.serie_id "
            "JOIN spalte sp ON sp.id = k.spalte "
            "WHERE k.serie_id IS NOT NULL AND k.faellig IS NOT NULL AND k.faellig < ? "
            "AND k.erfasst_sek = 0 AND sp.erledigt = 0 "
            "ORDER BY k.faellig",
            (heute.isoformat(),),
        ).fetchall()
    return [
        {
            "karte_id": r["id"], "schluessel": r["schluessel"], "titel": r["titel"],
            "datum": r["faellig"], "serie_titel": r["serie_titel"], "soll_min": r["dauer_min"],
        }
        for r in rows
    ]


def nachtragen(karte_id: str, dauer_min: int | None = None) -> "object | None":
    """Traegt fuer eine ignorierte Serien-Karte die Stunden ihres Tages nach und
    verschiebt sie in die Erledigt-Spalte. Ohne Dauer wird das Serien-Soll genutzt."""
    with verbindung() as conn:
        row = conn.execute("SELECT board_id, faellig, serie_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        if dauer_min is None and row["serie_id"]:
            s = conn.execute("SELECT dauer_min FROM serie WHERE id = ?", (row["serie_id"],)).fetchone()
            dauer_min = (s["dauer_min"] if s else None) or 60
        done = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? AND erledigt = 1 ORDER BY reihenfolge LIMIT 1",
            (row["board_id"],),
        ).fetchone()
    datum = row["faellig"] or date.today().isoformat()
    sek = max(0, int(dauer_min or 0)) * 60
    if sek > 0:
        k.erstelle_zeiteintrag("z_" + uuid4().hex[:8], karte_id, datum, sek, "Nachgetragen")
    if done is not None:
        k.verschiebe_karte(karte_id, done["id"], 1_000_000)
    return k.hole_karte(karte_id)


def init() -> None:
    """Schema anlegen und beim Start die anstehenden Instanzen vorbuchen."""
    db.init_db()
    try:
        materialisiere_alle()
    except Exception:
        # Vorbuchung darf den Start nie verhindern.
        pass
