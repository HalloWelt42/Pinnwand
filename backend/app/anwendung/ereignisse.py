"""Ereignisstrom der Pinnwand: jede Änderung geht an alle Personen, die sie sehen dürfen (Mitglieder der berührten
Boards, das berührte Konto). Im Prozess gehalten; die Pinnwand läuft als ein Prozess. Wer die Verbindung verliert, holt
den Stand neu (die Oberfläche tut das von selbst)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager

from ..modell import Kennung, Modell

HERZSCHLAG_S = 20
#: so viele Ereignisse wartet eine langsame Verbindung höchstens; danach wird sie getrennt und lädt neu
PUFFER = 500


class Geaendert(Modell):
    """Der neue Stand eines Aggregats, oder sein Wegfall (daten fehlt)."""

    tabelle: str
    id: Kennung
    daten: dict | None = None


class Neuigkeit(Modell):
    """Eine Änderung für den Strom: wer sie machte, ihre Meldung (ohne: still) und die neuen Stände."""

    von: Kennung
    text: str | None = None
    geaendert: list[Geaendert]


class Ereignisse:
    def __init__(self) -> None:
        self._hoerer: dict[Kennung, set[asyncio.Queue[Neuigkeit | None]]] = {}

    def senden(self, neuigkeit: Neuigkeit, empfaenger: set[Kennung] | None) -> None:
        """An die genannten Konten, None: an alle Verbundenen."""
        if not neuigkeit.geaendert:
            return
        ziele = self._hoerer.items() if empfaenger is None else ((k, self._hoerer.get(k, set())) for k in empfaenger)
        for _, schlangen in ziele:
            for q in list(schlangen):
                try:
                    q.put_nowait(neuigkeit)
                except asyncio.QueueFull:
                    # zu langsam: leeren und trennen; die Oberfläche verbindet neu und holt den ganzen Stand
                    while not q.empty():
                        q.get_nowait()
                    q.put_nowait(None)
                    schlangen.discard(q)

    @contextmanager
    def abo(self, konto: Kennung) -> Iterator[AsyncIterator[Neuigkeit | None]]:
        """Ereignisse für ein Konto, eingetragen schon beim Betreten (nichts geht verloren, bevor gelesen wird) und beim
        Verlassen sicher ausgetragen. Gelesen wird über den gelieferten Strom; None ist ein Herzschlag. Er endet, wenn
        die Verbindung zu langsam war."""
        q: asyncio.Queue[Neuigkeit | None] = asyncio.Queue(PUFFER)
        self._hoerer.setdefault(konto, set()).add(q)
        try:
            yield self._lesen(q)
        finally:
            schlangen = self._hoerer.get(konto)
            if schlangen is not None:
                schlangen.discard(q)
                if not schlangen:
                    del self._hoerer[konto]

    @staticmethod
    async def _lesen(q: asyncio.Queue[Neuigkeit | None]) -> AsyncIterator[Neuigkeit | None]:
        while True:
            try:
                teil = await asyncio.wait_for(q.get(), HERZSCHLAG_S)
            except TimeoutError:
                yield None
                continue
            if teil is None:
                return
            yield teil
