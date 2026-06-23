"""Transkript-Marken: verbinden eine Karte mit einer Stelle in einem Transkript.

Eine Marke zeigt auf einen Punkt im Transkript (Segment-Startzeit in Sekunden,
optional) und traegt eine editierbare Zusammenfassung des Abschnitts. Die
Transkripte selbst liegen extern; Name/Segment-Text werden denormalisiert
gespeichert, damit die Marke auch ohne Nachladen lesbar bleibt.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from uuid import uuid4

from app.db import verbindung

SCHEMA = """
CREATE TABLE IF NOT EXISTS transkript_marke (
    id TEXT PRIMARY KEY,
    karte_id TEXT NOT NULL,
    transkript_id TEXT NOT NULL,
    transkript_name TEXT,
    position_sek REAL,
    segment_text TEXT,
    sprecher TEXT,
    titel TEXT,
    zusammenfassung TEXT,
    reihenfolge INTEGER NOT NULL DEFAULT 0,
    erstellt_am TEXT
);
"""


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_marke_karte ON transkript_marke(karte_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_marke_transkript ON transkript_marke(transkript_id)")
        # Arbeitspool: die als relevant ausgewaehlten Transkripte (Vorfilter).
        conn.execute(
            "CREATE TABLE IF NOT EXISTS transkript_pool ("
            " transkript_id TEXT PRIMARY KEY, transkript_name TEXT, erstellt_am TEXT)"
        )


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "karte_id": r["karte_id"],
        "transkript_id": r["transkript_id"],
        "transkript_name": r["transkript_name"],
        "position_sek": r["position_sek"],
        "segment_text": r["segment_text"],
        "sprecher": r["sprecher"],
        "titel": r["titel"],
        "zusammenfassung": r["zusammenfassung"],
        "reihenfolge": r["reihenfolge"],
        "erstellt_am": r["erstellt_am"],
    }


def hole(mid: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM transkript_marke WHERE id = ?", (mid,)).fetchone()
    return _row(r) if r else None


def liste(karte_id: str) -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT * FROM transkript_marke WHERE karte_id = ? ORDER BY reihenfolge, erstellt_am, id",
            (karte_id,),
        ).fetchall()
    return [_row(r) for r in rows]


def je_transkript(transkript_id: str) -> list[dict]:
    """Alle Marken eines Transkripts inkl. Karten-Info (Markierung + Navigation)."""
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT m.*, k.schluessel AS karte_schluessel, k.titel AS karte_titel,"
            " k.board_id AS karte_board FROM transkript_marke m"
            " LEFT JOIN karte k ON k.id = m.karte_id"
            " WHERE m.transkript_id = ? ORDER BY m.position_sek",
            (transkript_id,),
        ).fetchall()
    out: list[dict] = []
    for r in rows:
        d = _row(r)
        d["karte_schluessel"] = r["karte_schluessel"]
        d["karte_titel"] = r["karte_titel"]
        d["karte_board"] = r["karte_board"]
        out.append(d)
    return out


def erstelle(daten: dict) -> dict:
    mid = "tm_" + uuid4().hex[:8]
    with verbindung() as conn:
        n = conn.execute(
            "SELECT COALESCE(MAX(reihenfolge), -1) + 1 AS r FROM transkript_marke WHERE karte_id = ?",
            (daten["karte_id"],),
        ).fetchone()["r"]
        conn.execute(
            "INSERT INTO transkript_marke (id, karte_id, transkript_id, transkript_name, position_sek,"
            " segment_text, sprecher, titel, zusammenfassung, reihenfolge, erstellt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mid,
                daten["karte_id"],
                daten["transkript_id"],
                daten.get("transkript_name"),
                daten.get("position_sek"),
                daten.get("segment_text"),
                daten.get("sprecher"),
                daten.get("titel"),
                daten.get("zusammenfassung"),
                n,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    return hole(mid) or {}


def aktualisiere(mid: str, felder: dict) -> dict | None:
    erlaubt = {"titel", "zusammenfassung", "position_sek", "segment_text", "sprecher", "reihenfolge"}
    f = {k: v for k, v in felder.items() if k in erlaubt}
    if not f:
        return hole(mid)
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE transkript_marke SET {zuweisung} WHERE id = ?", (*f.values(), mid))
    return hole(mid)


def loesche(mid: str) -> None:
    with verbindung() as conn:
        conn.execute("DELETE FROM transkript_marke WHERE id = ?", (mid,))


# -- Arbeitspool (Vorfilter relevanter Transkripte) -----------------------

def pool_liste() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT transkript_id, transkript_name FROM transkript_pool ORDER BY transkript_name, transkript_id"
        ).fetchall()
    return [{"transkript_id": r["transkript_id"], "transkript_name": r["transkript_name"]} for r in rows]


def pool_aufnehmen(transkript_id: str, name: str | None) -> None:
    with verbindung() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO transkript_pool (transkript_id, transkript_name, erstellt_am) VALUES (?, ?, ?)",
            (transkript_id, name, datetime.now().isoformat(timespec="seconds")),
        )


def pool_entfernen(transkript_id: str) -> None:
    with verbindung() as conn:
        conn.execute("DELETE FROM transkript_pool WHERE transkript_id = ?", (transkript_id,))
