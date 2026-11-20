"""Ohne abgehakte Checkliste nie fertig (HELF-255, Nutzer 20.11.2026: "ohne deren vollständige Abarbeiten niemals ein
Ticket fertig"). Eine Spalte mit `nur_abgehakt` nimmt keine Karte mit offenem Punkt: weder beim Verschieben (Ziehen,
Status, Telefon, Liste, Sammelaktion, Abhaken, mitziehende Verknüpfte) noch beim Anlegen oder Umzug. Kommt an einer Karte
dort ein Punkt dazu oder geht ein Haken weg, geht sie zurück in die erste Spalte ohne Sperre (`inhalt.bearbeiten`).

Beim Start bekommen Spalten, über die noch nie entschieden wurde (das Feld fehlt), den Schalter, wenn sie die
Erledigt-Spalte sind oder nach Prüfung heißen. Wer ihn ausschaltet, speichert das ausdrücklich (`nurAbgehakt: false`);
dann bleibt er aus, auch bei jedem weiteren Start. Karten, die schon mit offenem Punkt dort stehen, bleiben stehen."""

from __future__ import annotations

import json
import sqlite3

from ..modell import Karte, Spalte
from ..regeln.board import nimmt_nicht, offene_punkte
from .rahmen import Abgelehnt

#: Spalten dieser Namen prüfen (klein geschrieben), wie die Prüfspalten, die das Werkzeug des Helfers kennt
PRUEFSPALTEN = ("prüfung", "zur prüfung", "zu testen")


def punkte_text(n: int) -> str:
    return f"{n} offenen Punkt" if n == 1 else f"{n} offene Punkte"


def pruefen(ziel: Spalte, karten: list[Karte]) -> None:
    """Abgelehnt mit Grund, wenn die Spalte eine der Karten wegen offener Punkte nicht nimmt."""
    gesperrt = [c for c in karten if nimmt_nicht(ziel, c)]
    if not gesperrt:
        return
    regel = f"{ziel.name} nimmt nur Karten mit vollständig abgehakter Checkliste"
    if len(gesperrt) == 1:
        c = gesperrt[0]
        offen = offene_punkte(c)
        raise Abgelehnt(f"{c.schluessel} hat noch {punkte_text(len(offen))} der Checkliste (erster: {offen[0][:80]}); {regel}")
    namen = ", ".join(c.schluessel for c in gesperrt[:5]) + (" ..." if len(gesperrt) > 5 else "")
    raise Abgelehnt(f"{len(gesperrt)} Karten haben noch offene Punkte der Checkliste ({namen}); {regel}")


def nachtragen(v: sqlite3.Connection) -> int:
    """Ergebnis: wie viele Spalten ab jetzt nur abgehakte Karten nehmen."""
    zahl = 0
    for z in v.execute("SELECT id, daten FROM boards").fetchall():
        d = json.loads(z["daten"])
        neu = [s for s in d.get("spalten") or [] if "nurAbgehakt" not in s
               and (s.get("erledigt") or (s.get("name") or "").strip().lower() in PRUEFSPALTEN)]
        for s in neu:
            s["nurAbgehakt"] = True
        if neu:
            v.execute("UPDATE boards SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), z["id"]))
            zahl += len(neu)
    return zahl
