"""Regeln der Zeiterfassung als reine Funktionen: eine Timer-Sitzung in Teile je Tag zerlegen (an Mitternacht), über
zwölf Stunden deckeln, Einträge kürzen und die Reihenfolge, in der sie beim Kürzen gehen. Gleich `sitzungBuchen` und
den Hilfen in mockups/src/beispiel/anwendung/zeiten.svelte.ts. Zeitpunkte sind Ortszeit ohne Zone wie die Uhr der
Pinnwand; gerechnet wird mit der Zone, damit eine Nacht mit Zeitumstellung richtig zählt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta, tzinfo

from ..modell import Zeiteintrag

#: Ein Timer bucht höchstens so lange am Stück; mehr wird gedeckelt, und die Person nennt das echte Ende
DECKEL_SEK = 12 * 3600
#: Wer zuerst geht, wenn eine Tageszeit gekürzt wird: Korrektur, dann nachgetragen, dann Serie, dann Timer
RANG_DER_HERKUNFT = {"korrektur": 3, "hand": 2, "serie": 1, "timer": 0}


@dataclass(frozen=True)
class Teil:
    """Ein Teil einer Sitzung an einem Tag, Uhrzeiten als "HH:MM" (das Ende um Mitternacht als "24:00")."""

    tag: str
    von: str
    bis: str
    sekunden: int


def ortszeit(text: str, zone: tzinfo) -> datetime:
    return datetime.fromisoformat(text[:19]).replace(tzinfo=zone)


def sekunden_zwischen(a: datetime, b: datetime) -> int:
    """Echte Sekunden von a nach b (über UTC, also auch über eine Zeitumstellung richtig)."""
    return int((b.astimezone(UTC) - a.astimezone(UTC)).total_seconds())


def sitzung_teile(seit: str, bis: str, zone: tzinfo, deckeln: bool = True) -> tuple[list[Teil], int]:
    """Die Sitzung von `seit` bis `bis` in Teile je Tag. Ergebnis: die Teile (zusammen höchstens 12 Stunden, wenn
    gedeckelt wird) und die echte Dauer der Sitzung in Sekunden."""
    start, ende = ortszeit(seit, zone), ortszeit(bis, zone)
    gesamt = max(0, sekunden_zwischen(start, ende))
    rest = min(gesamt, DECKEL_SEK) if deckeln else gesamt
    teile: list[Teil] = []
    von = start
    while rest > 0:
        mitternacht = datetime.combine(von.date() + timedelta(days=1), time(), tzinfo=zone)
        bis_mitternacht = sekunden_zwischen(von, mitternacht)
        sek = min(rest, bis_mitternacht)
        stop = mitternacht if sek == bis_mitternacht else (von.astimezone(UTC) + timedelta(seconds=sek)).astimezone(zone)
        teile.append(Teil(von.date().isoformat(), von.strftime("%H:%M"),
                          "24:00" if stop == mitternacht else stop.strftime("%H:%M"), sek))
        rest -= sek
        von = stop
    return teile, gesamt


def minuten(uhrzeit: str) -> int:
    """"07:30" in Minuten seit Mitternacht ("24:00" ist 1440)."""
    h, m = uhrzeit.split(":")
    return int(h) * 60 + int(m)


def uhrzeit(minuten_: int) -> str:
    return f"{minuten_ // 60:02d}:{minuten_ % 60:02d}"


def rang(e: Zeiteintrag) -> int:
    """Jüngster zuerst: Korrektur, dann nachgetragen, dann Serie, dann Timer nach seinem Ende."""
    return RANG_DER_HERKUNFT[e.herkunft] * 10000 + (minuten(e.bis) if e.bis else 0)


def kuerzen(e: Zeiteintrag, sek: int) -> None:
    """Einen Eintrag um `sek` kürzen; bei einem Timer-Eintrag rückt das Ende mit, damit von, bis und Dauer
    zusammenpassen."""
    e.sekunden -= sek
    if e.herkunft == "timer" and e.von and e.bis:
        e.bis = uhrzeit(max(minuten(e.von), minuten(e.bis) - round(sek / 60)))
        if e.sitzungen:
            e.sitzungen[-1].bis = e.bis


def verlaengern(e: Zeiteintrag, sek: int) -> None:
    """Einen Eintrag auf `sek` verlängern; ein Timer-Eintrag aus einer Sitzung bekommt das passende Ende (höchstens
    Mitternacht)."""
    e.sekunden = sek
    if e.herkunft == "timer" and e.von and e.bis and not e.sitzungen:
        e.bis = uhrzeit(min(24 * 60, minuten(e.von) + round(sek / 60)))


def dauer_text(sek: int) -> str:
    """Dauer für Menschen wie in der Oberfläche: "1:30"."""
    return f"{sek // 3600}:{(sek % 3600) // 60:02d}"
