"""REST der Pinnwand unter /api/v1, nur über die Anwendung: der Stand, der Ereignisstrom, Rückgängig und die Router je
Bereich. Jede Änderung antwortet mit Meldung, Rückweg und den neuen Ständen; abgelehnte mit 400, 403, 404 oder 409 und
dem Grund in `detail`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from appkern.app import Geruest

from ..anwendung import Dienste
from ..anwendung.rahmen import Antwort
from ..anwendung.stand import Stand
from ..modell import Kennung, Konto
from . import (anhaenge, arbeitszeit, aufbau, berichte, boards, hinweise, karten, ki, mitglieder, ordner, papierkorb,
               planung, transkripte, zeiterfassung)
from .zugriff import Zugriff


def router(geruest: Geruest, d: Dienste) -> APIRouter:
    z = Zugriff(geruest, d)
    ich, tun = z.ich, z.tun
    r = APIRouter(prefix="/api/v1", tags=["pinnwand"])

    @r.get("/stand", response_model=Stand)
    async def stand(konto: Konto = Depends(ich)) -> Stand:
        return await d.abfragen.stand(konto)

    @r.get("/karten/{schluessel}")
    async def karte(schluessel: str, konto: Konto = Depends(ich)) -> dict:
        return await tun(d.abfragen.karte(konto, schluessel))

    @r.get("/boards/{board_id}/archiv")
    async def archiv(board_id: Kennung, versatz: int = Query(0, ge=0), grenze: int = Query(50, ge=1, le=500),
                     konto: Konto = Depends(ich)) -> dict:
        return await tun(d.abfragen.archiv(konto, board_id, versatz, grenze))

    @r.post("/rueckgaengig/{journal_id}", response_model=Antwort)
    async def rueckgaengig(journal_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.anwendung.rueckgaengig(konto, journal_id))

    @r.get("/ereignisse")
    async def ereignisse(konto: Konto = Depends(ich)) -> StreamingResponse:
        """Server-Sent Events: `event: geaendert` mit einer Neuigkeit als JSON (wer, Meldung, neue Stände); Kommentarzeilen
        halten die Verbindung. Endet der Strom, verbindet die Oberfläche neu und holt den ganzen Stand."""

        async def strom():
            with d.ereignisse.abo(konto.id) as teile:
                yield b"event: bereit\ndata: {}\n\n"           # erst eingetragen, dann bereit: nichts fällt dazwischen
                async for teil in teile:
                    if teil is None:
                        yield b": lebt\n\n"
                    else:
                        yield f"event: geaendert\ndata: {teil.model_dump_json(by_alias=True, exclude_none=True)}\n\n".encode()

        return StreamingResponse(strom(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    for bereich in (boards, karten, aufbau, mitglieder, ordner, papierkorb, hinweise, anhaenge, zeiterfassung, arbeitszeit,
                    planung, berichte, ki, transkripte):
        r.include_router(bereich.router(z))
    return r
