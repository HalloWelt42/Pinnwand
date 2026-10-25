"""Was jeder Router der Schnittstelle braucht: das Konto der Pinnwand zur Anmeldung (als Abhängigkeit) und die
Übersetzung einer abgelehnten Änderung in einen HTTP-Status mit dem Grund in `detail`."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar

from fastapi import HTTPException

from appkern.app import Geruest
from appkern.anmeldung.dienst import Konto as Anmeldekonto

from ..anwendung import Dienste
from ..anwendung.rahmen import Abgelehnt
from ..modell import Konto

T = TypeVar("T")


class Zugriff:
    def __init__(self, geruest: Geruest, dienste: Dienste) -> None:
        self.d = dienste

        async def ich(angemeldet: Anmeldekonto = geruest.pflicht) -> Konto:
            return await dienste.konten.ich(angemeldet)

        self.ich = ich

    @staticmethod
    async def tun(arbeit: Awaitable[T]) -> T:
        try:
            return await arbeit
        except Abgelehnt as f:
            raise HTTPException(f.status, detail=f.meldung) from f
