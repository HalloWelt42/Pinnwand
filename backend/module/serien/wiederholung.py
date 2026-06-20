"""Berechnung der Termine einer Serie in einem Datumsbereich.

Unterstuetzt taeglich/woechentlich/monatlich mit Intervall, ausgewaehlten
Wochentagen (z.B. Mo und Mi), Monatstag oder erstem/letztem Werktag des Monats
sowie optionalem Ueberspringen von Wochenenden und Feiertagen.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta


def _montag(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _erster_werktag(jahr: int, monat: int) -> int:
    for tag in range(1, 8):
        if date(jahr, monat, tag).weekday() < 5:
            return tag
    return 1


def _letzter_werktag(jahr: int, monat: int) -> int:
    letzter = calendar.monthrange(jahr, monat)[1]
    for tag in range(letzter, letzter - 7, -1):
        if date(jahr, monat, tag).weekday() < 5:
            return tag
    return letzter


def _ziel_monatstag(d: date, serie: dict, start: date) -> int:
    regel = serie.get("monatsregel") or "tag"
    if regel == "erster_werktag":
        return _erster_werktag(d.year, d.month)
    if regel == "letzter_werktag":
        return _letzter_werktag(d.year, d.month)
    return serie.get("monatstag") or start.day


def _passt(d: date, serie: dict, start: date) -> bool:
    typ = serie.get("typ")
    intervall = max(1, int(serie.get("intervall") or 1))
    if typ == "taeglich":
        return (d - start).days % intervall == 0
    if typ == "woechentlich":
        wochentage = serie.get("wochentage") or []
        if wochentage and d.weekday() not in wochentage:
            return False
        if not wochentage and d.weekday() != start.weekday():
            return False
        wochen = (_montag(d) - _montag(start)).days // 7
        return wochen % intervall == 0
    if typ == "monatlich":
        if d.day != _ziel_monatstag(d, serie, start):
            return False
        monate = (d.year - start.year) * 12 + (d.month - start.month)
        return monate % intervall == 0
    return False


def termine(serie: dict, von: date, bis: date, feiertage: set[str] | None = None) -> list[date]:
    start = date.fromisoformat(serie["start"]) if serie.get("start") else von
    ende = date.fromisoformat(serie["ende"]) if serie.get("ende") else None
    skip_we = bool(serie.get("wochenenden_ueberspringen"))
    skip_ft = bool(serie.get("feiertage_ueberspringen")) and bool(feiertage)
    out: list[date] = []
    cur = von
    while cur <= bis:
        if cur >= start and (ende is None or cur <= ende):
            if skip_we and cur.weekday() >= 5:
                pass
            elif skip_ft and cur.isoformat() in feiertage:
                pass
            elif _passt(cur, serie, start):
                out.append(cur)
        cur += timedelta(days=1)
    return out
