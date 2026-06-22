"""SQLite-Persistenz des Kanban-Moduls.

Nutzt die generische Verbindung des Kerns. Schema und Seed gehören dem Modul.
Reihenfolge-Werte werden bei jedem Verschieben lückenlos neu vergeben.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, time as _zeit, timedelta
from uuid import uuid4

from app.db import verbindung


def _jetzt() -> str:
    return datetime.now().isoformat(timespec="minutes")


def _jetzt_genau() -> str:
    return datetime.now().isoformat(timespec="seconds")

from .models import Board, BoardDetail, Dokument, Karte, Projektmappe, Spalte, Zeiteintrag

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
    reihenfolge INTEGER NOT NULL DEFAULT 0,
    erledigt INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS karte (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    spalte TEXT NOT NULL,
    titel TEXT NOT NULL,
    schluessel TEXT,
    beschreibung TEXT,
    notizen TEXT,
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
    laeuft_seit TEXT,
    serie_id TEXT,
    serie_datum TEXT,
    transkript_id TEXT,
    transkript_name TEXT
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
CREATE TABLE IF NOT EXISTS dokument (
    id TEXT PRIMARY KEY,
    kontext TEXT NOT NULL,
    kontext_id TEXT NOT NULL,
    titel TEXT NOT NULL,
    inhalt TEXT NOT NULL DEFAULT '',
    erstellt_am TEXT,
    bewegt_am TEXT
);
"""


def _verb() -> sqlite3.Connection:
    return verbindung()


def _migriere(conn: sqlite3.Connection) -> None:
    """Sanfte Schema-Migrationen für bestehende Datenbanken."""
    spalten = {r["name"] for r in conn.execute("PRAGMA table_info(spalte)").fetchall()}
    if "erledigt" not in spalten:
        conn.execute("ALTER TABLE spalte ADD COLUMN erledigt INTEGER NOT NULL DEFAULT 0")
    kspalten = {r["name"] for r in conn.execute("PRAGMA table_info(karte)").fetchall()}
    if "serie_id" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN serie_id TEXT")
    if "serie_datum" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN serie_datum TEXT")
    if "notizen" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN notizen TEXT")
    if "transkript_id" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN transkript_id TEXT")
    if "transkript_name" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN transkript_name TEXT")


def init_db() -> None:
    with _verb() as conn:
        conn.executescript(SCHEMA)
        _migriere(conn)
        # Serien-Vorbuchung auf DB-Ebene idempotent: hoechstens eine Karte je
        # (Serie, Datum). Defensiv, damit etwaige Altdaten-Duplikate den Start nicht
        # blockieren (dann greift der Index eben erst nach Bereinigung).
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_karte_serie "
                "ON karte(serie_id, serie_datum) WHERE serie_id IS NOT NULL"
            )
        except Exception:
            pass
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
        notizen=row["notizen"],
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
        transkript_id=row["transkript_id"],
        transkript_name=row["transkript_name"],
    )


