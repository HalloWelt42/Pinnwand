"""Wege an Anhängen: hochladen, aus der eigenen Kellerwolke verknüpfen (mit der Dateiwahl dazu), entfernen; dazu die
Inhaltsadresse zum Öffnen in einem neuen Reiter.

Hochladen schickt alle Dateien in einem Körper, damit sie in einer Änderung an die Karte kommen (ein Rückgängig für
alle): vorn eine Kopfzeile mit Namen, Größen und Typen (JSON, mit Zeilenende), dahinter die Inhalte hintereinander, je
Datei genau so viele Bytes wie angegeben. Erst nach der Kopfzeile werden Karte, Recht und Größen geprüft, erst dann die
Inhalte angenommen (vorläufig in einen eigenen Ordner, der danach wieder verschwindet)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import Field, ValidationError
from starlette.requests import ClientDisconnect

from appkern.anmeldung.dienst import Konto as Anmeldekonto
from appkern.app import Geruest

from ..anwendung import Dienste
from ..anwendung.anhaenge import Eingang, Gewaehlt, KellerwolkeOrdner
from ..anwendung.rahmen import Abgelehnt, Antwort
from ..modell import Kennung, Konto, Modell
from .ablage import KellerwolkeAblage
from .zugriff import Zugriff, sitzung

#: längste Kopfzeile beim Hochladen (Bytes)
KOPF_GRENZE = 64 * 1024


class Angabe(Modell):
    name: str
    groesse: int = Field(ge=0)
    typ: str = ""


class Angaben(Modell):
    """Kopfzeile beim Hochladen."""

    dateien: list[Angabe]


class AusKellerwolke(Modell):
    dateien: list[Gewaehlt]


class Entfernen(Modell):
    name: str


class Koerper:
    """Der Körper beim Hochladen, Stück für Stück gelesen: erst die Kopfzeile, dann die Inhalte."""

    def __init__(self, strom: AsyncIterator[bytes]) -> None:
        self._strom = strom
        self._rest = b""

    async def _stueck(self) -> bytes:
        """Das nächste Stück; leer am Ende."""
        if self._rest:
            stueck, self._rest = self._rest, b""
            return stueck
        try:
            while (stueck := await anext(self._strom, None)) is not None:
                if stueck:
                    return stueck
        except ClientDisconnect as f:
            raise Abgelehnt("Die Verbindung brach beim Hochladen ab") from f
        return b""

    async def angaben(self) -> list[Eingang]:
        kopf = b""
        while b"\n" not in kopf:
            if len(kopf) > KOPF_GRENZE:
                raise Abgelehnt("Die Angaben zu den Dateien sind zu lang")
            stueck = await self._stueck()
            if not stueck:
                raise Abgelehnt("Die Angaben zu den Dateien fehlen")
            kopf += stueck
        zeile, _, self._rest = kopf.partition(b"\n")
        if len(zeile) > KOPF_GRENZE:
            raise Abgelehnt("Die Angaben zu den Dateien sind zu lang")
        try:
            angaben = Angaben.model_validate_json(zeile)
        except ValidationError as f:
            raise Abgelehnt("Die Angaben zu den Dateien sind nicht lesbar") from f
        return [Eingang(name=a.name, groesse=a.groesse, inhaltstyp=a.typ or None) for a in angaben.dateien]

    async def inhalte(self, eingaenge: list[Eingang], ordner: Path) -> list[Eingang]:
        """Je Datei genau so viele Bytes wie angegeben, jede in eine eigene vorläufige Datei unter `ordner`."""
        angenommen: list[Eingang] = []
        for i, e in enumerate(eingaenge):
            ziel = ordner / str(i)
            offen = e.groesse
            with ziel.open("wb") as datei:
                while offen > 0:
                    stueck = await self._stueck()
                    if not stueck:
                        raise Abgelehnt("Die Dateien kamen nicht vollständig an")
                    teil, self._rest = stueck[:offen], stueck[offen:]
                    datei.write(teil)
                    offen -= len(teil)
            angenommen.append(e.model_copy(update={"inhalt": ziel}))
        if await self._stueck():
            raise Abgelehnt("Es kam mehr an als angegeben")
        return angenommen


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/karten/{karte_id}/anhaenge/hochladen", response_model=Antwort)
    async def hochladen(karte_id: Kennung, request: Request, konto: Konto = Depends(ich)) -> Antwort:
        koerper = Koerper(request.stream())
        eingaenge = await tun(d.anhaenge.pruefen(konto, karte_id, await tun(koerper.angaben())))
        with TemporaryDirectory(prefix="pinnwand-anhaenge-") as ort:
            angenommen = await tun(koerper.inhalte(eingaenge, Path(ort)))
            return await tun(d.anhaenge.hochladen(konto, karte_id, angenommen))

    @r.get("/anhaenge/kellerwolke", response_model=KellerwolkeOrdner, dependencies=[Depends(ich)])
    async def kellerwolke(request: Request, ordner: UUID | None = None) -> KellerwolkeOrdner:
        """Ein Ordner deiner Kellerwolke für die Dateiwahl (ohne: Meine Dateien)."""
        return await tun(d.anhaenge.kellerwolke(sitzung(request), str(ordner) if ordner else None))

    @r.post("/karten/{karte_id}/anhaenge/aus-kellerwolke", response_model=Antwort)
    async def aus_kellerwolke(karte_id: Kennung, e: AusKellerwolke, request: Request, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.anhaenge.aus_kellerwolke(konto, karte_id, sitzung(request), e.dateien))

    @r.post("/karten/{karte_id}/anhaenge/entfernen", response_model=Antwort)
    async def entfernen(karte_id: Kennung, e: Entfernen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.anhaenge.entfernen(konto, karte_id, e.name))

    return r


def inhalt(geruest: Geruest, d: Dienste, ablage: KellerwolkeAblage) -> APIRouter:
    """Inhaltsadresse eines Anhangs oder eines eigenen Berichts zum Öffnen in einem neuen Reiter. Ein Link sendet keinen
    Kopf; hier gilt darum auch das Inhalts-Cookie der Anmeldung, das der Appkern nur unter /api/v1/inhalt setzt."""
    r = APIRouter(prefix="/api/v1/inhalt", tags=["pinnwand"])

    @r.get("/anhaenge/{karte_id}/{datei}")
    async def oeffnen(karte_id: Kennung, datei: str, request: Request,
                      angemeldet: Anmeldekonto = geruest.lesen) -> Response:
        konto = await d.konten.ich(angemeldet)
        a = await Zugriff.tun(d.anhaenge.oeffnen(konto, karte_id, datei))
        return await Zugriff.tun(ablage.ausliefern(datei, a.name, request))

    @r.get("/berichte/{bericht_id}")
    async def bericht(bericht_id: Kennung, request: Request, angemeldet: Anmeldekonto = geruest.lesen) -> Response:
        konto = await d.konten.ich(angemeldet)
        b = await Zugriff.tun(d.berichte.eigener(konto, bericht_id))
        return await Zugriff.tun(ablage.ausliefern(b.datei_id, b.datei, request))

    return r
