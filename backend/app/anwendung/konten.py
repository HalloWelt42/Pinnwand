"""Konten der Pinnwand: wer sich mit dem Kellerwolke-Konto anmeldet, bekommt beim ersten Mal ein Konto der Pinnwand
(Kennung, Name, Kürzel, Farbe); Einladungen, die auf den Kontonamen warten, gelten ab dann mit der Kennung."""

from __future__ import annotations

from appkern.anmeldung.dienst import Konto as Anmeldekonto

from ..modell import Board, Konto
from ..regeln.kuerzel import person_kuerzel
from .rahmen import Anwendung, Kontext

FARBEN = ["himmel", "minze", "honig", "rose", "flieder", "petrol", "koralle", "tuerkis", "sand", "violett", "stahl"]


class Konten:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung
        self._bekannt: dict[str, Konto] = {}
        anwendung.beobachten("konten", lambda b: self.vergessen(b.id))

    async def ich(self, angemeldet: Anmeldekonto) -> Konto:
        """Das Konto der Pinnwand zur Anmeldung; legt es beim ersten Mal an und löst wartende Einladungen auf."""
        if angemeldet.id in self._bekannt:
            return self._bekannt[angemeldet.id]
        gespeichert = await self.a.v.lies("konten", angemeldet.id)
        if gespeichert is None or await self._wartende_einladungen(angemeldet.name):
            konto = await self._anlegen(angemeldet)
        else:
            konto = Konto.model_validate(gespeichert)
        self._bekannt[angemeldet.id] = konto
        return konto

    async def _wartende_einladungen(self, name: str) -> bool:
        boards = await self.a.v.alle("boards")
        return any(m.get("kellerwolke") == name and not m.get("konto") for b in boards for m in b.get("mitglieder", []))

    async def _anlegen(self, angemeldet: Anmeldekonto) -> Konto:
        vorlaeufig = Konto(id=angemeldet.id, name=angemeldet.name, kuerzel=angemeldet.kuerzel or person_kuerzel(angemeldet.name),
                           kellerwolke=angemeldet.name)

        def arbeit(k: Kontext) -> str | None:
            gespeichert = k.s.lies("konten", angemeldet.id)
            if gespeichert is None:
                vergeben = {d.get("farbe") for d in k.s.alle("konten")}
                farbe = next((f for f in FARBEN if f not in vergeben), FARBEN[0])
                k.s.schreib("konten", {**vorlaeufig.json_daten(), "farbe": farbe})
            for d in k.s.alle("boards"):
                b = Board.model_validate(d)
                offen = [m for m in b.mitglieder if m.kellerwolke == angemeldet.name and not m.konto]
                if offen:
                    for m in offen:
                        m.konto = angemeldet.id
                    k.s.schreib("boards", b.json_daten())
            return f"{angemeldet.name} ist angemeldet"

        await self.a.aendern(vorlaeufig, arbeit, rueckgaengig=False, melden=False)
        return Konto.model_validate(await self.a.v.lies("konten", angemeldet.id))

    def vergessen(self, konto_id: str) -> None:
        """Nach jeder Änderung am Konto (Kürzel, Farbe, auch Rückgängig) beim nächsten Mal neu lesen."""
        self._bekannt.pop(konto_id, None)
