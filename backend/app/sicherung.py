"""Nachtsicherung: einmal je Nacht (ab 3 Uhr Ortszeit) eine stimmige Kopie der Datenbank in den Ordner der Sicherungen,
mit denselben Namen wie die Sicherung vor dem Ausrollen (`pinnwand-JJJJMMTT-HHMMSS.sqlite`); die jüngsten zehn bleiben.
Ein Begleiter im Prozess wie die Fälligkeit: alle paar Minuten ein Blick auf die Uhr, so übersteht er Ruhezustand und
Neustarts, und eine verpasste Nacht holt er nach. Das zentrale Sicherungswerkzeug holt die Kopien von dort auf den Mac."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path

from appkern.app import Begleiter

from .uhr import Uhr

logger = logging.getLogger(__name__)

#: ab dieser Stunde (Ortszeit) gilt die Nacht als gekommen
AB_STUNDE = 3
#: so viele Kopien bleiben, die ältesten gehen (wie beim Ausrollen)
BEHALTEN = 10
TAKT_S = 600.0


def kopieren(quelle: Path, ziel: Path) -> None:
    """Stimmige Kopie über die Sicherung von SQLite, auch während die App schreibt."""
    q = sqlite3.connect(quelle)
    z = sqlite3.connect(ziel)
    try:
        q.backup(z)
    finally:
        z.close()
        q.close()


class Nachtsicherung(Begleiter):
    def __init__(self, datenbank: Path, ordner: Path, kennung: str, uhr: Uhr, takt_s: float = TAKT_S) -> None:
        self.datenbank = datenbank
        self.ordner = ordner
        self.kennung = kennung
        self.uhr = uhr
        self.takt_s = takt_s
        self._aufgabe: asyncio.Task[None] | None = None

    async def starten(self) -> None:
        self._aufgabe = asyncio.create_task(self._laufen(), name="pinnwand-nachtsicherung")

    async def stoppen(self) -> None:
        if self._aufgabe:
            self._aufgabe.cancel()
            await asyncio.gather(self._aufgabe, return_exceptions=True)
            self._aufgabe = None

    def _kopien(self) -> list[Path]:
        return sorted(self.ordner.glob(f"{self.kennung}-*.sqlite"))

    async def pruefen(self) -> Path | None:
        """Legt die Kopie dieser Nacht an, wenn es Zeit ist und es sie noch nicht gibt. Ergebnis: die neue Kopie."""
        jetzt = self.uhr.jetzt()
        if int(jetzt[11:13]) < AB_STUNDE or not self.datenbank.exists():
            return None
        tag = jetzt[:10].replace("-", "")
        if any(k.name.startswith(f"{self.kennung}-{tag}-") for k in self._kopien()):
            return None
        self.ordner.mkdir(parents=True, exist_ok=True)
        ziel = self.ordner / f"{self.kennung}-{tag}-{jetzt[11:19].replace(':', '')}.sqlite"
        await asyncio.to_thread(kopieren, self.datenbank, ziel)
        for alt in self._kopien()[:-BEHALTEN]:
            alt.unlink()
        logger.info("Nachtsicherung angelegt: %s", ziel.name)
        return ziel

    async def _laufen(self) -> None:
        while True:
            try:
                await self.pruefen()
            except Exception:  # noqa: BLE001 - der nächste Blick versucht es wieder
                logger.exception("Nachtsicherung")
            await asyncio.sleep(self.takt_s)
