"""Vorlesen (Modul vorlesen, Mechanik M-114): die Vertonung spricht, was die Oberfläche zeigt (Beschreibung, Karte,
Kommentar, Tagesplan, Bericht), Satz für Satz als Strom. Die Vertonung ist eine andere App hinter dem Anschluss
`Vertonung`; gefragt wird im Auftrag der Person. Der Server prüft Modul und Länge, teilt lange Texte an Satzgrenzen
(die Vertonung nimmt je Aufruf höchstens 8000 Zeichen) und zählt die Sätze über alle Teile durch. Was vor dem ersten
Satz scheitert, ist eine Ablehnung mit Grund; danach kommt eine Zeile `fehler`."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any, Protocol

from ..modell import Board, Kennung, Konto, Modell
from ..regeln.board import mitglied, modul_an
from .rahmen import Abgelehnt, Anwendung

#: so viel Text liest die Pinnwand am Stück vor; so groß ist ein Teil für die Vertonung (sie nimmt bis 8000)
TEXT_HOECHSTENS = 40_000
TEIL_HOECHSTENS = 7_500
_SATZENDE = re.compile(r"(?<=[.!?:;])\s+|\n+")


class Vertonung(Protocol):
    def adresse(self) -> str:
        """Wo die Vertonung liegt (leer: nicht eingerichtet)."""
        ...

    def strom(self, sitzung: str, text: str) -> AsyncIterator[dict[str, Any]]:
        """Die Zeilen der Vertonung für einen Teil (`satz`, `ende`, `fehler`), sobald sie kommen; abgelehnt mit Grund,
        wenn sie nicht kann."""
        ...


class KeineVertonung:
    def adresse(self) -> str:
        return ""

    def strom(self, sitzung: str, text: str) -> AsyncIterator[dict[str, Any]]:
        raise Abgelehnt("Die Vertonung ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)


class Vorlesetext(Modell):
    text: str
    #: das Board, aus dem der Text kommt; ohne (Heute, Berichte): eines deiner Boards mit Vorlesen genügt
    board: Kennung | None = None


def teile(text: str, hoechstens: int = TEIL_HOECHSTENS) -> list[str]:
    """Der Text in Teilen bis `hoechstens` Zeichen, an Satzgrenzen geschnitten; ein überlanger Satz an Leerzeichen."""
    stuecke: list[str] = []
    for satz in (s.strip() for s in _SATZENDE.split(text)):
        while len(satz) > hoechstens:
            schnitt = satz.rfind(" ", 0, hoechstens)
            schnitt = schnitt if schnitt > 0 else hoechstens
            stuecke.append(satz[:schnitt].strip())
            satz = satz[schnitt:].strip()
        if satz:
            stuecke.append(satz)
    ergebnis: list[str] = []
    for s in stuecke:
        if ergebnis and len(ergebnis[-1]) + 1 + len(s) <= hoechstens:
            ergebnis[-1] = f"{ergebnis[-1]} {s}"
        else:
            ergebnis.append(s)
    return ergebnis


def zeile(daten: dict[str, Any]) -> bytes:
    return json.dumps(daten, ensure_ascii=False).encode() + b"\n"


class Vorlesen:
    def __init__(self, anwendung: Anwendung, vertonung: Vertonung) -> None:
        self.a = anwendung
        self.v = vertonung

    async def vorbereiten(self, konto: Konto, e: Vorlesetext) -> list[str]:
        """Prüft, ob die Person das vorlesen lassen darf, und teilt den Text; abgelehnt mit Grund, bevor etwas spricht."""
        boards = [Board.model_validate(d) for d in await self.a.v.alle("boards")]
        if e.board:
            b = next((x for x in boards if x.id == e.board), None)
            if b is None:
                raise Abgelehnt("Dieses Board gibt es nicht (mehr)", 404)
            if mitglied(b, konto.id) is None:
                raise Abgelehnt(f"Im Board {b.name} bist du nicht Mitglied", 403)
            if not modul_an(b, "vorlesen"):
                raise Abgelehnt(f"Vorlesen ist im Board {b.name} aus", 403)
        elif not any(mitglied(b, konto.id) and modul_an(b, "vorlesen") for b in boards):
            raise Abgelehnt("Vorlesen ist in keinem deiner Boards an", 403)
        if not self.v.adresse():
            raise Abgelehnt("Die Vertonung ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)
        text = e.text.strip()
        if not text:
            raise Abgelehnt("Es gibt nichts vorzulesen")
        if len(text) > TEXT_HOECHSTENS:
            raise Abgelehnt(f"Der Text ist länger als {TEXT_HOECHSTENS} Zeichen")
        return teile(text)

    async def sprechen(self, sitzung: str, stuecke: list[str]) -> AsyncIterator[bytes]:
        """Die Zeilen für den Browser: jeder Satz, sobald er gesprochen ist (über alle Teile durchgezählt), am Ende
        `ende`; scheitert die Vertonung mittendrin, eine Zeile `fehler` und Schluss. Lehnt sie vor dem ersten Satz ab,
        kommt die Ablehnung als Ausnahme."""
        nr, dauer_ms = 0, 0
        try:
            for teil in stuecke:
                async for z in self.v.strom(sitzung, teil):
                    if z.get("art") == "satz":
                        yield zeile({**z, "nr": nr})
                        nr += 1
                        dauer_ms += int(z.get("dauer_ms") or 0)
                    elif z.get("art") == "fehler":
                        yield zeile({"art": "fehler", "meldung": z.get("meldung") or "Vorlesen brach ab"})
                        return
            yield zeile({"art": "ende", "saetze": nr, "dauer_ms": dauer_ms})
        except Abgelehnt as f:
            if not nr:
                raise                          # vor dem ersten Satz: eine Ablehnung mit Grund (der Weg wartet darauf)
            yield zeile({"art": "fehler", "meldung": f.meldung})
