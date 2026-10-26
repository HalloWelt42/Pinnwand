"""Wege des Papierkorbs: Karten, eine Spalte oder ein Board hineinlegen, einen Eintrag wiederherstellen, gewählte
Einträge oder den ganzen Papierkorb eines Boards endgültig entfernen (ohne Rückweg); eine Karte oder ein Board gleich
endgültig löschen, bestätigt mit Schlüssel oder Kürzel."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .karten import Sammel
from .zugriff import Zugriff


class Bestaetigung(Modell):
    #: zur Sicherheit eingetippt: Schlüssel der Karte oder Kürzel des Boards
    bestaetigung: str


class SpalteLoeschen(Modell):
    #: Spalte, in die die Karten vorher wandern; ohne: sie liegen mit der Spalte im Papierkorb
    nach: Kennung | None = None


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/karten/in-papierkorb", response_model=Antwort)
    async def in_papierkorb(e: Sammel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.in_papierkorb(konto, e.ids))

    @r.post("/karten/{karte_id}/endgueltig", response_model=Antwort)
    async def karte_endgueltig(karte_id: Kennung, e: Bestaetigung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.karte_endgueltig(konto, karte_id, e.bestaetigung))

    @r.post("/boards/{board_id}/endgueltig", response_model=Antwort)
    async def board_endgueltig(board_id: Kennung, e: Bestaetigung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.board_endgueltig(konto, board_id, e.bestaetigung))

    @r.post("/boards/{board_id}/in-papierkorb", response_model=Antwort)
    async def board_in_papierkorb(board_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.board_in_papierkorb(konto, board_id))

    @r.post("/boards/{board_id}/spalten/{spalte_id}/loeschen", response_model=Antwort)
    async def spalte_loeschen(board_id: Kennung, spalte_id: Kennung, e: SpalteLoeschen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.spalte_loeschen(konto, board_id, spalte_id, e.nach))

    @r.post("/boards/{board_id}/papierkorb/leeren", response_model=Antwort)
    async def leeren(board_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.leeren(konto, board_id))

    @r.post("/papierkorb/entfernen", response_model=Antwort)
    async def entfernen(e: Sammel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.entfernen(konto, e.ids))

    @r.post("/papierkorb/{eintrag_id}/wiederherstellen", response_model=Antwort)
    async def wiederherstellen(eintrag_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.papierkorb.wiederherstellen(konto, eintrag_id))

    return r
