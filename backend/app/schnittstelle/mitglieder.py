"""Wege an Rollen und Mitgliedern: Rolle anlegen, umbenennen, Recht setzen, löschen; Rolle eines Mitglieds setzen,
Mitglied entfernen, Besitz übertragen. Mitglieder heißen hier wie ihr Konto der Kellerwolke (auch wer noch wartet).
Eingeladen wird über den Weg der Boards."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.rahmen import Antwort
from ..modell import Kennung, Konto, Modell
from .boards import Name
from .zugriff import Zugriff


class NeueRolle(Modell):
    name: str
    #: die Rolle, deren Rechte die neue bekommt
    kopie_von: Kennung


class Rechtwahl(Modell):
    recht: str
    an: bool


class Ersatz(Modell):
    #: neue Rolle für die Personen, die die gelöschte hatten
    ersatz: Kennung | None = None


class Rollenwahl(Modell):
    kellerwolke: str
    rolle: Kennung


class Person(Modell):
    kellerwolke: str


class Besitz(Modell):
    #: Kontoname der Kellerwolke des neuen Besitzers
    an: str
    #: deine Rolle danach
    ich_werde: Kennung


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/boards/{board_id}/rollen", response_model=Antwort)
    async def rolle_anlegen(board_id: Kennung, e: NeueRolle, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.rolle_anlegen(konto, board_id, e.name, e.kopie_von))

    @r.post("/boards/{board_id}/rollen/{rolle_id}/umbenennen", response_model=Antwort)
    async def rolle_umbenennen(board_id: Kennung, rolle_id: Kennung, e: Name, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.rolle_umbenennen(konto, board_id, rolle_id, e.name))

    @r.post("/boards/{board_id}/rollen/{rolle_id}/recht", response_model=Antwort)
    async def recht_setzen(board_id: Kennung, rolle_id: Kennung, e: Rechtwahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.recht_setzen(konto, board_id, rolle_id, e.recht, e.an))

    @r.post("/boards/{board_id}/rollen/{rolle_id}/loeschen", response_model=Antwort)
    async def rolle_loeschen(board_id: Kennung, rolle_id: Kennung, e: Ersatz, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.rolle_loeschen(konto, board_id, rolle_id, e.ersatz))

    @r.post("/boards/{board_id}/mitglieder/rolle", response_model=Antwort)
    async def rolle_setzen(board_id: Kennung, e: Rollenwahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.rolle_setzen(konto, board_id, e.kellerwolke, e.rolle))

    @r.post("/boards/{board_id}/mitglieder/entfernen", response_model=Antwort)
    async def mitglied_entfernen(board_id: Kennung, e: Person, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.mitglied_entfernen(konto, board_id, e.kellerwolke))

    @r.post("/boards/{board_id}/besitz", response_model=Antwort)
    async def besitz_uebertragen(board_id: Kennung, e: Besitz, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.mitglieder.besitz_uebertragen(konto, board_id, e.an, e.ich_werde))

    return r
