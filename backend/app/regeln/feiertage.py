"""Gesetzliche Feiertage je Bundesland als reine Regel: feste Tage und die beweglichen nach der Osterformel. Gleich
frontend/src/regeln/feiertage.ts; im Server für die Serien (Werktage, Feiertage überspringen)."""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from .tage import plus_tage, tag


def ostersonntag(jahr: int) -> str:
    """Ostersonntag nach der Gaußschen Osterformel (gregorianisch)."""
    a, b, c = jahr % 19, jahr // 100, jahr % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    monat = (h + l - 7 * m + 114) // 31
    tag_ = (h + l - 7 * m + 114) % 31 + 1
    return date(jahr, monat, tag_).isoformat()


def buss_und_bettag(jahr: int) -> str:
    """Der Mittwoch vor dem 23. November."""
    d = date(jahr, 11, 22)
    while d.weekday() != 2:
        d -= timedelta(days=1)
    return d.isoformat()


@dataclass(frozen=True)
class Regel:
    name: str
    tag: Callable[[int], str]
    #: leer: in allen Ländern
    laender: tuple[str, ...] = ()


def fest(mmtt: str) -> Callable[[int], str]:
    return lambda jahr: f"{jahr}-{mmtt}"


def ostern(n: int) -> Callable[[int], str]:
    return lambda jahr: plus_tage(ostersonntag(jahr), n)


REGELN: tuple[Regel, ...] = (
    Regel("Neujahr", fest("01-01")),
    Regel("Heilige Drei Könige", fest("01-06"), ("Baden-Württemberg", "Bayern", "Sachsen-Anhalt")),
    Regel("Frauentag", fest("03-08"), ("Berlin", "Mecklenburg-Vorpommern")),
    Regel("Karfreitag", ostern(-2)),
    Regel("Ostersonntag", ostern(0), ("Brandenburg",)),
    Regel("Ostermontag", ostern(1)),
    Regel("Tag der Arbeit", fest("05-01")),
    Regel("Christi Himmelfahrt", ostern(39)),
    Regel("Pfingstsonntag", ostern(49), ("Brandenburg",)),
    Regel("Pfingstmontag", ostern(50)),
    Regel("Fronleichnam", ostern(60), ("Baden-Württemberg", "Bayern", "Hessen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
                                      "Saarland")),
    Regel("Mariä Himmelfahrt", fest("08-15"), ("Saarland",)),
    Regel("Weltkindertag", fest("09-20"), ("Thüringen",)),
    Regel("Tag der Deutschen Einheit", fest("10-03")),
    Regel("Reformationstag", fest("10-31"), ("Brandenburg", "Bremen", "Hamburg", "Mecklenburg-Vorpommern", "Niedersachsen",
                                            "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen")),
    Regel("Allerheiligen", fest("11-01"), ("Baden-Württemberg", "Bayern", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland")),
    Regel("Buß- und Bettag", buss_und_bettag, ("Sachsen",)),
    Regel("1. Weihnachtstag", fest("12-25")),
    Regel("2. Weihnachtstag", fest("12-26")),
)


@functools.cache
def feiertage(jahr: int, bundesland: str) -> dict[str, str]:
    """Feiertage eines Jahres in einem Bundesland: Tag auf Name."""
    return {r.tag(jahr): r.name for r in REGELN if not r.laender or bundesland in r.laender}


def feiertag(t: str, bundesland: str) -> str | None:
    """Name des Feiertags an diesem Tag im Bundesland, sonst None."""
    return feiertage(tag(t).year, bundesland).get(t[:10])
