"""Kapazitaetsberechnung: Wochen-Soll je Person abzueglich Wochenende,
Feiertag und Urlaub (halbe Tage anteilig)."""
from __future__ import annotations

from datetime import date, timedelta

from . import persistence as db


def kapazitaet(person_id: str, von: str, bis: str) -> dict | None:
    p = db.hole_person(person_id)
    if not p:
        return None
    ws = p["wochenstunden"]
    feier = {f["datum"] for f in db.feiertage_relevant(von, bis, p.get("bundesland"))}
    url = {u["datum"]: u["anteil"] for u in db.liste_urlaub(person_id, von, bis)}
    tage: list[dict] = []
    summe = 0.0
    cur = date.fromisoformat(von)
    ende = date.fromisoformat(bis)
    while cur <= ende:
        iso = cur.isoformat()
        wd = cur.weekday()
        basis = float(ws[wd]) if wd < len(ws) else 0.0
        grund = None
        if basis == 0 and wd >= 5:
            grund = "wochenende"
        if iso in feier:
            basis = 0.0
            grund = "feiertag"
        elif iso in url:
            anteil = url[iso]
            basis = round(basis * (1 - anteil), 2)
            grund = "urlaub" if anteil >= 1 else "urlaub_halb"
        summe += basis
        tage.append({"datum": iso, "soll_std": round(basis, 2), "grund": grund})
        cur += timedelta(days=1)
    return {"person_id": person_id, "name": p["name"], "summe_std": round(summe, 2), "tage": tage}


def tage_overlay(von: str, bis: str, person_id: str | None = None) -> list[dict]:
    """Pro Tag: Wochenende, Feiertagsname, Urlaubsanteil - fuer die Kalender-Einfaerbung.

    Mit Person werden nur deren Feiertage (bundesweit + eigenes Bundesland) gezeigt,
    ohne Person alle hinterlegten Feiertage.
    """
    url: dict[str, float] = {}
    if person_id:
        p = db.hole_person(person_id)
        feier = {f["datum"]: f["name"] for f in db.feiertage_relevant(von, bis, p.get("bundesland") if p else None)}
        url = {u["datum"]: u["anteil"] for u in db.liste_urlaub(person_id, von, bis)}
    else:
        feier = {f["datum"]: f["name"] for f in db.liste_feiertage(von, bis)}
    out: list[dict] = []
    cur = date.fromisoformat(von)
    ende = date.fromisoformat(bis)
    while cur <= ende:
        iso = cur.isoformat()
        out.append({
            "datum": iso,
            "wochenende": cur.weekday() >= 5,
            "feiertag": feier.get(iso),
            "urlaub": url.get(iso, 0),
        })
        cur += timedelta(days=1)
    return out
