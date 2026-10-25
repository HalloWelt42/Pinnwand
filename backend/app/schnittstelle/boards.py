"""Wege an Boards: anlegen aus einer Vorlage (vorher das Kürzel prüfen), Personen einladen, Name, Farbe, Kartenart,
Einstellungen, Module, als Vorlage speichern. Hier stehen auch die kleinen Eingaben, die mehrere Bereiche teilen."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.boards import Einladung, Einstellungsteil, KuerzelPruefung
from ..anwendung.rahmen import Antwort
from ..modell import Farbe, Kartenart, Kennung, Konto, Modell
from .zugriff import Zugriff


class NeuesBoard(Modell):
    vorlage: Kennung
    name: str
    kuerzel: str
    ordner: Kennung | None = None
    einladungen: list[Einladung] = []


class Name(Modell):
    name: str


class Farbwahl(Modell):
    farbe: Farbe


class Kartenartwahl(Modell):
    kartenart: Kartenart


class Schalter(Modell):
    an: bool


class Reihenfolge(Modell):
    """Die Kennungen in der neuen Reihenfolge, jede genau einmal."""

    ids: list[Kennung]


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.get("/kuerzel/{kuerzel}", response_model=KuerzelPruefung)
    async def kuerzel(kuerzel: str, konto: Konto = Depends(ich)) -> KuerzelPruefung:
        return await d.boards.kuerzel_pruefen(konto, kuerzel)

    @r.post("/boards", response_model=Antwort)
    async def anlegen(e: NeuesBoard, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.anlegen(konto, e.vorlage, e.name, e.kuerzel, e.ordner, e.einladungen))

    @r.post("/boards/{board_id}/mitglieder", response_model=Antwort)
    async def einladen(board_id: Kennung, e: Einladung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.einladen(konto, board_id, e))

    @r.post("/boards/{board_id}/umbenennen", response_model=Antwort)
    async def umbenennen(board_id: Kennung, e: Name, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.umbenennen(konto, board_id, e.name))

    @r.post("/boards/{board_id}/farbe", response_model=Antwort)
    async def farbe(board_id: Kennung, e: Farbwahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.farbe_setzen(konto, board_id, e.farbe))

    @r.post("/boards/{board_id}/kartenart", response_model=Antwort)
    async def kartenart(board_id: Kennung, e: Kartenartwahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.kartenart_setzen(konto, board_id, e.kartenart))

    @r.post("/boards/{board_id}/einstellungen", response_model=Antwort)
    async def einstellungen(board_id: Kennung, e: Einstellungsteil, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.einstellungen_setzen(konto, board_id, e))

    @r.post("/boards/{board_id}/module/{modul}", response_model=Antwort)
    async def modul(board_id: Kennung, modul: str, e: Schalter, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.modul_schalten(konto, board_id, modul, e.an))

    @r.post("/boards/{board_id}/vorlage", response_model=Antwort)
    async def vorlage(board_id: Kennung, e: Name, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.als_vorlage(konto, board_id, e.name))

    return r
