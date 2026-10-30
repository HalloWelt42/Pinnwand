"""Gesamtnummer der Karten nachtragen (HELF-49): einmal beim ersten Start mit der Schemastufe, in einer Transaktion.

Jede vorhandene Karte bekommt in der Reihenfolge ihrer Anlage die nächste Nummer ab 1; in derselben Sekunde angelegte
ordnet ihre Nummer im Board, in dem sie entstanden (der erste Schlüssel), danach die Kennung;
auch die Karten im Papierkorb (sie kommen beim Wiederherstellen mit ihrer Nummer zurück). Danach steht der Zähler auf
der höchsten Nummer, und jede neue Karte holt ihre Nummer im Rahmen der Änderung (`Kontext.neue_nummern`). Rückgängig
von Änderungen aus der Zeit davor ginge auf einen Stand ohne Nummer zurück; diese Rückwege gelten darum nicht mehr.
Läuft nur, solange es den Zähler noch nicht gibt; ein zweiter Lauf ändert nichts."""

from __future__ import annotations

import json
import sqlite3

from .rahmen import GESAMTNUMMER


def _reihenfolge(d: dict) -> tuple[str, int, str]:
    """Wann die Karte entstand: Anlagezeit, dann ihre Nummer im ersten Board (die Zeit hat nur Sekunden)."""
    erster = (d.get("frueher") or [d.get("schluessel") or ""])[0]
    nummer = erster.rsplit("-", 1)[-1]
    return d.get("erstelltAm") or "", int(nummer) if nummer.isdigit() else 0, d["id"]


def nachtragen(v: sqlite3.Connection) -> int:
    """Nummeriert alle Karten, wenn der Zähler noch fehlt. Ergebnis: wie viele Karten eine Nummer bekamen."""
    if v.execute("SELECT 1 FROM zaehler WHERE id=?", (GESAMTNUMMER,)).fetchone():
        return 0
    # (Reihenfolge, Kennung, Ort, Eintrag): Ort "karten" oder "papierkorb" mit der Kennung des Eintrags
    alle: list[tuple[tuple[str, int, str], str, str, str | None]] = []
    for z in v.execute("SELECT id, daten FROM karten"):
        d = json.loads(z["daten"])
        alle.append((_reihenfolge({**d, "id": z["id"]}), z["id"], "karten", None))
    eintraege: dict[str, dict] = {}
    for z in v.execute("SELECT id, daten FROM papierkorb"):
        d = json.loads(z["daten"])
        eintraege[z["id"]] = d
        for c in d.get("karten") or []:
            alle.append((_reihenfolge(c), c["id"], "papierkorb", z["id"]))
    alle.sort(key=lambda x: x[0])
    nummern = {(ort, eintrag, kid): i for i, (_, kid, ort, eintrag) in enumerate(alle, start=1)}
    for (ort, eintrag, kid), n in nummern.items():
        if ort != "karten":
            continue
        d = json.loads(v.execute("SELECT daten FROM karten WHERE id=?", (kid,)).fetchone()["daten"])
        d["nummer"] = n
        v.execute("UPDATE karten SET daten=?, nummer=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), n, kid))
    for eid, d in eintraege.items():
        for c in d.get("karten") or []:
            c["nummer"] = nummern[("papierkorb", eid, c["id"])]
        v.execute("UPDATE papierkorb SET daten=?, fassung=fassung+1 WHERE id=?", (json.dumps(d, ensure_ascii=False), eid))
    v.execute("INSERT INTO zaehler (id, fassung, daten) VALUES (?, 1, ?)",
              (GESAMTNUMMER, json.dumps({"id": GESAMTNUMMER, "zahl": len(alle)})))
    v.execute("UPDATE journal SET rueckgaengig=0 WHERE rueckgaengig=1")
    return len(alle)
