"""Wege an Boards: anlegen aus einer Vorlage, Personen einladen."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.boards import Einladung
from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .zugriff import Zugriff


class NeuesBoard(Modell):
    vorlage: Kennung
    name: str
    kuerzel: str
    ordner: Kennung | None = None
    einladungen: list[Einladung] = []


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/boards", response_model=Antwort)
    async def anlegen(e: NeuesBoard, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.anlegen(konto, e.vorlage, e.name, e.kuerzel, e.ordner, e.einladungen))

    @r.post("/boards/{board_id}/mitglieder", response_model=Antwort)
    async def einladen(board_id: Kennung, e: Einladung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.einladen(konto, board_id, e))

    return r
