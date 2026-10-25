"""Wege des Moduls Zeiterfassung: der eigene Timer, Zeit buchen und setzen, Einträge ändern und löschen, die Rückfrage
nach dem Deckel. Feste Pfade stehen vor denen mit Kennung (sonst nimmt /zeiten/{id}/... auch "deckel")."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .zugriff import Zugriff


class TimerStart(Modell):
    karte: Kennung


class Buchung(Modell):
    karte: Kennung
    datum: str
    sekunden: int
    notiz: str = ""


class Tageszeit(Modell):
    karte: Kennung
    datum: str
    sekunden: int


class Ticketzeit(Modell):
    karte: Kennung
    sekunden: int


class Deckel(Modell):
    ids: list[Kennung]


class DeckelEnde(Deckel):
    ende: str


class Dauer(Modell):
    sekunden: int


class Datum(Modell):
    datum: str


class Notiz(Modell):
    notiz: str = ""


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/timer/starten", response_model=Antwort)
    async def starten(e: TimerStart, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.starten(konto, e.karte))

    @r.post("/timer/anhalten", response_model=Antwort)
    async def anhalten(konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.anhalten(konto))

    @r.post("/timer/fortsetzen", response_model=Antwort)
    async def fortsetzen(konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.fortsetzen(konto))

    @r.post("/timer/stoppen", response_model=Antwort)
    async def stoppen(konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.stoppen(konto))

    @r.post("/zeiten", response_model=Antwort)
    async def buchen(e: Buchung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.buchen(konto, e.karte, e.datum, e.sekunden, e.notiz))

    @r.post("/zeiten/tag", response_model=Antwort)
    async def tag_setzen(e: Tageszeit, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.tag_setzen(konto, e.karte, e.datum, e.sekunden))

    @r.post("/zeiten/ticketzeit", response_model=Antwort)
    async def ticketzeit_setzen(e: Ticketzeit, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.ticketzeit_setzen(konto, e.karte, e.sekunden))

    @r.post("/zeiten/deckel", response_model=Antwort)
    async def deckel_korrigieren(e: DeckelEnde, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.deckel_korrigieren(konto, e.ids, e.ende))

    @r.post("/zeiten/deckel/bestaetigen", response_model=Antwort)
    async def deckel_bestaetigen(e: Deckel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.deckel_bestaetigen(konto, e.ids))

    @r.post("/zeiten/{eintrag_id}/dauer", response_model=Antwort)
    async def dauer_aendern(eintrag_id: Kennung, e: Dauer, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.dauer_aendern(konto, eintrag_id, e.sekunden))

    @r.post("/zeiten/{eintrag_id}/datum", response_model=Antwort)
    async def datum_aendern(eintrag_id: Kennung, e: Datum, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.datum_aendern(konto, eintrag_id, e.datum))

    @r.post("/zeiten/{eintrag_id}/notiz", response_model=Antwort)
    async def notiz_aendern(eintrag_id: Kennung, e: Notiz, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.notiz_aendern(konto, eintrag_id, e.notiz))

    @r.delete("/zeiten/{eintrag_id}", response_model=Antwort)
    async def loeschen(eintrag_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.zeiterfassung.loeschen(konto, eintrag_id))

    return r
