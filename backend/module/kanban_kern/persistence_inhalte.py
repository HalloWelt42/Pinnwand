"""Persistenz der Inhalte des Kanban-Moduls.

Kanban-Einstellungen, Dokumente, Label-Definitionen, Datei-Anhänge,
Aktivitäts-Lesefunktionen, JSON-Export sowie die Lese-Übersichten
(was_steht_an, faellige_karten).
"""
from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4

from app.db import DB_PFAD

from .models import (
    Aktivitaet,
    Anhang,
    Dokument,
    DokumentUpdate,
    FaelligEintrag,
    HeuteUebersicht,
    LabelDefinition,
    LabelUpdate,
)
from .persistence_basis import _als_int, _jetzt, _jetzt_genau, _protokolliere, _verb


def hole_kanban_einstellungen() -> dict[str, int]:
    with _verb() as conn:
        rows = conn.execute("SELECT schluessel, wert FROM kanban_einstellung").fetchall()
    roh = {r["schluessel"]: r["wert"] for r in rows}
    return {
        "fertig_seitengroesse": _als_int(roh.get("fertig_seitengroesse"), 50, 1, 500),
        "archiv_tage": _als_int(roh.get("archiv_tage"), 365, 1, 100000),
        # Karten-Alterung (Badge): amber ab X Tagen, rot ab Y Tagen; 0 = aus.
        "aging_amber_tage": _als_int(roh.get("aging_amber_tage"), 4, 0, 365),
        "aging_rot_tage": _als_int(roh.get("aging_rot_tage"), 8, 0, 365),
    }


def setze_kanban_einstellungen(fertig_seitengroesse: int, archiv_tage: int,
                               aging_amber_tage: int = 4, aging_rot_tage: int = 8) -> dict[str, int]:
    seiten = _als_int(fertig_seitengroesse, 50, 1, 500)
    tage = _als_int(archiv_tage, 365, 1, 100000)
    amber = _als_int(aging_amber_tage, 4, 0, 365)
    rot = _als_int(aging_rot_tage, 8, 0, 365)
    with _verb() as conn:
        for schluessel, wert in (("fertig_seitengroesse", seiten), ("archiv_tage", tage),
                                 ("aging_amber_tage", amber), ("aging_rot_tage", rot)):
            conn.execute(
                "INSERT INTO kanban_einstellung (schluessel, wert) VALUES (?, ?) "
                "ON CONFLICT(schluessel) DO UPDATE SET wert = excluded.wert",
                (schluessel, str(wert)),
            )
    return {"fertig_seitengroesse": seiten, "archiv_tage": tage}


# -- Dokumente (Karten- und Mappen-Dokumente) -----------------------------

def _dokument_aus_row(r: sqlite3.Row) -> Dokument:
    return Dokument(
        id=r["id"], kontext=r["kontext"], kontext_id=r["kontext_id"],
        titel=r["titel"], inhalt=r["inhalt"], erstellt_am=r["erstellt_am"], bewegt_am=r["bewegt_am"],
    )


def liste_dokumente(kontext: str, kontext_id: str) -> list[Dokument]:
    with _verb() as conn:
        rows = conn.execute(
            "SELECT * FROM dokument WHERE kontext = ? AND kontext_id = ? ORDER BY titel",
            (kontext, kontext_id),
        ).fetchall()
    return [_dokument_aus_row(r) for r in rows]


def hole_dokument(dokument_id: str) -> Dokument | None:
    with _verb() as conn:
        r = conn.execute("SELECT * FROM dokument WHERE id = ?", (dokument_id,)).fetchone()
    return _dokument_aus_row(r) if r else None


def erstelle_dokument(dokument_id: str, kontext: str, kontext_id: str, titel: str) -> Dokument:
    jetzt = _jetzt_genau()
    with _verb() as conn:
        conn.execute(
            "INSERT INTO dokument (id, kontext, kontext_id, titel, inhalt, erstellt_am, bewegt_am)"
            " VALUES (?, ?, ?, ?, '', ?, ?)",
            (dokument_id, kontext, kontext_id, titel, jetzt, jetzt),
        )
    return Dokument(id=dokument_id, kontext=kontext, kontext_id=kontext_id, titel=titel, inhalt="", erstellt_am=jetzt, bewegt_am=jetzt)


