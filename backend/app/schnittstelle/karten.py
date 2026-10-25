"""Wege an Karten: anlegen, verschieben (einzeln, gesammelt, erledigen), verknüpfen, duplizieren, Inhalte bearbeiten,
kommentieren, Sammelaktionen. Feste Pfade stehen vor denen mit Kennung (sonst nimmt /karten/{id}/... auch "sammel")."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from ..anwendung.inhalt import Kartenfelder
from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell, Prioritaet
from .zugriff import Zugriff


class NeueKarte(Modell):
    titel: str
    spalte: Kennung | None = None
    art: Literal["arbeit", "idee"] | None = None
    faellig: str | None = None
    beschreibung: str | None = None


class Verschieben(Modell):
    nach: Kennung
    #: Platz in der Zielspalte (ab 0); ohne: ans Ende
    platz: int | None = None


class Sammel(Modell):
    ids: list[Kennung]


class SammelVerschieben(Sammel):
    nach: Kennung


class SammelZuweisen(Sammel):
    konto: Kennung


class SammelLabel(Sammel):
    label: Kennung


class SammelPrioritaet(Sammel):
    prioritaet: Prioritaet


class Verknuepfen(Modell):
    mit: Kennung


class Bearbeiten(Modell):
    felder: Kartenfelder
    #: die geänderten Felder, wie die Oberfläche sie kannte (Konflikt, wenn eines inzwischen anders ist)
    vorher: Kartenfelder | None = None
    #: Text der Meldung ("fällig Di 27.10.")
    text: str | None = None


class Art(Modell):
    art: Literal["arbeit", "idee"]


class Kommentar(Modell):
    text: str


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/boards/{board_id}/karten", response_model=Antwort)
    async def anlegen(board_id: Kennung, e: NeueKarte, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.anlegen(konto, board_id, e.titel, e.spalte, e.art, e.faellig, e.beschreibung))

    @r.post("/karten/sammel/verschieben", response_model=Antwort)
    async def sammel_verschieben(e: SammelVerschieben, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.sammel_verschieben(konto, e.ids, e.nach))

    @r.post("/karten/sammel/zuweisen", response_model=Antwort)
    async def sammel_zuweisen(e: SammelZuweisen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.sammel_zuweisen(konto, e.ids, e.konto))

    @r.post("/karten/sammel/label", response_model=Antwort)
    async def sammel_label(e: SammelLabel, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.sammel_label(konto, e.ids, e.label))

    @r.post("/karten/sammel/prioritaet", response_model=Antwort)
    async def sammel_prioritaet(e: SammelPrioritaet, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.sammel_prioritaet(konto, e.ids, e.prioritaet))

    @r.post("/karten/{karte_id}/verschieben", response_model=Antwort)
    async def verschieben(karte_id: Kennung, e: Verschieben, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.verschieben(konto, karte_id, e.nach, e.platz))

    @r.post("/karten/{karte_id}/erledigen", response_model=Antwort)
    async def erledigen(karte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.erledigen(konto, karte_id))

    @r.post("/karten/{karte_id}/verknuepfen", response_model=Antwort)
    async def verknuepfen(karte_id: Kennung, e: Verknuepfen, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.verknuepfen(konto, karte_id, e.mit))

    @r.post("/karten/{karte_id}/loesen", response_model=Antwort)
    async def loesen(karte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.loesen(konto, karte_id))

    @r.post("/karten/{karte_id}/duplizieren", response_model=Antwort)
    async def duplizieren(karte_id: Kennung, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.karten.duplizieren(konto, karte_id))

    @r.post("/karten/{karte_id}/bearbeiten", response_model=Antwort)
    async def bearbeiten(karte_id: Kennung, e: Bearbeiten, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.bearbeiten(konto, karte_id, e.felder, e.vorher, e.text))

    @r.post("/karten/{karte_id}/art", response_model=Antwort)
    async def art(karte_id: Kennung, e: Art, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.art_setzen(konto, karte_id, e.art))

    @r.post("/karten/{karte_id}/kommentieren", response_model=Antwort)
    async def kommentieren(karte_id: Kennung, e: Kommentar, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.inhalte.kommentieren(konto, karte_id, e.text))

    return r
