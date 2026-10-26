"""Wege des Moduls Transkripte: suchen, verknüpfen, Notiz, lösen, Notiz vorschlagen (mit KI an der Karte), Spracheingabe
beim Erfassen; dazu der Ton einer Stelle über die Inhaltsadresse (auch mit dem Inhalts-Cookie, der Spieler sendet keinen
Kopf). Die Sitzung der Person geht an die Transkription mit."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from fastapi.responses import Response

from appkern.anmeldung.dienst import Konto as Anmeldekonto
from appkern.app import Geruest

from ..anwendung import Dienste
from ..anwendung.ki import Zusammenfassung
from ..anwendung.rahmen import Antwort
from ..anwendung.transkripte import SPRACHE_HOECHSTENS, Gehoert, Trefferseite
from ..modell import Kennung, Konto, Modell
from .transkription import VerbundTranskription
from .zugriff import Zugriff, sitzung


class Verknuepfen(Modell):
    transkript: str
    #: Stelle in Sekunden; ohne: das ganze Transkript
    sekunde: float | None = None


class Notiz(Modell):
    notiz: str


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.get("/karten/{karte_id}/transkripte/suche", response_model=Trefferseite)
    async def suchen(karte_id: Kennung, request: Request, text: str = "", ab: int = Query(0, ge=0),
                     konto: Konto = Depends(ich)) -> Trefferseite:
        return await tun(d.transkripte.suchen(konto, karte_id, sitzung(request), text, ab))

    @r.post("/karten/{karte_id}/transkripte", response_model=Antwort)
    async def verknuepfen(karte_id: Kennung, e: Verknuepfen, request: Request, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.transkripte.verknuepfen(konto, karte_id, sitzung(request), e.transkript, e.sekunde))

    @r.post("/karten/{karte_id}/transkripte/{marke_id}/notiz", response_model=Antwort)
    async def notiz(karte_id: Kennung, marke_id: Kennung, e: Notiz, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.transkripte.notiz_setzen(konto, karte_id, marke_id, e.notiz))

    @r.delete("/karten/{karte_id}/transkripte/{marke_id}", response_model=Antwort)
    async def loesen(karte_id: Kennung, marke_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.transkripte.entfernen(konto, karte_id, marke_id))

    @r.post("/karten/{karte_id}/transkripte/{marke_id}/ki/notiz", response_model=Zusammenfassung)
    async def notiz_vorschlagen(karte_id: Kennung, marke_id: Kennung, request: Request,
                                konto: Konto = Depends(ich)) -> Zusammenfassung:
        return await tun(d.ki.notiz_vorschlagen(konto, karte_id, marke_id, sitzung(request)))

    @r.post("/boards/{board_id}/sprache", response_model=Gehoert)
    async def sprache(board_id: Kennung, datei: UploadFile, request: Request, konto: Konto = Depends(ich)) -> Gehoert:
        """Ein Stück Sprache (Feld `datei`, wie der Hördienst der Transkription): die Live-Mitschrift der Aufnahme schickt
        es an Sprechpausen, die Antwort ist sein Text."""
        inhalt = await datei.read(SPRACHE_HOECHSTENS + 1)
        return await tun(d.transkripte.hoeren(konto, board_id, sitzung(request), inhalt, datei.filename or "sprache.wav",
                                              datei.content_type or "application/octet-stream"))

    return r


def inhalt(geruest: Geruest, d: Dienste, transkription: VerbundTranskription) -> APIRouter:
    r = APIRouter(prefix="/api/v1/inhalt", tags=["pinnwand"])

    @r.get("/transkripte/{karte_id}/{marke_id}/ton")
    async def ton(karte_id: Kennung, marke_id: Kennung, request: Request,
                  angemeldet: Anmeldekonto = geruest.lesen) -> Response:
        konto = await d.konten.ich(angemeldet)
        m = await Zugriff.tun(d.transkripte.zum_abspielen(konto, karte_id, marke_id))
        return await Zugriff.tun(transkription.ton(m.transkript, request, sitzung(request)))

    return r
