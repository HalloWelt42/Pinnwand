"""Kapazitätsberechnung: Wochen-Soll je Person abzüglich Wochenende, Feiertag,
Sonderregeln (halbe Tage) und Abwesenheit. Nutzt die gemeinsame Tageslogik aus
kalender.py, damit Auswertung und Kalenderanzeige konsistent sind."""
from __future__ import annotations

from datetime import date, timedelta

from app.db import verbindung

from . import kalender
from . import persistence as db


def _grund(z: dict) -> str | None:
    """Leitet den dominanten Grund der Soll-Reduktion aus einer Tageszelle ab (für Berichte)."""
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


def _ist_sek_gesamt(von: str, bis: str) -> int:
    """Geleistete Sekunden insgesamt im Zeitraum: alle Zeiteintraege (auch ohne
    Zustaendigen) plus bestaetigte Termine als zweite Ist-Quelle."""
    with verbindung() as conn:
        r = conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) AS s FROM zeiteintrag WHERE datum >= ? AND datum <= ?",
            (von, bis),
        ).fetchone()
    ist = int(r["s"] or 0)
    try:
        from module.termine import dienst as _td
        ist += sum(int(m) for m in _td.ist_minuten_je_tag_person(von, bis).values()) * 60
    except Exception:
        pass
    return ist


def _soll_sek_gesamt(von: str, bis: str) -> int:
    """Soll-Sekunden insgesamt im Zeitraum: Summe der Kapazitaet aller Personen."""
    total_std = 0.0
    for p in db.liste_personen():
        k = kapazitaet(p["id"], von, bis)
        if k:
            total_std += k["summe_std"]
    return int(round(total_std * 3600))


def _zeitraeume(heute: date) -> dict[str, tuple[date, date]]:
    montag = heute - timedelta(days=heute.weekday())
    monat_anf = heute.replace(day=1)
    naechster = (monat_anf.replace(year=monat_anf.year + 1, month=1)
                 if monat_anf.month == 12 else monat_anf.replace(month=monat_anf.month + 1))
    monat_end = naechster - timedelta(days=1)
    return {
        "heute": (heute, heute),
        "woche": (montag, montag + timedelta(days=6)),
        "monat": (monat_anf, monat_end),
        "jahr": (heute.replace(month=1, day=1), heute.replace(month=12, day=31)),
    }


def stunden_uebersicht(heute: date | None = None) -> dict:
    """Geleistete Stunden (Ist) gegen Soll je Heute/Woche/Monat/Jahr - in Sekunden."""
    bezug = heute or date.today()
    out: dict[str, dict[str, int]] = {}
    for name, (a, b) in _zeitraeume(bezug).items():
        va, vb = a.isoformat(), b.isoformat()
        out[name] = {"ist_sek": _ist_sek_gesamt(va, vb), "soll_sek": _soll_sek_gesamt(va, vb)}
    return out


def tage_overlay(von: str, bis: str, person_id: str | None = None) -> list[dict]:
    """Pro Tag: Wochenende, Feiertagsname, Urlaubsanteil - für die Kalender-Einfärbung.

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
