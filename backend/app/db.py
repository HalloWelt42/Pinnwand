"""Generischer Datenbankzugang des Kerns.

Der Kern kennt keine Domäne - er stellt nur die SQLite-Verbindung bereit.
Tabellen, Modelle und Seed gehören in die jeweiligen Module.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Standard ist pinnwand.db im Projektwurzelverzeichnis; per PINNWAND_DB_PFAD
# umstellbar (z.B. fuer Tests gegen eine temporaere Datenbank).
DB_PFAD = Path(os.environ.get("PINNWAND_DB_PFAD") or (Path(__file__).resolve().parent.parent / "pinnwand.db"))


def verbindung() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PFAD)
    conn.row_factory = sqlite3.Row
    # Kurze Wartezeit statt sofortigem "database is locked", wenn zwei Requests
    # (FastAPI-Threadpool) gleichzeitig schreiben. Journal bleibt bewusst beim
    # SQLite-Standard (DELETE): WAL ist auf macOS-Bind-Mounts fehleranfaellig
    # und der Ein-Prozess-Betrieb braucht es nicht.
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn
