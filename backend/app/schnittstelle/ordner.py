"""Wege an dem, was der Person allein gehört: Ordner (anlegen, ordnen, umbenennen, löschen, ein Board einsortieren),
das eigene Kürzel und das eigene Konto (zurücksetzen, löschen; andere Konten nur als Besitzer der App). Feste Pfade
stehen vor denen mit Kennung."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import Field

from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .boards import Name, Reihenfolge
from .zugriff import Zugriff


class Ordnerwahl(Modell):
    #: null: ohne Ordner
    ordner: Kennung | None = None
    #: Stelle im Ordner (ab 0); ohne Angabe ans Ende
    stelle: int | None = Field(default=None, ge=0)


class Bestaetigung(Modell):
    #: zur Sicherheit eingetippt: der Name des Kontos
    bestaetigung: str


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
        return await tun(d.persoenlich.ordner_setzen(konto, board_id, e.ordner, e.stelle))

    @r.post("/konten/{konto_id}/zuruecksetzen", response_model=Antwort)
    async def zuruecksetzen(konto_id: Kennung, e: Bestaetigung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.konten.zuruecksetzen(konto, konto_id, e.bestaetigung))

    @r.post("/konten/{konto_id}/entfernen", response_model=Antwort)
    async def loeschen_konto(konto_id: Kennung, e: Bestaetigung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.konten.zuruecksetzen(konto, konto_id, e.bestaetigung, loeschen=True))

    @r.post("/ich/kuerzel", response_model=Antwort)
    async def kuerzel(e: Kuerzel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.persoenlich.kuerzel_setzen(konto, e.kuerzel))

    return r
