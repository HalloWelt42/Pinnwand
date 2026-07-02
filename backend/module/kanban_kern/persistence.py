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

from .models import (
    Board,
    BoardDetail,
    Dokument,
    DokumentUpdate,
    GruppenMitglied,
    HeuteUebersicht,
    Karte,
    KarteUpdate,
    LabelDefinition,
    LabelUpdate,
    MappeUpdate,
    ProjektAufwand,
    ProjektBoardAufwand,
    ProjektDetail,
    ProjektPersonAufwand,
    Projektmappe,
    Spalte,
    SpalteUpdate,
    Zeiteintrag,
    ZeiteintragUpdate,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS mappe (
    id TEXT PRIMARY KEY,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    owner TEXT,
    budget_min INTEGER,
    status TEXT NOT NULL DEFAULT 'aktiv'
);
CREATE TABLE IF NOT EXISTS mappe_mitglied (
    mappe_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    PRIMARY KEY (mappe_id, person_id)
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
    transkript_name TEXT,
    typ TEXT NOT NULL DEFAULT 'arbeit',
    gruppe_id TEXT
);
CREATE TABLE IF NOT EXISTS kartengruppe (
    id TEXT PRIMARY KEY,
    zeit_geteilt INTEGER NOT NULL DEFAULT 1,
    erstellt_am TEXT
);
CREATE TABLE IF NOT EXISTS label_definition (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    familie TEXT NOT NULL,
    erstellt_am TEXT
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
    manuell INTEGER NOT NULL DEFAULT 0,
    kuerzel TEXT
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
CREATE TABLE IF NOT EXISTS kanban_einstellung (
    schluessel TEXT PRIMARY KEY,
    wert TEXT NOT NULL
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
    if "typ" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN typ TEXT NOT NULL DEFAULT 'arbeit'")
    if "gruppe_id" not in kspalten:
        conn.execute("ALTER TABLE karte ADD COLUMN gruppe_id TEXT")
    # Person am Zeiteintrag (Snapshot beim Buchen): macht die Zuordnung historiefest -
    # Karten-Uebergaben oder Umbenennungen verschieben Alt-Zeiten nicht mehr.
    zspalten = {r["name"] for r in conn.execute("PRAGMA table_info(zeiteintrag)").fetchall()}
    if "kuerzel" not in zspalten:
        conn.execute("ALTER TABLE zeiteintrag ADD COLUMN kuerzel TEXT")
    conn.execute(
        "UPDATE zeiteintrag SET kuerzel = ("
        " SELECT k.zustaendig FROM karte k WHERE k.id = zeiteintrag.karte_id)"
        " WHERE kuerzel IS NULL"
    )
    # Mappe = Projekt: Projektfelder fuer den Aufwands-Ueberblick.
    mspalten = {r["name"] for r in conn.execute("PRAGMA table_info(mappe)").fetchall()}
    if "owner" not in mspalten:
        conn.execute("ALTER TABLE mappe ADD COLUMN owner TEXT")
    if "budget_min" not in mspalten:
        conn.execute("ALTER TABLE mappe ADD COLUMN budget_min INTEGER")
    if "status" not in mspalten:
        conn.execute("ALTER TABLE mappe ADD COLUMN status TEXT NOT NULL DEFAULT 'aktiv'")
    # Defensiver Backfill: alte Zeiteintraege ohne mappe_id ueber ihr Board zuordnen,
    # damit die Ist-Summe je Projekt vollstaendig ist (idempotent).
    conn.execute(
        "UPDATE zeiteintrag SET mappe_id = ("
        " SELECT b.mappe_id FROM board b WHERE b.id = zeiteintrag.board_id)"
        " WHERE mappe_id IS NULL AND board_id IS NOT NULL"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kartengruppe ("
        "id TEXT PRIMARY KEY, zeit_geteilt INTEGER NOT NULL DEFAULT 1, erstellt_am TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS label_definition ("
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, familie TEXT NOT NULL, erstellt_am TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kanban_einstellung ("
        "schluessel TEXT PRIMARY KEY, wert TEXT NOT NULL)"
    )
    # Altdaten aufraeumen: bestehende Start/Stopp-Fragmente je Karte+Tag zusammenfassen
    # (idempotent, einmalige Roh-Sicherung). Neue Sitzungen fasst _pause_intern direkt zusammen.
    _konsolidiere_auto_zeiten(conn)


def init_db() -> None:
    with _verb() as conn:
        conn.executescript(SCHEMA)
        _migriere(conn)
        # Indizes auf die heissen Pfade (Zeit-Summen, Board-Rendering, Fenster).
        for idx in (
            "CREATE INDEX IF NOT EXISTS ix_zeiteintrag_karte ON zeiteintrag(karte_id)",
            "CREATE INDEX IF NOT EXISTS ix_zeiteintrag_mappe_datum ON zeiteintrag(mappe_id, datum)",
            "CREATE INDEX IF NOT EXISTS ix_zeiteintrag_datum ON zeiteintrag(datum)",
            "CREATE INDEX IF NOT EXISTS ix_karte_board_spalte ON karte(board_id, spalte)",
            "CREATE INDEX IF NOT EXISTS ix_karte_serie ON karte(serie_id)",
        ):
            conn.execute(idx)
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
        typ=row["typ"] if "typ" in row.keys() else "arbeit",
        gruppe_id=row["gruppe_id"] if "gruppe_id" in row.keys() else None,
    )


def _spalten(conn: sqlite3.Connection, board_id: str) -> list[Spalte]:
    rows = conn.execute(
        "SELECT * FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)
    ).fetchall()
    return [Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"], erledigt=bool(r["erledigt"])) for r in rows]


def liste_mappen(person_id: str | None = None, alle: bool = True) -> list[Projektmappe]:
    """Projektmappen. alle=True (Admin/offener Modus): alle. Sonst nur Mappen, die
    entweder KEINE Mitglieder haben (geteilt) ODER in denen die Person Mitglied ist."""
    with _verb() as conn:
        if alle or not person_id:
            rows = conn.execute("SELECT * FROM mappe ORDER BY titel").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mappe m WHERE"
                " NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
                " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)"
                " ORDER BY titel",
                (person_id,),
            ).fetchall()
    return [Projektmappe(**dict(r)) for r in rows]


# -- Projekt-Mitgliedschaft (Sichtbarkeit von Mappen/Projekten je Person) --------
# Regel: eine Mappe OHNE Mitglieder ist fuer alle sichtbar (geteilt, rueckwaerts-
# kompatibel). Sobald Mitglieder hinterlegt sind, sehen nur diese (plus Admin) sie.

def mappe_mitglieder(mappe_id: str) -> list[str]:
    with _verb() as conn:
        rows = conn.execute("SELECT person_id FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,)).fetchall()
    return [r[0] for r in rows]


def mappe_sichtbar_fuer(mappe_id: str, person_id: str | None) -> bool:
    with _verb() as conn:
        anzahl = conn.execute("SELECT COUNT(*) FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,)).fetchone()[0]
        if anzahl == 0:
            return True
        if not person_id:
            return False
        treffer = conn.execute(
            "SELECT 1 FROM mappe_mitglied WHERE mappe_id = ? AND person_id = ?", (mappe_id, person_id)
        ).fetchone()
    return treffer is not None


def setze_mappe_mitglied(mappe_id: str, person_id: str) -> None:
    with _verb() as conn:
        conn.execute("INSERT OR IGNORE INTO mappe_mitglied (mappe_id, person_id) VALUES (?, ?)", (mappe_id, person_id))


def entferne_mappe_mitglied(mappe_id: str, person_id: str) -> bool:
    with _verb() as conn:
        cur = conn.execute("DELETE FROM mappe_mitglied WHERE mappe_id = ? AND person_id = ?", (mappe_id, person_id))
    return cur.rowcount > 0


def gruppe_mappe_id(gruppe_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM karte k JOIN board b ON b.id = k.board_id WHERE k.gruppe_id = ? LIMIT 1",
            (gruppe_id,),
        ).fetchone()
    return r[0] if r else None


def karte_mappe_id(karte_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM karte k JOIN board b ON b.id = k.board_id WHERE k.id = ?", (karte_id,)
        ).fetchone()
    return r[0] if r else None


def spalte_mappe_id(spalte_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM spalte s JOIN board b ON b.id = s.board_id WHERE s.id = ?", (spalte_id,)
        ).fetchone()
    return r[0] if r else None


def sichtbare_mappen_ids(person_id: str | None) -> set[str]:
    """Alle Mappen, die diese Person sehen darf (memberlos = geteilt)."""
    with _verb() as conn:
        rows = conn.execute(
            "SELECT m.id FROM mappe m WHERE"
            " NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
            " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)",
            (person_id,),
        ).fetchall()
    return {r[0] for r in rows}


def board_mappe_id(board_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute("SELECT mappe_id FROM board WHERE id = ?", (board_id,)).fetchone()
    return r[0] if r else None


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
    erlaubt = {k: v for k, v in felder.items() if k in MappeUpdate.model_fields}
    with _verb() as conn:
        if erlaubt:
            sql = ", ".join(f"{k} = ?" for k in erlaubt)
            conn.execute(f"UPDATE mappe SET {sql} WHERE id = ?", (*erlaubt.values(), mappe_id))
        r = conn.execute("SELECT * FROM mappe WHERE id = ?", (mappe_id,)).fetchone()
    return Projektmappe(**dict(r)) if r else None


# -- Projekt-Aufwand (Mappe = Projekt) --------------------------------------------
# Ist = tatsaechlich erfasste Zeit (zeiteintrag.sekunden als SSOT), Soll = Summe der
# Karten-Schaetzungen (karte.schaetzung_min). Bewusst getrennt gehalten. Die
# Sichtbarkeit folgt derselben Mitgliedschaftsregel wie liste_mappen.

def _sichtbarkeits_klausel(alle: bool, person_id: str | None) -> tuple[str, tuple]:
    if alle or not person_id:
        return "", ()
    return (
        " WHERE NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
        " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)",
        (person_id,),
    )


def projekt_aufwand_liste(person_id: str | None = None, alle: bool = True) -> list[ProjektAufwand]:
    klausel, params = _sichtbarkeits_klausel(alle, person_id)
    sql = (
        "SELECT m.id AS mappe_id, m.titel, COALESCE(m.status, 'aktiv') AS status,"
        " m.owner, m.budget_min,"
        " (SELECT COALESCE(SUM(z.sekunden), 0) FROM zeiteintrag z WHERE z.mappe_id = m.id) AS ist_sekunden,"
        " (SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k JOIN board b ON k.board_id = b.id"
        "  WHERE b.mappe_id = m.id) AS soll_minuten,"
        " (SELECT COUNT(*) FROM karte k JOIN board b ON k.board_id = b.id WHERE b.mappe_id = m.id) AS karten,"
        " (SELECT COUNT(*) FROM board b WHERE b.mappe_id = m.id) AS boards"
        " FROM mappe m" + klausel + " ORDER BY m.titel"
    )
    with _verb() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [ProjektAufwand(**dict(r)) for r in rows]


def projekt_detail(mappe_id: str) -> ProjektDetail | None:
    with _verb() as conn:
        m = conn.execute(
            "SELECT id, titel, COALESCE(status, 'aktiv') AS status, owner, budget_min"
            " FROM mappe WHERE id = ?", (mappe_id,)
        ).fetchone()
        if not m:
            return None
        ist = conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) FROM zeiteintrag WHERE mappe_id = ?", (mappe_id,)
        ).fetchone()[0]
        soll = conn.execute(
            "SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k JOIN board b ON k.board_id = b.id"
            " WHERE b.mappe_id = ?", (mappe_id,)
        ).fetchone()[0]
        boards = conn.execute(
            "SELECT b.id AS board_id, b.titel,"
            " (SELECT COALESCE(SUM(z.sekunden), 0) FROM zeiteintrag z WHERE z.board_id = b.id) AS ist_sekunden,"
            " (SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k WHERE k.board_id = b.id) AS soll_minuten,"
            " (SELECT COUNT(*) FROM karte k WHERE k.board_id = b.id) AS karten"
            " FROM board b WHERE b.mappe_id = ? ORDER BY b.laufnummer, b.titel", (mappe_id,)
        ).fetchall()
        personen = conn.execute(
            "SELECT COALESCE(z.kuerzel, k.zustaendig) AS kuerzel, COALESCE(SUM(z.sekunden), 0) AS ist_sekunden"
            " FROM zeiteintrag z LEFT JOIN karte k ON z.karte_id = k.id"
            " WHERE z.mappe_id = ? GROUP BY COALESCE(z.kuerzel, k.zustaendig) ORDER BY ist_sekunden DESC", (mappe_id,)
        ).fetchall()
    d = dict(m)
    return ProjektDetail(
        mappe_id=d["id"],
        titel=d["titel"],
        status=d["status"],
        owner=d["owner"],
        budget_min=d["budget_min"],
        ist_sekunden=ist,
        soll_minuten=soll,
        boards=[ProjektBoardAufwand(**dict(b)) for b in boards],
        personen=[ProjektPersonAufwand(**dict(p)) for p in personen],
    )


def loesche_mappe(mappe_id: str) -> tuple[bool, list[str]]:
    """Loescht die Mappe samt aller Boards, Spalten, Karten und Zeiteintraege.

    Die letzte verbliebene Mappe bleibt erhalten, damit die Anwendung immer eine
    nutzbare Mappe hat.
    """
    with _verb() as conn:
        if conn.execute("SELECT COUNT(*) FROM mappe").fetchone()[0] <= 1:
            return False, []
        board_ids = [r[0] for r in conn.execute("SELECT id FROM board WHERE mappe_id = ?", (mappe_id,)).fetchall()]
        alle_karten: list[str] = []
        for bid in board_ids:
            karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (bid,)).fetchall()]
            alle_karten.extend(karten)
            _raeume_karten_restdaten(conn, karten)
            conn.execute("DELETE FROM karte WHERE board_id = ?", (bid,))
            conn.execute("DELETE FROM spalte WHERE board_id = ?", (bid,))
        _loesche_serien_fuer_boards(conn, board_ids)
        conn.execute("DELETE FROM dokument WHERE kontext = 'mappe' AND kontext_id = ?", (mappe_id,))
        conn.execute("DELETE FROM zeiteintrag WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM board WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM mappe WHERE id = ?", (mappe_id,))
    return True, alle_karten


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
        # Karten in Erledigt-Spalten werden hier NICHT geladen - sie kommen gefenstert
        # ueber fertige_seite() (Zeitfilter + Anzahl-Deckel + Nachladen), damit das Board
        # bei vielen fertigen Karten nicht geflutet wird. Sehr alte fertige Karten liegen
        # ausserdem im Archiv (archiv_seite). Offene Spalten werden voll geladen.
        rows = conn.execute(
            "SELECT k.* FROM karte k JOIN spalte s ON k.spalte = s.id "
            "WHERE k.board_id = ? AND s.erledigt = 0 ORDER BY k.reihenfolge, k.id",
            (board_id,),
        ).fetchall()
        karten = [_karte_aus_row(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return BoardDetail(
        id=b["id"], mappe_id=b["mappe_id"], titel=b["titel"], kuerzel=b["kuerzel"],
        spalten=spalten, karten=karten,
    )


# -- Fertig-Karten: Fenster, Deckel, Nachladen + Archiv --------------------
# Erledigt-Spalten werden nicht komplett geladen, sondern serverseitig gefiltert
# (Zeitfenster), gedeckelt (Seitengroesse) und beim Scrollen nachgeladen. Karten,
# deren Abschluss aelter als die Archiv-Schwelle ist, erscheinen nur im Archiv.

# Abschlussdatum (YYYY-MM-DD) als SQL-Ausdruck, konsistent zu Karte.abschluss_am:
# Serien-/REKO-Karten haben ein FESTES Datum (faellig), alle anderen zaehlen ab dem
# Erledigt-Zeitpunkt (bewegt_am). Ohne beides bleibt der Abschluss NULL.
_ABSCHLUSS_SQL = (
    "CASE WHEN serie_id IS NOT NULL AND faellig IS NOT NULL THEN faellig "
    "WHEN bewegt_am IS NOT NULL THEN substr(bewegt_am, 1, 10) ELSE NULL END"
)

# Volltext ueber alle durchsuchbaren Felder (labels/checkliste/kommentare sind JSON-Text
# und enthalten die Begriffe im Klartext) - spiegelt die Tiefensuche des Frontends.
_VOLLTEXT_SQL = (
    "LOWER(COALESCE(titel,'') || ' ' || COALESCE(schluessel,'') || ' ' || "
    "COALESCE(beschreibung,'') || ' ' || COALESCE(notizen,'') || ' ' || "
    "COALESCE(zustaendig,'') || ' ' || COALESCE(prioritaet,'') || ' ' || "
    "COALESCE(labels,'') || ' ' || COALESCE(checkliste,'') || ' ' || COALESCE(kommentare,''))"
)


def _als_int(wert, standard: int, minimum: int, maximum: int) -> int:
    try:
        n = int(wert)
    except (TypeError, ValueError):
        return standard
    return max(minimum, min(n, maximum))


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


def _karte_mit_abschluss(row: sqlite3.Row) -> Karte:
    k = _karte_aus_row(row)
    if row["serie_id"] and row["faellig"]:
        k.abschluss_am = row["faellig"]
    elif row["bewegt_am"]:
        k.abschluss_am = row["bewegt_am"][:10]
    return k


def _zeitfenster(zeitraum: str) -> tuple[str | None, str | None]:
    """(von, bis) als ISO-Datum fuer den Fertig-Zeitfilter; (None, None) = alle."""
    heute = datetime.now().date()
    if zeitraum == "heute":
        return heute.isoformat(), heute.isoformat()
    if zeitraum == "gestern":
        g = heute - timedelta(days=1)
        return g.isoformat(), g.isoformat()
    if zeitraum == "woche":
        mo = heute - timedelta(days=heute.weekday())
        return mo.isoformat(), (mo + timedelta(days=6)).isoformat()
    if zeitraum == "monat":
        von = heute.replace(day=1)
        naechster = (von + timedelta(days=32)).replace(day=1)
        return von.isoformat(), (naechster - timedelta(days=1)).isoformat()
    if zeitraum == "jahr":
        return heute.replace(month=1, day=1).isoformat(), heute.replace(month=12, day=31).isoformat()
    return None, None


def _archiv_grenze(archiv_tage: int) -> str:
    return (datetime.now().date() - timedelta(days=archiv_tage)).isoformat()


def _suchbedingung(
    q: str | None, labels: list[str] | None, prioritaet: str | None
) -> tuple[list[str], list]:
    """WHERE-Teilbedingungen + Argumente fuer Suche/Label/Prio (alle als UND verknuepft;
    innerhalb der Suche muss jedes Wort vorkommen, Labels sind ODER-verknuepft)."""
    bed: list[str] = []
    args: list = []
    if q and q.strip():
        for wort in q.strip().lower().split():
            bed.append(f"{_VOLLTEXT_SQL} LIKE ?")
            args.append(f"%{wort}%")
    if labels:
        teil = ["labels LIKE ?" for _ in labels]
        args += [f'%"{name}"%' for name in labels]
        bed.append("(" + " OR ".join(teil) + ")")
    if prioritaet:
        bed.append("prioritaet = ?")
        args.append(prioritaet)
    return bed, args


def fertige_seite(
    spalte_id: str,
    zeitraum: str = "heute",
    offset: int = 0,
    limit: int | None = None,
    q: str | None = None,
    labels: list[str] | None = None,
    prioritaet: str | None = None,
    zustaendig: list[str] | None = None,
) -> tuple[list[Karte], int]:
    """Eine Seite fertiger Karten EINER Erledigt-Spalte: nach Abschlussdatum (neueste
    zuerst), ohne archivierte (aelter als die Schwelle), gedeckelt + per Offset nachladbar.
    Sind Suche/Label/Prio aktiv, wird das Zeitfenster ausgesetzt (wie im Frontend)."""
    conf = hole_kanban_einstellungen()
    seite = _als_int(limit, conf["fertig_seitengroesse"], 1, 500)
    offset = max(0, int(offset))
    grenze = _archiv_grenze(conf["archiv_tage"])
    such_bed, such_args = _suchbedingung(q, labels, prioritaet)
    where = ["spalte = ?", f"({_ABSCHLUSS_SQL} IS NULL OR {_ABSCHLUSS_SQL} >= ?)"]
    args: list = [spalte_id, grenze]
    if not such_bed and zeitraum != "alle":
        von, bis = _zeitfenster(zeitraum)
        if von and bis:
            where.append(f"{_ABSCHLUSS_SQL} BETWEEN ? AND ?")
            args += [von, bis]
    where += such_bed
    args += such_args
    if zustaendig:
        platz = ",".join("?" for _ in zustaendig)
        where.append(f"zustaendig IN ({platz})")
        args += zustaendig
    wsql = " AND ".join(where)
    with _verb() as conn:
        gesamt = conn.execute(f"SELECT COUNT(*) AS n FROM karte WHERE {wsql}", args).fetchone()["n"]
        rows = conn.execute(
            f"SELECT * FROM karte WHERE {wsql} ORDER BY {_ABSCHLUSS_SQL} DESC, reihenfolge, id LIMIT ? OFFSET ?",
            args + [seite, offset],
        ).fetchall()
        karten = [_karte_mit_abschluss(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return karten, int(gesamt)


def archiv_seite(
    board_id: str,
    offset: int = 0,
    limit: int | None = None,
    q: str | None = None,
) -> tuple[list[Karte], int]:
    """Archivierte fertige Karten eines Boards (Abschluss aelter als die Schwelle), ueber
    alle Erledigt-Spalten, neueste zuerst, gedeckelt + nachladbar, optional durchsucht."""
    conf = hole_kanban_einstellungen()
    seite = _als_int(limit, conf["fertig_seitengroesse"], 1, 500)
    offset = max(0, int(offset))
    grenze = _archiv_grenze(conf["archiv_tage"])
    such_bed, such_args = _suchbedingung(q, None, None)
    with _verb() as conn:
        erledigt = [
            r["id"]
            for r in conn.execute(
                "SELECT id FROM spalte WHERE board_id = ? AND erledigt = 1", (board_id,)
            ).fetchall()
        ]
        if not erledigt:
            return [], 0
        platz = ",".join("?" for _ in erledigt)
        where = [
            "board_id = ?",
            f"spalte IN ({platz})",
            f"{_ABSCHLUSS_SQL} IS NOT NULL",
            f"{_ABSCHLUSS_SQL} < ?",
        ]
        args: list = [board_id, *erledigt, grenze]
        where += such_bed
        args += such_args
        wsql = " AND ".join(where)
        gesamt = conn.execute(f"SELECT COUNT(*) AS n FROM karte WHERE {wsql}", args).fetchone()["n"]
        rows = conn.execute(
            f"SELECT * FROM karte WHERE {wsql} ORDER BY {_ABSCHLUSS_SQL} DESC, id LIMIT ? OFFSET ?",
            args + [seite, offset],
        ).fetchall()
        karten = [_karte_mit_abschluss(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return karten, int(gesamt)


def _reichere_gruppen_an(conn: sqlite3.Connection, karten: list[Karte]) -> None:
    """Setzt je verknuepfter Karte gruppe_mitglieder, gruppe_sek und gruppe_zeit_geteilt.

    Zeit zaehlt nur einmal: die echten Zeiteintraege bleiben je Karte; gruppe_sek ist
    eine reine ANZEIGE (kombinierte erfasst_sek der Gruppe, wenn die Gruppe die Zeit
    teilt). Mitglieder werden ueber alle Boards hinweg gesucht (eine Gruppe darf
    boarduebergreifend sein), nicht nur im aktuellen Board.
    """
    gids = {k.gruppe_id for k in karten if k.gruppe_id}
    if not gids:
        return
    platz = ",".join("?" for _ in gids)
    gliste = list(gids)
    mit_rows = conn.execute(
        f"SELECT id, schluessel, titel, erfasst_sek, gruppe_id FROM karte WHERE gruppe_id IN ({platz})",
        gliste,
    ).fetchall()
    geteilt_rows = conn.execute(
        f"SELECT id, zeit_geteilt FROM kartengruppe WHERE id IN ({platz})", gliste
    ).fetchall()
    geteilt = {r["id"]: bool(r["zeit_geteilt"]) for r in geteilt_rows}
    je_gruppe: dict[str, list[sqlite3.Row]] = {}
    for r in mit_rows:
        je_gruppe.setdefault(r["gruppe_id"], []).append(r)
    for k in karten:
        if not k.gruppe_id:
            continue
        mitglieder = je_gruppe.get(k.gruppe_id, [])
        ist_geteilt = geteilt.get(k.gruppe_id, True)
        k.gruppe_zeit_geteilt = ist_geteilt
        k.gruppe_mitglieder = [
            GruppenMitglied(id=m["id"], schluessel=m["schluessel"], titel=m["titel"])
            for m in mitglieder if m["id"] != k.id
        ]
        if ist_geteilt:
            k.gruppe_sek = sum(int(m["erfasst_sek"] or 0) for m in mitglieder)
        else:
            k.gruppe_sek = k.erfasst_sek


def hole_karte(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM karte WHERE id = ?", (karte_id,)).fetchone()
        karte = _karte_aus_row(row) if row else None
        if karte and karte.gruppe_id:
            _reichere_gruppen_an(conn, [karte])
    return karte


# -- Verknuepfung / Zeitgruppe -------------------------------------------

def verknuepfe_karten(karte_id: str, ziel_id: str) -> Karte | None:
    """Legt beide Karten in EINE Gruppe. Bestehende Gruppe(n) werden verwendet bzw.
    zusammengefuehrt; sonst entsteht eine neue Gruppe (Zeit teilen = Standard an)."""
    if karte_id == ziel_id:
        return hole_karte(karte_id)
    with _verb() as conn:
        a = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        b = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (ziel_id,)).fetchone()
        if a is None or b is None:
            return None
        ga, gb = a["gruppe_id"], b["gruppe_id"]
        if ga and gb and ga != gb:
            # Beide haben Gruppen -> b-Gruppe in a-Gruppe ueberfuehren.
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE gruppe_id = ?", (ga, gb))
            conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gb,))
            ziel_gruppe = ga
        elif ga:
            ziel_gruppe = ga
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id = ?", (ga, ziel_id))
        elif gb:
            ziel_gruppe = gb
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id = ?", (gb, karte_id))
        else:
            ziel_gruppe = "g_" + uuid4().hex[:8]
            conn.execute(
                "INSERT INTO kartengruppe (id, zeit_geteilt, erstellt_am) VALUES (?, 1, ?)",
                (ziel_gruppe, _jetzt()),
            )
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id IN (?, ?)", (ziel_gruppe, karte_id, ziel_id))
    return hole_karte(karte_id)


def loese_verknuepfung(karte_id: str) -> Karte | None:
    """Loest die Karte aus ihrer Gruppe. Bleibt danach < 2 Mitglieder, wird die Gruppe
    (und der Rest-Verweis) aufgeloest."""
    with _verb() as conn:
        row = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        gid = row["gruppe_id"]
        conn.execute("UPDATE karte SET gruppe_id = NULL WHERE id = ?", (karte_id,))
        if gid:
            rest = conn.execute("SELECT id FROM karte WHERE gruppe_id = ?", (gid,)).fetchall()
            if len(rest) < 2:
                conn.execute("UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ?", (gid,))
                conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))
    return hole_karte(karte_id)


def setze_gruppe_zeit_geteilt(gruppe_id: str, geteilt: bool) -> bool:
    with _verb() as conn:
        cur = conn.execute(
            "UPDATE kartengruppe SET zeit_geteilt = ? WHERE id = ?", (1 if geteilt else 0, gruppe_id)
        )
        return cur.rowcount > 0


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
    typ: str = "arbeit",
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
            " checkliste, kommentare, cover, reihenfolge, start, faellig, zustaendig, erstellt_am, bewegt_am, typ)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', ?, ?, ?, ?, ?, ?, ?, ?)",
            (karte_id, board_id, spalte, titel, f"{kuerzel}-{nummer}", beschreibung, json.dumps(labels),
             prioritaet, cover, reihenfolge, start, faellig, zustaendig, jetzt, jetzt,
             "idee" if typ == "idee" else "arbeit"),
        )
    karte = hole_karte(karte_id)
    assert karte is not None
    return karte


def verschiebe_karte(karte_id: str, ziel_spalte: str, ziel_reihenfolge: int) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT board_id, spalte, gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        board_id, quelle, gruppe_id = row["board_id"], row["spalte"], row["gruppe_id"]
        conn.execute(
            "UPDATE karte SET reihenfolge = reihenfolge + 1"
            " WHERE board_id = ? AND spalte = ? AND reihenfolge >= ? AND id != ?",
            (board_id, ziel_spalte, ziel_reihenfolge, karte_id),
        )
        conn.execute("UPDATE karte SET spalte = ?, reihenfolge = ? WHERE id = ?", (ziel_spalte, ziel_reihenfolge, karte_id))
        jetzt = _jetzt()
        # Wechsel der Spalte setzt die Verweildauer (Card-Aging) zurück.
        if quelle != ziel_spalte:
            conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (jetzt, karte_id))
        betroffene = {quelle, ziel_spalte}
        # Verknuepfte Tickets ziehen bei Spaltenwechsel als Gruppe mit (ans Ende der
        # Zielspalte, dort frei sortierbar). Nur im selben Board und nur Mitglieder,
        # die nicht ohnehin schon in der Zielspalte stehen. Innerhalb derselben Spalte
        # (reines Umsortieren) bleibt die Gruppe unberuehrt.
        if gruppe_id and quelle != ziel_spalte:
            mitglieder = conn.execute(
                "SELECT id, spalte FROM karte"
                " WHERE board_id = ? AND gruppe_id = ? AND id != ? AND spalte != ?",
                (board_id, gruppe_id, karte_id, ziel_spalte),
            ).fetchall()
            for m in mitglieder:
                ziel_pos = _naechste_reihenfolge(conn, board_id, ziel_spalte)
                conn.execute(
                    "UPDATE karte SET spalte = ?, reihenfolge = ?, bewegt_am = ? WHERE id = ?",
                    (ziel_spalte, ziel_pos, jetzt, m["id"]),
                )
                betroffene.add(m["spalte"])
        # Erledigen stoppt laufende Timer sauber (bucht die Sitzung) - fuer die Karte
        # selbst und fuer mitgezogene Gruppenmitglieder.
        if quelle != ziel_spalte:
            ziel = conn.execute("SELECT erledigt FROM spalte WHERE id = ?", (ziel_spalte,)).fetchone()
            if ziel is not None and ziel["erledigt"]:
                laufende = conn.execute(
                    "SELECT id FROM karte WHERE board_id = ? AND spalte = ? AND laeuft_seit IS NOT NULL",
                    (board_id, ziel_spalte),
                ).fetchall()
                for r in laufende:
                    _pause_intern(conn, r["id"])
        for spalte in betroffene:
            _kompaktiere(conn, board_id, spalte)
    return hole_karte(karte_id)


def aktualisiere_karte(karte_id: str, aenderungen: dict) -> Karte | None:
    # KarteUpdate ist die einzige Feldquelle - keine doppelte Whitelist, die driften koennte.
    felder = {k: v for k, v in aenderungen.items() if k in KarteUpdate.model_fields}
    if not felder:
        return hole_karte(karte_id)
    # Ein Spaltenwechsel ist ein echtes Verschieben und laeuft ueber verschiebe_karte,
    # damit bewegt_am, Gruppen-Mitzug und Kompaktierung auf JEDEM Weg greifen
    # (Drawer-Status, Agenten-API) - nicht nur beim Drag ueber den Move-Endpunkt.
    neue_spalte = felder.pop("spalte", None)
    if neue_spalte is not None:
        with _verb() as conn:
            row = conn.execute("SELECT board_id, spalte FROM karte WHERE id = ?", (karte_id,)).fetchone()
            if row is None:
                return None
            ziel_pos = _naechste_reihenfolge(conn, row["board_id"], neue_spalte)
        if row["spalte"] != neue_spalte:
            verschiebe_karte(karte_id, neue_spalte, ziel_pos)
    # Wechsel auf 'idee' stoppt einen laufenden Timer sauber (bucht die Sitzung),
    # sonst tickt die Zeit unsichtbar auf einem Ticket weiter, das keine erfasst.
    if felder.get("typ") == "idee":
        with _verb() as conn:
            r = conn.execute("SELECT laeuft_seit FROM karte WHERE id = ?", (karte_id,)).fetchone()
            if r is not None and r["laeuft_seit"]:
                _pause_intern(conn, karte_id)
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
        # Atomar in SQL anhaengen (json_insert) - ein Read-Modify-Write kann bei
        # zwei gleichzeitigen Kommentaren einen davon verlieren.
        cur = conn.execute(
            "UPDATE karte SET kommentare = json_insert(kommentare, '$[#]', json(?)) WHERE id = ?",
            (json.dumps({"autor": autor, "text": text, "zeit": zeit}, ensure_ascii=False), karte_id),
        )
        if cur.rowcount == 0:
            return None
    return hole_karte(karte_id)


def _loesche_marken(conn: sqlite3.Connection, wo: str, params: tuple) -> None:
    """Transkript-Marken der betroffenen Karten mitloeschen (Tabelle aus dem
    transkripte-Modul; defensiv, falls dieses Modul nicht geladen ist)."""
    try:
        conn.execute(f"DELETE FROM transkript_marke {wo}", params)
    except sqlite3.OperationalError:
        pass


def loesche_karte(karte_id: str, auslass_merken: bool = True) -> None:
    with _verb() as conn:
        row = conn.execute(
            "SELECT board_id, spalte, gruppe_id, serie_id, serie_datum FROM karte WHERE id = ?", (karte_id,)
        ).fetchone()
        # Bewusst geloeschte Serien-Instanz merken, sonst legt der naechste
        # Vorbuchungslauf sie kommentarlos wieder an (Tabelle des serien-Moduls).
        if auslass_merken and row is not None and row["serie_id"] and row["serie_datum"]:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO serie_auslass (serie_id, datum) VALUES (?, ?)",
                    (row["serie_id"], row["serie_datum"]),
                )
            except sqlite3.OperationalError:
                pass
        conn.execute("DELETE FROM karte WHERE id = ?", (karte_id,))
        conn.execute("DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id = ?", (karte_id,))
        # Zeiteintraege der Karte mitloeschen, sonst verfaelschen Waisen die Ist-Summen.
        conn.execute("DELETE FROM zeiteintrag WHERE karte_id = ?", (karte_id,))
        _loesche_marken(conn, "WHERE karte_id = ?", (karte_id,))
        # Verwaiste Zeitgruppe aufloesen, wenn nach dem Loeschen < 2 Mitglieder bleiben.
        if row is not None and row["gruppe_id"]:
            gid = row["gruppe_id"]
            rest = conn.execute("SELECT id FROM karte WHERE gruppe_id = ?", (gid,)).fetchall()
            if len(rest) < 2:
                conn.execute("UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ?", (gid,))
                conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))
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


