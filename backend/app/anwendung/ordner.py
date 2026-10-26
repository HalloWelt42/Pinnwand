"""Was jeder Person allein gehört: ihre Ordner in der Seitenleiste (anlegen, umbenennen, löschen, ordnen, ein Board
einsortieren) und ihr Kürzel. Ordner ordnen nur, sie tragen keine Rechte; ein gelöschter Ordner lässt seine Boards ohne
Ordner stehen. Das Kürzel ist nur Anzeige auf Karten (Zeiten, Kommentare und Rechte hängen am Konto); nach einer
Änderung liest die Anmeldung das Konto neu."""

from __future__ import annotations

import re

from ..modell import Kennung, Konto, Ordner
from .boards import anzahl, name_pruefen, neue_reihenfolge
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: Kürzel einer Person: ein bis drei Buchstaben, groß geschrieben
PERSON_KUERZEL = re.compile(r"^[A-ZÄÖÜ]{1,3}$")


class OrdnerZeile(Ordner):
    """Ein Ordner, wie er gespeichert ist: wem er gehört und sein Platz in der Seitenleiste (aufsteigend)."""

    konto: Kennung
    reihe: float = 0


def meine_ordner(k: Kontext) -> list[OrdnerZeile]:
    return [OrdnerZeile.model_validate(d) for d in k.s.alle("ordner", "konto=?", (k.konto.id,), "reihe")]


def ordner_von(alle: list[OrdnerZeile], ordner_id: Kennung) -> OrdnerZeile:
    o = next((x for x in alle if x.id == ordner_id), None)
    if o is None:
        raise Abgelehnt("Diesen Ordner gibt es nicht", 404)
    return o


def speichern(k: Kontext, o: OrdnerZeile) -> None:
    k.s.schreib("ordner", o.json_daten())


class Persoenliches:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    # --- Ordner -------------------------------------------------------------------------------------------------

    async def ordner_anlegen(self, konto: Konto, name: str) -> Antwort:
        """Neuer Ordner am Ende der Seitenleiste, noch leer."""

        def arbeit(k: Kontext) -> str:
            n = name_pruefen(name, "Ein Ordner")
            alle = meine_ordner(k)
            speichern(k, OrdnerZeile(id=neue_kennung("o"), name=n, konto=konto.id, reihe=(alle[-1].reihe if alle else 0) + 1))
            return f"Ordner {n} angelegt"

        return await self.a.aendern(konto, arbeit)

    async def ordner_umbenennen(self, konto: Konto, ordner_id: Kennung, name: str) -> Antwort:
        def arbeit(k: Kontext) -> str | None:
            o = ordner_von(meine_ordner(k), ordner_id)
            n = name_pruefen(name, "Ein Ordner")
            if n == o.name:
                return None
            alt, o.name = o.name, n
            speichern(k, o)
            return f"Ordner {alt} heißt jetzt {n}"

        return await self.a.aendern(konto, arbeit)

    async def ordner_loeschen(self, konto: Konto, ordner_id: Kennung) -> Antwort:
        """Die Boards des Ordners stehen danach ohne Ordner; an ihnen ändert sich nichts."""

        def arbeit(k: Kontext) -> str:
            o = ordner_von(meine_ordner(k), ordner_id)
            k.s.loesch("ordner", o.id)
            boards = [i for i in o.boards if k.s.lies("boards", i)]
            return f"Ordner {o.name} gelöscht" + (
                f"; {anzahl(len(boards), 'Board steht', 'Boards stehen')} jetzt ohne Ordner" if boards else "")

        return await self.a.aendern(konto, arbeit)

    async def ordner_ordnen(self, konto: Konto, ids: list[Kennung]) -> Antwort:
        """Reihenfolge der Ordner in der Seitenleiste; die Liste nennt genau deine Ordner."""

        def arbeit(k: Kontext) -> str | None:
            neu = neue_reihenfolge(meine_ordner(k), ids, "jeden deiner Ordner")
            if neu is None:
                return None
            for platz, o in enumerate(neu, start=1):
                if o.reihe != platz:
                    o.reihe = platz
                    speichern(k, o)
            return "Ordner neu geordnet"

        return await self.a.aendern(konto, arbeit)

    async def ordner_setzen(self, konto: Konto, board_id: Kennung, ordner_id: Kennung | None,
                            stelle: int | None = None) -> Antwort:
        """Board in einen deiner Ordner (an die Stelle, ohne Angabe ans Ende) oder ohne Ordner; es hängt nur in deiner
        Seitenleiste um. Im selben Ordner ordnet die Stelle es um."""

        def arbeit(k: Kontext) -> str | None:
            b = k.board(board_id)
            if not any(m.konto == konto.id for m in b.mitglieder):
                raise Abgelehnt("Dieses Board siehst du nicht", 403)
            alle = meine_ordner(k)
            ziel = ordner_von(alle, ordner_id) if ordner_id else None
            bisher = [o.id for o in alle if b.id in o.boards]
            schon_da = bisher == ([ziel.id] if ziel else [])
            if schon_da and (ziel is None or stelle is None or ziel.boards.index(b.id) == min(stelle, len(ziel.boards) - 1)):
                return None
            for o in alle:
                if b.id in o.boards:
                    o.boards = [x for x in o.boards if x != b.id]
                    if o is not ziel:
                        speichern(k, o)
            if ziel:
                ziel.boards.insert(len(ziel.boards) if stelle is None else max(0, stelle), b.id)
                speichern(k, ziel)
            if schon_da:
                return f"{b.name} umsortiert"
            return f"{b.name} liegt jetzt im Ordner {ziel.name}" if ziel else f"{b.name} liegt jetzt ohne Ordner"

        return await self.a.aendern(konto, arbeit)

    # --- Eigenes Kürzel -----------------------------------------------------------------------------------------

    async def kuerzel_setzen(self, konto: Konto, kuerzel: str) -> Antwort:
        """Ein bis drei Buchstaben; gilt für alle sofort auf Karten, in Listen und im Board."""
        neu = kuerzel.strip().upper()

        def arbeit(k: Kontext) -> str | None:
            if not PERSON_KUERZEL.match(neu):
                raise Abgelehnt("Ein Kürzel hat ein bis drei Buchstaben")
            d = k.s.lies("konten", konto.id)
            if d is None:
                raise Abgelehnt("Dein Konto gibt es nicht (mehr)", 404)
            if d.get("kuerzel") == neu:
                return None
            k.s.schreib("konten", {**d, "kuerzel": neu})
            return f"Dein Kürzel ist jetzt {neu}"

        return await self.a.aendern(konto, arbeit)
