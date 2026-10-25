"""Wege an dem, was der Person allein gehört: Ordner (anlegen, ordnen, umbenennen, löschen, ein Board einsortieren) und
das eigene Kürzel. Feste Pfade stehen vor denen mit Kennung."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .boards import Name, Reihenfolge
from .zugriff import Zugriff


class Ordnerwahl(Modell):
    #: null: ohne Ordner
    ordner: Kennung | None = None


class Kuerzel(Modell):
    kuerzel: str


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/ordner", response_model=Antwort)
    async def anlegen(e: Name, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.ordner_anlegen(konto, e.name))

    @r.post("/ordner/ordnen", response_model=Antwort)
    async def ordnen(e: Reihenfolge, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.ordner_ordnen(konto, e.ids))

    @r.post("/ordner/{ordner_id}/umbenennen", response_model=Antwort)
    async def umbenennen(ordner_id: Kennung, e: Name, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.ordner_umbenennen(konto, ordner_id, e.name))

    @r.post("/ordner/{ordner_id}/loeschen", response_model=Antwort)
    async def loeschen(ordner_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.ordner_loeschen(konto, ordner_id))

    @r.post("/boards/{board_id}/ordner", response_model=Antwort)
    async def einsortieren(board_id: Kennung, e: Ordnerwahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.ordner_setzen(konto, board_id, e.ordner))

    @r.post("/ich/kuerzel", response_model=Antwort)
    async def kuerzel(e: Kuerzel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.kuerzel_setzen(konto, e.kuerzel))

    return r
