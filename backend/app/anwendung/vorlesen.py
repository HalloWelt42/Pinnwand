"""Vorlesen (Modul vorlesen, Mechanik M-114): die Vertonung spricht, was die Oberfläche zeigt (Beschreibung, Karte,
Kommentar, Tagesplan, Bericht), Satz für Satz als Strom. Sie ist eine andere App hinter dem Anschluss `Sprachausgabe`
(Baustein `appkern.vorlesen`, HELF-73); gefragt wird im Auftrag der Person, mit der Vorlesestimme der Pinnwand. Der
Server prüft Modul, Mitgliedschaft und Länge; was vor dem ersten Satz scheitert, ist eine Ablehnung mit Grund, danach
kommt eine Zeile `fehler`. Die Zeilen gehen an den Vorleser des Appkerns."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from ..modell import Board, Kennung, Konto, Modell
from ..regeln.board import mitglied, modul_an
from .rahmen import Abgelehnt, Anwendung

#: so viel Text liest die Pinnwand am Stück vor
TEXT_HOECHSTENS = 40_000
NICHT_EINGERICHTET = "Vorlesen ist nicht eingerichtet (Einstellungen, Verbindungen)"


class Sprachausgabe(Protocol):
    def adresse(self) -> str:
        """Wo die Vertonung liegt (leer: nicht eingerichtet)."""
        ...

    def zeilen(self, sitzung: str, text: str) -> AsyncIterator[bytes]:
        """Die Zeilen der Vertonung (`satz`, `ende`, `fehler`, je mit Zeilenende), sobald sie kommen; abgelehnt mit
        Grund, bevor die erste kommt."""
        ...


class KeineSprachausgabe:
    def adresse(self) -> str:
        return ""

    def zeilen(self, sitzung: str, text: str) -> AsyncIterator[bytes]:
        raise Abgelehnt(NICHT_EINGERICHTET, 503)


class Vorlesetext(Modell):
    text: str
    #: das Board, aus dem der Text kommt; ohne (Heute, Berichte): eines deiner Boards mit Vorlesen genügt
    board: Kennung | None = None


class Vorlesen:
    def __init__(self, anwendung: Anwendung, sprachausgabe: Sprachausgabe) -> None:
        self.a = anwendung
        self.s = sprachausgabe

    async def vorbereiten(self, konto: Konto, e: Vorlesetext) -> str:
        """Prüft, ob die Person das vorlesen lassen darf; abgelehnt mit Grund, bevor etwas spricht. Liefert den Text."""
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
        if not self.s.adresse():
            raise Abgelehnt(NICHT_EINGERICHTET, 503)
        text = e.text.strip()
        if not text:
            raise Abgelehnt("Es gibt nichts vorzulesen")
        if len(text) > TEXT_HOECHSTENS:
            raise Abgelehnt(f"Der Text ist länger als {TEXT_HOECHSTENS} Zeichen")
        return text

    def sprechen(self, sitzung: str, text: str) -> AsyncIterator[bytes]:
        """Die Zeilen für den Browser, wie die Vertonung sie liefert. Lehnt sie vor dem ersten Satz ab, kommt die
        Ablehnung als Ausnahme beim ersten Lesen."""
        return self.s.zeilen(sitzung, text)
