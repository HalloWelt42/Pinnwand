"""Wege der Commits an Karten (HELF-35): Einspielen durch den Commitsammler (nur der Besitzer der App), Suchen,
Verknüpfen und Lösen am Ticket."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.commits import Eingespielt, Sendung
from ..anwendung.rahmen import Antwort
from ..modell import Commit, Kennung, Konto, Modell
from .zugriff import Zugriff


class Verknuepfen(Modell):
    #: Kennung des Commits (repo@hash), wie die Suche sie liefert
    commit: Kennung


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/commits/einspielen", response_model=Eingespielt)
    async def einspielen(s: Sendung, konto: Konto = Depends(ich)) -> Eingespielt:
        return await tun(d.commits.einspielen(konto, s))

    @r.get("/karten/{karte_id}/commits/suche", response_model=list[Commit])
    async def suchen(karte_id: Kennung, text: str = "", konto: Konto = Depends(ich)) -> list[Commit]:
        return await tun(d.commits.suchen(konto, karte_id, text))

    @r.post("/karten/{karte_id}/commits", response_model=Antwort)
    async def verknuepfen(karte_id: Kennung, v: Verknuepfen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.commits.verknuepfen(konto, karte_id, v.commit))

    @r.delete("/karten/{karte_id}/commits/{bezug_id}", response_model=Antwort)
    async def loesen(karte_id: Kennung, bezug_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.commits.loesen(konto, karte_id, bezug_id))

    return r
