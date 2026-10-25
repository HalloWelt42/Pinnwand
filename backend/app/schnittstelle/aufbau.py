"""Wege am Aufbau eines Boards: Spalten (anlegen, ändern, ordnen, zur Erledigt-Spalte), Labels (anlegen, ändern, löschen),
eigene Felder (anlegen, ändern, Optionen, ordnen, löschen). Feste Pfade stehen vor denen mit Kennung."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.aufbau import Feldaenderung, Spaltenaenderung
from ..anwendung.rahmen import Antwort
from ..modell import Farbe, FeldArt, Kennung, Konto, Modell
from .boards import Reihenfolge
from .zugriff import Zugriff


class NeueSpalte(Modell):
    name: str
    farbe: Farbe


class NeuesLabel(Modell):
    name: str
    farbe: Farbe


class Labelaenderung(Modell):
    name: str | None = None
    farbe: Farbe | None = None


class NeuesFeld(Modell):
    name: str
    art: FeldArt


class Option(Modell):
    option: str
    #: hinzufügen, sonst entfernen
    dazu: bool = True


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/boards/{board_id}/spalten", response_model=Antwort)
    async def spalte_anlegen(board_id: Kennung, e: NeueSpalte, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.spalte_anlegen(konto, board_id, e.name, e.farbe))

    @r.post("/boards/{board_id}/spalten/ordnen", response_model=Antwort)
    async def spalten_ordnen(board_id: Kennung, e: Reihenfolge, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.spalten_ordnen(konto, board_id, e.ids))

    @r.post("/boards/{board_id}/spalten/{spalte_id}/aendern", response_model=Antwort)
    async def spalte_aendern(board_id: Kennung, spalte_id: Kennung, e: Spaltenaenderung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.spalte_aendern(konto, board_id, spalte_id, e))

    @r.post("/boards/{board_id}/spalten/{spalte_id}/erledigt", response_model=Antwort)
    async def zur_erledigt_spalte(board_id: Kennung, spalte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.zur_erledigt_spalte(konto, board_id, spalte_id))

    @r.post("/boards/{board_id}/labels", response_model=Antwort)
    async def label_anlegen(board_id: Kennung, e: NeuesLabel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.label_anlegen(konto, board_id, e.name, e.farbe))

    @r.post("/boards/{board_id}/labels/{label_id}/aendern", response_model=Antwort)
    async def label_aendern(board_id: Kennung, label_id: Kennung, e: Labelaenderung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.label_aendern(konto, board_id, label_id, e.name, e.farbe))

    @r.post("/boards/{board_id}/labels/{label_id}/loeschen", response_model=Antwort)
    async def label_loeschen(board_id: Kennung, label_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.label_loeschen(konto, board_id, label_id))

    @r.post("/boards/{board_id}/felder", response_model=Antwort)
    async def feld_anlegen(board_id: Kennung, e: NeuesFeld, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.feld_anlegen(konto, board_id, e.name, e.art))

    @r.post("/boards/{board_id}/felder/ordnen", response_model=Antwort)
    async def felder_ordnen(board_id: Kennung, e: Reihenfolge, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.felder_ordnen(konto, board_id, e.ids))

    @r.post("/boards/{board_id}/felder/{feld_id}/aendern", response_model=Antwort)
    async def feld_aendern(board_id: Kennung, feld_id: Kennung, e: Feldaenderung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.feld_aendern(konto, board_id, feld_id, e))

    @r.post("/boards/{board_id}/felder/{feld_id}/option", response_model=Antwort)
    async def feld_option(board_id: Kennung, feld_id: Kennung, e: Option, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.feld_option(konto, board_id, feld_id, e.option, e.dazu))

    @r.post("/boards/{board_id}/felder/{feld_id}/loeschen", response_model=Antwort)
    async def feld_loeschen(board_id: Kennung, feld_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.aufbau.feld_loeschen(konto, board_id, feld_id))

    return r
