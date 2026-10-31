"""Kennung der Kommentare nachtragen (HELF-94): beim Start, in einer Transaktion.

Bearbeiten und Löschen treffen einen Kommentar über seine Kennung; die Stelle an der Karte taugt nicht, denn nach dem
Löschen rücken die folgenden nach. Kommentare von früher haben keine Kennung: jeder bekommt eine, an Karten und an
Karten im Papierkorb. Rückgängig von Änderungen aus der Zeit davor ginge auf einen Stand ohne Kennungen zurück; diese
Rückwege gelten darum nicht mehr (wie beim Nachtrag der Gesamtnummer). Gibt es nichts nachzutragen, ändert der Lauf
nichts."""

from __future__ import annotations

import json
import sqlite3

from .rahmen import neue_kennung


def _ergaenzen(karte: dict) -> bool:
    """Gibt jedem Kommentar der Karte ohne Kennung eine; True, wenn sich etwas änderte."""
    fehlend = [c for c in karte.get("kommentare") or [] if not c.get("id")]
    for c in fehlend:
        c["id"] = neue_kennung("m")
    return bool(fehlend)


def nachtragen(v: sqlite3.Connection) -> int:
    """Ergebnis: wie viele Karten (auch im Papierkorb) Kennungen bekamen."""
    zahl = 0
    for z in v.execute("SELECT id, daten FROM karten").fetchall():
        d = json.loads(z["daten"])
        if _ergaenzen(d):
            v.execute("UPDATE karten SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), z["id"]))
            zahl += 1
    for z in v.execute("SELECT id, daten FROM papierkorb").fetchall():
        d = json.loads(z["daten"])
        geaendert = [_ergaenzen(c) for c in d.get("karten") or []]
        if any(geaendert):
            v.execute("UPDATE papierkorb SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), z["id"]))
            zahl += sum(geaendert)
    if zahl:
        v.execute("UPDATE journal SET rueckgaengig=0 WHERE rueckgaengig=1")
    return zahl
