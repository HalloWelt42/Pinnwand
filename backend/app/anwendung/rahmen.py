"""Der Rahmen jeder Änderung: eine Transaktion, die Rechte und Regeln prüft, schreibt, Vorher und Nachher ins Journal legt
und danach die neuen Stände als Ereignis an alle sendet, die sie sehen dürfen (je Zeile nach der Regel in sicht.py).
Rückgängig stellt die Vorher-Stände her, wenn jede Zeile noch ihren Nachher-Stand hat. Es gibt keinen zweiten Weg zu
schreiben."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass

from ..modell import Board, Kennung, Konto, Modell
from ..regeln.board import hat_recht
from ..uhr import Uhr
from ..verzeichnis import Bild, Schreiber, Verzeichnis
from .ereignisse import Ereignisse, Geaendert, Neuigkeit
from .sicht import Sicht

#: Zähler laufen nur vorwärts: Rückgängig lässt sie stehen (und prüft sie nicht)
NUR_VORWAERTS = {"laufnummern"}
#: Folgen für andere (ein Hinweis an sie): Rückgängig nimmt sie mit, auch wenn die Person sie inzwischen gelesen hat
NACHSICHTIG = {"hinweise"}

NAMEN_DER_RECHTE = {
    "board.verwalten": "Board verwalten", "mitglieder.verwalten": "Mitglieder und Rollen verwalten",
    "karten.anlegen": "Karten anlegen", "karten.bearbeiten": "Karten bearbeiten", "karten.verschieben": "Karten verschieben",
    "karten.loeschen": "Karten löschen", "kommentieren": "Kommentieren", "papierkorb.leeren": "Papierkorb leeren",
    "zeit.buchen": "Eigene Zeit buchen", "zeit.andere.sehen": "Zeiten anderer sehen",
    "zeit.andere.bearbeiten": "Zeiten anderer bearbeiten", "abwesenheit.sehen": "Abwesenheiten sehen",
    "serien.verwalten": "Serien verwalten", "berichte.erstellen": "Berichte erstellen",
}


class Abgelehnt(Exception):
    """Eine Änderung, die nicht geht, mit Grund für die Meldung. 403 ohne Recht, 404 unbekannt, 409 veraltet, 400 sonst."""

    def __init__(self, meldung: str, status: int = 400, stand: dict | None = None) -> None:
        super().__init__(meldung)
        self.meldung = meldung
        self.status = status
        self.stand = stand


class Antwort(Modell):
    """Ergebnis einer Änderung: die Meldung, die Kennung des Rückwegs (wenn es einen gibt) und die neuen Stände."""

    meldung: str | None = None
    rueckgaengig: Kennung | None = None
    geaendert: list[Geaendert] = []


@dataclass
class Anteil:
    """Eine geschriebene Zeile mit denen, die ihren alten und ihren neuen Stand sehen (None: alle)."""

    geaendert: Geaendert
    sahen: set[Kennung] | None
    sehen: set[Kennung] | None

    def fuer(self, konto: Kennung) -> Geaendert | None:
        """Was diese Person von der Zeile erfährt: den neuen Stand, wenn sie ihn sieht; den Wegfall, wenn sie nur den
        alten sah; sonst nichts."""
        if self.sehen is None or konto in self.sehen:
            return self.geaendert
        if self.sahen is None or konto in self.sahen:
            return Geaendert(tabelle=self.geaendert.tabelle, id=self.geaendert.id)
        return None


def neue_kennung(vorsatz: str) -> Kennung:
    """Kennung ohne Zähler: Vorsatz und 16 zufällige Hexzeichen."""
    return f"{vorsatz}-{secrets.token_hex(8)}"


class Kontext:
    """Was ein Anwendungsfall in seiner Transaktion braucht: lesen und schreiben (Schreiber), wer handelt, wann, und die
    Rechte im Board."""

    def __init__(self, s: Schreiber, konto: Konto, uhr: Uhr) -> None:
        self.s = s
        self.konto = konto
        self.jetzt = uhr.jetzt()
        self.heute = self.jetzt[:10]

    def board(self, board_id: Kennung) -> Board:
        d = self.s.lies("boards", board_id)
        if d is None:
            raise Abgelehnt("Dieses Board gibt es nicht (mehr)", 404)
        return Board.model_validate(d)

    def board_mit_recht(self, board_id: Kennung, recht: str) -> Board:
        """Das Board, wenn die handelnde Person dort das Recht hat; sonst abgelehnt mit Grund."""
        b = self.board(board_id)
        if not hat_recht(b, recht, self.konto.id):
            raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE.get(recht, recht)}", 403)
        return b

    def naechste_nummer(self, board_id: Kennung) -> int:
        """Die nächste Kartennummer des Boards; der Zähler steht danach auf ihr."""
        d = self.s.lies("laufnummern", board_id) or {"id": board_id, "board": board_id, "zahl": 0}
        zahl = int(d["zahl"]) + 1
        self.s.schreib("laufnummern", {**d, "zahl": zahl})
        return zahl

    def pruefe_fassung(self, stand: dict, fassung: int | None, was: str) -> None:
        """Schreiben auf veralteter Fassung wird abgelehnt (mit dem aktuellen Stand), nie still überschrieben."""
        if fassung is not None and stand.get("fassung") != fassung:
            raise Abgelehnt(f"{was} wurde inzwischen geändert; deine Änderung ist nicht gespeichert", 409, stand)


class Anwendung:
    def __init__(self, verzeichnis: Verzeichnis, ereignisse: Ereignisse, uhr: Uhr | None = None) -> None:
        self.v = verzeichnis
        self.ereignisse = ereignisse
        self.uhr = uhr or Uhr()
        self._beobachter: dict[str, list[Callable[[Bild], None]]] = {}

    def beobachten(self, tabelle: str, nach_aenderung: Callable[[Bild], None]) -> None:
        """Nach jeder Änderung einer Zeile dieser Tabelle Bescheid geben (mit Vorher und Nachher), auch nach Rückgängig;
        für Zwischenspeicher außerhalb der Datenbank und für Folgen nach außen (Mitteilungen). Läuft nach der
        Transaktion, darf nicht warten und nicht scheitern."""
        self._beobachter.setdefault(tabelle, []).append(nach_aenderung)

    async def aendern(self, konto: Konto, arbeit: Callable[[Kontext], str | None], *, rueckgaengig: bool = True,
                      melden: bool = True) -> Antwort:
        """Führt `arbeit` in einer Transaktion aus. `arbeit` gibt den Text der Meldung zurück oder None, wenn nichts
        geschah; Ablehnungen kommen als `Abgelehnt`."""
        uhr = self.uhr

        def transaktion(s: Schreiber) -> tuple[str | None, Kennung | None, dict[tuple[str, str], tuple]]:
            k = Kontext(s, konto, uhr)
            text = arbeit(k)
            sicht = Sicht(s)
            sichten = {(b.tabelle, b.id): (sicht.wer(b.tabelle, b.vorher, vorher=True) if b.vorher else set(),
                                           sicht.wer(b.tabelle, b.nachher) if b.nachher else set()) for b in s.bilder}
            if text is None or not s.bilder:
                return text, None, sichten
            journal = neue_kennung("j")
            s.v.execute("INSERT INTO journal (id, konto, zeit, text, bilder, rueckgaengig) VALUES (?, ?, ?, ?, ?, ?)",
                        (journal, konto.id, k.jetzt, text, json.dumps([b.__dict__ for b in s.bilder], ensure_ascii=False),
                         1 if rueckgaengig else 0))
            return text, journal, sichten

        (text, journal, sichten), bilder = await self.v.transaktion(transaktion)
        for b in bilder:
            for melden_an in self._beobachter.get(b.tabelle, []):
                melden_an(b)
        anteile = [Anteil(Geaendert(tabelle=b.tabelle, id=b.id, daten=b.nachher), *sichten[(b.tabelle, b.id)]) for b in bilder]
        self._verteilen(anteile, konto.id, text if melden else None)
        return Antwort(meldung=text if melden else None, rueckgaengig=journal if (rueckgaengig and journal) else None,
                       geaendert=[g for a in anteile if (g := a.fuer(konto.id))])

    async def rueckgaengig(self, konto: Konto, journal_id: Kennung) -> Antwort:
        """Stellt die Vorher-Stände einer Änderung her, wenn jede Zeile noch ihren Nachher-Stand hat."""

        def arbeit(k: Kontext) -> str:
            z = k.s.v.execute("SELECT konto, text, bilder, rueckgaengig, zurueckgenommen FROM journal WHERE id=?",
                              (journal_id,)).fetchone()
            if z is None or not z["rueckgaengig"]:
                raise Abgelehnt("Das lässt sich nicht rückgängig machen", 404)
            if z["konto"] != k.konto.id:
                raise Abgelehnt("Rückgängig geht nur für deine eigenen Änderungen", 403)
            if z["zurueckgenommen"]:
                raise Abgelehnt("Das ist schon rückgängig gemacht")
            bilder = [b for b in (Bild(**b) for b in json.loads(z["bilder"])) if b.tabelle not in NUR_VORWAERTS]
            for b in (b for b in bilder if b.tabelle not in NACHSICHTIG):
                jetzt = k.s.lies(b.tabelle, b.id)
                if (jetzt or {}).get("fassung") != (b.nachher or {}).get("fassung"):
                    raise Abgelehnt("Inzwischen hat sich hier etwas geändert; Rückgängig würde es überschreiben", 409)
            for b in bilder:
                k.s.zurueckschreiben(b.tabelle, b.id, {**b.vorher, "fassung": None} if b.vorher else None)
            k.s.v.execute("UPDATE journal SET zurueckgenommen=? WHERE id=?", (k.jetzt, journal_id))
            return f"Rückgängig: {z['text']}"

        return await self.aendern(konto, arbeit, rueckgaengig=False)

    def _verteilen(self, anteile: list[Anteil], von: Kennung, text: str | None) -> None:
        """Jede Person bekommt in einer Neuigkeit, was sie von den Zeilen erfahren darf, mit der Person, die änderte,
        und der Meldung."""
        alle = self.ereignisse.verbunden() | {von}
        empfaenger: set[Kennung] = set()
        for a in anteile:
            empfaenger |= alle if a.sahen is None or a.sehen is None else (a.sahen | a.sehen)
        for konto in empfaenger:
            geaendert = [g for a in anteile if (g := a.fuer(konto))]
            self.ereignisse.senden(Neuigkeit(von=von, text=text, geaendert=geaendert), {konto})
