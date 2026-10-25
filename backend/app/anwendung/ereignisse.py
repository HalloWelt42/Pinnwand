"""Ereignisstrom der Pinnwand: jede Änderung geht an alle Personen, die sie sehen dürfen (Mitglieder der berührten
Boards, das berührte Konto). Im Prozess gehalten; die Pinnwand läuft als ein Prozess. Wer die Verbindung verliert, holt
den Stand neu (die Oberfläche tut das von selbst)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from ..modell import Kennung, Modell

HERZSCHLAG_S = 20
#: so viele Ereignisse wartet eine langsame Verbindung höchstens; danach wird sie getrennt und lädt neu
PUFFER = 500


class Geaendert(Modell):
    """Der neue Stand eines Aggregats, oder sein Wegfall (daten fehlt)."""

    tabelle: str
    id: Kennung
    daten: dict | None = None


class Ereignisse:
    def __init__(self) -> None:
        self._hoerer: dict[Kennung, set[asyncio.Queue[list[Geaendert] | None]]] = {}

    def senden(self, geaendert: list[Geaendert], empfaenger: set[Kennung] | None) -> None:
        """An die genannten Konten, None: an alle Verbundenen."""
        if not geaendert:
            return
        ziele = self._hoerer.items() if empfaenger is None else ((k, self._hoerer.get(k, set())) for k in empfaenger)
        for _, schlangen in ziele:
            for q in list(schlangen):
                try:
                    q.put_nowait(geaendert)
                except asyncio.QueueFull:
                    # zu langsam: leeren und trennen; die Oberfläche verbindet neu und holt den ganzen Stand
                    while not q.empty():
                        q.get_nowait()
                    q.put_nowait(None)
                    schlangen.discard(q)

    async def strom(self, konto: Kennung) -> AsyncIterator[list[Geaendert] | None]:
        """Ereignisse für ein Konto; None ist ein Herzschlag. Endet, wenn die Verbindung zu langsam war."""
        q: asyncio.Queue[list[Geaendert] | None] = asyncio.Queue(PUFFER)
        self._hoerer.setdefault(konto, set()).add(q)
        try:
            while True:
                try:
                    teil = await asyncio.wait_for(q.get(), HERZSCHLAG_S)
                except TimeoutError:
                    yield None
                    continue
                if teil is None:
                    return
                yield teil
        finally:
            self._hoerer.get(konto, set()).discard(q)