def aktualisiere_dokument(dokument_id: str, felder: dict) -> Dokument | None:
    erlaubt = {k: v for k, v in felder.items() if k in DokumentUpdate.model_fields}
    with _verb() as conn:
        if erlaubt:
            sql = ", ".join(f"{k} = ?" for k in erlaubt)
            conn.execute(
                f"UPDATE dokument SET {sql}, bewegt_am = ? WHERE id = ?",
                (*erlaubt.values(), _jetzt_genau(), dokument_id),
            )
        r = conn.execute("SELECT * FROM dokument WHERE id = ?", (dokument_id,)).fetchone()
    return _dokument_aus_row(r) if r else None


def loesche_dokument(dokument_id: str) -> bool:
    with _verb() as conn:
        cur = conn.execute("DELETE FROM dokument WHERE id = ?", (dokument_id,))
    return cur.rowcount > 0


# -- Label-Definitionen ---------------------------------------------------

class LabelNameBelegt(Exception):
    """Ein Label mit diesem Namen existiert bereits (case-insensitiv)."""


def liste_labels() -> list[LabelDefinition]:
    with _verb() as conn:
        rows = conn.execute(
            "SELECT id, name, familie FROM label_definition ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [LabelDefinition(id=r["id"], name=r["name"], familie=r["familie"]) for r in rows]


def hole_label(label_id: str) -> LabelDefinition | None:
    with _verb() as conn:
        r = conn.execute("SELECT id, name, familie FROM label_definition WHERE id = ?", (label_id,)).fetchone()
    return LabelDefinition(id=r["id"], name=r["name"], familie=r["familie"]) if r else None


def erstelle_label(label_id: str, name: str, familie: str) -> LabelDefinition | None:
    """Legt eine Label-Definition an; None bei bereits belegtem Namen (case-insensitiv)."""
    with _verb() as conn:
        belegt = conn.execute(
            "SELECT 1 FROM label_definition WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if belegt:
            return None
        conn.execute(
            "INSERT INTO label_definition (id, name, familie, erstellt_am) VALUES (?, ?, ?, ?)",
            (label_id, name, familie, _jetzt()),
        )
    return hole_label(label_id)


def aktualisiere_label(label_id: str, aenderungen: dict) -> LabelDefinition | None:
    felder = {k: v for k, v in aenderungen.items() if k in LabelUpdate.model_fields}
    with _verb() as conn:
        row = conn.execute("SELECT name FROM label_definition WHERE id = ?", (label_id,)).fetchone()
        if row is None:
            return None
        alt_name = row["name"]
        if "name" in felder:
            neu_name = (felder["name"] or "").strip()
            if not neu_name:
                felder.pop("name")  # leere Umbenennung ignorieren
            else:
                belegt = conn.execute(
                    "SELECT 1 FROM label_definition WHERE name = ? COLLATE NOCASE AND id != ?",
                    (neu_name, label_id),
                ).fetchone()
                if belegt:
                    raise LabelNameBelegt()
                felder["name"] = neu_name
        if felder:
            zuweisung = ", ".join(f"{k} = ?" for k in felder)
            conn.execute(f"UPDATE label_definition SET {zuweisung} WHERE id = ?", (*felder.values(), label_id))
        # Namensänderung auf die Label-Strings aller Karten übertragen (JSON-sicher).
        if "name" in felder and felder["name"].lower() != alt_name.lower():
            _benenne_label_in_karten(conn, alt_name, felder["name"])
    return hole_label(label_id)


def _benenne_label_in_karten(conn: sqlite3.Connection, alt: str, neu: str) -> None:
    """Ersetzt in karte.labels jeden (case-insensitiv) gleichen Namen durch den neuen.
    Liest die JSON-Arrays und schreibt sie zurück - kein blindes SQL-Replace.
    Dedupliziert case-insensitiv, damit nicht zwei gleiche Namen in anderer
    Schreibweise auf derselben Karte landen."""
    alt_l = alt.lower()
    rows = conn.execute("SELECT id, labels FROM karte").fetchall()
    for r in rows:
        liste = json.loads(r["labels"])
        neu_liste: list[str] = []
        gesehen: set[str] = set()
        geaendert = False
        for l in liste:
            ist_treffer = isinstance(l, str) and l.lower() == alt_l
            if ist_treffer:
                geaendert = True
            ziel = neu if ist_treffer else l
            schluessel = ziel.lower() if isinstance(ziel, str) else str(ziel)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            neu_liste.append(ziel)
        if geaendert:
            conn.execute("UPDATE karte SET labels = ? WHERE id = ?", (json.dumps(neu_liste), r["id"]))


def loesche_label(label_id: str) -> bool:
    """Entfernt nur die Definition; die Label-Strings an Karten bleiben unangetastet
    (sie fallen dann auf die Hash-Fallbackfarbe zurück)."""
    with _verb() as conn:
        cur = conn.execute("DELETE FROM label_definition WHERE id = ?", (label_id,))
        return cur.rowcount > 0


# -- Datei-Anhaenge --------------------------------------------------------
# Dateien liegen neben der Datenbank unter anhaenge/<karte_id>/<anhang_id>;
# der Original-Name steht nur in der Tabelle (keine Dateisystem-Fallen durch
# Sonderzeichen). Backup/Restore nehmen den Ordner mit.

ANHANG_MAX_BYTES = 25 * 1024 * 1024


def anhaenge_dir() -> Path:
    return DB_PFAD.parent / "anhaenge"


def _anhang_aus_row(row: sqlite3.Row) -> Anhang:
    return Anhang(**dict(row))


def liste_anhaenge(karte_id: str) -> list[Anhang]:
    with _verb() as conn:
        rows = conn.execute(
            "SELECT * FROM anhang WHERE karte_id = ? ORDER BY erstellt_am, name", (karte_id,)
        ).fetchall()
    return [_anhang_aus_row(r) for r in rows]


def speichere_anhang(karte_id: str, name: str, daten: bytes, typ: str | None,
                     akteur: str | None = None) -> Anhang | None:
    """Legt die Datei ab und registriert sie an der Karte (None = Karte fehlt)."""
    sauber = Path(name).name.strip() or "datei"
    anhang_id = f"an_{uuid4().hex[:10]}"
    with _verb() as conn:
        if conn.execute("SELECT 1 FROM karte WHERE id = ?", (karte_id,)).fetchone() is None:
            return None
        ordner = anhaenge_dir() / karte_id
        ordner.mkdir(parents=True, exist_ok=True)
        (ordner / anhang_id).write_bytes(daten)
        conn.execute(
            "INSERT INTO anhang (id, karte_id, name, groesse, typ, erstellt_am) VALUES (?, ?, ?, ?, ?, ?)",
            (anhang_id, karte_id, sauber, len(daten), typ, _jetzt()),
        )
        _protokolliere(conn, karte_id, "anhang", f"Anhang hinzugefügt: {sauber}", akteur)
    return hole_anhang(anhang_id)


def hole_anhang(anhang_id: str) -> Anhang | None:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM anhang WHERE id = ?", (anhang_id,)).fetchone()
    return _anhang_aus_row(row) if row else None


def anhang_pfad(anhang: Anhang) -> Path:
    return anhaenge_dir() / anhang.karte_id / anhang.id


def loesche_anhang(anhang_id: str, akteur: str | None = None) -> bool:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM anhang WHERE id = ?", (anhang_id,)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM anhang WHERE id = ?", (anhang_id,))
        _protokolliere(conn, row["karte_id"], "anhang", f"Anhang entfernt: {row['name']}", akteur)
    (anhaenge_dir() / row["karte_id"] / anhang_id).unlink(missing_ok=True)
    return True


def _loesche_anhang_dateien(karten_ids: list[str]) -> None:
    """Datei-Ordner geloeschter Karten entfernen (Rows loescht der Aufrufer)."""
    for kid in karten_ids:
        shutil.rmtree(anhaenge_dir() / kid, ignore_errors=True)


def _export_karten(conn: sqlite3.Connection, board_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM karte WHERE board_id = ? ORDER BY spalte, reihenfolge", (board_id,)
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        for feld in ("labels", "checkliste", "kommentare"):
            d[feld] = json.loads(d[feld] or "[]")
        out.append(d)
    return out


def _export_board_kern(conn: sqlite3.Connection, board_row: sqlite3.Row) -> dict:
    board_id = board_row["id"]
    spalten = [dict(r) for r in conn.execute(
        "SELECT * FROM spalte WHERE board_id = ? ORDER BY reihenfolge", (board_id,)
    ).fetchall()]
    karten = _export_karten(conn, board_id)
    zeiten = [dict(r) for r in conn.execute(
        "SELECT * FROM zeiteintrag WHERE board_id = ? ORDER BY datum, id", (board_id,)
    ).fetchall()]
    karten_ids = [k["id"] for k in karten]
    dokumente: list[dict] = []
    if karten_ids:
        platz = ",".join("?" for _ in karten_ids)
        dokumente = [dict(r) for r in conn.execute(
            f"SELECT * FROM dokument WHERE kontext = 'karte' AND kontext_id IN ({platz})", karten_ids
        ).fetchall()]
    return {
        "board": dict(board_row),
        "spalten": spalten,
        "karten": karten,
        "zeiteintraege": zeiten,
        "dokumente": dokumente,
    }


def export_board(board_id: str) -> dict | None:
    """Vollstaendiger, lesbarer JSON-Export eines Boards (alle Karten inklusive
    erledigter und archivierter, Zeiteintraege, Karten-Dokumente)."""
    with _verb() as conn:
        b = conn.execute("SELECT * FROM board WHERE id = ?", (board_id,)).fetchone()
        if b is None:
            return None
        return {"format": "pinnwand-board", "version": 1, **_export_board_kern(conn, b)}


def export_mappe(mappe_id: str) -> dict | None:
    """Vollstaendiger JSON-Export einer Mappe (Projekt): alle Boards samt Inhalt
    plus die Mappen-Dokumente."""
    with _verb() as conn:
        m = conn.execute("SELECT * FROM mappe WHERE id = ?", (mappe_id,)).fetchone()
        if m is None:
            return None
        boards = [
            _export_board_kern(conn, b)
            for b in conn.execute("SELECT * FROM board WHERE mappe_id = ? ORDER BY titel", (mappe_id,)).fetchall()
        ]
        dokumente = [dict(r) for r in conn.execute(
            "SELECT * FROM dokument WHERE kontext = 'mappe' AND kontext_id = ?", (mappe_id,)
        ).fetchall()]
        return {
            "format": "pinnwand-mappe",
            "version": 1,
            "mappe": dict(m),
            "boards": boards,
            "dokumente": dokumente,
        }


def faellige_karten(von: str, bis: str, nur_mappen: list[str] | None = None) -> list[FaelligEintrag]:
    """Alle Karten mit Faelligkeit im Zeitraum (fuer den Faelligkeits-Kalender) -
    auch erledigte, damit der Monat vollstaendig erzaehlt, was anstand."""
    sql = (
        "SELECT k.id, k.board_id, k.schluessel, k.titel, k.faellig, k.zustaendig,"
        " COALESCE(s.erledigt, 0) AS erledigt"
        " FROM karte k"
        " JOIN board b ON b.id = k.board_id"
        " LEFT JOIN spalte s ON s.id = k.spalte"
        " WHERE k.faellig IS NOT NULL AND k.faellig >= ? AND k.faellig <= ?"
    )
    params: list = [von, bis]
    if nur_mappen is not None:
        platzhalter = ",".join("?" for _ in nur_mappen) or "''"
        sql += f" AND b.mappe_id IN ({platzhalter})"
        params.extend(nur_mappen)
    sql += " ORDER BY k.faellig, k.titel"
    with _verb() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        FaelligEintrag(
            id=r["id"], board_id=r["board_id"], schluessel=r["schluessel"], titel=r["titel"],
            faellig=r["faellig"], zustaendig=r["zustaendig"], erledigt=bool(r["erledigt"]),
        )
        for r in rows
    ]


def karten_aktivitaet(karte_id: str, limit: int = 200) -> list[Aktivitaet]:
    """Das Aktivitaetsprotokoll einer Karte, Juengstes zuerst."""
    with _verb() as conn:
        rows = conn.execute(
            "SELECT id, karte_id, zeit, kuerzel, art, text FROM aktivitaet"
            " WHERE karte_id = ? ORDER BY zeit DESC, rowid DESC LIMIT ?",
            (karte_id, limit),
        ).fetchall()
    return [Aktivitaet(**dict(r)) for r in rows]


def aktivitaet_fuer(kuerzel: str, seit: str | None = None,
                    nur_mappen: list[str] | None = None, limit: int = 50) -> list[Aktivitaet]:
    """Fremde Ereignisse auf den Karten einer Person (Benachrichtigungs-Glocke):
    alles, was jemand anderes (oder das System, z.B. eine Serien-Vorbuchung) an
    Karten getan hat, fuer die die Person zustaendig ist - optional erst ab
    einem Zeitstempel und beschraenkt auf sichtbare Mappen."""
    sql = (
        "SELECT a.id, a.karte_id, a.zeit, a.kuerzel, a.art, a.text,"
        " k.titel AS karte_titel, k.schluessel AS karte_schluessel, k.board_id AS board_id"
        " FROM aktivitaet a"
        " JOIN karte k ON k.id = a.karte_id"
        " JOIN board b ON b.id = k.board_id"
        " WHERE k.zustaendig = ? AND (a.kuerzel IS NULL OR a.kuerzel != ?)"
    )
    params: list = [kuerzel, kuerzel]
    if seit:
        sql += " AND a.zeit > ?"
        params.append(seit)
    if nur_mappen is not None:
        platzhalter = ",".join("?" for _ in nur_mappen) or "''"
        sql += f" AND b.mappe_id IN ({platzhalter})"
        params.extend(nur_mappen)
    sql += " ORDER BY a.zeit DESC, a.rowid DESC LIMIT ?"
    params.append(limit)
    with _verb() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Aktivitaet(**dict(r)) for r in rows]


