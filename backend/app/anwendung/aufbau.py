"""Anwendungsfälle am Aufbau eines Boards, alle mit dem Recht "Board verwalten": Spalten anlegen, ändern, ordnen und zur
Erledigt-Spalte machen (genau eine je Board); Labels, deren Namen je Board ohne Beachtung von Groß und klein eindeutig
sind; eigene Felder mit Art, Optionen und Reihenfolge. Was an den Karten hängt, ziehen die Fälle mit: ein gelöschtes
Label oder Feld und eine entfernte Option fallen an allen Karten des Boards weg, auch an archivierten. Spalten löscht
der Papierkorb."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..modell import Board, Farbe, Feld, FeldArt, Karte, Kennung, Konto, Label, Modell, Spalte, Zeitfenster
from ..regeln.board import abschluss, spalte_von, zahl_fehler
from .boards import ZEITFENSTER_VORGABE, am_board, anzahl, name_pruefen, neue_reihenfolge, vergeben
from .kartenbasis import speichern
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung


class Spaltenaenderung(Modell):
    """Was sich an einer Spalte ändert; nur die gesendeten Felder gelten."""

    name: str | None = None
    farbe: Farbe | None = None
    #: null: keine Grenze
    grenze: int | None = None
    zeitfenster: Zeitfenster | None = None
    #: Vorgabe für alle: die Spalte steht anfangs eingeklappt (jede Person klappt für sich um)
    eingeklappt: bool | None = None

    def gesendet(self) -> dict[str, Any]:
        return {n: getattr(self, n) for n in self.model_fields_set}


class Feldaenderung(Modell):
    name: str | None = None
    art: FeldArt | None = None
    auf_karte: bool | None = None


def karten_des_boards(k: Kontext, b: Board) -> list[Karte]:
    """Alle Karten des Boards, auch die archivierten."""
    return [Karte.model_validate(d) for d in k.s.alle("karten", "board=?", (b.id,))]


def spalte_lesen(b: Board, spalte_id: Kennung) -> Spalte:
    s = spalte_von(b, spalte_id)
    if s is None:
        raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht (mehr)", 404)
    return s


def label_lesen(b: Board, label_id: Kennung) -> Label:
    l = next((x for x in b.labels if x.id == label_id), None)
    if l is None:
        raise Abgelehnt("Dieses Label gibt es in diesem Board nicht (mehr)", 404)
    return l


def label_frei(b: Board, name: str, ausser: Kennung = "") -> None:
    doppelt = vergeben(((l.id, l.name) for l in b.labels), name, ausser)
    if doppelt:
        raise Abgelehnt(f"Das Label {doppelt} gibt es schon", 409)


def feld_lesen(b: Board, feld_id: Kennung) -> Feld:
    f = next((x for x in b.felder if x.id == feld_id), None)
    if f is None:
        raise Abgelehnt("Dieses Feld gibt es in diesem Board nicht (mehr)", 404)
    return f


def karten_mit_wert(k: Kontext, b: Board, feld_id: Kennung) -> list[Karte]:
    return [c for c in karten_des_boards(k, b) if c.felder.get(feld_id)]


def spalte_aendern(s: Spalte, neu: dict[str, Any]) -> list[str]:
    """Wendet die gesendeten Angaben auf die Spalte an. Ergebnis: was sich geändert hat, für die Meldung."""
    teile: list[str] = []
    if neu.get("name") is not None:
        n = name_pruefen(neu["name"], "Eine Spalte")
        if n != s.name:
            s.name = n
            teile.append(f"heißt jetzt {n}")
    if neu.get("farbe") and neu["farbe"] != s.farbe:
        s.farbe = neu["farbe"]
        teile.append("neue Farbe")
    if "grenze" in neu:
        g = neu["grenze"]
        if g is not None and s.erledigt:
            raise Abgelehnt("Die Erledigt-Spalte hat keine Grenze")
        fehler = zahl_fehler("grenze", g) if g is not None else None
        if fehler:
            raise Abgelehnt(f"Grenze: {fehler}, leer heißt keine")
        if g != s.grenze:
            s.grenze = g
            teile.append("ohne Grenze" if g is None else f"Grenze {g}")
    if neu.get("zeitfenster"):
        if not s.erledigt:
            raise Abgelehnt("Ein Zeitfenster hat nur die Erledigt-Spalte")
        if neu["zeitfenster"] != s.zeitfenster:
            s.zeitfenster = neu["zeitfenster"]
            teile.append("neues Zeitfenster")
    if neu.get("eingeklappt") is not None:
        wert = neu["eingeklappt"] or None
        if wert != s.eingeklappt:
            s.eingeklappt = wert
            teile.append("anfangs eingeklappt" if wert else "anfangs aufgeklappt")
    return teile


class Aufbau:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def _am_board(self, konto: Konto, board_id: Kennung, tun: Callable[[Kontext, Board], str | None]) -> Antwort:
        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    # --- Spalten ------------------------------------------------------------------------------------------------

    async def spalte_anlegen(self, konto: Konto, board_id: Kennung, name: str, farbe: Farbe) -> Antwort:
        """Neue Spalte ans Ende, ohne Grenze, offen."""

        def tun(k: Kontext, b: Board) -> str:
            n = name_pruefen(name, "Eine Spalte")
            b.spalten.append(Spalte(id=neue_kennung("s"), name=n, farbe=farbe))
            return f"Spalte {n} angelegt, am Ende"

        return await self._am_board(konto, board_id, tun)

    async def spalte_aendern(self, konto: Konto, board_id: Kennung, spalte_id: Kennung, a: Spaltenaenderung) -> Antwort:
        """Name, Farbe, Grenze (offene Spalten), Zeitfenster (die Erledigt-Spalte) und ob sie anfangs eingeklappt steht."""
        neu = a.gesendet()

        def tun(k: Kontext, b: Board) -> str | None:
            s = spalte_lesen(b, spalte_id)
            teile = spalte_aendern(s, neu)
            return f"Spalte {s.name}: {', '.join(teile)}" if teile else None

        return await self._am_board(konto, board_id, tun)

    async def spalten_ordnen(self, konto: Konto, board_id: Kennung, ids: list[Kennung]) -> Antwort:
        def tun(k: Kontext, b: Board) -> str | None:
            neu = neue_reihenfolge(b.spalten, ids, "jede Spalte des Boards")
            if neu is None:
                return None
            b.spalten = neu
            return f"Spalten von {b.name} neu geordnet"

        return await self._am_board(konto, board_id, tun)

    async def zur_erledigt_spalte(self, konto: Konto, board_id: Kennung, spalte_id: Kennung) -> Antwort:
        """Genau eine Erledigt-Spalte je Board: die gewählte wird es, die bisherige wird offen. Karten der neuen gelten als
        erledigt (Abschluss heute, Serienkarten ihr Termintag), die der alten sind wieder offen (Alter neu)."""

        def tun(k: Kontext, b: Board) -> str | None:
            neu = spalte_lesen(b, spalte_id)
            if neu.erledigt:
                return None
            alt = next((s for s in b.spalten if s.erledigt), None)
            if alt:
                alt.erledigt = False
                for c in (Karte.model_validate(d) for d in k.s.alle("karten", "spalte=?", (alt.id,))):
                    c.abgeschlossen = None
                    c.bewegt_am = k.jetzt
                    speichern(k, c)
            neu.erledigt = True
            neu.zeitfenster = neu.zeitfenster or ZEITFENSTER_VORGABE
            neu.grenze = None
            for c in (Karte.model_validate(d) for d in k.s.alle("karten", "spalte=?", (neu.id,))):
                if not c.abgeschlossen:
                    c.abgeschlossen = abschluss(c, k.heute)
                    speichern(k, c)
            return f"{neu.name} ist jetzt die Erledigt-Spalte" + (f"; Karten in {alt.name} sind wieder offen" if alt else "")

        return await self._am_board(konto, board_id, tun)

    # --- Labels -------------------------------------------------------------------------------------------------

    async def label_anlegen(self, konto: Konto, board_id: Kennung, name: str, farbe: Farbe) -> Antwort:
        def tun(k: Kontext, b: Board) -> str:
            n = name_pruefen(name, "Ein Label")
            label_frei(b, n)
            b.labels.append(Label(id=neue_kennung("l"), name=n, farbe=farbe))
            return f"Label {n} angelegt"

        return await self._am_board(konto, board_id, tun)

    async def label_aendern(self, konto: Konto, board_id: Kennung, label_id: Kennung, name: str | None = None,
                            farbe: Farbe | None = None) -> Antwort:
        """Umbenennen und Umfärben gelten sofort auf allen Karten (sie tragen das Label, nicht seinen Text)."""

        def tun(k: Kontext, b: Board) -> str | None:
            l = label_lesen(b, label_id)
            alt, alte_farbe = l.name, l.farbe
            if name is not None:
                l.name = name_pruefen(name, "Ein Label")
                label_frei(b, l.name, l.id)
            if farbe:
                l.farbe = farbe
            if l.name != alt:
                return f"Label {alt} heißt jetzt {l.name}, auf allen Karten"
            return f"Farbe des Labels {l.name} geändert" if l.farbe != alte_farbe else None

        return await self._am_board(konto, board_id, tun)

    async def label_loeschen(self, konto: Konto, board_id: Kennung, label_id: Kennung) -> Antwort:
        """Das Label fällt an allen Karten des Boards weg, sonst ändert sich nichts an ihnen."""

        def tun(k: Kontext, b: Board) -> str:
            l = label_lesen(b, label_id)
            traeger = [c for c in karten_des_boards(k, b) if l.id in c.labels]
            for c in traeger:
                c.labels = [x for x in c.labels if x != l.id]
                speichern(k, c)
            b.labels = [x for x in b.labels if x.id != l.id]
            return f"Label {l.name} gelöscht" + (f", an {anzahl(len(traeger), 'Karte', 'Karten')} entfernt" if traeger else "")

        return await self._am_board(konto, board_id, tun)

    # --- Eigene Felder ------------------------------------------------------------------------------------------

    async def feld_anlegen(self, konto: Konto, board_id: Kennung, name: str, art: FeldArt) -> Antwort:
        def tun(k: Kontext, b: Board) -> str:
            n = name_pruefen(name, "Ein Feld")
            b.felder.append(Feld(id=neue_kennung("f"), name=n, art=art, optionen=[] if art == "auswahl" else None))
            return f"Feld {n} angelegt"

        return await self._am_board(konto, board_id, tun)

    async def feld_aendern(self, konto: Konto, board_id: Kennung, feld_id: Kennung, a: Feldaenderung) -> Antwort:
        """Name, Art und "auf der Karte"; die Art bleibt fest, solange Karten einen Wert tragen."""

        def tun(k: Kontext, b: Board) -> str | None:
            f = feld_lesen(b, feld_id)
            teile: list[str] = []
            if a.name is not None:
                n = name_pruefen(a.name, "Ein Feld")
                if n != f.name:
                    f.name = n
                    teile.append(f"heißt jetzt {n}")
            if a.art is not None and a.art != f.art:
                if karten_mit_wert(k, b, f.id):
                    raise Abgelehnt(f"Die Art von {f.name} bleibt fest, solange Karten Werte tragen")
                f.art = a.art
                if a.art == "auswahl" and f.optionen is None:
                    f.optionen = []
                teile.append("neue Art")
            if a.auf_karte is not None and a.auf_karte != f.auf_karte:
                f.auf_karte = a.auf_karte
                teile.append("auf der Karte" if a.auf_karte else "nur im Detail")
            return f"Feld {f.name}: {', '.join(teile)}" if teile else None

        return await self._am_board(konto, board_id, tun)

    async def feld_option(self, konto: Konto, board_id: Kennung, feld_id: Kennung, option: str, dazu: bool) -> Antwort:
        """Option einer Auswahl hinzufügen (ohne Dublette in anderer Schreibweise) oder entfernen; Karten mit der entfernten
        Option verlieren den Wert, damit nichts mehr gilt, was nicht zur Wahl steht."""

        def tun(k: Kontext, b: Board) -> str | None:
            f = feld_lesen(b, feld_id)
            if f.art != "auswahl":
                raise Abgelehnt("Optionen hat nur ein Feld der Art Auswahl")
            o = name_pruefen(option, "Eine Option")
            optionen = list(f.optionen or [])
            if dazu:
                doppelt = vergeben(((x, x) for x in optionen), o)
                if doppelt:
                    raise Abgelehnt(f"Die Option {doppelt} gibt es schon", 409)
                f.optionen = [*optionen, o]
                return f"Option {o} in {f.name} hinzugefügt"
            if o not in optionen:
                return None
            f.optionen = [x for x in optionen if x != o]
            mit = [c for c in karten_mit_wert(k, b, f.id) if c.felder[f.id] == o]
            for c in mit:
                del c.felder[f.id]
                speichern(k, c)
            return f"Option {o} aus {f.name} entfernt" + (f", an {anzahl(len(mit), 'Karte', 'Karten')} geleert" if mit else "")

        return await self._am_board(konto, board_id, tun)

    async def felder_ordnen(self, konto: Konto, board_id: Kennung, ids: list[Kennung]) -> Antwort:
        """So stehen die Felder im Kartendetail und auf der Karte."""

        def tun(k: Kontext, b: Board) -> str | None:
            neu = neue_reihenfolge(b.felder, ids, "jedes Feld des Boards")
            if neu is None:
                return None
            b.felder = neu
            return "Felder neu geordnet"

        return await self._am_board(konto, board_id, tun)

    async def feld_loeschen(self, konto: Konto, board_id: Kennung, feld_id: Kennung) -> Antwort:
        """Die Werte an den Karten fallen mit dem Feld weg."""

        def tun(k: Kontext, b: Board) -> str:
            f = feld_lesen(b, feld_id)
            mit = karten_mit_wert(k, b, f.id)
            for c in mit:
                del c.felder[f.id]
                speichern(k, c)
            b.felder = [x for x in b.felder if x.id != f.id]
            return f"Feld {f.name} gelöscht" + (f", Werte an {anzahl(len(mit), 'Karte', 'Karten')} entfernt" if mit else "")

        return await self._am_board(konto, board_id, tun)
