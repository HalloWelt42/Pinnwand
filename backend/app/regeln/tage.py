"""Rechnen mit Kalendertagen als reine Funktionen (Tage als ISO-Zeichenkette JJJJ-MM-TT), gleich frontend/src/regeln/tage.ts."""

from __future__ import annotations

import re
from datetime import date, timedelta

TAG_MUSTER = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
