"""Wege an Hinweisen: einen gelesen oder ungelesen (still, ohne Rückweg), alle gelesen, einen Weg je Art ein- oder
ausschalten. Feste Pfade stehen vor denen mit Kennung."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..modell import HinweisArt, HinweisWeg, Kennung, Konto, Modell
from .zugriff import Zugriff


class Gelesen(Modell):
    gelesen: bool = True


class Weg(Modell):
    art: HinweisArt
    weg: HinweisWeg
    an: bool


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/hinweise/alle-gelesen", response_model=Antwort)
    async def alle_gelesen(konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.hinweise.alle_gelesen(konto))

    @r.post("/hinweise/weg", response_model=Antwort)
    async def weg_setzen(e: Weg, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.hinweise.weg_setzen(konto, e.art, e.weg, e.an))

    @r.post("/hinweise/{hinweis_id}/gelesen", response_model=Antwort)
    async def gelesen(hinweis_id: Kennung, e: Gelesen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.hinweise.gelesen(konto, hinweis_id, e.gelesen))

    return r
