"""Persistenz der Serien (wiederkehrende Termine/Aufgaben)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from uuid import uuid4

from app.db import verbindung

from .models import SerieUpdate

SCHEMA = """
CREATE TABLE IF NOT EXISTS serie (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    spalte_id TEXT,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    labels TEXT NOT NULL DEFAULT '[]',
    zustaendig TEXT,
    typ TEXT NOT NULL DEFAULT 'woechentlich',
    intervall INTEGER NOT NULL DEFAULT 1,
    wochentage TEXT NOT NULL DEFAULT '',
    monatstag INTEGER,
    monatsregel TEXT NOT NULL DEFAULT 'tag',
    uhrzeit TEXT,
    dauer_min INTEGER,
    wochenenden_ueberspringen INTEGER NOT NULL DEFAULT 0,
    feiertage_ueberspringen INTEGER NOT NULL DEFAULT 0,
    vorlauf_tage INTEGER NOT NULL DEFAULT 14,
    start TEXT,
    ende TEXT,
    aktiv INTEGER NOT NULL DEFAULT 1,
    erstellt_am TEXT
);
"""


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)
        spalten = {r["name"] for r in conn.execute("PRAGMA table_info(serie)").fetchall()}
        if "monatsregel" not in spalten:
            conn.execute("ALTER TABLE serie ADD COLUMN monatsregel TEXT NOT NULL DEFAULT 'tag'")
        if "feiertage_ueberspringen" not in spalten:
            conn.execute("ALTER TABLE serie ADD COLUMN feiertage_ueberspringen INTEGER NOT NULL DEFAULT 0")


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"], "board_id": r["board_id"], "spalte_id": r["spalte_id"],
        "titel": r["titel"], "beschreibung": r["beschreibung"],
        "labels": json.loads(r["labels"] or "[]"), "zustaendig": r["zustaendig"],
        "typ": r["typ"], "intervall": r["intervall"],
        "wochentage": [int(x) for x in (r["wochentage"] or "").split(",") if x != ""],
        "monatstag": r["monatstag"], "monatsregel": r["monatsregel"],
        "uhrzeit": r["uhrzeit"], "dauer_min": r["dauer_min"],
        "wochenenden_ueberspringen": bool(r["wochenenden_ueberspringen"]),
        "feiertage_ueberspringen": bool(r["feiertage_ueberspringen"]),
        "vorlauf_tage": r["vorlauf_tage"], "start": r["start"], "ende": r["ende"],
        "aktiv": bool(r["aktiv"]),
    }


def liste(board_id: str | None = None) -> list[dict]:
    with verbindung() as conn:
        if board_id:
            rows = conn.execute("SELECT * FROM serie WHERE board_id = ? ORDER BY titel", (board_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM serie ORDER BY titel").fetchall()
    return [_row(r) for r in rows]


def hole(sid: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM serie WHERE id = ?", (sid,)).fetchone()
    return _row(r) if r else None


def erstelle(daten: dict) -> dict:
    sid = "se_" + uuid4().hex[:8]
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO serie (id, board_id, spalte_id, titel, beschreibung, labels, zustaendig, typ,"
            " intervall, wochentage, monatstag, monatsregel, uhrzeit, dauer_min, wochenenden_ueberspringen,"
            " feiertage_ueberspringen, vorlauf_tage, start, ende, aktiv, erstellt_am)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                sid, daten["board_id"], daten.get("spalte_id"), daten["titel"], daten.get("beschreibung"),
                json.dumps(daten.get("labels") or [], ensure_ascii=False), daten.get("zustaendig"),
                daten.get("typ", "woechentlich"), int(daten.get("intervall") or 1),
                ",".join(str(x) for x in (daten.get("wochentage") or [])), daten.get("monatstag"),
                daten.get("monatsregel", "tag"),
                daten.get("uhrzeit"), daten.get("dauer_min"),
                1 if daten.get("wochenenden_ueberspringen") else 0,
                1 if daten.get("feiertage_ueberspringen") else 0,
                int(daten["vorlauf_tage"]) if daten.get("vorlauf_tage") is not None else 14,
                daten.get("start"), daten.get("ende"), 1 if daten.get("aktiv", True) else 0,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    return hole(sid)  # type: ignore[return-value]


def aktualisiere(sid: str, aenderungen: dict) -> dict | None:
    f = {k: v for k, v in aenderungen.items() if k in SerieUpdate.model_fields}
    if not f:
        return hole(sid)
    if "labels" in f:
        f["labels"] = json.dumps(f["labels"] or [], ensure_ascii=False)
    if "wochentage" in f:
        f["wochentage"] = ",".join(str(x) for x in (f["wochentage"] or []))
    for b in ("wochenenden_ueberspringen", "feiertage_ueberspringen", "aktiv"):
        if b in f:
            f[b] = 1 if f[b] else 0
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE serie SET {zuweisung} WHERE id = ?", (*f.values(), sid))
    return hole(sid)


def loesche(sid: str) -> bool:
    with verbindung() as conn:
        cur = conn.execute("DELETE FROM serie WHERE id = ?", (sid,))
    return cur.rowcount > 0
