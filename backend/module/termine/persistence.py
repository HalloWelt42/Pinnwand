"""Persistenz der Termine (Termin-Serien und ihre Vorkommen-Instanzen)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from uuid import uuid4

from app.db import verbindung

from .models import TerminInstanz, TerminSerie, TerminSerieUpdate

SCHEMA = """
CREATE TABLE IF NOT EXISTS termin_serie (
    id TEXT PRIMARY KEY,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    kuerzel TEXT,
    typ TEXT NOT NULL DEFAULT 'taeglich',
    intervall INTEGER NOT NULL DEFAULT 1,
    wochentage TEXT NOT NULL DEFAULT '',
    monatstag INTEGER,
    monatsregel TEXT NOT NULL DEFAULT 'tag',
    uhrzeit TEXT,
    dauer_min INTEGER NOT NULL DEFAULT 60,
    wochenenden_ueberspringen INTEGER NOT NULL DEFAULT 0,
    feiertage_ueberspringen INTEGER NOT NULL DEFAULT 0,
    urlaub_ueberspringen INTEGER NOT NULL DEFAULT 1,
    rueckblick_tage INTEGER NOT NULL DEFAULT 14,
    start TEXT,
    ende TEXT,
    aktiv INTEGER NOT NULL DEFAULT 1,
    erstellt_am TEXT
);
CREATE TABLE IF NOT EXISTS termin_instanz (
    id TEXT PRIMARY KEY,
    serie_id TEXT NOT NULL,
    datum TEXT NOT NULL,
    kuerzel TEXT,
    titel TEXT NOT NULL,
    uhrzeit TEXT,
    geplant_min INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'schwebend',
    effektiv_min INTEGER,
    bestaetigt_am TEXT,
    erstellt_am TEXT,
    UNIQUE(serie_id, datum)
);
CREATE INDEX IF NOT EXISTS ix_termin_instanz_datum ON termin_instanz(datum);
CREATE INDEX IF NOT EXISTS ix_termin_instanz_status ON termin_instanz(status);
"""


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)


# -- Serien ---------------------------------------------------------------

def _serie(r: sqlite3.Row) -> TerminSerie:
    return TerminSerie(
        id=r["id"], titel=r["titel"], beschreibung=r["beschreibung"],
        kuerzel=r["kuerzel"], typ=r["typ"], intervall=r["intervall"],
        wochentage=[int(x) for x in (r["wochentage"] or "").split(",") if x != ""],
        monatstag=r["monatstag"], monatsregel=r["monatsregel"], uhrzeit=r["uhrzeit"],
        dauer_min=r["dauer_min"],
        wochenenden_ueberspringen=bool(r["wochenenden_ueberspringen"]),
        feiertage_ueberspringen=bool(r["feiertage_ueberspringen"]),
        urlaub_ueberspringen=bool(r["urlaub_ueberspringen"]),
        rueckblick_tage=r["rueckblick_tage"],
        start=r["start"], ende=r["ende"], aktiv=bool(r["aktiv"]),
    )


def liste_serien() -> list[TerminSerie]:
    with verbindung() as conn:
        rows = conn.execute("SELECT * FROM termin_serie ORDER BY titel").fetchall()
    return [_serie(r) for r in rows]


def hole_serie(sid: str) -> TerminSerie | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM termin_serie WHERE id = ?", (sid,)).fetchone()
    return _serie(r) if r else None


def erstelle_serie(daten: dict) -> TerminSerie:
    sid = "ts_" + uuid4().hex[:8]
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO termin_serie (id, titel, beschreibung, kuerzel, typ, intervall, wochentage,"
            " monatstag, monatsregel, uhrzeit, dauer_min, wochenenden_ueberspringen, feiertage_ueberspringen,"
            " urlaub_ueberspringen, rueckblick_tage, start, ende, aktiv, erstellt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sid, daten["titel"], daten.get("beschreibung"), daten.get("kuerzel"),
                daten.get("typ", "taeglich"), int(daten.get("intervall") or 1),
                ",".join(str(x) for x in (daten.get("wochentage") or [])),
                daten.get("monatstag"), daten.get("monatsregel", "tag"), daten.get("uhrzeit"),
                int(daten.get("dauer_min") or 60),
                1 if daten.get("wochenenden_ueberspringen") else 0,
                1 if daten.get("feiertage_ueberspringen") else 0,
                1 if daten.get("urlaub_ueberspringen", True) else 0,
                int(daten.get("rueckblick_tage") or 14),
                daten.get("start"), daten.get("ende"), 1 if daten.get("aktiv", True) else 0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    s = hole_serie(sid)
    assert s is not None
    return s


def aktualisiere_serie(sid: str, aenderungen: dict) -> TerminSerie | None:
    f = {k: v for k, v in aenderungen.items() if k in TerminSerieUpdate.model_fields}
    if not f:
        return hole_serie(sid)
    if "wochentage" in f:
        f["wochentage"] = ",".join(str(x) for x in (f["wochentage"] or []))
    for b in ("wochenenden_ueberspringen", "feiertage_ueberspringen", "urlaub_ueberspringen", "aktiv"):
        if b in f:
            f[b] = 1 if f[b] else 0
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE termin_serie SET {zuweisung} WHERE id = ?", (*f.values(), sid))
    return hole_serie(sid)


def loesche_serie(sid: str) -> bool:
    """Loescht die Serie. Bestaetigte Instanzen bleiben als Verlauf/Gutschrift erhalten."""
    with verbindung() as conn:
        conn.execute(
            "DELETE FROM termin_instanz WHERE serie_id = ? AND status != 'bestaetigt'", (sid,)
        )
        cur = conn.execute("DELETE FROM termin_serie WHERE id = ?", (sid,))
    return cur.rowcount > 0


# -- Instanzen ------------------------------------------------------------

def _instanz(r: sqlite3.Row) -> TerminInstanz:
    return TerminInstanz(
        id=r["id"], serie_id=r["serie_id"], datum=r["datum"], kuerzel=r["kuerzel"],
        titel=r["titel"], uhrzeit=r["uhrzeit"], geplant_min=r["geplant_min"],
        status=r["status"], effektiv_min=r["effektiv_min"], bestaetigt_am=r["bestaetigt_am"],
    )


def instanz_existiert(serie_id: str, datum: str) -> bool:
    with verbindung() as conn:
        return conn.execute(
            "SELECT 1 FROM termin_instanz WHERE serie_id = ? AND datum = ?", (serie_id, datum)
        ).fetchone() is not None


def erstelle_instanz(serie: TerminSerie, datum: str) -> None:
    with verbindung() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO termin_instanz (id, serie_id, datum, kuerzel, titel, uhrzeit,"
            " geplant_min, status, erstellt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, 'schwebend', ?)",
            (
                "ti_" + uuid4().hex[:8], serie.id, datum, serie.kuerzel,
                serie.titel, serie.uhrzeit, int(serie.dauer_min or 60),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def liste_instanzen(status: str | None = None, von: str | None = None, bis: str | None = None) -> list[TerminInstanz]:
    klauseln, args = [], []
    if status:
        klauseln.append("status = ?")
        args.append(status)
    if von:
        klauseln.append("datum >= ?")
        args.append(von)
    if bis:
        klauseln.append("datum <= ?")
        args.append(bis)
    wo = (" WHERE " + " AND ".join(klauseln)) if klauseln else ""
    with verbindung() as conn:
        rows = conn.execute(f"SELECT * FROM termin_instanz{wo} ORDER BY datum, uhrzeit, titel", args).fetchall()
    return [_instanz(r) for r in rows]


def hole_instanz(iid: str) -> TerminInstanz | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM termin_instanz WHERE id = ?", (iid,)).fetchone()
    return _instanz(r) if r else None


def zaehle_offen(bis: str) -> int:
    with verbindung() as conn:
        r = conn.execute(
            "SELECT COUNT(*) AS n FROM termin_instanz WHERE status = 'schwebend' AND datum <= ?", (bis,)
        ).fetchone()
    return int(r["n"])


def bestaetige(iid: str, dauer_min: int) -> TerminInstanz | None:
    with verbindung() as conn:
        conn.execute(
            "UPDATE termin_instanz SET status = 'bestaetigt', effektiv_min = ?, bestaetigt_am = ? WHERE id = ?",
            (int(dauer_min), datetime.now().isoformat(timespec="seconds"), iid),
        )
    return hole_instanz(iid)


def lehne_ab(iid: str) -> TerminInstanz | None:
    with verbindung() as conn:
        conn.execute(
            "UPDATE termin_instanz SET status = 'abgelehnt', effektiv_min = NULL, bestaetigt_am = ? WHERE id = ?",
            (datetime.now().isoformat(timespec="seconds"), iid),
        )
    return hole_instanz(iid)


def ist_minuten_je_tag_person(von: str, bis: str) -> dict[tuple[str, str], int]:
    """(kuerzel, datum) -> Summe bestaetigter Termin-Minuten im Bereich (zweite Ist-Quelle)."""
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT kuerzel, datum, COALESCE(SUM(effektiv_min), 0) AS m FROM termin_instanz"
            " WHERE status = 'bestaetigt' AND kuerzel IS NOT NULL AND datum >= ? AND datum <= ?"
            " GROUP BY kuerzel, datum",
            (von, bis),
        ).fetchall()
    return {(r["kuerzel"], r["datum"]): int(r["m"] or 0) for r in rows}
