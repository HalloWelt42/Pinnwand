"""Altbestand des Helfers übertragen (HELF-43, Nutzer 30.10.: "Ja, eindeutige übertragen"): einmal beim Start, in einer
Transaktion, sobald es die Person des App-Zugangs Helfer gibt.

Bevor der App-Zugang eine eigene Person war (30.10.2026, ab 15:00 arbeitete der Helfer über ihn), lief alles unter
seinem Inhaber. Übertragen wird nur, was eindeutig der Helfer tat, erkannt am Journal: Änderungen des Inhabers ab 15:00
mit einer Meldung, die nur die Werkzeuge des Helfers schreiben (Priorität "Einschätzung des Helfers", "Start gesetzt"
und "Start nachgetragen", Umschreibungen der Tickets, gebuchte Zeit mit der Notiz "Helfer:"), und Kommentare im Board
Helfer mit den Merkmalen seiner Berichte (Ursache, Fassung, ausgerollt, Zitate "Nutzer 30.10.", ...). Deren Zeilen im
Verlauf und die Kommentare gehen auf den Helfer über; alles andere (Verschieben, Anlegen, Erledigen) bleibt beim
Inhaber, denn das sieht vom Menschen gleich aus. Läuft nur einmal (Merker in der Tabelle zaehler)."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter

#: Merker in der Tabelle zaehler: der Altbestand ist übertragen
MERKER = "altbestand-helfer"
#: Name des App-Zugangs und Board, um die es geht; ab wann der Helfer über den Zugang arbeitete
ZUGANG = "Helfer"
AB = "2026-10-30T15:00:00"
#: Meldungen, die nur die Werkzeuge des Helfers schreiben (ticket.py und seine Umschreibungen)
MELDUNGEN = re.compile(r"\(Einschätzung des Helfers\)$|: Start gesetzt$|: Start nachgetragen$"
                       r"|: Anforderung umgeschrieben, Wortlaut erhalten$|: Titel gekürzt$|^\d+:\d\d auf [A-Z][A-Z0-9]+-\d+ gebucht")
KOMMENTAR_MELDUNG = re.compile(r"^Kommentar an [A-Z][A-Z0-9]+-\d+ gespeichert$")
#: Merkmale der Berichte des Helfers in Kommentaren
BERICHT = re.compile(r"Ursache|ausgerollt|Fassung|Erledigt|Umgesetzt|Gebaut|[Gg]emessen|Nutzer|Bestandsaufnahme|Angesehen"
                     r"|braucht|Vorschlag|Prüfen|Regelwerk angelegt|Reihenfolge berichtigt|Damit ich|Bearbeiten selbst funktioniert"
                     r"|Pinnwand: Erfassen")


def _neu(vorher: list[dict], nachher: list[dict], von: str, zeit: str) -> list[dict]:
    """Einträge (Verlauf oder Kommentare), die mit dieser Änderung dazukamen: im Nachher, nicht im Vorher, von der Person
    zur Zeit der Änderung."""
    alt = {json.dumps(e, sort_keys=True) for e in vorher}
    return [e for e in nachher if e.get("von") == von and e.get("zeit") == zeit and json.dumps(e, sort_keys=True) not in alt]


def uebertragen(v: sqlite3.Connection, ab: str = AB) -> int:
    """Überträgt den eindeutigen Altbestand (ab `ab`) auf die Person des Zugangs. Ergebnis: wie viele Einträge
    übergingen."""
    if v.execute("SELECT 1 FROM zaehler WHERE id=?", (MERKER,)).fetchone():
        return 0
    person = next((json.loads(z["daten"]) for z in v.execute("SELECT daten FROM konten")
                   if json.loads(z["daten"]).get("app") == ZUGANG), None)
    if person is None or not person.get("inhaber"):
        return 0                                     # die Person gibt es noch nicht: beim nächsten Start
    inhaber, helfer = person["inhaber"], person["id"]
    boards = {json.loads(z["daten"])["id"] for z in v.execute("SELECT daten FROM boards")
              if json.loads(z["daten"]).get("name", "").strip().lower() == ZUGANG.lower()}
    # je Karte die Einträge (Art, Zeit, Text), die übergehen, mit ihrer Anzahl (gleiche Zeilen in derselben Sekunde
    # zählen einzeln: geht ein Kommentar über, dann genau eine Zeile "hat kommentiert")
    weg: dict[str, Counter[tuple[str, str, str]]] = {}
    for z in v.execute("SELECT zeit, text, bilder FROM journal WHERE konto=? AND zeit>=? ORDER BY zeit", (inhaber, ab)):
        meldung, kommentar = MELDUNGEN.search(z["text"]), KOMMENTAR_MELDUNG.match(z["text"])
        if not meldung and not kommentar:
            continue
        for b in json.loads(z["bilder"]):
            if b["tabelle"] != "karten" or not b.get("nachher"):
                continue
            vorher, nachher = b.get("vorher") or {}, b["nachher"]
            if kommentar:
                if nachher.get("board") not in boards:
                    continue
                for c in _neu(vorher.get("kommentare") or [], nachher.get("kommentare") or [], inhaber, z["zeit"]):
                    if BERICHT.search(c.get("text") or ""):
                        weg.setdefault(b["id"], Counter())[("kommentare", c["zeit"], c["text"])] += 1
                        weg[b["id"]][("verlauf", z["zeit"], "hat kommentiert")] += 1
            else:
                for e in _neu(vorher.get("verlauf") or [], nachher.get("verlauf") or [], inhaber, z["zeit"]):
                    weg.setdefault(b["id"], Counter())[("verlauf", e["zeit"], e["text"])] += 1
    zahl = 0
    for karte, eintraege in weg.items():
        zeile = v.execute("SELECT daten FROM karten WHERE id=?", (karte,)).fetchone()
        if zeile is None:
            continue
        d = json.loads(zeile["daten"])
        for art in ("kommentare", "verlauf"):
            for e in d.get(art) or []:
                schluessel = (art, e.get("zeit"), e.get("text"))
                if e.get("von") == inhaber and eintraege[schluessel] > 0:
                    eintraege[schluessel] -= 1
                    e["von"] = helfer
                    zahl += 1
        v.execute("UPDATE karten SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), karte))
    v.execute("INSERT INTO zaehler (id, fassung, daten) VALUES (?, 1, ?)", (MERKER, json.dumps({"id": MERKER, "zahl": zahl})))
    # Rückgängig ginge auf Stände mit dem alten Urheber zurück
    v.execute("UPDATE journal SET rueckgaengig=0 WHERE rueckgaengig=1 AND konto=? AND zeit>=?", (inhaber, ab))
    return zahl
