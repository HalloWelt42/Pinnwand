"""Persistenz der Planung: Personen, Urlaub, Feiertage.

Personen tragen ihr Wochen-Soll je Wochentag (Mo..So in Stunden). Urlaub wird
taggenau gefuehrt (Anteil 1.0 oder 0.5). Feiertage werden importiert (mit
Region-Kennung) und in die Kapazitaet eingerechnet.
"""
from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from app.db import verbindung

SCHEMA = """
CREATE TABLE IF NOT EXISTS person (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kuerzel TEXT,
    farbe TEXT,
    wochenstunden TEXT NOT NULL DEFAULT '[8,8,8,8,8,0,0]',
    bundesland TEXT,
    urlaubsanspruch REAL NOT NULL DEFAULT 30,
    resturlaub_vorjahr REAL NOT NULL DEFAULT 0,
    aktiv INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS urlaub (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    datum TEXT NOT NULL,
    anteil REAL NOT NULL DEFAULT 1.0,
    typ TEXT NOT NULL DEFAULT 'urlaub',
    notiz TEXT
);
CREATE TABLE IF NOT EXISTS feiertag (
    datum TEXT NOT NULL,
    name TEXT NOT NULL,
    region TEXT,
    PRIMARY KEY (datum, region)
);
"""

_STD_WOCHE = [8, 8, 8, 8, 8, 0, 0]


def _migriere(conn: sqlite3.Connection) -> None:
    """Ergaenzt neue Personen-Spalten in einer bestehenden Datenbank."""
    spalten = {r["name"] for r in conn.execute("PRAGMA table_info(person)").fetchall()}
    if "bundesland" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN bundesland TEXT")
    if "urlaubsanspruch" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN urlaubsanspruch REAL NOT NULL DEFAULT 30")
    if "resturlaub_vorjahr" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN resturlaub_vorjahr REAL NOT NULL DEFAULT 0")


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)
        _migriere(conn)
        if conn.execute("SELECT COUNT(*) AS n FROM person").fetchone()["n"] == 0:
            for kuerzel, name in [("AK", "Anke Krause"), ("TB", "Tom Berger"), ("ML", "Mara Lang")]:
                conn.execute(
                    "INSERT INTO person (id, name, kuerzel, wochenstunden, aktiv) VALUES (?, ?, ?, ?, 1)",
                    ("p_" + uuid4().hex[:8], name, kuerzel, json.dumps(_STD_WOCHE)),
                )


# -- Personen -------------------------------------------------------------

def _person(r: sqlite3.Row) -> dict:
    schluessel = r.keys()
    return {
        "id": r["id"], "name": r["name"], "kuerzel": r["kuerzel"], "farbe": r["farbe"],
        "wochenstunden": json.loads(r["wochenstunden"]),
        "bundesland": r["bundesland"] if "bundesland" in schluessel else None,
        "urlaubsanspruch": r["urlaubsanspruch"] if "urlaubsanspruch" in schluessel else 30,
        "resturlaub_vorjahr": r["resturlaub_vorjahr"] if "resturlaub_vorjahr" in schluessel else 0,
        "aktiv": bool(r["aktiv"]),
    }


def liste_personen() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute("SELECT * FROM person ORDER BY name").fetchall()
    return [_person(r) for r in rows]


def hole_person(pid: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM person WHERE id = ?", (pid,)).fetchone()
    return _person(r) if r else None


def erstelle_person(name: str, kuerzel: str | None, wochenstunden: list | None, farbe: str | None,
                    bundesland: str | None = None, urlaubsanspruch: float = 30,
                    resturlaub_vorjahr: float = 0) -> dict:
    pid = "p_" + uuid4().hex[:8]
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO person (id, name, kuerzel, farbe, wochenstunden, bundesland, urlaubsanspruch, resturlaub_vorjahr, aktiv)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (pid, name, kuerzel, farbe, json.dumps(wochenstunden or _STD_WOCHE), bundesland, urlaubsanspruch, resturlaub_vorjahr),
        )
    return hole_person(pid)  # type: ignore[return-value]


def aktualisiere_person(pid: str, aenderungen: dict) -> dict | None:
    f = {k: v for k, v in aenderungen.items()
         if k in {"name", "kuerzel", "farbe", "wochenstunden", "bundesland", "urlaubsanspruch", "resturlaub_vorjahr", "aktiv"}}
    if not f:
        return hole_person(pid)
    if "wochenstunden" in f:
        f["wochenstunden"] = json.dumps(f["wochenstunden"])
    if "aktiv" in f:
        f["aktiv"] = 1 if f["aktiv"] else 0
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE person SET {zuweisung} WHERE id = ?", (*f.values(), pid))
    return hole_person(pid)