def _spalten(conn: sqlite3.Connection, board_id: str) -> list[Spalte]:
    rows = conn.execute(
        "SELECT * FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)
    ).fetchall()
    return [Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"], erledigt=bool(r["erledigt"])) for r in rows]


def liste_mappen() -> list[Projektmappe]:
    with _verb() as conn:
        rows = conn.execute("SELECT * FROM mappe ORDER BY titel").fetchall()
    return [Projektmappe(**dict(r)) for r in rows]


def zaehle_mappen() -> int:
    with _verb() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM mappe").fetchone()[0])


def erstelle_mappe(mappe_id: str, titel: str, beschreibung: str | None = None) -> Projektmappe:
    """Legt eine Projektmappe an und gibt ihr direkt ein erstes nutzbares Board mit."""
    with _verb() as conn:
        conn.execute("INSERT INTO mappe (id, titel, beschreibung) VALUES (?, ?, ?)",
                     (mappe_id, titel, beschreibung))
    erstelle_board(f"b_{uuid4().hex[:8]}", mappe_id, "Aufgaben")
    return Projektmappe(id=mappe_id, titel=titel, beschreibung=beschreibung)


def aktualisiere_mappe(mappe_id: str, felder: dict) -> Projektmappe | None:
    erlaubt = {k: v for k, v in felder.items() if k in ("titel", "beschreibung")}
    with _verb() as conn:
        if erlaubt:
            sql = ", ".join(f"{k} = ?" for k in erlaubt)
            conn.execute(f"UPDATE mappe SET {sql} WHERE id = ?", (*erlaubt.values(), mappe_id))
        r = conn.execute("SELECT * FROM mappe WHERE id = ?", (mappe_id,)).fetchone()
    return Projektmappe(**dict(r)) if r else None


def loesche_mappe(mappe_id: str) -> bool:
    """Loescht die Mappe samt aller Boards, Spalten, Karten und Zeiteintraege.

    Die letzte verbliebene Mappe bleibt erhalten, damit die Anwendung immer eine
    nutzbare Mappe hat.
    """
    with _verb() as conn:
        if conn.execute("SELECT COUNT(*) FROM mappe").fetchone()[0] <= 1:
            return False
        board_ids = [r[0] for r in conn.execute("SELECT id FROM board WHERE mappe_id = ?", (mappe_id,)).fetchall()]
        for bid in board_ids:
            karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (bid,)).fetchall()]
            for kid in karten:
                conn.execute("DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id = ?", (kid,))
            conn.execute("DELETE FROM karte WHERE board_id = ?", (bid,))
            conn.execute("DELETE FROM spalte WHERE board_id = ?", (bid,))
        conn.execute("DELETE FROM dokument WHERE kontext = 'mappe' AND kontext_id = ?", (mappe_id,))
        conn.execute("DELETE FROM zeiteintrag WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM board WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM mappe WHERE id = ?", (mappe_id,))
    return True


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
    return Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"], erledigt=bool(r["erledigt"])) if r else None


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
        # Wechsel der Spalte setzt die Verweildauer (Card-Aging) zurück.
        if quelle != ziel_spalte:
            conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (_jetzt(), karte_id))
        for spalte in {quelle, ziel_spalte}:
            _kompaktiere(conn, board_id, spalte)
    return hole_karte(karte_id)


def aktualisiere_karte(karte_id: str, aenderungen: dict) -> Karte | None:
    erlaubt = {"titel", "beschreibung", "notizen", "labels", "prioritaet", "checkliste", "cover", "spalte", "reihenfolge", "start", "faellig", "zustaendig", "schaetzung_min", "transkript_id", "transkript_name"}
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
        conn.execute("DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id = ?", (karte_id,))
        # Zeiteintraege der Karte mitloeschen, sonst verfaelschen Waisen die Ist-Summen.
        conn.execute("DELETE FROM zeiteintrag WHERE karte_id = ?", (karte_id,))
        if row is not None:
            _kompaktiere(conn, row["board_id"], row["spalte"])


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
    erlaubt = {k: v for k, v in felder.items() if k in ("titel", "inhalt")}
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


# -- Zeiterfassung --------------------------------------------------------

def _mappe_fuer_board(conn: sqlite3.Connection, board_id: str | None) -> str | None:
    if not board_id:
        return None
    r = conn.execute("SELECT mappe_id FROM board WHERE id = ?", (board_id,)).fetchone()
    return r["mappe_id"] if r else None


def _recompute_erfasst(conn: sqlite3.Connection, karte_id: str) -> None:
    """erfasst_sek einer Karte = Summe ihrer Zeiteinträge (Single Source of Truth)."""
    r = conn.execute("SELECT COALESCE(SUM(sekunden), 0) AS s FROM zeiteintrag WHERE karte_id = ?", (karte_id,)).fetchone()
    conn.execute("UPDATE karte SET erfasst_sek = ? WHERE id = ?", (int(r["s"]), karte_id))


_KORREKTUR = "Manuelle Korrektur"