def _konsolidiere_auto_zeiten(conn: sqlite3.Connection) -> int:
    """Fasst bestehende automatische Start/Stopp-Eintraege (manuell=0) je Karte+Tag zu
    einem Eintrag zusammen. Summen bleiben exakt gleich (nur Verschmelzung der Fragmente).
    Idempotent: liegt schon hoechstens ein Auto-Eintrag je Karte+Tag vor, passiert nichts.
    Vor der ersten Verschmelzung wird einmalig eine Roh-Sicherung der Tabelle angelegt.
    Gibt die Anzahl betroffener Karten zurueck."""
    gruppen = conn.execute(
        "SELECT karte_id, datum FROM zeiteintrag WHERE manuell = 0 "
        "GROUP BY karte_id, datum HAVING COUNT(*) > 1"
    ).fetchall()
    if not gruppen:
        return 0
    # Einmalige Sicherung der Rohdaten, bevor Fragmente verschmolzen werden.
    hat_backup = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'zeiteintrag_roh_backup'"
    ).fetchone()
    if not hat_backup:
        conn.execute("CREATE TABLE zeiteintrag_roh_backup AS SELECT * FROM zeiteintrag")
    betroffen: set[str] = set()
    for g in gruppen:
        karte_id, datum = g["karte_id"], g["datum"]
        rows = conn.execute(
            "SELECT id, start, ende, sekunden FROM zeiteintrag "
            "WHERE manuell = 0 AND karte_id = ? AND datum = ? ORDER BY start, id",
            (karte_id, datum),
        ).fetchall()
        if len(rows) < 2:
            continue
        ziel = rows[0]
        summe = sum(int(r["sekunden"]) for r in rows)
        starts = [r["start"] for r in rows if r["start"]]
        enden = [r["ende"] for r in rows if r["ende"]]
        neu_start = min(starts) if starts else ziel["start"]
        neu_ende = max(enden) if enden else ziel["ende"]
        conn.execute(
            "UPDATE zeiteintrag SET sekunden = ?, start = ?, ende = ? WHERE id = ?",
            (summe, neu_start, neu_ende, ziel["id"]),
        )
        conn.executemany(
            "DELETE FROM zeiteintrag WHERE id = ?", [(r["id"],) for r in rows[1:]]
        )
        betroffen.add(karte_id)
    for kid in betroffen:
        _recompute_erfasst(conn, kid)
    return len(betroffen)


