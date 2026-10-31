"""Vorlesen über die Vertonung mit dem Baustein des Appkerns (`appkern.vorlesen`): Felder `vertonung_adresse` und
`vorlesen_stimme` mit Angeboten (Verzeichnis, Stimmen der Vertonung für die Pinnwand), Verbindung in der Fußleiste,
Strom mit dem App-Schlüssel im Auftrag der Person. Die Anwendung kennt nur den Anschluss `Sprachausgabe`."""

from __future__ import annotations

from collections.abc import AsyncIterator

from appkern.app import Geruest
from appkern.vorlesen import Vorlesen, VorlesenFehler

from ..anwendung.rahmen import Abgelehnt


class VorlesenUeberVertonung:
    def __init__(self, geruest: Geruest) -> None:
        self.baustein = Vorlesen(geruest)

    def adresse(self) -> str:
        return self.baustein.adresse()

    async def zeilen(self, sitzung: str, text: str) -> AsyncIterator[bytes]:
        try:
            async for z in self.baustein.zeilen(text, sitzung=sitzung or None):
                yield z
        except VorlesenFehler as f:
            raise Abgelehnt(f.meldung, f.status) from f