def setze_erfasst(karte_id: str, ziel_sek: int) -> Karte | None:
    """Setzt die erfasste Gesamtzeit exakt - ueber genau eine Korrektur-Position.

    Timer- und Nachtrags-Eintraege bleiben unangetastet; die Differenz zum Ziel
    landet in einem einzigen manuellen Eintrag (idempotent bei erneutem Setzen,
    wird bei Differenz 0 wieder entfernt).
    """
    ziel = max(0, int(ziel_sek))
    with _verb() as conn:
        row = conn.execute("SELECT board_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        rest = conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) AS s FROM zeiteintrag"
            " WHERE karte_id = ? AND NOT (manuell = 1 AND kommentar = ?)",
            (karte_id, _KORREKTUR),
        ).fetchone()["s"]
        korr = ziel - int(rest)
        vorhanden = conn.execute(
            "SELECT id FROM zeiteintrag WHERE karte_id = ? AND manuell = 1 AND kommentar = ? LIMIT 1",
            (karte_id, _KORREKTUR),
        ).fetchone()
        if korr == 0:
            if vorhanden:
                conn.execute("DELETE FROM zeiteintrag WHERE id = ?", (vorhanden["id"],))
        elif vorhanden:
            conn.execute(
                "UPDATE zeiteintrag SET sekunden = ?, datum = ? WHERE id = ?",
                (korr, _jetzt_genau()[:10], vorhanden["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, sekunden, kommentar, manuell)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                (f"z_{uuid4().hex[:8]}", karte_id, row["board_id"], _mappe_fuer_board(conn, row["board_id"]),
                 _jetzt_genau()[:10], korr, _KORREKTUR),
            )
        _recompute_erfasst(conn, karte_id)
    return hole_karte(karte_id)


def _tagessegmente(start_iso: str, ende_iso: str) -> list[tuple[str, str, str, int]]:
    """Zerlegt ein Start-Ende-Intervall in (datum, start, ende, sekunden) je Kalendertag,
    damit ein ueber Mitternacht laufender Timer die Zeit dem richtigen Tag gutschreibt."""
    a = datetime.fromisoformat(start_iso)
    b = datetime.fromisoformat(ende_iso)
    segs: list[tuple[str, str, str, int]] = []
    cur = a
    while cur < b:
        naechste_mitternacht = datetime.combine(cur.date() + timedelta(days=1), _zeit.min)
        seg_ende = min(b, naechste_mitternacht)
        sek = int((seg_ende - cur).total_seconds())
        if sek >= 1:
            segs.append((cur.date().isoformat(), cur.isoformat(timespec="seconds"), seg_ende.isoformat(timespec="seconds"), sek))
        cur = seg_ende
    return segs


def _pause_intern(conn: sqlite3.Connection, karte_id: str) -> None:
    """Stoppt eine laufende Karte, schreibt einen Zeiteintrag und berechnet erfasst_sek neu."""
    row = conn.execute("SELECT laeuft_seit, board_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
    if row is None or not row["laeuft_seit"]:
        return
    start = row["laeuft_seit"]
    ende = _jetzt_genau()
    conn.execute("UPDATE karte SET laeuft_seit = NULL WHERE id = ?", (karte_id,))
    try:
        segmente = _tagessegmente(start, ende)
    except ValueError:
        segmente = []
    mappe_id = _mappe_fuer_board(conn, row["board_id"])
    for datum, seg_start, seg_ende, sek in segmente:
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)",
            (f"z_{uuid4().hex[:8]}", karte_id, row["board_id"], mappe_id, datum, seg_start, seg_ende, sek),
        )
    _recompute_erfasst(conn, karte_id)


