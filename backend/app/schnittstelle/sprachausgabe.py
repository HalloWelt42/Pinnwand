"""Die App Vorlesen über den Baustein des Appkerns (`appkern.vorlesen`): Feld `vorlesen_adresse` mit Angebot aus dem
Verzeichnis, Verbindung in der Fußleiste, Strom mit dem App-Schlüssel im Auftrag der Person. Die Anwendung kennt nur
den Anschluss `Sprachausgabe`; Stimme und Tempo wählt man in der App Vorlesen."""

from __future__ import annotations

from collections.abc import AsyncIterator

from appkern.app import Geruest
from appkern.vorlesen import Vorlesen, VorlesenFehler

from ..anwendung.rahmen import Abgelehnt


class VorlesenApp:
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
