"""Leichtes Protokoll der KI-Aufrufe.

Nur zur Nachvollziehbarkeit (welcher Aufgabentyp, welches Modell, wie viele
Vorschlaege, erfolgreich?). Bewusst ohne Inhalte der Daten - die KI ist eine
Hilfe, kein Datensammler. Das Schreiben ist fire-and-forget und darf den
eigentlichen Aufruf nie stoeren.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.db import verbindung

SCHEMA = """
CREATE TABLE IF NOT EXISTS ki_protokoll (
    id TEXT PRIMARY KEY,
    zeit TEXT NOT NULL,
    typ TEXT NOT NULL,
    modell TEXT,
    anzahl INTEGER NOT NULL DEFAULT 0,
    ok INTEGER NOT NULL DEFAULT 0
);
"""


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)


def protokolliere(typ: str, modell: str | None, anzahl: int, ok: bool) -> None:
    try:
        with verbindung() as conn:
            conn.execute(
                "INSERT INTO ki_protokoll (id, zeit, typ, modell, anzahl, ok) VALUES (?, ?, ?, ?, ?, ?)",
                ("kp_" + uuid4().hex[:8], datetime.now().isoformat(timespec="seconds"), typ, modell, int(anzahl), 1 if ok else 0),
            )
    except Exception:
        # Protokoll darf den KI-Aufruf nie verhindern.
        pass
