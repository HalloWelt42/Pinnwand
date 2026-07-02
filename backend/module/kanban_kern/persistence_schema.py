"""Schema, Migrationen, Indizes und Seed der Kanban-Persistenz."""
from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from .persistence_basis import _verb
from .persistence_karten import _recompute_erfasst


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
    gruppe_id TEXT,
    blockiert_grund TEXT
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
CREATE TABLE IF NOT EXISTS aktivitaet (
    id TEXT PRIMARY KEY,
    karte_id TEXT NOT NULL,
    zeit TEXT NOT NULL,
    kuerzel TEXT,
    art TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS anhang (
    id TEXT PRIMARY KEY,
    karte_id TEXT NOT NULL,
    name TEXT NOT NULL,
    groesse INTEGER NOT NULL DEFAULT 0,
    typ TEXT,
    erstellt_am TEXT
);
"""


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
    if "blockiert_grund" not in kspalten:
        # Leichtes Blockiert-Flag mit Freitext-Grund (NULL = frei).
        conn.execute("ALTER TABLE karte ADD COLUMN blockiert_grund TEXT")
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
            "CREATE INDEX IF NOT EXISTS ix_aktivitaet_karte ON aktivitaet(karte_id, zeit)",
            "CREATE INDEX IF NOT EXISTS ix_aktivitaet_zeit ON aktivitaet(zeit)",
            "CREATE INDEX IF NOT EXISTS ix_anhang_karte ON anhang(karte_id)",
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
