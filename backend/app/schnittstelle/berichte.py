"""Wege des Moduls Berichte: die Vorschau des Inhalts und das Erstellen der Datei in der Ablage der Pinnwand; geladen
wird eine Datei über die Inhaltsadresse (schnittstelle/anhaenge.py)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..anwendung.berichte import Auswahl, Vorschau
from ..anwendung.rahmen import Antwort
from ..modell import Konto
from .zugriff import Zugriff


def router(z: Zugriff) -> APIRouter:
    r = APIRouter()
    d, ich, tun = z.d, z.ich, z.tun

    @r.post("/berichte/vorschau", response_model=Vorschau)
    async def vorschau(e: Auswahl, konto: Konto = Depends(ich)) -> Vorschau:
        return await tun(d.berichte.vorschau(konto, e))

    @r.post("/berichte", response_model=Antwort)
    async def erstellen(e: Auswahl, konto: Konto = Depends(ich)) -> Antwort:
        return await tun(d.berichte.erstellen(konto, e))

    return r
