"""Anwendungsfälle an Boards: ein Board aus einer Vorlage anlegen (wer anlegt, ist Besitzer) und Personen einladen.
Das Kürzel ist über alle Boards eindeutig und bleibt beim Umbenennen fest. Eingeladen wird per Kontoname der
Kellerwolke; wer noch nie angemeldet war, wartet als Mitglied ohne Kennung, bis er sich das erste Mal anmeldet. Damit
er sich anmelden darf, schaltet der `Zugang` den Namen in der App frei."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol

from ..modell import MODULE, Board, BoardEinstellungen, Farbe, Feld, Kennung, Konto, Label, Mitglied, Modell, Ordner, Spalte, Vorlage
from ..regeln.kuerzel import kuerzel_fehler
from ..vorlagen import start_rollen
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: Farben neuer Boards: die erste, die noch kein Board trägt (unterscheidbar in der Seitenleiste)
NEU_FARBEN: list[Farbe] = ["tuerkis", "himmel", "honig", "violett", "rose", "sand", "stahl", "koralle", "petrol", "minze", "flieder"]
#: Vorgabe des Zeitfensters neuer Erledigt-Spalten (wie in der alten App)
ZEITFENSTER_VORGABE = "heute"
#: Kontonamen der Kellerwolke: Buchstaben, Ziffern, Punkt, Bindestrich, Unterstrich, @
KONTONAME = re.compile(r"^[\w.@-]{1,64}$")


class Zugang(Protocol):
    """Wer die App nutzen darf. Eingeladene Kontonamen werden freigeschaltet; entzogen wird nie selbsttätig."""

    async def freischalten(self, namen: Iterable[str]) -> None: ...


class Einladung(Modell):
    kellerwolke: str
    rolle: Kennung = "mitglied"


def kuerzel_inhaber(k: Kontext):
    """Wem ein Kürzel gehört: Name des Boards, wenn ich es sehe, sonst "" (fremdes Board), None: frei."""
    def inhaber(kuerzel: str) -> str | None:
        d = k.s.alle("boards", "kuerzel=?", (kuerzel,))
        if not d:
            return None
        b = Board.model_validate(d[0])
        return b.name if any(m.konto == k.konto.id for m in b.mitglieder) else ""
    return inhaber


def mitglied_hinzu(k: Kontext, b: Board, e: Einladung) -> bool:
    """Nimmt die Person ins Board auf (mit ihrer Kennung, wenn sie schon ein Konto hat). False: war schon Mitglied."""
    name = e.kellerwolke.strip()
    if not KONTONAME.match(name):
        raise Abgelehnt(f"{name or 'Ein leerer Name'} ist kein Kontoname der Kellerwolke")
    if not any(r.id == e.rolle for r in b.rollen):
        raise Abgelehnt(f"Die Rolle {e.rolle} gibt es im Board {b.name} nicht")
    if any(m.kellerwolke == name for m in b.mitglieder):
        return False
    konto = k.s.alle("konten", "kellerwolke=?", (name,))
    b.mitglieder.append(Mitglied(konto=konto[0]["id"] if konto else "", kellerwolke=name, rolle=e.rolle, seit=k.heute))
    return True


class Boards:
    def __init__(self, anwendung: Anwendung, zugang: Zugang) -> None:
        self.a = anwendung
        self.zugang = zugang

    async def anlegen(self, konto: Konto, vorlage_id: Kennung, name: str, kuerzel: str, ordner: Kennung | None = None,
                      einladungen: list[Einladung] | None = None) -> Antwort:
        name = name.strip()
        einladungen = einladungen or []

        def arbeit(k: Kontext) -> str:
            if not name:
                raise Abgelehnt("Ein Board braucht einen Namen")
            fehler = kuerzel_fehler(kuerzel, kuerzel_inhaber(k))
            if fehler:
                raise Abgelehnt(fehler, 409 if "vergeben" in fehler else 400)
            d = k.s.lies("vorlagen", vorlage_id)
            if d is None or (d.get("konto") and d["konto"] != konto.id):
                raise Abgelehnt("Diese Vorlage gibt es nicht", 404)
            v = Vorlage.model_validate(d)
            vergeben = {b.get("farbe") for b in k.s.alle("boards")}
            b = Board(
                id=neue_kennung("b"), name=name, kuerzel=kuerzel,
                farbe=next((f for f in NEU_FARBEN if f not in vergeben), NEU_FARBEN[0]),
                spalten=[Spalte(id=neue_kennung("s"), name=s.name, farbe=s.farbe, erledigt=s.erledigt, grenze=s.grenze,
                                zeitfenster=ZEITFENSTER_VORGABE if s.erledigt else None) for s in v.spalten],
                labels=[Label(id=neue_kennung("l"), name=l.name, farbe=l.farbe) for l in v.labels],
                felder=[Feld(id=neue_kennung("f"), **f.model_dump()) for f in v.felder],
                rollen=start_rollen(),
                mitglieder=[Mitglied(konto=konto.id, kellerwolke=konto.kellerwolke, rolle="besitzer", seit=k.heute)],
                module={m: m in v.module for m in MODULE},
                einstellungen=BoardEinstellungen(),
            )
            for e in einladungen:
                mitglied_hinzu(k, b, e)
            k.s.schreib("boards", b.json_daten())
            if ordner:
                od = k.s.lies("ordner", ordner)
                if od is None or od.get("konto") != konto.id:
                    raise Abgelehnt("Diesen Ordner gibt es nicht", 404)
                o = Ordner.model_validate(od)
                o.boards.append(b.id)
                k.s.schreib("ordner", {**od, **o.json_daten()})
            return f"Board {name} angelegt, Karten heißen {kuerzel}-1 und so weiter"

        antwort = await self.a.aendern(konto, arbeit)
        await self.zugang.freischalten(e.kellerwolke.strip() for e in einladungen)
        return antwort

    async def einladen(self, konto: Konto, board_id: Kennung, e: Einladung) -> Antwort:
        """Die Person sieht das Board sofort (oder ab ihrer ersten Anmeldung) in der Seitenleiste."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "mitglieder.verwalten")
            if not mitglied_hinzu(k, b, e):
                raise Abgelehnt(f"{e.kellerwolke.strip()} ist schon im Board {b.name}", 409)
            k.s.schreib("boards", b.json_daten())
            return f"{e.kellerwolke.strip()} ist eingeladen und sieht {b.name} ab sofort in der Seitenleiste"

        antwort = await self.a.aendern(konto, arbeit)
        await self.zugang.freischalten([e.kellerwolke.strip()])
        return antwort
