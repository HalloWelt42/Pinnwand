"""Berichts-Archiv: speichert erzeugte Berichte unveränderlich als Nachweis.

Die Datei liegt unter backend/data/berichte, die Metadaten in der DB.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.db import verbindung

DATEN = Path(__file__).resolve().parents[2] / "data" / "berichte"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bericht_archiv (
    id TEXT PRIMARY KEY,
    typ TEXT,
    titel TEXT,
    zeitraum TEXT,
    format TEXT,
    person TEXT,
    erstellt_am TEXT,
    dateiname TEXT,
    groesse INTEGER
);
"""

_EXT = {"pdf": "pdf", "csv": "csv", "markdown": "md", "md": "md"}
_MIME = {"pdf": "application/pdf", "csv": "text/csv", "markdown": "text/markdown", "md": "text/markdown"}


def init_db() -> None:
    DATEN.mkdir(parents=True, exist_ok=True)
    with verbindung() as conn:
        conn.executescript(SCHEMA)


def archiviere(typ: str, titel: str, zeitraum: str, fmt: str, person: str | None, inhalt: bytes) -> dict:
    bid = "b_" + uuid4().hex[:10]
    dateiname = f"{bid}.{_EXT.get(fmt, 'bin')}"
    DATEN.mkdir(parents=True, exist_ok=True)
    (DATEN / dateiname).write_bytes(inhalt)
    erstellt = datetime.now().isoformat(timespec="seconds")
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO bericht_archiv (id, typ, titel, zeitraum, format, person, erstellt_am, dateiname, groesse)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (bid, typ, titel, zeitraum, fmt, person, erstellt, dateiname, len(inhalt)),
        )
    return {"id": bid, "typ": typ, "titel": titel, "zeitraum": zeitraum, "format": fmt,
            "person": person, "erstellt_am": erstellt, "groesse": len(inhalt)}


def liste() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT id, typ, titel, zeitraum, format, person, erstellt_am, groesse FROM bericht_archiv ORDER BY erstellt_am DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def hole(bid: str) -> tuple[bytes, str, str] | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM bericht_archiv WHERE id = ?", (bid,)).fetchone()
    if r is None:
        return None
    pfad = DATEN / r["dateiname"]
    if not pfad.is_file():
        return None
    return pfad.read_bytes(), r["dateiname"], _MIME.get(r["format"], "application/octet-stream")
