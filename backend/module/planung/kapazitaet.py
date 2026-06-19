"""Kapazitaetsberechnung: Wochen-Soll je Person abzueglich Wochenende, Feiertag,
Sonderregeln (halbe Tage) und Abwesenheit. Nutzt die gemeinsame Tageslogik aus
kalender.py, damit Auswertung und Kalenderanzeige konsistent sind."""
from __future__ import annotations

from datetime import date, timedelta

from . import kalender
from . import persistence as db


def _grund(z: dict) -> str | None:
    """Leitet den dominanten Grund der Soll-Reduktion aus einer Tageszelle ab (fuer Berichte)."""
    if z["feiertag"] is not None:
        return "feiertag"
    if z["abw"]:
        return z["abw"]["typ"]
    if z["regel"] is not None:
        return "regel"
    if z["soll"] == 0:
        return "wochenende"
    return None


def kapazitaet(person_id: str, von: str, bis: str) -> dict | None:
    p = db.hole_person(person_id)
    if not p:
        return None
    zellen = kalender.tageszellen(p, von, bis)
    tage = [{"datum": z["datum"], "soll_std": z["soll"], "grund": _grund(z)} for z in zellen]
    summe = round(sum(z["soll"] for z in zellen), 2)
    return {"person_id": person_id, "name": p["name"], "summe_std": summe, "tage": tage}


def tage_overlay(von: str, bis: str, person_id: str | None = None) -> list[dict]:
    """Pro Tag: Wochenende, Feiertagsname, Urlaubsanteil - fuer die Kalender-Einfaerbung.

    Mit Person werden nur deren Feiertage (bundesweit + eigenes Bundesland) sowie
    deren Abwesenheit gezeigt, ohne Person alle hinterlegten Feiertage.
    """
    if person_id:
        p = db.hole_person(person_id)
        if p:
            return [
                {
                    "datum": z["datum"],
                    "wochenende": date.fromisoformat(z["datum"]).weekday() >= 5,
                    "feiertag": z["feiertag"],
                    "urlaub": z["abw"]["anteil"] if z["abw"] else 0,
                }
                for z in kalender.tageszellen(p, von, bis)
            ]
    feier = {f["datum"]: f["name"] for f in db.liste_feiertage(von, bis)}
    out: list[dict] = []
    cur = date.fromisoformat(von)
    ende = date.fromisoformat(bis)
    while cur <= ende:
        iso = cur.isoformat()
        out.append({"datum": iso, "wochenende": cur.weekday() >= 5, "feiertag": feier.get(iso), "urlaub": 0})
        cur += timedelta(days=1)
    return out
