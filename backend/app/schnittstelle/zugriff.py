"""Was jeder Router der Schnittstelle braucht: das Konto der Pinnwand zur Anmeldung (als Abhängigkeit), die Sitzung der
Person für Aufrufe in ihrem Auftrag und die Übersetzung einer abgelehnten Änderung in einen HTTP-Status mit dem Grund in
`detail`."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar

from fastapi import HTTPException, Request

from appkern.app import Geruest
from appkern.anmeldung.api import KOPF
from appkern.anmeldung.dienst import Konto as Anmeldekonto

from ..anwendung import Dienste
from ..anwendung.rahmen import Abgelehnt
from ..modell import Konto

T = TypeVar("T")


def sitzung(request: Request) -> str:
    """Die Anmeldung der Person an dieser App (Kopf, bei Inhaltsadressen auch das Inhalts-Cookie der Pinnwand, das je App
    eigen ist): mit ihr fragt die Pinnwand die Kellerwolke und andere Apps in ihrem Auftrag."""
    return request.headers.get(KOPF) or request.cookies.get(request.app.state.geruest.inhalt_cookie, "")


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
