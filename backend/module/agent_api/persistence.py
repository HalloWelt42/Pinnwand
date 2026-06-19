"""Persistenz der Agenten-API: Token, Audit-Log und Idempotenz.

Eigene Tabellen ueber die generische Verbindung des Kerns. Token werden nur
gehasht gespeichert; der Klartext ist ausschliesslich einmal bei der Erstellung
sichtbar. Jede schreibende Agenten-Aktion wird im Audit-Log festgehalten.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime
from uuid import uuid4

from app.db import verbindung

SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_token (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    scopes TEXT NOT NULL DEFAULT 'read',
    erstellt_am TEXT NOT NULL,
    zuletzt_genutzt TEXT,
    aktiv INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS agent_audit (
    id TEXT PRIMARY KEY,
    zeit TEXT NOT NULL,
    akteur TEXT,
    aktion TEXT NOT NULL,
    ziel TEXT,
    ergebnis TEXT NOT NULL,
    details TEXT
);
CREATE TABLE IF NOT EXISTS agent_idempotenz (
    schluessel TEXT PRIMARY KEY,
    zeit TEXT NOT NULL,
    ergebnis TEXT
);
"""


def _jetzt() -> str:
    return datetime.now().isoformat(timespec="seconds")


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# -- Token ----------------------------------------------------------------

def erstelle_token(name: str, scopes: list[str]) -> dict:
    """Legt ein Token an und gibt den Klartext genau einmal zurueck."""
    token = "pw_" + secrets.token_urlsafe(32)
    tid = "t_" + uuid4().hex[:8]
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO agent_token (id, name, token_hash, scopes, erstellt_am, aktiv)"
            " VALUES (?, ?, ?, ?, ?, 1)",
            (tid, name, _hash(token), ",".join(scopes), _jetzt()),
        )
    return {"id": tid, "name": name, "scopes": scopes, "token": token}


def liste_token() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT id, name, scopes, erstellt_am, zuletzt_genutzt, aktiv FROM agent_token ORDER BY erstellt_am"
        ).fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "scopes": r["scopes"].split(","),
            "erstellt_am": r["erstellt_am"],
            "zuletzt_genutzt": r["zuletzt_genutzt"],
            "aktiv": bool(r["aktiv"]),
        }
        for r in rows
    ]


def widerrufe_token(tid: str) -> bool:
    with verbindung() as conn:
        cur = conn.execute("UPDATE agent_token SET aktiv = 0 WHERE id = ?", (tid,))
    return cur.rowcount > 0


def pruefe_token(token: str) -> tuple[str, set[str]] | None:
    """Gibt (Name, Scopes) eines gueltigen, aktiven Tokens zurueck, sonst None."""
    with verbindung() as conn:
        r = conn.execute(
            "SELECT id, name, scopes, aktiv FROM agent_token WHERE token_hash = ?", (_hash(token),)
        ).fetchone()
        if r is None or not r["aktiv"]:
            return None
        conn.execute("UPDATE agent_token SET zuletzt_genutzt = ? WHERE id = ?", (_jetzt(), r["id"]))
    return r["name"], set(r["scopes"].split(","))


# -- Audit-Log ------------------------------------------------------------

def protokolliere(akteur: str | None, aktion: str, ziel: str | None, ergebnis: str, details: dict | None = None) -> None:
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO agent_audit (id, zeit, akteur, aktion, ziel, ergebnis, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "a_" + uuid4().hex[:10],
                _jetzt(),
                akteur,
                aktion,
                ziel,
                ergebnis,
                json.dumps(details, ensure_ascii=False) if details is not None else None,
            ),
        )


def liste_audit(limit: int = 100) -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_audit ORDER BY zeit DESC, id DESC LIMIT ?", (max(1, min(limit, 1000)),)
        ).fetchall()
    return [
        {
            "id": r["id"],
            "zeit": r["zeit"],
            "akteur": r["akteur"],
            "aktion": r["aktion"],
            "ziel": r["ziel"],
            "ergebnis": r["ergebnis"],
            "details": json.loads(r["details"]) if r["details"] else None,
        }
        for r in rows
    ]


# -- Idempotenz -----------------------------------------------------------

def _idem_schluessel(akteur: str, schluessel: str) -> str:
    """Bindet den Idempotenz-Schluessel an den Akteur.

    Sonst koennte ein Akteur mit dem Schluessel eines anderen dessen Ergebnis
    erhalten oder dessen Schreibaktion unterdruecken.
    """
    return f"{akteur}:{schluessel}"


def idempotenz_treffer(akteur: str, schluessel: str | None) -> dict | None:
    if not schluessel:
        return None
    with verbindung() as conn:
        r = conn.execute(
            "SELECT ergebnis FROM agent_idempotenz WHERE schluessel = ?",
            (_idem_schluessel(akteur, schluessel),),
        ).fetchone()
    if r is None:
        return None
    return json.loads(r["ergebnis"]) if r["ergebnis"] else {}


def idempotenz_merke(akteur: str, schluessel: str | None, ergebnis: dict) -> None:
    if not schluessel:
        return
    with verbindung() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agent_idempotenz (schluessel, zeit, ergebnis) VALUES (?, ?, ?)",
            (_idem_schluessel(akteur, schluessel), _jetzt(), json.dumps(ergebnis, ensure_ascii=False)),
        )
