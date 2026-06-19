"""SQLite-Persistenz des Kanban-Moduls.

Nutzt die generische Verbindung des Kerns. Schema und Seed gehoeren dem Modul.
Reihenfolge-Werte werden bei jedem Verschieben luecklos neu vergeben.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from uuid import uuid4

from app.db import verbindung


def _jetzt() -> str:
    return datetime.now().isoformat(timespec="minutes")


def _jetzt_genau() -> str:
    return datetime.now().isoformat(timespec="seconds")

from .models import Board, BoardDetail, Karte, Projektmappe, Spalte, Zeiteintrag

SCHEMA = """
CREATE TABLE IF NOT EXISTS mappe (
    id TEXT PRIMARY KEY,
    titel TEXT NOT NULL,
    beschreibung TEXT
);
CREATE TABLE IF NOT EXISTS board (
    id TEXT PRIMARY KEY,
    mappe_id TEXT NOT NULL,
    titel TEXT NOT NULL,
    kuerzel TEXT,
    laufnummer INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS spalte (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    titel TEXT NOT NULL,
    wip_limit INTEGER,
    reihenfolge INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS karte (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    spalte TEXT NOT NULL,
    titel TEXT NOT NULL,
    schluessel TEXT,
    beschreibung TEXT,
    labels TEXT NOT NULL DEFAULT '[]',
    prioritaet TEXT,
    checkliste TEXT NOT NULL DEFAULT '[]',
    kommentare TEXT NOT NULL DEFAULT '[]',
    cover TEXT,
    reihenfolge INTEGER NOT NULL DEFAULT 0,
    start TEXT,
    faellig TEXT,
    zustaendig TEXT,
    erstellt_am TEXT,
    bewegt_am TEXT,
    schaetzung_min INTEGER,
    erfasst_sek INTEGER NOT NULL DEFAULT 0,
    laeuft_seit TEXT
);
CREATE TABLE IF NOT EXISTS zeiteintrag (
    id TEXT PRIMARY KEY,
    karte_id TEXT NOT NULL,
    board_id TEXT,
    mappe_id TEXT,
    datum TEXT NOT NULL,
    start TEXT,
    ende TEXT,
    sekunden INTEGER NOT NULL DEFAULT 0,
    kommentar TEXT,
    manuell INTEGER NOT NULL DEFAULT 0
);
"""


def _verb() -> sqlite3.Connection:
    return verbindung()


def init_db() -> None:
    with _verb() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) AS n FROM mappe").fetchone()["n"] == 0:
            _seed(conn)


# -- Lesen ----------------------------------------------------------------

def _karte_aus_row(row: sqlite3.Row) -> Karte:
    return Karte(
        id=row["id"],
        board_id=row["board_id"],
        spalte=row["spalte"],
        titel=row["titel"],
        schluessel=row["schluessel"],
        beschreibung=row["beschreibung"],
        labels=json.loads(row["labels"]),
        prioritaet=row["prioritaet"],
        checkliste=json.loads(row["checkliste"]),
        kommentare=json.loads(row["kommentare"]),
        cover=row["cover"],
        reihenfolge=row["reihenfolge"],
        start=row["start"],
        faellig=row["faellig"],
        zustaendig=row["zustaendig"],
        erstellt_am=row["erstellt_am"],
        bewegt_am=row["bewegt_am"],
        schaetzung_min=row["schaetzung_min"],
        erfasst_sek=row["erfasst_sek"],
        laeuft_seit=row["laeuft_seit"],
    )


def _spalten(conn: sqlite3.Connection, board_id: str) -> list[Spalte]:
    rows = conn.execute(
        "SELECT * FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)
    ).fetchall()
    return [Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"]) for r in rows]


def liste_mappen() -> list[Projektmappe]:
    with _verb() as conn:
        rows = conn.execute("SELECT * FROM mappe ORDER BY titel").fetchall()
    return [Projektmappe(**dict(r)) for r in rows]


def liste_boards(mappe_id: str) -> list[Board]:
    with _verb() as conn:
        rows = conn.execute("SELECT * FROM board WHERE mappe_id = ? ORDER BY titel", (mappe_id,)).fetchall()
        return [
            Board(id=r["id"], mappe_id=r["mappe_id"], titel=r["titel"], kuerzel=r["kuerzel"], spalten=_spalten(conn, r["id"]))
            for r in rows
        ]


def board_detail(board_id: str) -> BoardDetail | None:
    with _verb() as conn:
        b = conn.execute("SELECT * FROM board WHERE id = ?", (board_id,)).fetchone()
        if b is None:
            return None
        spalten = _spalten(conn, board_id)
        rows = conn.execute("SELECT * FROM karte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)).fetchall()
    return BoardDetail(
        id=b["id"], mappe_id=b["mappe_id"], titel=b["titel"], kuerzel=b["kuerzel"],
        spalten=spalten, karten=[_karte_aus_row(r) for r in rows],
    )


def hole_karte(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM karte WHERE id = ?", (karte_id,)).fetchone()
    return _karte_aus_row(row) if row else None


def hole_spalte(spalte_id: str) -> Spalte | None:
    with _verb() as conn:
        r = conn.execute("SELECT * FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
    return Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"]) if r else None


# -- Karten schreiben -----------------------------------------------------

def _naechste_reihenfolge(conn: sqlite3.Connection, board_id: str, spalte: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(reihenfolge), -1) AS m FROM karte WHERE board_id = ? AND spalte = ?",
        (board_id, spalte),
    ).fetchone()
    return int(row["m"]) + 1


def _kompaktiere(conn: sqlite3.Connection, board_id: str, spalte: str) -> None:
    rows = conn.execute(
        "SELECT id FROM karte WHERE board_id = ? AND spalte = ? ORDER BY reihenfolge, id", (board_id, spalte)
    ).fetchall()
    for index, r in enumerate(rows):
        conn.execute("UPDATE karte SET reihenfolge = ? WHERE id = ?", (index, r["id"]))


def erstelle_karte(
    karte_id: str, board_id: str, spalte: str, titel: str,
    beschreibung: str | None, labels: list[str], prioritaet: str | None,
    cover: str | None, start: str | None, faellig: str | None, zustaendig: str | None,
) -> Karte:
    with _verb() as conn:
        b = conn.execute("SELECT kuerzel, laufnummer FROM board WHERE id = ?", (board_id,)).fetchone()
        kuerzel = (b["kuerzel"] if b and b["kuerzel"] else "K")
        nummer = (b["laufnummer"] if b and b["laufnummer"] is not None else 0) + 1
        conn.execute("UPDATE board SET laufnummer = ? WHERE id = ?", (nummer, board_id))
        reihenfolge = _naechste_reihenfolge(conn, board_id, spalte)
        jetzt = _jetzt()
        conn.execute(
            "INSERT INTO karte (id, board_id, spalte, titel, schluessel, beschreibung, labels, prioritaet,"
            " checkliste, kommentare, cover, reihenfolge, start, faellig, zustaendig, erstellt_am, bewegt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', ?, ?, ?, ?, ?, ?, ?)",
            (karte_id, board_id, spalte, titel, f"{kuerzel}-{nummer}", beschreibung, json.dumps(labels),
             prioritaet, cover, reihenfolge, start, faellig, zustaendig, jetzt, jetzt),
        )
    karte = hole_karte(karte_id)
    assert karte is not None
    return karte


def verschiebe_karte(karte_id: str, ziel_spalte: str, ziel_reihenfolge: int) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT board_id, spalte FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        board_id, quelle = row["board_id"], row["spalte"]
        conn.execute(
            "UPDATE karte SET reihenfolge = reihenfolge + 1"
            " WHERE board_id = ? AND spalte = ? AND reihenfolge >= ? AND id != ?",
            (board_id, ziel_spalte, ziel_reihenfolge, karte_id),
        )
        conn.execute("UPDATE karte SET spalte = ?, reihenfolge = ? WHERE id = ?", (ziel_spalte, ziel_reihenfolge, karte_id))
        # Wechsel der Spalte setzt die Verweildauer (Card-Aging) zurueck.
        if quelle != ziel_spalte:
            conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (_jetzt(), karte_id))
        for spalte in {quelle, ziel_spalte}:
            _kompaktiere(conn, board_id, spalte)
    return hole_karte(karte_id)


def aktualisiere_karte(karte_id: str, aenderungen: dict) -> Karte | None:
    erlaubt = {"titel", "beschreibung", "labels", "prioritaet", "checkliste", "cover", "spalte", "reihenfolge", "start", "faellig", "zustaendig", "schaetzung_min"}
    felder = {k: v for k, v in aenderungen.items() if k in erlaubt}
    if not felder:
        return hole_karte(karte_id)
    for json_feld in ("labels", "checkliste"):
        if json_feld in felder:
            felder[json_feld] = json.dumps(felder[json_feld])
    zuweisung = ", ".join(f"{k} = ?" for k in felder)
    with _verb() as conn:
        conn.execute(f"UPDATE karte SET {zuweisung} WHERE id = ?", (*felder.values(), karte_id))
    return hole_karte(karte_id)


def kommentar_anhaengen(karte_id: str, autor: str, text: str, zeit: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT kommentare FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        liste = json.loads(row["kommentare"])
        liste.append({"autor": autor, "text": text, "zeit": zeit})
        conn.execute("UPDATE karte SET kommentare = ? WHERE id = ?", (json.dumps(liste, ensure_ascii=False), karte_id))
    return hole_karte(karte_id)


def loesche_karte(karte_id: str) -> None:
    with _verb() as conn:
        row = conn.execute("SELECT board_id, spalte FROM karte WHERE id = ?", (karte_id,)).fetchone()
        conn.execute("DELETE FROM karte WHERE id = ?", (karte_id,))
        if row is not None:
            _kompaktiere(conn, row["board_id"], row["spalte"])


# -- Zeiterfassung --------------------------------------------------------

def _mappe_fuer_board(conn: sqlite3.Connection, board_id: str | None) -> str | None:
    if not board_id:
        return None
    r = conn.execute("SELECT mappe_id FROM board WHERE id = ?", (board_id,)).fetchone()
    return r["mappe_id"] if r else None


def _recompute_erfasst(conn: sqlite3.Connection, karte_id: str) -> None:
    """erfasst_sek einer Karte = Summe ihrer Zeiteintraege (Single Source of Truth)."""
    r = conn.execute("SELECT COALESCE(SUM(sekunden), 0) AS s FROM zeiteintrag WHERE karte_id = ?", (karte_id,)).fetchone()
    conn.execute("UPDATE karte SET erfasst_sek = ? WHERE id = ?", (int(r["s"]), karte_id))


def _pause_intern(conn: sqlite3.Connection, karte_id: str) -> None:
    """Stoppt eine laufende Karte, schreibt einen Zeiteintrag und berechnet erfasst_sek neu."""
    row = conn.execute("SELECT laeuft_seit, board_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
    if row is None or not row["laeuft_seit"]:
        return
    start = row["laeuft_seit"]
    ende = _jetzt_genau()
    try:
        verstrichen = int((datetime.fromisoformat(ende) - datetime.fromisoformat(start)).total_seconds())
    except ValueError:
        verstrichen = 0
    conn.execute("UPDATE karte SET laeuft_seit = NULL WHERE id = ?", (karte_id,))
    if verstrichen >= 1:
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)",
            (f"z_{uuid4().hex[:8]}", karte_id, row["board_id"], _mappe_fuer_board(conn, row["board_id"]),
             start[:10], start, ende, verstrichen),
        )
    _recompute_erfasst(conn, karte_id)


def timer_start(karte_id: str) -> Karte | None:
    with _verb() as conn:
        if conn.execute("SELECT 1 FROM karte WHERE id = ?", (karte_id,)).fetchone() is None:
            return None
        # Nur eine Karte darf gleichzeitig laufen -> alle anderen pausieren.
        for r in conn.execute("SELECT id FROM karte WHERE laeuft_seit IS NOT NULL").fetchall():
            _pause_intern(conn, r["id"])
        conn.execute("UPDATE karte SET laeuft_seit = ? WHERE id = ?", (_jetzt_genau(), karte_id))
    return hole_karte(karte_id)


def timer_pause(karte_id: str) -> Karte | None:
    with _verb() as conn:
        if conn.execute("SELECT 1 FROM karte WHERE id = ?", (karte_id,)).fetchone() is None:
            return None
        _pause_intern(conn, karte_id)
    return hole_karte(karte_id)


def laufende_karte() -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM karte WHERE laeuft_seit IS NOT NULL LIMIT 1").fetchone()
    return _karte_aus_row(row) if row else None


# -- Zeiteintraege (Auswertung / Korrektur) -------------------------------

_ZE_SELECT = (
    "SELECT z.*, k.titel AS karte_titel, k.schluessel AS karte_schluessel "
    "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
)


def _zeiteintrag_aus_row(row: sqlite3.Row) -> Zeiteintrag:
    return Zeiteintrag(
        id=row["id"], karte_id=row["karte_id"], board_id=row["board_id"], mappe_id=row["mappe_id"],
        datum=row["datum"], start=row["start"], ende=row["ende"], sekunden=row["sekunden"],
        kommentar=row["kommentar"], manuell=bool(row["manuell"]),
        karte_titel=row["karte_titel"], karte_schluessel=row["karte_schluessel"],
    )


def zeiteintraege_range(von: str, bis: str) -> list[Zeiteintrag]:
    with _verb() as conn:
        rows = conn.execute(
            _ZE_SELECT + "WHERE z.datum >= ? AND z.datum <= ? ORDER BY z.datum, z.start, z.id",
            (von, bis),
        ).fetchall()
    return [_zeiteintrag_aus_row(r) for r in rows]


def hole_zeiteintrag(eintrag_id: str) -> Zeiteintrag | None:
    with _verb() as conn:
        r = conn.execute(_ZE_SELECT + "WHERE z.id = ?", (eintrag_id,)).fetchone()
    return _zeiteintrag_aus_row(r) if r else None


def erstelle_zeiteintrag(eintrag_id: str, karte_id: str, datum: str, sekunden: int, kommentar: str | None) -> Zeiteintrag | None:
    with _verb() as conn:
        b = conn.execute("SELECT board_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if b is None:
            return None
        board_id = b["board_id"]
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell)"
            " VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, 1)",
            (eintrag_id, karte_id, board_id, _mappe_fuer_board(conn, board_id), datum, max(0, sekunden), kommentar),
        )
        _recompute_erfasst(conn, karte_id)
    return hole_zeiteintrag(eintrag_id)


def aktualisiere_zeiteintrag(eintrag_id: str, aenderungen: dict) -> Zeiteintrag | None:
    with _verb() as conn:
        row = conn.execute("SELECT karte_id FROM zeiteintrag WHERE id = ?", (eintrag_id,)).fetchone()
        if row is None:
            return None
        felder = {k: v for k, v in aenderungen.items() if k in {"datum", "sekunden", "kommentar"}}
        if "sekunden" in felder and felder["sekunden"] is not None:
            felder["sekunden"] = max(0, int(felder["sekunden"]))
        if felder:
            zuweisung = ", ".join(f"{k} = ?" for k in felder)
            conn.execute(f"UPDATE zeiteintrag SET {zuweisung} WHERE id = ?", (*felder.values(), eintrag_id))
        _recompute_erfasst(conn, row["karte_id"])
    return hole_zeiteintrag(eintrag_id)


def loesche_zeiteintrag(eintrag_id: str) -> bool:
    with _verb() as conn:
        row = conn.execute("SELECT karte_id FROM zeiteintrag WHERE id = ?", (eintrag_id,)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM zeiteintrag WHERE id = ?", (eintrag_id,))
        _recompute_erfasst(conn, row["karte_id"])
    return True


# -- Spalten schreiben ----------------------------------------------------

def _kompaktiere_spalten(conn: sqlite3.Connection, board_id: str) -> None:
    rows = conn.execute("SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)).fetchall()
    for index, r in enumerate(rows):
        conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, r["id"]))


def erstelle_spalte(spalte_id: str, board_id: str, titel: str, wip_limit: int | None) -> Spalte:
    with _verb() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(reihenfolge), -1) AS m FROM spalte WHERE board_id = ?", (board_id,)
        ).fetchone()
        conn.execute(
            "INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge) VALUES (?, ?, ?, ?, ?)",
            (spalte_id, board_id, titel, wip_limit, int(row["m"]) + 1),
        )
    spalte = hole_spalte(spalte_id)
    assert spalte is not None
    return spalte


def aktualisiere_spalte(spalte_id: str, aenderungen: dict) -> Spalte | None:
    felder = {k: v for k, v in aenderungen.items() if k in {"titel", "wip_limit"}}
    if not felder:
        return hole_spalte(spalte_id)
    zuweisung = ", ".join(f"{k} = ?" for k in felder)
    with _verb() as conn:
        conn.execute(f"UPDATE spalte SET {zuweisung} WHERE id = ?", (*felder.values(), spalte_id))
    return hole_spalte(spalte_id)


def verschiebe_spalte(spalte_id: str, richtung: int) -> Spalte | None:
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return None
        ids = [x["id"] for x in conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (r["board_id"],)
        ).fetchall()]
        idx = ids.index(spalte_id)
        ziel = idx + richtung
        if 0 <= ziel < len(ids):
            ids[idx], ids[ziel] = ids[ziel], ids[idx]
            for index, sid in enumerate(ids):
                conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, sid))
    return hole_spalte(spalte_id)


def setze_spalten_reihenfolge(board_id: str, spalten_ids: list[str]) -> bool:
    with _verb() as conn:
        vorhandene = {x["id"] for x in conn.execute("SELECT id FROM spalte WHERE board_id = ?", (board_id,)).fetchall()}
        if vorhandene != set(spalten_ids):
            return False
        for index, sid in enumerate(spalten_ids):
            conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, sid))
    return True


def loesche_spalte(spalte_id: str) -> str:
    """Loescht eine Spalte samt ihrer Karten. 'ok' | 'letzte' | 'fehlt'."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return "fehlt"
        board_id = r["board_id"]
        anzahl = conn.execute("SELECT COUNT(*) AS n FROM spalte WHERE board_id = ?", (board_id,)).fetchone()["n"]
        if anzahl <= 1:
            return "letzte"
        conn.execute("DELETE FROM karte WHERE board_id = ? AND spalte = ?", (board_id, spalte_id))
        conn.execute("DELETE FROM spalte WHERE id = ?", (spalte_id,))
        _kompaktiere_spalten(conn, board_id)
    return "ok"


# -- Boards schreiben -----------------------------------------------------

def _kuerzel(titel: str) -> str:
    woerter = re.findall(r"[A-Za-z0-9]+", titel)
    if not woerter:
        return "B"
    if len(woerter) == 1:
        return woerter[0][:3].upper()
    return "".join(w[0] for w in woerter[:3]).upper()


def erstelle_board(board_id: str, mappe_id: str, titel: str) -> BoardDetail | None:
    with _verb() as conn:
        conn.execute(
            "INSERT INTO board (id, mappe_id, titel, kuerzel, laufnummer) VALUES (?, ?, ?, ?, 0)",
            (board_id, mappe_id, titel, _kuerzel(titel)),
        )
        for ordnung, titel_s in enumerate(["Offen", "In Arbeit", "Erledigt"]):
            conn.execute(
                "INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge) VALUES (?, ?, ?, ?, ?)",
                (f"s_{uuid4().hex[:8]}", board_id, titel_s, None, ordnung),
            )
    return board_detail(board_id)


def aktualisiere_board(board_id: str, titel: str) -> Board | None:
    with _verb() as conn:
        conn.execute("UPDATE board SET titel = ? WHERE id = ?", (titel, board_id))
        r = conn.execute("SELECT * FROM board WHERE id = ?", (board_id,)).fetchone()
        if r is None:
            return None
        spalten = _spalten(conn, board_id)
    return Board(id=r["id"], mappe_id=r["mappe_id"], titel=r["titel"], kuerzel=r["kuerzel"], spalten=spalten)


def loesche_board(board_id: str) -> None:
    with _verb() as conn:
        conn.execute("DELETE FROM karte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM spalte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM board WHERE id = ?", (board_id,))


# -- Seed -----------------------------------------------------------------

def _seed(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO mappe (id, titel, beschreibung) VALUES (?, ?, ?)",
                 ("m_r3", "Gerät R3", "Produktion und Abnahme des Geräts R3"))
    conn.execute("INSERT INTO board (id, mappe_id, titel, kuerzel, laufnummer) VALUES (?, ?, ?, ?, ?)",
                 ("b_prod", "m_r3", "Produktionsplanung", "R3", 131))
    for sid, titel, wip, ordnung in [
        ("s_backlog", "Backlog", None, 0),
        ("s_arbeit", "In Arbeit", 3, 1),
        ("s_pruefung", "Prüfung", None, 2),
        ("s_fertig", "Fertig", None, 3),
    ]:
        conn.execute("INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge) VALUES (?, ?, ?, ?, ?)",
                     (sid, "b_prod", titel, wip, ordnung))

    cl_flash = [
        {"text": "JTAG-Adapter einrichten", "erledigt": True},
        {"text": "Flash-Skript schreiben", "erledigt": True},
        {"text": "Prüfsumme verifizieren", "erledigt": True},
        {"text": "Protokoll-Anbindung", "erledigt": False},
        {"text": "Fehlerfall behandeln", "erledigt": False},
    ]
    km_flash = [{"autor": "Markus L.", "text": "Adapter läuft, Skript flasht sauber.", "zeit": "2026-06-18T09:40"}]

    erstellt = "2026-06-01T09:00"
    karten = [
        # id, schluessel, spalte, titel, beschreibung, labels, prio, checkliste, kommentare, cover, ordnung, start, faellig, zustaendig, bewegt_am
        ("k1", "R3-118", "s_backlog", "Gehäuse-Toleranzen prüfen",
         "Spaltmaße an Front und Deckel gegen Zeichnung Rev. C messen.", ["Mechanik"], "mittel", [], [], None, 0, None, "2026-06-24", "AK", "2026-06-17"),
        ("k2", "R3-121", "s_backlog", "Stückliste v2 importieren",
         None, ["Doku"], "niedrig", [], [{"autor": "Tina B.", "text": "Quelle ist die neue CSV.", "zeit": "2026-06-17T14:10"}], None, 1, None, None, None, "2026-06-09"),
        ("k3", "R3-130", "s_arbeit", "Firmware-Flash-Routine",
         "Flash-Routine über JTAG automatisieren und Ergebnis ins Protokoll schreiben.", ["Software"], "hoch", cl_flash, km_flash, "#1565C0", 0, "2026-06-15", "2026-06-20", "AK", "2026-06-16"),
        ("k4", "R3-131", "s_arbeit", "Bedienpanel-Layout",
         "Anordnung der Bedienelemente final abstimmen.", ["Design", "Blocker"], "hoch", [], [], None, 1, None, "2026-06-10", "TB", "2026-06-06"),
        ("k5", "R3-119", "s_arbeit", "Montagevorrichtung bauen",
         None, ["Mechanik"], "mittel", [], [], None, 2, None, None, "ML", "2026-06-13"),
        ("k6", "R3-126", "s_pruefung", "Sensorkalibrierung",
         "Kalibrierkurve aufnehmen und gegen Referenz prüfen.", ["Software"],
         "mittel", [{"text": "Referenz messen", "erledigt": True}, {"text": "Kurve aufnehmen", "erledigt": True}, {"text": "Abweichung dokumentieren", "erledigt": True}], [], None, 0, None, None, "AK", "2026-06-18"),
        ("k7", "R3-100", "s_fertig", "Lastenheft freigeben",
         None, ["Doku"], None, [], [], None, 0, None, None, None, "2026-06-14"),
    ]
    for kid, schluessel, spalte, titel, beschr, labels, prio, cl, km, cover, ordnung, start, faellig, zust, bewegt in karten:
        conn.execute(
            "INSERT INTO karte (id, board_id, spalte, titel, schluessel, beschreibung, labels, prioritaet,"
            " checkliste, kommentare, cover, reihenfolge, start, faellig, zustaendig, erstellt_am, bewegt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (kid, "b_prod", spalte, titel, schluessel, beschr, json.dumps(labels), prio,
             json.dumps(cl, ensure_ascii=False), json.dumps(km, ensure_ascii=False), cover, ordnung, start, faellig, zust, erstellt, bewegt),
        )

    # Beispiel-Zeiteintraege (zwei Arbeitswochen) fuer Auswertung/Heatmap/Kalender.
    eintraege = [
        # karte, datum, sekunden, kommentar
        ("k4", "2026-06-09", 7200, "Erste Layout-Entwuerfe"),
        ("k5", "2026-06-10", 5400, "Vorrichtung skizziert"),
        ("k4", "2026-06-11", 9000, "Bedienelemente angeordnet"),
        ("k6", "2026-06-12", 3600, "Referenz vermessen"),
        ("k3", "2026-06-15", 5400, "JTAG-Adapter eingerichtet"),
        ("k3", "2026-06-16", 7200, "Flash-Skript geschrieben"),
        ("k6", "2026-06-16", 4500, "Kalibrierkurve aufgenommen"),
        ("k1", "2026-06-17", 2700, "Toleranzen gemessen"),
        ("k3", "2026-06-18", 3600, "Pruefsumme verifiziert"),
        ("k1", "2026-06-19", 1800, "Nacharbeit Gehaeuse"),
    ]
    betroffen = set()
    for kid, datum, sek, komm in eintraege:
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell)"
            " VALUES (?, ?, 'b_prod', 'm_r3', ?, ?, NULL, ?, ?, 0)",
            (f"z_{uuid4().hex[:8]}", kid, datum, f"{datum}T09:00:00", sek, komm),
        )
        betroffen.add(kid)
    for kid in betroffen:
        _recompute_erfasst(conn, kid)
    # Schaetzungen (Soll) fuer einige Karten, damit Soll/Ist gleich aussagekraeftig ist.
    for kid, mins in [("k3", 300), ("k4", 240), ("k6", 180), ("k1", 120), ("k5", 150)]:
        conn.execute("UPDATE karte SET schaetzung_min = ? WHERE id = ?", (mins, kid))
