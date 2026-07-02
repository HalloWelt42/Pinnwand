"""Persistenz der Anmeldung: Sitzungen und einfache App-Einstellungen.

Sitzungs-Token werden nur GEHASHT gespeichert (wie die Agenten-Token), sodass die
Datenbank kein nutzbares Geheimnis enthaelt. Eine Sitzung laeuft nach einer Frist
ab. Die Tabelle app_einstellung haelt globale Schalter (z.B. ob Anmeldung
erforderlich ist) als schlichte Schluessel/Wert-Paare.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from app.db import verbindung

SCHEMA = """
CREATE TABLE IF NOT EXISTS sitzung (
    token_hash TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    erstellt_am TEXT,
    ablauf TEXT
);
CREATE TABLE IF NOT EXISTS app_einstellung (
    schluessel TEXT PRIMARY KEY,
    wert TEXT
);
"""

_GUELTIG_TAGE = 30


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)
    # Hygiene: abgelaufene Sitzungen wachsen sonst unbegrenzt. Vergleich mit
    # lokaler Zeit, weil ablauf mit datetime.now() (lokal) geschrieben wird.
    with verbindung() as conn:
        conn.execute("DELETE FROM sitzung WHERE ablauf < ?", (datetime.now().isoformat(timespec="seconds"),))


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def erstelle_sitzung(person_id: str) -> str:
    """Legt eine Sitzung an und gibt den (nur hier sichtbaren) Klartext-Token zurueck."""
    token = secrets.token_urlsafe(32)
    jetzt = datetime.now()
    ablauf = jetzt + timedelta(days=_GUELTIG_TAGE)
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO sitzung (token_hash, person_id, erstellt_am, ablauf) VALUES (?, ?, ?, ?)",
            (_hash(token), person_id, jetzt.isoformat(timespec="seconds"), ablauf.isoformat(timespec="seconds")),
        )
    return token


def sitzung_person(token: str) -> str | None:
    """person_id einer gueltigen, nicht abgelaufenen Sitzung, sonst None."""
    if not token:
        return None
    with verbindung() as conn:
        r = conn.execute("SELECT person_id, ablauf FROM sitzung WHERE token_hash = ?", (_hash(token),)).fetchone()
    if r is None:
        return None
    if r["ablauf"] and r["ablauf"] < datetime.now().isoformat(timespec="seconds"):
        return None
    return r["person_id"]


def loesche_sitzung(token: str) -> None:
    if not token:
        return
    with verbindung() as conn:
        conn.execute("DELETE FROM sitzung WHERE token_hash = ?", (_hash(token),))


def loesche_sitzungen_von(person_id: str) -> None:
    """Alle Sitzungen einer Person beenden (z.B. nach Passwort-Aenderung)."""
    with verbindung() as conn:
        conn.execute("DELETE FROM sitzung WHERE person_id = ?", (person_id,))


def hole_einstellung(schluessel: str) -> str | None:
    with verbindung() as conn:
        r = conn.execute("SELECT wert FROM app_einstellung WHERE schluessel = ?", (schluessel,)).fetchone()
    return r["wert"] if r else None


def setze_einstellung(schluessel: str, wert: str) -> None:
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO app_einstellung (schluessel, wert) VALUES (?, ?)"
            " ON CONFLICT(schluessel) DO UPDATE SET wert = excluded.wert",
            (schluessel, wert),
        )