def was_steht_an(heute: str, nur_mappen: set[str] | None = None) -> HeuteUebersicht:
    """Handlungsorientierte Übersicht: überfällig, heute, diese Woche, laufend, liegengeblieben.

    Wiederkehrende Termine erscheinen automatisch über ihre Fälligkeit.
    """
    from datetime import date, timedelta

    heute_d = date.fromisoformat(heute)
    woche = (heute_d + timedelta(days=7)).isoformat()
    alt = (heute_d - timedelta(days=7)).isoformat()
    with _verb() as conn:
        done = {r["board_id"]: r["id"] for r in conn.execute("SELECT board_id, id FROM spalte WHERE erledigt = 1").fetchall()}
        if nur_mappen is not None:
            # Projekt-Scoping: nur Karten aus sichtbaren Mappen.
            platz = ",".join("?" for _ in nur_mappen) or "''"
            rows = conn.execute(
                "SELECT k.id, k.board_id, k.spalte, k.schluessel, k.titel, k.faellig, k.laeuft_seit, k.bewegt_am, k.blockiert_grund"
                f" FROM karte k JOIN board b ON b.id = k.board_id WHERE b.mappe_id IN ({platz})",
                tuple(sorted(nur_mappen)),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, board_id, spalte, schluessel, titel, faellig, laeuft_seit, bewegt_am, blockiert_grund FROM karte"
            ).fetchall()

    def offen(r) -> bool:
        return done.get(r["board_id"]) != r["spalte"]

    def eintrag(r) -> dict:
        return {"id": r["id"], "board_id": r["board_id"], "schluessel": r["schluessel"],
                "titel": r["titel"], "faellig": r["faellig"]}

    ueberfaellig, heute_f, diese_woche, laufend, liegengeblieben, blockiert = [], [], [], [], [], []
    faellig_ids: set[str] = set()
    for r in rows:
        if r["blockiert_grund"] and offen(r):
            blockiert.append(eintrag(r))
        if r["laeuft_seit"]:
            laufend.append(eintrag(r))
        if r["faellig"] and offen(r):
            if r["faellig"] < heute:
                ueberfaellig.append(eintrag(r)); faellig_ids.add(r["id"])
            elif r["faellig"] == heute:
                heute_f.append(eintrag(r)); faellig_ids.add(r["id"])
            elif r["faellig"] <= woche:
                diese_woche.append(eintrag(r)); faellig_ids.add(r["id"])
    for r in rows:
        if offen(r) and not r["laeuft_seit"] and r["id"] not in faellig_ids and r["bewegt_am"] and r["bewegt_am"] < alt:
            liegengeblieben.append(eintrag(r))
    return HeuteUebersicht(
        datum=heute, ueberfaellig=ueberfaellig, heute=heute_f,
        diese_woche=diese_woche, laufend=laufend, liegengeblieben=liegengeblieben,
        blockiert=blockiert,
    )