def timer_start(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT start FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        # Nur eine Karte darf gleichzeitig laufen -> alle anderen pausieren.
        for r in conn.execute("SELECT id FROM karte WHERE laeuft_seit IS NOT NULL").fetchall():
            _pause_intern(conn, r["id"])
        jetzt = _jetzt_genau()
        # Ohne gesetztes Start-Datum gilt der erste Timer-Start als Arbeitsbeginn;
        # einmal gesetzt wird der Wert beim Fortsetzen nie wieder ueberschrieben.
        if not row["start"]:
            conn.execute("UPDATE karte SET laeuft_seit = ?, start = ? WHERE id = ?", (jetzt, jetzt[:10], karte_id))
        else:
            conn.execute("UPDATE karte SET laeuft_seit = ? WHERE id = ?", (jetzt, karte_id))
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


# -- Zeiteinträge (Auswertung / Korrektur) -------------------------------

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


def setze_erledigt_spalte(spalte_id: str) -> Spalte | None:
    """Markiert eine Spalte als Erledigt-Spalte des Boards (genau eine pro Board)."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return None
        conn.execute("UPDATE spalte SET erledigt = 0 WHERE board_id = ?", (r["board_id"],))
        conn.execute("UPDATE spalte SET erledigt = 1 WHERE id = ?", (spalte_id,))
    return hole_spalte(spalte_id)


def done_spalte_id(board_id: str) -> str | None:
    """Id der als Erledigt markierten Spalte, sonst die letzte Spalte als Rückfall."""
    with _verb() as conn:
        r = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? AND erledigt = 1 ORDER BY reihenfolge LIMIT 1",
            (board_id,),
        ).fetchone()
        if r:
            return r["id"]
        letzte = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge DESC, id DESC LIMIT 1",
            (board_id,),
        ).fetchone()
    return letzte["id"] if letzte else None


def finde_karte_per_text(text: str, board_id: str | None = None) -> Karte | None:
    """Löst eine Karte über ihren Schlüssel (z.B. R3-130) oder per Titel auf.

    Reihenfolge: exakter Schlüssel, dann Titel-Gleichheit, dann Titel enthält.
    Ohne board_id wird über alle Boards gesucht.
    """
    suchtext = (text or "").strip()
    if not suchtext:
        return None
    bedingung = " AND board_id = ?" if board_id else ""
    args_basis: tuple = (board_id,) if board_id else ()
    with _verb() as conn:
        row = conn.execute(
            f"SELECT * FROM karte WHERE LOWER(schluessel) = LOWER(?){bedingung} LIMIT 1",
            (suchtext, *args_basis),
        ).fetchone()
        if row is None:
            row = conn.execute(
                f"SELECT * FROM karte WHERE LOWER(titel) = LOWER(?){bedingung} ORDER BY bewegt_am DESC LIMIT 1",
                (suchtext, *args_basis),
            ).fetchone()
        if row is None:
            row = conn.execute(
                f"SELECT * FROM karte WHERE titel LIKE ?{bedingung} ORDER BY bewegt_am DESC LIMIT 1",
                (f"%{suchtext}%", *args_basis),
            ).fetchone()
    return _karte_aus_row(row) if row else None


def was_steht_an(heute: str) -> dict:
    """Handlungsorientierte Übersicht: überfällig, heute, diese Woche, laufend, liegengeblieben.

    Wiederkehrende Termine erscheinen automatisch über ihre Fälligkeit.
    """
    from datetime import date, timedelta

    heute_d = date.fromisoformat(heute)
    woche = (heute_d + timedelta(days=7)).isoformat()
    alt = (heute_d - timedelta(days=7)).isoformat()
    with _verb() as conn:
        done = {r["board_id"]: r["id"] for r in conn.execute("SELECT board_id, id FROM spalte WHERE erledigt = 1").fetchall()}
        rows = conn.execute(
            "SELECT id, board_id, spalte, schluessel, titel, faellig, laeuft_seit, bewegt_am FROM karte"
        ).fetchall()

    def offen(r) -> bool:
        return done.get(r["board_id"]) != r["spalte"]

    def eintrag(r) -> dict:
        return {"id": r["id"], "board_id": r["board_id"], "schluessel": r["schluessel"],
                "titel": r["titel"], "faellig": r["faellig"]}

    ueberfaellig, heute_f, diese_woche, laufend, liegengeblieben = [], [], [], [], []
    faellig_ids: set[str] = set()
    for r in rows:
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
    return {
        "datum": heute, "ueberfaellig": ueberfaellig, "heute": heute_f,
        "diese_woche": diese_woche, "laufend": laufend, "liegengeblieben": liegengeblieben,
    }


def markiere_serie(karte_id: str, serie_id: str, datum: str) -> None:
    """Verknüpft eine Karte mit einer Serie und ihrem Termin-Datum (für Vorbuchung/Dedup)."""
    with _verb() as conn:
        conn.execute("UPDATE karte SET serie_id = ?, serie_datum = ? WHERE id = ?", (serie_id, datum, karte_id))


def serien_instanz_existiert(serie_id: str, datum: str) -> bool:
    with _verb() as conn:
        r = conn.execute(
            "SELECT 1 FROM karte WHERE serie_id = ? AND serie_datum = ? LIMIT 1", (serie_id, datum)
        ).fetchone()
    return r is not None


def letztes_serie_datum(serie_id: str) -> str | None:
    """Spätestes bereits materialisiertes Datum einer Serie (für Backfill verpasster Tage)."""
    with _verb() as conn:
        r = conn.execute(
            "SELECT MAX(serie_datum) AS m FROM karte WHERE serie_id = ?", (serie_id,)
        ).fetchone()
    return r["m"] if r and r["m"] else None


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
    """Löscht eine Spalte samt ihrer Karten. 'ok' | 'letzte' | 'fehlt'."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return "fehlt"
        board_id = r["board_id"]
        anzahl = conn.execute("SELECT COUNT(*) AS n FROM spalte WHERE board_id = ?", (board_id,)).fetchone()["n"]
        if anzahl <= 1:
            return "letzte"
        conn.execute(
            "DELETE FROM zeiteintrag WHERE karte_id IN (SELECT id FROM karte WHERE board_id = ? AND spalte = ?)",
            (board_id, spalte_id),
        )
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
                "INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge, erledigt) VALUES (?, ?, ?, ?, ?, ?)",
                (f"s_{uuid4().hex[:8]}", board_id, titel_s, None, ordnung, 1 if titel_s == "Erledigt" else 0),
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
        karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (board_id,)).fetchall()]
        for kid in karten:
            conn.execute("DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id = ?", (kid,))
        conn.execute("DELETE FROM zeiteintrag WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM karte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM spalte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM board WHERE id = ?", (board_id,))