# Hinweis: Es gibt bewusst keine undatierte Gesamt-Eingabe der erfassten Zeit mehr.
# Ticketzeit (erfasst_sek) = Summe der datierten Zeiteintraege je Karte; jede Korrektur
# laeuft ueber einen datierten Zeiteintrag, damit die Arbeitszeit dem richtigen Tag
# zugeordnet wird. Siehe docs/ZEITMODELL.md.


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
    """Stoppt eine laufende Karte, schreibt einen Zeiteintrag und berechnet erfasst_sek neu.

    Start/Stopp-Sitzungen derselben Karte am selben Tag werden zu EINEM automatischen
    Eintrag zusammengefasst (Summe der Sekunden, frueheste Start- und spaeteste End-Zeit),
    damit die Uebersichten nicht mit vielen Fragmenten volllaufen. Die erfasste Zeit
    bleibt exakt gleich - es ist eine Zusammenfassung, kein Verlust. Siehe ZEITMODELL.md.
    """
    row = conn.execute("SELECT laeuft_seit, board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
    if row is None or not row["laeuft_seit"]:
        return
    start = row["laeuft_seit"]
    ende = _jetzt_genau()
    conn.execute("UPDATE karte SET laeuft_seit = NULL WHERE id = ?", (karte_id,))
    try:
        segmente = _tagessegmente(start, ende)
    except ValueError:
        segmente = []
    # Plausibilitaets-Deckel: ein vergessener Timer (Standby, Absturz, Wochenende)
    # bucht sonst kommentarlos zig Stunden. Sitzungen ueber 12 h werden auf die
    # ersten 12 h gedeckelt - der Rest ist mit hoher Sicherheit keine Arbeitszeit.
    MAX_SITZUNG_SEK = 12 * 3600
    if sum(s[3] for s in segmente) > MAX_SITZUNG_SEK:
        gedeckelt: list[tuple[str, str, str, int]] = []
        rest = MAX_SITZUNG_SEK
        for datum, s_start, s_ende, sek in segmente:
            if rest <= 0:
                break
            gedeckelt.append((datum, s_start, s_ende, min(sek, rest)))
            rest -= min(sek, rest)
        segmente = gedeckelt
    mappe_id = _mappe_fuer_board(conn, row["board_id"])
    for datum, seg_start, seg_ende, sek in segmente:
        vorhanden = conn.execute(
            "SELECT id, start, ende FROM zeiteintrag WHERE manuell = 0 AND karte_id = ? AND datum = ? LIMIT 1",
            (karte_id, datum),
        ).fetchone()
        if vorhanden:
            neu_start = min(vorhanden["start"], seg_start) if vorhanden["start"] else seg_start
            neu_ende = max(vorhanden["ende"], seg_ende) if vorhanden["ende"] else seg_ende
            conn.execute(
                "UPDATE zeiteintrag SET sekunden = sekunden + ?, start = ?, ende = ? WHERE id = ?",
                (sek, neu_start, neu_ende, vorhanden["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?)",
                (f"z_{uuid4().hex[:8]}", karte_id, row["board_id"], mappe_id, datum, seg_start, seg_ende, sek, row["zustaendig"]),
            )
    _recompute_erfasst(conn, karte_id)


def timer_start(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT start FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        # Timer je PERSON: der Start pausiert nur laufende Karten derselben Person
        # (gleiches Zustaendigkeits-Kuerzel; IS vergleicht auch NULL korrekt) -
        # fremde Timer laufen weiter, statt still gestoppt zu werden.
        eigene = conn.execute("SELECT zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        for r in conn.execute(
            "SELECT id FROM karte WHERE laeuft_seit IS NOT NULL AND id != ? AND zustaendig IS ?",
            (karte_id, eigene["zustaendig"] if eigene else None),
        ).fetchall():
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


def laufende_karte(kuerzel: str | None = None, nur_eigene: bool = False) -> Karte | None:
    """Die laufende Karte - mit kuerzel bevorzugt die der Person (Timer je Person);
    nur_eigene unterdrueckt den Fallback auf fremde Timer (Nicht-Admins)."""
    with _verb() as conn:
        row = None
        if kuerzel:
            row = conn.execute(
                "SELECT * FROM karte WHERE laeuft_seit IS NOT NULL AND zustaendig = ? LIMIT 1", (kuerzel,)
            ).fetchone()
        if row is None and not nur_eigene:
            row = conn.execute("SELECT * FROM karte WHERE laeuft_seit IS NOT NULL LIMIT 1").fetchone()
    return _karte_aus_row(row) if row else None


# -- Zeiteinträge (Auswertung / Korrektur) -------------------------------

_ZE_SELECT = (
    "SELECT z.*, k.titel AS karte_titel, k.schluessel AS karte_schluessel, k.zustaendig AS karte_zustaendig "
    "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
)


def _zeiteintrag_aus_row(row: sqlite3.Row) -> Zeiteintrag:
    return Zeiteintrag(
        id=row["id"], karte_id=row["karte_id"], board_id=row["board_id"], mappe_id=row["mappe_id"],
        datum=row["datum"], start=row["start"], ende=row["ende"], sekunden=row["sekunden"],
        kommentar=row["kommentar"], manuell=bool(row["manuell"]), kuerzel=row["kuerzel"],
        karte_titel=row["karte_titel"], karte_schluessel=row["karte_schluessel"],
        karte_zustaendig=row["karte_zustaendig"],
    )


def zeiteintraege_range(von: str | None = None, bis: str | None = None, karte_id: str | None = None,
                        nur_mappen: set[str] | None = None) -> list[Zeiteintrag]:
    """Zeiteintraege gefiltert. Mit karte_id (ohne von/bis) liefert es ALLE Eintraege
    einer Karte ueber alle Tage - Grundlage der Tages-Aufschluesselung im Ticket."""
    bed: list[str] = []
    params: list[str] = []
    if von:
        bed.append("z.datum >= ?")
        params.append(von)
    if bis:
        bed.append("z.datum <= ?")
        params.append(bis)
    if karte_id:
        bed.append("z.karte_id = ?")
        params.append(karte_id)
    if nur_mappen is not None:
        # Projekt-Scoping fuer Nicht-Admins: nur Eintraege sichtbarer Mappen.
        if not nur_mappen:
            return []
        platz = ",".join("?" for _ in nur_mappen)
        bed.append(f"z.mappe_id IN ({platz})")
        params.extend(sorted(nur_mappen))
    where = ("WHERE " + " AND ".join(bed) + " ") if bed else ""
    with _verb() as conn:
        rows = conn.execute(
            _ZE_SELECT + where + "ORDER BY z.datum, z.start, z.id",
            tuple(params),
        ).fetchall()
    return [_zeiteintrag_aus_row(r) for r in rows]


def hole_zeiteintrag(eintrag_id: str) -> Zeiteintrag | None:
    with _verb() as conn:
        r = conn.execute(_ZE_SELECT + "WHERE z.id = ?", (eintrag_id,)).fetchone()
    return _zeiteintrag_aus_row(r) if r else None


def erstelle_zeiteintrag(eintrag_id: str, karte_id: str, datum: str, sekunden: int, kommentar: str | None,
                         kuerzel: str | None = None) -> Zeiteintrag | None:
    """kuerzel = Person, der die Zeit gehoert (Akteur beim Buchen); ohne Angabe
    faellt es auf die Karten-Zustaendigkeit zurueck (offener Modus, Timer)."""
    with _verb() as conn:
        b = conn.execute("SELECT board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if b is None:
            return None
        board_id = b["board_id"]
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
            " VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, 1, ?)",
            (eintrag_id, karte_id, board_id, _mappe_fuer_board(conn, board_id), datum, max(0, sekunden), kommentar,
             kuerzel or b["zustaendig"]),
        )
        _recompute_erfasst(conn, karte_id)
    return hole_zeiteintrag(eintrag_id)


def setze_ticketzeit(karte_id: str, ziel_sek: int, kuerzel: str | None = None) -> bool:
    """Setzt die Gesamt-Ticketzeit in EINER Transaktion (gegen die aktuelle Summe
    gerechnet): Mehrzeit wird als manueller Eintrag heute gebucht, Minderzeit von
    den juengsten Eintraegen abgezogen. Keine halben Korrekturen bei Abbruechen."""
    ziel = max(0, int(ziel_sek))
    with _verb() as conn:
        b = conn.execute("SELECT board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if b is None:
            return False
        summe = int(conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) FROM zeiteintrag WHERE karte_id = ?", (karte_id,)
        ).fetchone()[0])
        if ziel > summe:
            heute = _jetzt()[:10]
            conn.execute(
                "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
                " VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, 'Korrektur', 1, ?)",
                (f"z_{uuid4().hex[:8]}", karte_id, b["board_id"], _mappe_fuer_board(conn, b["board_id"]),
                 heute, ziel - summe, kuerzel or b["zustaendig"]),
            )
        elif ziel < summe:
            rest = summe - ziel
            for r in conn.execute(
                "SELECT id, sekunden FROM zeiteintrag WHERE karte_id = ? ORDER BY datum DESC, id DESC", (karte_id,)
            ).fetchall():
                if rest <= 0:
                    break
                if r["sekunden"] <= rest:
                    conn.execute("DELETE FROM zeiteintrag WHERE id = ?", (r["id"],))
                    rest -= r["sekunden"]
                else:
                    conn.execute("UPDATE zeiteintrag SET sekunden = sekunden - ? WHERE id = ?", (rest, r["id"]))
                    rest = 0
        _recompute_erfasst(conn, karte_id)
    return True


def aktualisiere_zeiteintrag(eintrag_id: str, aenderungen: dict) -> Zeiteintrag | None:
    with _verb() as conn:
        row = conn.execute("SELECT karte_id FROM zeiteintrag WHERE id = ?", (eintrag_id,)).fetchone()
        if row is None:
            return None
        felder = {k: v for k, v in aenderungen.items() if k in ZeiteintragUpdate.model_fields}
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
    felder = {k: v for k, v in aenderungen.items() if k in SpalteUpdate.model_fields}
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
                "SELECT k.id, k.board_id, k.spalte, k.schluessel, k.titel, k.faellig, k.laeuft_seit, k.bewegt_am"
                f" FROM karte k JOIN board b ON b.id = k.board_id WHERE b.mappe_id IN ({platz})",
                tuple(sorted(nur_mappen)),
            ).fetchall()
        else:
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
    return HeuteUebersicht(
        datum=heute, ueberfaellig=ueberfaellig, heute=heute_f,
        diese_woche=diese_woche, laufend=laufend, liegengeblieben=liegengeblieben,
    )


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


def _raeume_karten_restdaten(conn: sqlite3.Connection, karten_ids: list[str]) -> None:
    """Alles, was an Karten haengt, konsistent mitloeschen - EIN Pfad fuer alle
    Massen-Loeschungen (Spalte/Board/Mappe): Dokumente, Zeiteintraege,
    Transkript-Marken und verwaiste Zeitgruppen."""
    if not karten_ids:
        return
    platz = ",".join("?" for _ in karten_ids)
    try:
        conn.execute(
            f"INSERT OR IGNORE INTO serie_auslass (serie_id, datum)"
            f" SELECT serie_id, serie_datum FROM karte"
            f" WHERE id IN ({platz}) AND serie_id IS NOT NULL AND serie_datum IS NOT NULL",
            karten_ids,
        )
    except sqlite3.OperationalError:
        pass
    conn.execute(f"DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id IN ({platz})", karten_ids)
    conn.execute(f"DELETE FROM zeiteintrag WHERE karte_id IN ({platz})", karten_ids)
    _loesche_marken(conn, f"WHERE karte_id IN ({platz})", tuple(karten_ids))
    gruppen = [r[0] for r in conn.execute(
        f"SELECT DISTINCT gruppe_id FROM karte WHERE id IN ({platz}) AND gruppe_id IS NOT NULL", karten_ids
    ).fetchall()]
    for gid in gruppen:
        rest = conn.execute(
            f"SELECT COUNT(*) FROM karte WHERE gruppe_id = ? AND id NOT IN ({platz})", (gid, *karten_ids)
        ).fetchone()[0]
        if rest < 2:
            conn.execute(
                f"UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ? AND id NOT IN ({platz})", (gid, *karten_ids)
            )
            conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))


