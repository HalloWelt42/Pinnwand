"""Zugang über das Gerüst: Eingeladene kommen in die Einstellung "Weitere Konten", damit sie sich anmelden dürfen.
Entzogen wird dort nur von Hand (ein Name kann auch aus anderem Grund eingetragen sein)."""

from __future__ import annotations

from collections.abc import Iterable

from appkern.app import Geruest


class GeruestZugang:
    def __init__(self, geruest: Geruest) -> None:
        self.g = geruest

    def besitzer(self) -> str | None:
        return self.g.besitzer

    async def freischalten(self, namen: Iterable[str]) -> None:
        weitere = list(self.g.einstellungen.stand.weitere_konten)
        neu = [n for n in dict.fromkeys(namen) if n and n != self.g.besitzer and n not in weitere]
        if neu:
            await self.g.einstellungen.aendern({"weitere_konten": [*weitere, *neu]})
