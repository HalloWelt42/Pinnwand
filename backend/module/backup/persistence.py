"""Ablage der Snapshots: Dateien unter backend/data/backups, Metadaten in der DB."""
from __future__ import annotations

from pathlib import Path

from app.db import verbindung

DATEN = Path(__file__).resolve().parents[2] / "data" / "backups"

SCHEMA = """
CREATE TABLE IF NOT EXISTS backup_archiv (
    id TEXT PRIMARY KEY,
    dateiname TEXT,
    erstellt_am TEXT,
    groesse INTEGER,
    version TEXT,
    art TEXT,
    notiz TEXT
);
"""


def init_db() -> None:
    DATEN.mkdir(parents=True, exist_ok=True)
    with verbindung() as conn:
        conn.executescript(SCHEMA)
    # Verzögerter Import vermeidet einen Ringschluss mit dem Dienst.
    from . import dienst

    # Nur den Index mit den vorhandenen Dateien abgleichen. Die automatische
    # Sicherung läuft bewusst NICHT hier, sondern im Lebenszyklus - sonst
    # entstünde sie, bevor die anderen Module (kanban_kern, planung, ...) ihre
    # Tabellen und Seed-Daten angelegt haben, und der Snapshot wäre leer.
    dienst.synchronisiere_index()


def speichere_meta(info: dict) -> None:
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO backup_archiv (id, dateiname, erstellt_am, groesse, version, art, notiz)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (info["id"], info["dateiname"], info["erstellt_am"], info["groesse"],
             info["version"], info["art"], info.get("notiz", "")),
        )


def liste() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT id, dateiname, erstellt_am, groesse, version, art, notiz"
            " FROM backup_archiv ORDER BY erstellt_am DESC, rowid DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def hole_meta(sid: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM backup_archiv WHERE id = ?", (sid,)).fetchone()
    return dict(r) if r else None


def loesche_meta(sid: str) -> None:
    with verbindung() as conn:
        conn.execute("DELETE FROM backup_archiv WHERE id = ?", (sid,))


def letzter_automatischer() -> dict | None:
    with verbindung() as conn:
        r = conn.execute(
            "SELECT * FROM backup_archiv WHERE art = 'automatisch' ORDER BY erstellt_am DESC, rowid DESC LIMIT 1"
        ).fetchone()
    return dict(r) if r else None


def automatische_aelter_als(behalten: int) -> list[dict]:
    """Automatische Snapshots, die über die Aufbewahrungsgrenze hinausgehen (älteste zuerst zum Löschen)."""
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT * FROM backup_archiv WHERE art = 'automatisch' ORDER BY erstellt_am DESC, rowid DESC"
        ).fetchall()
    ueberzaehlig = [dict(r) for r in rows[max(behalten, 0):]]
    return ueberzaehlig