def _loesche_serien_fuer_boards(conn: sqlite3.Connection, board_ids: list[str]) -> None:
    """Serien geloeschter Boards mitloeschen - sonst materialisieren sie weiter
    Geisterkarten in ein Board, das es nicht mehr gibt (Tabelle des serien-Moduls,
    defensiv falls nicht geladen)."""
    if not board_ids:
        return
    platz = ",".join("?" for _ in board_ids)
    try:
        conn.execute(
            f"DELETE FROM serie_auslass WHERE serie_id IN (SELECT id FROM serie WHERE board_id IN ({platz}))",
            board_ids,
        )
        conn.execute(f"DELETE FROM serie WHERE board_id IN ({platz})", board_ids)
    except sqlite3.OperationalError:
        pass


def loesche_spalte(spalte_id: str) -> tuple[str, list[str]]:
    """Löscht eine Spalte samt ihrer Karten. Liefert ('ok'|'letzte'|'fehlt', karten_ids)."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return "fehlt", []
        board_id = r["board_id"]
        anzahl = conn.execute("SELECT COUNT(*) AS n FROM spalte WHERE board_id = ?", (board_id,)).fetchone()["n"]
        if anzahl <= 1:
            return "letzte", []
        karten = [x[0] for x in conn.execute(
            "SELECT id FROM karte WHERE board_id = ? AND spalte = ?", (board_id, spalte_id)
        ).fetchall()]
        _raeume_karten_restdaten(conn, karten)
        conn.execute("DELETE FROM karte WHERE board_id = ? AND spalte = ?", (board_id, spalte_id))
        conn.execute("DELETE FROM spalte WHERE id = ?", (spalte_id,))
        _kompaktiere_spalten(conn, board_id)
    return "ok", karten


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


def loesche_board(board_id: str) -> list[str]:
    """Loescht das Board samt Spalten/Karten/Restdaten; liefert die Karten-IDs."""
    with _verb() as conn:
        karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (board_id,)).fetchall()]
        _raeume_karten_restdaten(conn, karten)
        conn.execute("DELETE FROM zeiteintrag WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM karte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM spalte WHERE board_id = ?", (board_id,))
        _loesche_serien_fuer_boards(conn, [board_id])
        conn.execute("DELETE FROM board WHERE id = ?", (board_id,))
    return karten


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
