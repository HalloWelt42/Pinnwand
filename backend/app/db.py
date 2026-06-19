"""Generischer Datenbankzugang des Kerns.

Der Kern kennt keine Domaene - er stellt nur die SQLite-Verbindung bereit.
Tabellen, Modelle und Seed gehoeren in die jeweiligen Module.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PFAD = Path(__file__).resolve().parent.parent / "pinnwand.db"


def verbindung() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PFAD)
    conn.row_factory = sqlite3.Row
    return conn
