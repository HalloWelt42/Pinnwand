"""Querschnitts-Helfer der Kanban-Persistenz.

Verbindung, Zeit-Helfer und Aktivitätsprotokoll - kleine Bausteine, die
mehrere Themenmodule brauchen. Bewusst ohne Abhängigkeiten auf andere
persistence_*-Module.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, time as _zeit, timedelta
from uuid import uuid4

from app.db import verbindung


def _jetzt() -> str:
    return datetime.now().isoformat(timespec="minutes")


def _jetzt_genau() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _verb() -> sqlite3.Connection:
    return verbindung()


def _als_int(wert, standard: int, minimum: int, maximum: int) -> int:
    try:
        n = int(wert)
    except (TypeError, ValueError):
        return standard
    return max(minimum, min(n, maximum))


def _tagessegmente(start_iso: str, ende_iso: str) -> list[tuple[str, str, str, int]]:
    """Zerlegt ein Start-Ende-Intervall in (datum, start, ende, sekunden) je Kalendertag,
    damit ein ueber Mitternacht laufender Timer die Zeit dem richtigen Tag gutschreibt."""
    a = datetime.fromisoformat(start_iso)
    b = datetime.fromisoformat(ende_iso)
    segs: list[tuple[str, str, str, int]] = []
    cur = a
    while cur < b:
        naechste_mitternacht = datetime.combine(cur.date() + timedelta(days=1), _zeit.min)
        seg_ende = min(b, naechste_mitternacht)
        sek = int((seg_ende - cur).total_seconds())
        if sek >= 1:
            segs.append((cur.date().isoformat(), cur.isoformat(timespec="seconds"), seg_ende.isoformat(timespec="seconds"), sek))
        cur = seg_ende
    return segs


def _protokolliere(conn: sqlite3.Connection, karte_id: str, art: str, text: str,
                   kuerzel: str | None = None) -> None:
    """Haengt einen Eintrag an das Aktivitaetsprotokoll der Karte an - in der
    laufenden Transaktion, damit Ereignis und Datenaenderung zusammen landen
    (oder zusammen zurueckrollen)."""
    conn.execute(
        "INSERT INTO aktivitaet (id, karte_id, zeit, kuerzel, art, text) VALUES (?, ?, ?, ?, ?, ?)",
        (f"a_{uuid4().hex[:8]}", karte_id, _jetzt_genau(), kuerzel, art, text),
    )


def _protokolliere_feldaenderungen(conn: sqlite3.Connection, karte_id: str,
                                   vorher: sqlite3.Row, felder: dict,
                                   akteur: str | None) -> None:
    """Protokolliert die nachvollziehenswerten Feld-Aenderungen einer Karte
    (Zustaendigkeit, Faelligkeit, Prioritaet, Blockade, Typ) - bewusst NICHT
    jeden Tastendruck in Titel/Beschreibung, sonst ersaeuft das Protokoll."""
    if "zustaendig" in felder and felder["zustaendig"] != vorher["zustaendig"]:
        neu = felder["zustaendig"]
        _protokolliere(conn, karte_id, "zustaendig",
                       f"Zuständig: {neu}" if neu else "Zuständigkeit entfernt", akteur)
    if "faellig" in felder and felder["faellig"] != vorher["faellig"]:
        neu = felder["faellig"]
        _protokolliere(conn, karte_id, "faellig",
                       f"Fällig am {neu}" if neu else "Fälligkeit entfernt", akteur)
    if "prioritaet" in felder and felder["prioritaet"] != vorher["prioritaet"]:
        neu = felder["prioritaet"]
        _protokolliere(conn, karte_id, "prioritaet",
                       f"Priorität: {neu}" if neu else "Priorität entfernt", akteur)
    if "blockiert_grund" in felder and felder["blockiert_grund"] != vorher["blockiert_grund"]:
        neu = felder["blockiert_grund"]
        if neu and not vorher["blockiert_grund"]:
            text = f"Blockiert: {neu}"
        elif not neu:
            text = "Blockade aufgehoben"
        else:
            text = f"Blockade-Grund geändert: {neu}"
        _protokolliere(conn, karte_id, "blockiert", text, akteur)
    if "typ" in felder and felder["typ"] != vorher["typ"]:
        _protokolliere(conn, karte_id, "typ",
                       "In eine Idee umgewandelt" if felder["typ"] == "idee" else "In Arbeit umgewandelt",
                       akteur)
