"""REST der Pinnwand unter /api/v1, nur über die Anwendung. Jede Änderung antwortet mit Meldung, Rückweg und den neuen
Ständen; abgelehnte mit 400, 403, 404 oder 409 und dem Grund in `detail`."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Literal, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from appkern.app import Geruest
from appkern.anmeldung.dienst import Konto as Anmeldekonto

from ..anwendung import Dienste
from ..anwendung.boards import Einladung
from ..anwendung.rahmen import Abgelehnt, Antwort
from ..anwendung.stand import Stand
from ..modell import Kennung, Konto, Modell

T = TypeVar("T")


class Verschieben(Modell):
    nach: Kennung
    #: Platz in der Zielspalte (ab 0); ohne: ans Ende
    platz: int | None = None


class SammelVerschieben(Modell):
    ids: list[Kennung]
    nach: Kennung


class NeueKarte(Modell):
    titel: str
    spalte: Kennung | None = None
    art: Literal["arbeit", "idee"] | None = None
    faellig: str | None = None
    beschreibung: str | None = None


class Verknuepfen(Modell):
    mit: Kennung


class NeuesBoard(Modell):
    vorlage: Kennung
    name: str
    kuerzel: str
    ordner: Kennung | None = None
    einladungen: list[Einladung] = []


def router(geruest: Geruest, d: Dienste) -> APIRouter:
    r = APIRouter(prefix="/api/v1", tags=["pinnwand"])

    async def ich(angemeldet: Anmeldekonto = geruest.pflicht) -> Konto:
        return await d.konten.ich(angemeldet)

    async def tun(arbeit: Awaitable[T]) -> T:
        try:
            return await arbeit
        except Abgelehnt as f:
            raise HTTPException(f.status, detail=f.meldung) from f

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

    @r.post("/boards", response_model=Antwort)
    async def board_anlegen(e: NeuesBoard, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.anlegen(konto, e.vorlage, e.name, e.kuerzel, e.ordner, e.einladungen))

    @r.post("/boards/{board_id}/mitglieder", response_model=Antwort)
    async def einladen(board_id: Kennung, e: Einladung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.boards.einladen(konto, board_id, e))

    @r.post("/boards/{board_id}/karten", response_model=Antwort)
    async def karte_anlegen(board_id: Kennung, e: NeueKarte, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.anlegen(konto, board_id, e.titel, e.spalte, e.art, e.faellig, e.beschreibung))

    # feste Pfade vor denen mit Kennung, sonst nimmt /karten/{karte_id}/... auch "sammel"
    @r.post("/karten/sammel/verschieben", response_model=Antwort)
    async def sammel_verschieben(e: SammelVerschieben, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.sammel_verschieben(konto, e.ids, e.nach))

    @r.post("/karten/{karte_id}/verknuepfen", response_model=Antwort)
    async def verknuepfen(karte_id: Kennung, e: Verknuepfen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.verknuepfen(konto, karte_id, e.mit))

    @r.post("/karten/{karte_id}/loesen", response_model=Antwort)
    async def loesen(karte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.loesen(konto, karte_id))

    @r.post("/karten/{karte_id}/verschieben", response_model=Antwort)
    async def verschieben(karte_id: Kennung, e: Verschieben, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.verschieben(konto, karte_id, e.nach, e.platz))

    @r.post("/karten/{karte_id}/erledigen", response_model=Antwort)
    async def erledigen(karte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.erledigen(konto, karte_id))

    @r.post("/rueckgaengig/{journal_id}", response_model=Antwort)
    async def rueckgaengig(journal_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.anwendung.rueckgaengig(konto, journal_id))

    @r.get("/ereignisse")
    async def ereignisse(konto: Konto = Depends(ich)) -> StreamingResponse:
        """Server-Sent Events: `event: geaendert` mit den neuen Ständen als JSON; Kommentarzeilen halten die Verbindung.
        Endet der Strom, verbindet die Oberfläche neu und holt den ganzen Stand."""

        async def strom():
            yield b"event: bereit\ndata: {}\n\n"
            async for teil in d.ereignisse.strom(konto.id):
                if teil is None:
                    yield b": lebt\n\n"
                else:
                    daten = "[" + ",".join(g.model_dump_json(by_alias=True) for g in teil) + "]"
                    yield f"event: geaendert\ndata: {daten}\n\n".encode()

        return StreamingResponse(strom(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    return r

