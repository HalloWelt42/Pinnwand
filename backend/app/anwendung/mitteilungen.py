"""Hinweise als Mitteilung aufs Telefon (Weg Push): ein neuer Hinweis (auch ein erneuerter Hinweis "fällig" und ein
Bündel, das eine wichtigere Art bekam) geht an
alle Geräte der Person, wenn sie Push für seine Art an hat. Gesendet wird nach der Änderung, nie in ihr: der Rahmen
meldet neue Hinweise, ein Begleiter schickt sie aus seiner Warteschlange. Was nicht ankommt, steht im Protokoll; der
Hinweis bleibt in der Pinnwand."""

from __future__ import annotations

import asyncio
import logging

from appkern.app import Begleiter
from appkern.push import Mitteilung, Push

from ..verzeichnis import Bild
from .hinweise import NAMEN_DER_ARTEN, weg_an
from .rahmen import Anwendung

logger = logging.getLogger("pinnwand.mitteilungen")


def ziel(hinweis: dict, board: dict | None) -> str:
    """Wohin ein Tippen führt: zur Karte über ihren Schlüssel (auch archiviert oder umgezogen), sonst zu den Hinweisen."""
    schluessel = hinweis.get("schluessel")
    if board and schluessel and "-" in schluessel:
        return f"/board/{board['kuerzel'].lower()}/{schluessel.split('-')[1]}"
    return "/hinweise"


class Mitteilungen(Begleiter):
    def __init__(self, anwendung: Anwendung, push: Push | None) -> None:
        self.a = anwendung
        self.push = push
        self.warteschlange: asyncio.Queue[dict] = asyncio.Queue()
        self._aufgabe: asyncio.Task[None] | None = None
        if push is not None:
            anwendung.beobachten("hinweise", self._gesehen)

    def _gesehen(self, b: Bild) -> None:
        neu, alt = b.nachher, b.vorher
        if neu and not neu.get("gelesen") and self._neuer_anlass(alt, neu):
            self.warteschlange.put_nowait(neu)

    @staticmethod
    def _neuer_anlass(alt: dict | None, neu: dict) -> bool:
        """Ein neuer Hinweis; ein erneuerter "fällig" (neuer Tag); oder ein Bündel, das eine wichtigere Art bekam (etwa
        eine Zuweisung zu einem Kommentar, HELF-54). Kommt in ein Bündel nur ein weiterer Anlass derselben Art, klingelt
        das Telefon nicht noch einmal."""
        if alt is None or alt.get("gelesen"):
            return True
        if neu.get("art") == "faellig":
            return alt.get("zeit") != neu.get("zeit")
        return alt.get("art") != neu.get("art")

    async def starten(self) -> None:
        if self.push is not None:
            self._aufgabe = asyncio.create_task(self._laufen(), name="pinnwand-mitteilungen")

    async def stoppen(self) -> None:
        if self._aufgabe:
            self._aufgabe.cancel()
            await asyncio.gather(self._aufgabe, return_exceptions=True)
            self._aufgabe = None

    async def leeren(self) -> None:
        """Warten, bis alles Gemeldete gesendet ist (für Tests)."""
        await self.warteschlange.join()

    async def _laufen(self) -> None:
        while True:
            h = await self.warteschlange.get()
            try:
                await self._senden(h)
            except Exception:  # noqa: BLE001 - eine Mitteilung darf den Begleiter nicht beenden
                logger.exception("Mitteilung zum Hinweis %s", h.get("id"))
            finally:
                self.warteschlange.task_done()

    async def _senden(self, h: dict) -> None:
        if self.push is None or not weg_an(await self.a.v.lies("person_einstellungen", h["konto"]), h["art"], "push"):
            return
        board = await self.a.v.lies("boards", h["board"])
        titel = f"{NAMEN_DER_ARTEN.get(h['art'], 'Hinweis')}" + (f", {board['name']}" if board else "")
        await self.push.senden(h["konto"], Mitteilung(titel=titel, text=h["text"], url=ziel(h, board), tag=f"hinweis-{h['id']}"))
