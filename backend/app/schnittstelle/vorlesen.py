"""Weg des Moduls Vorlesen: der Text, den die Oberfläche zeigt, als Strom gesprochener Sätze (Format der Vertonung,
`application/x-ndjson`); der Vorleser des Appkerns spielt ihn. Die Sitzung der Person geht an die Vertonung mit."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..anwendung.vorlesen import Vorlesetext
from ..modell import Konto
from .zugriff import Zugriff, sitzung


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/vorlesen")
    async def vorlesen(e: Vorlesetext, request: Request, konto: Konto = Depends(ich)) -> StreamingResponse:
        stuecke = await tun(d.vorlesen.vorbereiten(konto, e))
        strom = d.vorlesen.sprechen(sitzung(request), stuecke)
        erste = await tun(anext(strom))                     # lehnt die Vertonung gleich ab, ist das noch eine Antwort

        async def alles() -> AsyncIterator[bytes]:
            yield erste
            async for z in strom:
                yield z

        return StreamingResponse(alles(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache"})

    return r
