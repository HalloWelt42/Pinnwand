"""Wege des Moduls KI an der Karte: Vorschläge holen, nichts schreiben. Übernommen wird über die gewohnten Wege
(bearbeiten, mehrere Karten anlegen)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.ki import Kartenvorschlag, Labelvorschlag, Punktvorschlag, Zusammenfassung
from ..modell import Kennung, Konto, Modell
from .zugriff import Zugriff


class AusText(Modell):
    text: str


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/karten/{karte_id}/ki/zusammenfassung", response_model=Zusammenfassung)
    async def zusammenfassung(karte_id: Kennung, konto: Konto = Depends(ich)) -> Zusammenfassung:
        return await tun(d.ki.zusammenfassen(konto, karte_id))

    @r.post("/karten/{karte_id}/ki/checkliste", response_model=Punktvorschlag)
    async def checkliste(karte_id: Kennung, konto: Konto = Depends(ich)) -> Punktvorschlag:
        return await tun(d.ki.checkliste(konto, karte_id))

    @r.post("/karten/{karte_id}/ki/labels", response_model=Labelvorschlag)
    async def labels(karte_id: Kennung, konto: Konto = Depends(ich)) -> Labelvorschlag:
        return await tun(d.ki.labels(konto, karte_id))

    @r.post("/boards/{board_id}/ki/karten", response_model=Kartenvorschlag)
    async def karten_aus_text(board_id: Kennung, e: AusText, konto: Konto = Depends(ich)) -> Kartenvorschlag:
        return await tun(d.ki.karten_aus_text(konto, board_id, e.text))

    return r