# -- Seed -----------------------------------------------------------------

def _seed(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO mappe (id, titel, beschreibung) VALUES (?, ?, ?)",
                 ("m_r3", "Gerät R3", "Produktion und Abnahme des Geräts R3"))
    conn.execute("INSERT INTO board (id, mappe_id, titel, kuerzel, laufnummer) VALUES (?, ?, ?, ?, ?)",
                 ("b_prod", "m_r3", "Produktionsplanung", "R3", 131))
    for sid, titel, wip, ordnung, erledigt in [
        ("s_backlog", "Backlog", None, 0, 0),
        ("s_arbeit", "In Arbeit", 3, 1, 0),
        ("s_pruefung", "Prüfung", None, 2, 0),
        ("s_fertig", "Fertig", None, 3, 1),
    ]:
        conn.execute("INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge, erledigt) VALUES (?, ?, ?, ?, ?, ?)",
                     (sid, "b_prod", titel, wip, ordnung, erledigt))

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

    # Beispiel-Zeiteinträge (zwei Arbeitswochen) für Auswertung/Heatmap/Kalender.
    eintraege = [
        # karte, datum, sekunden, kommentar
        ("k4", "2026-06-09", 7200, "Erste Layout-Entwürfe"),
        ("k5", "2026-06-10", 5400, "Vorrichtung skizziert"),
        ("k4", "2026-06-11", 9000, "Bedienelemente angeordnet"),
        ("k6", "2026-06-12", 3600, "Referenz vermessen"),
        ("k3", "2026-06-15", 5400, "JTAG-Adapter eingerichtet"),
        ("k3", "2026-06-16", 7200, "Flash-Skript geschrieben"),
        ("k6", "2026-06-16", 4500, "Kalibrierkurve aufgenommen"),
        ("k1", "2026-06-17", 2700, "Toleranzen gemessen"),
        ("k3", "2026-06-18", 3600, "Prüfsumme verifiziert"),
        ("k1", "2026-06-19", 1800, "Nacharbeit Gehäuse"),
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
    # Schätzungen (Soll) für einige Karten, damit Soll/Ist gleich aussagekräftig ist.
    for kid, mins in [("k3", 300), ("k4", 240), ("k6", 180), ("k1", 120), ("k5", 150)]:
        conn.execute("UPDATE karte SET schaetzung_min = ? WHERE id = ?", (mins, kid))
