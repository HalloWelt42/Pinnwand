"""Zeit läuft in "Dran" (HELF-193): beim Start, in einer Transaktion. Spalten, über deren Messung noch nie entschieden
wurde (das Feld fehlt) und die "Dran" heißen, messen ab jetzt; so arbeitete der Helfer schon immer ("Dran heißt, man
arbeitet dran"). Wer eine Spalte ausschaltet, speichert das ausdrücklich (`misst: false`); sie bleibt dann aus, auch bei
jedem weiteren Start. Neue Boards bekommen die Messung aus ihrer Vorlage. Gibt es nichts nachzutragen, ändert der Lauf
nichts."""

from __future__ import annotations

import json
import sqlite3

#: Spalten mit diesem Namen messen, solange niemand anders entschieden hat
NAME = "dran"


def nachtragen(v: sqlite3.Connection) -> int:
    """Ergebnis: wie viele Spalten ab jetzt messen."""
    zahl = 0
    for z in v.execute("SELECT id, daten FROM boards").fetchall():
        d = json.loads(z["daten"])
        neu = [s for s in d.get("spalten") or [] if s.get("misst") is None and not s.get("erledigt") and (s.get("name") or "").strip().lower() == NAME]
        for s in neu:
            s["misst"] = True
        if neu:
            v.execute("UPDATE boards SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), z["id"]))
            zahl += len(neu)
    return zahl
