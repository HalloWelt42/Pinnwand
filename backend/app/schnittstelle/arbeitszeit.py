"""Wege des Moduls Arbeitszeit: eigene Abwesenheiten eintragen und entfernen, eine neue Fassung des eigenen Zeitkontos,
und die Tagessummen eines Boards für die Ansicht Team."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..anwendung.rahmen import Antwort
from ..anwendung.stand import Team
from ..modell import AbwesenheitArt, Halbtagsregel, Kennung, Konto, Modell
from .zugriff import Zugriff


class NeueAbwesenheit(Modell):
    von: str
    bis: str
    art: AbwesenheitArt
    anteil: float | None = None
    notiz: str = ""


class Abwesenheiten(Modell):
    ids: list[Kennung]


class NeuesZeitkonto(Modell):
    ab: str
    wochenstunden: float
    tage: list[int]
    bundesland: str
    urlaubsanspruch: float
    resturlaub_vorjahr: float = 0
    halbtage: list[Halbtagsregel] = []


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/abwesenheiten", response_model=Antwort)
    async def eintragen(e: NeueAbwesenheit, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.arbeitszeit.eintragen(konto, e.von, e.bis, e.art, e.anteil, e.notiz))

    @r.post("/abwesenheiten/entfernen", response_model=Antwort)
    async def entfernen(e: Abwesenheiten, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.arbeitszeit.entfernen(konto, e.ids))

    @r.post("/zeitkonten", response_model=Antwort)
    async def zeitkonto_speichern(e: NeuesZeitkonto, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.arbeitszeit.zeitkonto_speichern(konto, e.ab, e.wochenstunden, e.tage, e.bundesland,
                                                           e.urlaubsanspruch, e.resturlaub_vorjahr, e.halbtage))

    @r.get("/team/{board_id}", response_model=Team)
    async def team(board_id: Kennung, von: str = Query(...), bis: str = Query(...), konto: Konto = Depends(ich)) -> Team:
        return await tun(d.abfragen.team(konto, board_id, von, bis))

    return r
