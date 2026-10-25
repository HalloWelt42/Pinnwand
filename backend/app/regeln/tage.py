"""Rechnen mit Kalendertagen als reine Funktionen (Tage als ISO-Zeichenkette JJJJ-MM-TT), gleich frontend/src/regeln/tage.ts."""

from __future__ import annotations

import re
from datetime import date, timedelta

TAG_MUSTER = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: Wochentage kurz, Montag zuerst (wie date.weekday())
TAGE_KURZ = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def tag(text: str) -> date:
    return date.fromisoformat(text[:10])


def ist_tag(text: str) -> bool:
    """Ein gültiger Kalendertag in der Form JJJJ-MM-TT."""
    if not TAG_MUSTER.match(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def tage_zwischen(a: str, b: str) -> int:
    """Ganze Kalendertage von a nach b (negativ, wenn b vor a liegt)."""
    return (tag(b) - tag(a)).days


def plus_tage(t: str, n: int) -> str:
    return (tag(t) + timedelta(days=n)).isoformat()


def montag_von(t: str) -> str:
    d = tag(t)
    return (d - timedelta(days=d.weekday())).isoformat()


def datum_text(t: str) -> str:
    """Tag lesbar mit Wochentag: "Di 27.10.2026" (wie datumJahr der Oberfläche)."""
    d = tag(t)
    return f"{TAGE_KURZ[d.weekday()]} {d.day:02d}.{d.month:02d}.{d.year}"


def datum_kurz(t: str) -> str:
    """Tag lesbar ohne Jahr: "Di 27.10." (wie datum der Oberfläche mit Wochentag)."""
    d = tag(t)
    return f"{TAGE_KURZ[d.weekday()]} {d.day:02d}.{d.month:02d}."


def spanne_text(von: str, bis: str) -> str:
    """Zeitraum zweier Tage wie spanne der Oberfläche: "Di 27.10.2026" oder "Mo 26.10. bis Fr 30.10.2026"."""
    return datum_text(von) if von == bis else f"{datum_kurz(von)} bis {datum_text(bis)}"


def wochentag(t: str) -> int:
    """0 Sonntag, 1 Montag bis 6 Samstag, wie die Oberfläche (Zeitkonto.tage, Serie.tage)."""
    return (tag(t).weekday() + 1) % 7


def ist_wochenende(t: str) -> bool:
    return wochentag(t) in (0, 6)


def tage_von(von: str, bis: str) -> list[str]:
    """Alle Tage von bis einschließlich bis."""
    a, b = tag(von), tag(bis)
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def tage_im_monat(jahr: int, monat: int) -> int:
    folgemonat = date(jahr + monat // 12, monat % 12 + 1, 1)
    return (folgemonat - timedelta(days=1)).day