def loesche_person(pid: str) -> bool:
    with verbindung() as conn:
        conn.execute("DELETE FROM urlaub WHERE person_id = ?", (pid,))
        cur = conn.execute("DELETE FROM person WHERE id = ?", (pid,))
    return cur.rowcount > 0


# -- Urlaub ---------------------------------------------------------------

def liste_urlaub(person_id: str | None, von: str, bis: str) -> list[dict]:
    with verbindung() as conn:
        if person_id:
            rows = conn.execute(
                "SELECT * FROM urlaub WHERE person_id = ? AND datum >= ? AND datum <= ? ORDER BY datum",
                (person_id, von, bis),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM urlaub WHERE datum >= ? AND datum <= ? ORDER BY datum", (von, bis)
            ).fetchall()
    return [{"id": r["id"], "person_id": r["person_id"], "datum": r["datum"], "anteil": r["anteil"],
             "typ": r["typ"], "notiz": r["notiz"]} for r in rows]


def setze_urlaub(person_id: str, datum: str, anteil: float, typ: str, notiz: str | None) -> dict:
    """Setzt/aktualisiert einen Urlaubstag (ein Eintrag je Person+Datum)."""
    with verbindung() as conn:
        vorhanden = conn.execute(
            "SELECT id FROM urlaub WHERE person_id = ? AND datum = ?", (person_id, datum)
        ).fetchone()
        if vorhanden:
            conn.execute("UPDATE urlaub SET anteil = ?, typ = ?, notiz = ? WHERE id = ?",
                         (anteil, typ, notiz, vorhanden["id"]))
            uid = vorhanden["id"]
        else:
            uid = "u_" + uuid4().hex[:8]
            conn.execute("INSERT INTO urlaub (id, person_id, datum, anteil, typ, notiz) VALUES (?, ?, ?, ?, ?, ?)",
                         (uid, person_id, datum, anteil, typ, notiz))
    return {"id": uid, "person_id": person_id, "datum": datum, "anteil": anteil, "typ": typ, "notiz": notiz}


def loesche_urlaub(uid: str) -> bool:
    with verbindung() as conn:
        cur = conn.execute("DELETE FROM urlaub WHERE id = ?", (uid,))
    return cur.rowcount > 0


def _genommen(conn: sqlite3.Connection, person_id: str, jahr: int) -> float:
    """Summe der im Jahr genommenen Urlaubstage (nur typ 'urlaub', Anteil 1.0/0.5)."""
    r = conn.execute(
        "SELECT COALESCE(SUM(anteil), 0) AS s FROM urlaub"
        " WHERE person_id = ? AND typ = 'urlaub' AND datum >= ? AND datum <= ?",
        (person_id, f"{jahr}-01-01", f"{jahr}-12-31"),
    ).fetchone()
    return round(float(r["s"] or 0), 2)


def urlaubskonto(person_id: str, jahr: int) -> dict | None:
    p = hole_person(person_id)
    if p is None:
        return None
    anspruch = float(p["urlaubsanspruch"] or 0)
    uebertrag = float(p["resturlaub_vorjahr"] or 0)
    with verbindung() as conn:
        genommen = _genommen(conn, person_id, jahr)
        genommen_vorjahr = _genommen(conn, person_id, jahr - 1)
    verfuegbar = round(anspruch + uebertrag, 2)
    return {
        "person_id": person_id,
        "jahr": jahr,
        "anspruch": anspruch,
        "uebertrag": uebertrag,
        "verfuegbar": verfuegbar,
        "genommen": genommen,
        "verbleibend": round(verfuegbar - genommen, 2),
        "genommen_vorjahr": genommen_vorjahr,
    }


def urlaubskonten(jahr: int) -> list[dict]:
    return [k for p in liste_personen() if (k := urlaubskonto(p["id"], jahr)) is not None]


# -- Feiertage ------------------------------------------------------------

def liste_feiertage(von: str, bis: str) -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT DISTINCT datum, name, region FROM feiertag WHERE datum >= ? AND datum <= ? ORDER BY datum",
            (von, bis),
        ).fetchall()
    return [{"datum": r["datum"], "name": r["name"], "region": r["region"]} for r in rows]


def uebernehme_feiertage(eintraege: list[dict], region: str | None) -> int:
    n = 0
    with verbindung() as conn:
        for e in eintraege:
            conn.execute(
                "INSERT OR REPLACE INTO feiertag (datum, name, region) VALUES (?, ?, ?)",
                (e["datum"], e["name"], region or e.get("region")),
            )
            n += 1
    return n


def loesche_feiertage(jahr: int, region: str | None) -> int:
    with verbindung() as conn:
        if region:
            cur = conn.execute("DELETE FROM feiertag WHERE datum LIKE ? AND region = ?", (f"{jahr}-%", region))
        else:
            cur = conn.execute("DELETE FROM feiertag WHERE datum LIKE ?", (f"{jahr}-%",))
    return cur.rowcount
