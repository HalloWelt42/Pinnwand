"""Wege des Moduls Serien und Termine: Serien anlegen, ändern, pausieren, fortsetzen, löschen, einen Tag auslassen;
Termine anlegen und zusagen; der Nachtrag am Folgetag (einzeln je Serie und Termin oder alle in einer Änderung). Feste
Pfade stehen vor denen mit Kennung."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..anwendung.serien import Serienangaben
from ..modell import Kennung, Konto, Modell
from .zugriff import Zugriff


class NeueSerie(Serienangaben):
    board: Kennung


class Tag(Modell):
    tag: str


class Bestaetigung(Tag):
    sekunden: int


class NeuerTermin(Modell):
    board: Kennung
    titel: str
    datum: str
    von: str
    bis: str
    teilnehmer: list[Kennung]
    ort: str = ""


class Zusage(Modell):
    ja: bool = True


class Posten(Modell):
    art: Literal["serie", "termin"]
    #: Kennung der Serie oder des Termins
    bezug: Kennung
    tag: str
    #: nur bei einer Serie; ohne: die geplante Dauer
    sekunden: int | None = None


class Nachtrag(Modell):
    posten: list[Posten]


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/serien", response_model=Antwort)
    async def serie_anlegen(e: NeueSerie, konto: Konto = Depends(ich)) -> Antwort:
        angaben = Serienangaben.model_validate(e.model_dump(exclude_unset=True, exclude={"board"}))
        return await tun(d.serien.anlegen(konto, e.board, angaben))

    @r.patch("/serien/{serie_id}", response_model=Antwort)
    async def serie_aendern(serie_id: Kennung, e: Serienangaben, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.aendern(konto, serie_id, e))

    @r.delete("/serien/{serie_id}", response_model=Antwort)
    async def serie_loeschen(serie_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.loeschen(konto, serie_id))

    @r.post("/serien/{serie_id}/pausieren", response_model=Antwort)
    async def pausieren(serie_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.pausieren(konto, serie_id))

    @r.post("/serien/{serie_id}/fortsetzen", response_model=Antwort)
    async def fortsetzen(serie_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.fortsetzen(konto, serie_id))

    @r.post("/serien/{serie_id}/auslassen", response_model=Antwort)
    async def auslassen(serie_id: Kennung, e: Tag, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.auslassen(konto, serie_id, e.tag))

    @r.post("/serien/{serie_id}/bestaetigen", response_model=Antwort)
    async def serie_bestaetigen(serie_id: Kennung, e: Bestaetigung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.bestaetigen(konto, serie_id, e.tag, e.sekunden))

    @r.post("/serien/{serie_id}/verwerfen", response_model=Antwort)
    async def serie_verwerfen(serie_id: Kennung, e: Tag, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.verwerfen(konto, serie_id, e.tag))

    @r.post("/termine", response_model=Antwort)
    async def termin_anlegen(e: NeuerTermin, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.termine.anlegen(konto, e.board, e.titel, e.datum, e.von, e.bis, e.teilnehmer, e.ort))

    @r.post("/termine/{termin_id}/zusagen", response_model=Antwort)
    async def zusagen(termin_id: Kennung, e: Zusage, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.termine.zusagen(konto, termin_id, e.ja))

    @r.post("/termine/{termin_id}/bestaetigen", response_model=Antwort)
    async def termin_bestaetigen(termin_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.termine.bestaetigen(konto, termin_id))

    @r.post("/termine/{termin_id}/verwerfen", response_model=Antwort)
    async def termin_verwerfen(termin_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.termine.verwerfen(konto, termin_id))

    @r.post("/nachtrag", response_model=Antwort)
    async def nachtrag(e: Nachtrag, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.serien.nachtrag(konto, [(p.art, p.bezug, p.tag, p.sekunden) for p in e.posten]))

    return r
