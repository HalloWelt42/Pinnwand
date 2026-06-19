"""Berechnung der Termine einer Serie in einem Datumsbereich.

Unterstuetzt taeglich/woechentlich/monatlich mit Intervall, ausgewaehlten
Wochentagen (z.B. Mo und Mi), Monatstag und optionalem Ueberspringen von
Wochenenden. Feiertage/Urlaub werden spaeter (Phase Planung) zusaetzlich
ausgenommen.
"""
from __future__ import annotations

from datetime import date, timedelta


def _montag(d: date) -> date:
    return d - timedelta(days=d.weekday())


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
        monatstag = serie.get("monatstag") or start.day
        if d.day != monatstag:
            return False
        monate = (d.year - start.year) * 12 + (d.month - start.month)
        return monate % intervall == 0
    return False


def termine(serie: dict, von: date, bis: date) -> list[date]:
    start = date.fromisoformat(serie["start"]) if serie.get("start") else von
    ende = date.fromisoformat(serie["ende"]) if serie.get("ende") else None
    skip_we = bool(serie.get("wochenenden_ueberspringen"))
    out: list[date] = []
    cur = von
    while cur <= bis:
        if cur >= start and (ende is None or cur <= ende):
            if not (skip_we and cur.weekday() >= 5) and _passt(cur, serie, start):
                out.append(cur)
        cur += timedelta(days=1)
    return out
