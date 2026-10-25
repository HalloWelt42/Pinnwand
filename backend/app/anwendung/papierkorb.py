"""Anwendungsfälle des Papierkorbs: Karten, Spalten und ganze Boards hineinlegen, an die alte Stelle wiederherstellen,
endgültig entfernen. Karten und Spalten liegen im Papierkorb ihres Boards, ein ganzes Board als Eintrag im Papierkorb
der App, mit allem, was daran hängt; sein Kürzel bleibt so lange vergeben. Wiederherstellen braucht dasselbe Recht wie
das Hineinlegen. Der Papierkorb leert sich nicht von selbst: endgültig entfernen geht nur mit dem Recht "Papierkorb
leeren", ohne Rückweg, und lässt für jede Karte ihren Namen in `entfernt` (für Zeiten, die weiter gebucht sind)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..modell import Board, Entfernt, Geloescht, Gruppe, Karte, Kennung, Konto, Modell, Spalte, Stelle
from ..regeln.board import abschluss, hat_recht, spalte_von
from .inhalt import anzahl, gleiche_karten
from . import zeiterfassung
from .karten import einreihen, hinein
from .kartenbasis import karten_der_spalte, speichern, vermerken
from .rahmen import NAMEN_DER_RECHTE, Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung


class BoardInhalt(Modell):
    """Was ein gelöschtes Board außer seinen Karten (die stehen im Eintrag) zum Wiederherstellen braucht: das Board
    selbst, seine Gruppen und die Ordner, in denen es lag. Die Laufnummer bleibt in ihrer Zeile stehen."""

    board: Board
    gruppen: list[Gruppe] = Field(default_factory=list)
    ordner: list[Kennung] = Field(default_factory=list)


# --- Helfer ------------------------------------------------------------------------------------------------------

def geloeschtes_board(k: Kontext, kuerzel: str) -> Board | None:
    """Das Board im Papierkorb, das dieses Kürzel trägt (es bleibt vergeben, damit Wiederherstellen immer geht)."""
    zeilen = k.s.alle("papierkorb", "json_extract(daten, '$.inhalt.board.kuerzel')=?", (kuerzel,))
    return BoardInhalt.model_validate(zeilen[0]["inhalt"]).board if zeilen else None


def eintrag_lesen(k: Kontext, eintrag_id: Kennung) -> Geloescht:
    d = k.s.lies("papierkorb", eintrag_id)
    if d is None:
        raise Abgelehnt("Das liegt nicht (mehr) im Papierkorb", 404)
    return Geloescht.model_validate(d)


def eintrag_name(e: Geloescht) -> str:
    if e.art == "board":
        return f"Board {board_inhalt(e).board.name}"
    return f"Spalte {e.spalte.name}" if e.art == "spalte" and e.spalte else e.karten[0].schluessel


def board_inhalt(e: Geloescht) -> BoardInhalt:
    return BoardInhalt.model_validate(e.inhalt or {})


def mit_recht(k: Kontext, b: Board, recht: str) -> Board:
    """Wie `Kontext.board_mit_recht`, für ein schon gelesenes Board, auch eines, das nur noch im Papierkorb steht."""
    if not hat_recht(b, recht, k.konto.id):
        raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE.get(recht, recht)}", 403)
    return b


def ablegen(k: Kontext, board_id: Kennung, art: Literal["karte", "spalte", "board"], karten: list[Karte], stelle: Stelle,
            spalte: Spalte | None = None, inhalt: dict | None = None) -> None:
    """Ein neuer Eintrag im Papierkorb; er hält fest, wer wann gelöscht hat."""
    e = Geloescht(id=neue_kennung("p"), board=board_id, art=art, spalte=spalte, karten=karten, stelle=stelle,
                  von=k.konto.id, am=k.jetzt, inhalt=inhalt)
    k.s.schreib("papierkorb", e.json_daten())


def gruppen_aufraeumen(k: Kontext, board_id: Kennung, gruppen: set[Kennung]) -> None:
    """Gruppen, aus denen Karten in den Papierkorb gingen: bleibt nur eine Karte übrig, endet die Gruppe (wie beim
    Lösen)."""
    for g in gruppen:
        rest = [Karte.model_validate(d) for d in k.s.alle("karten", "board=?", (board_id,)) if d.get("gruppe") == g]
        if len(rest) < 2:
            for x in rest:
                x.gruppe = None
                speichern(k, x)
            k.s.loesch("gruppen", g)


def gruppen_zurueck(k: Kontext, board_id: Kennung, karten: list[Karte]) -> None:
    """Wiederhergestellte Karten kommen in ihre Gruppe zurück, solange es sie gibt. Endete sie inzwischen, verbinden
    sich nur die Karten des Eintrags wieder, die sie teilten (mindestens zwei); sonst kommt die Karte ohne zurück."""
    for g in {c.gruppe for c in karten if c.gruppe}:
        teilen = [c for c in karten if c.gruppe == g]
        if k.s.lies("gruppen", g):
            continue
        if len(teilen) >= 2:
            k.s.schreib("gruppen", Gruppe(id=g, board=board_id).json_daten())
        else:
            for c in teilen:
                c.gruppe = None


def endgueltig(k: Kontext, e: Geloescht) -> None:
    """Einen Eintrag endgültig entfernen; je Karte bleibt ihr Name. Mit einem Board gehen auch die Einträge seines
    eigenen Papierkorbs und seine Laufnummer; das Kürzel ist danach frei."""
    karten = list(e.karten)
    if e.art == "board":
        for d in k.s.alle("papierkorb", "board=? AND id<>?", (e.board, e.id)):
            karten += Geloescht.model_validate(d).karten
            k.s.loesch("papierkorb", d["id"])
        k.s.loesch("laufnummern", e.board)
    for c in karten:
        name = Entfernt(karte=c.id, board=c.board, schluessel=c.schluessel, titel=c.titel, am=k.jetzt)
        k.s.schreib("entfernt", {"id": c.id, **name.json_daten()})
    k.s.loesch("papierkorb", e.id)


def entfernt_text(eintraege: list[Geloescht]) -> str:
    if len(eintraege) == 1:
        return f"{eintrag_name(eintraege[0])} endgültig entfernt"
    return f"{len(eintraege)} Einträge endgültig entfernt"


# --- Wiederherstellen je Art -------------------------------------------------------------------------------------

def angleichen(b: Board, c: Karte) -> None:
    """Eine Karte, die im Papierkorb lag, an das Board von heute angleichen: Labels, eigene Felder und Optionen, die es
    nicht mehr gibt, und Zuständige, die nicht mehr Mitglied sind, fallen weg."""
    labels = {l.id for l in b.labels}
    felder = {f.id: f for f in b.felder}
    mitglieder = {m.konto for m in b.mitglieder if m.konto}
    c.labels = [l for l in c.labels if l in labels]
    c.felder = {fid: w for fid, w in c.felder.items()
                if fid in felder and (felder[fid].art != "auswahl" or w in (felder[fid].optionen or []))}
    c.zustaendig = [x for x in c.zustaendig if x in mitglieder]


def karte_zurueck(k: Kontext, e: Geloescht) -> str:
    """In ihre Spalte am alten Platz; gibt es die Spalte nicht mehr, in die erste des Boards."""
    b = k.board_mit_recht(e.board, "karten.loeschen")
    c = e.karten[0]
    alt = spalte_von(b, e.stelle.spalte) if e.stelle.spalte else None
    ziel = alt or b.spalten[0]
    if alt is None:
        c.spalte = ziel.id
        c.bewegt_am = k.jetzt
    if ziel.erledigt != bool(c.abgeschlossen):
        c.abgeschlossen = abschluss(c, k.heute) if ziel.erledigt else None
    angleichen(b, c)
    gruppen_zurueck(k, b.id, [c])
    vermerken(k, c, "hat sie wiederhergestellt")
    einreihen(k, ziel, [c], e.stelle.platz)
    speichern(k, c)
    if alt is None:
        return f"{c.schluessel} wiederhergestellt, in {ziel.name} in {b.name}; ihre Spalte gibt es nicht mehr"
    return f"{c.schluessel} wiederhergestellt, an der alten Stelle in {ziel.name} in {b.name}"


def spalte_zurueck(k: Kontext, e: Geloescht) -> str:
    """Die Spalte an ihren Platz in der Spaltenfolge, mit ihren Karten in ihrer Reihenfolge."""
    b = k.board_mit_recht(e.board, "board.verwalten")
    s = e.spalte
    if s is None or spalte_von(b, s.id):
        raise Abgelehnt("Diese Spalte steht schon im Board", 409)
    b.spalten.insert(min(e.stelle.platz, len(b.spalten)), s)
    k.s.schreib("boards", b.json_daten())
    gruppen_zurueck(k, b.id, e.karten)
    for c in e.karten:
        angleichen(b, c)
        vermerken(k, c, f"hat sie mit der Spalte {s.name} wiederhergestellt")
        speichern(k, c)
    return f"Spalte {s.name} wiederhergestellt, an der alten Stelle in {b.name}"


def board_zurueck(k: Kontext, e: Geloescht) -> str:
    """Das Board mit Karten und Gruppen, zurück in die Ordner, in denen es lag (soweit es sie noch gibt)."""
    i = board_inhalt(e)
    b = mit_recht(k, i.board, "board.verwalten")
    if k.s.lies("boards", b.id) or k.s.alle("boards", "kuerzel=?", (b.kuerzel,)):
        raise Abgelehnt(f"Das Kürzel {b.kuerzel} trägt inzwischen ein anderes Board", 409)
    k.s.schreib("boards", b.json_daten())
    for g in i.gruppen:
        k.s.schreib("gruppen", g.json_daten())
    for c in e.karten:
        speichern(k, c)
    for ordner_id in i.ordner:
        d = k.s.lies("ordner", ordner_id)
        if d is not None and b.id not in d.get("boards", []):
            k.s.schreib("ordner", {**d, "boards": [*d.get("boards", []), b.id]})
    return f"Board {b.name} wiederhergestellt, mit {anzahl(len(e.karten))}"


class Papierkorb:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def in_papierkorb(self, konto: Konto, ids: list[Kennung]) -> Antwort:
        """Karten eines Boards in seinen Papierkorb, jede mit ihrer Stelle (Spalte, Platz) und allem, was daran hängt."""

        def arbeit(k: Kontext) -> str:
            b, karten = gleiche_karten(k, ids, "karten.loeschen")
            gebucht = zeiterfassung.timer_beenden(k, karten)
            for c in karten:
                platz = [x.id for x in karten_der_spalte(k, c.spalte)].index(c.id)
                k.s.loesch("karten", c.id)
                vermerken(k, c, "hat sie in den Papierkorb gelegt")
                ablegen(k, b.id, "karte", [c], Stelle(spalte=c.spalte, platz=platz))
            gruppen_aufraeumen(k, b.id, {c.gruppe for c in karten if c.gruppe})
            return (f"{anzahl(len(karten))} im Papierkorb, mit Kommentaren und Anhängen wiederherstellbar"
                    + zeiterfassung.gestoppt(gebucht))

        return await self.a.aendern(konto, arbeit)

    async def spalte_loeschen(self, konto: Konto, board_id: Kennung, spalte_id: Kennung, nach: Kennung | None = None) -> Antwort:
        """Mit Ziel wandern die Karten vorher dorthin (derselbe Weg wie Verschieben, verknüpfte ziehen mit) und die leere
        Spalte liegt im Papierkorb; ohne Ziel liegt sie dort mit ihren Karten. Erledigt-Spalte und letzte Spalte bleiben."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "board.verwalten")
            s = spalte_von(b, spalte_id)
            if s is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 404)
            if s.erledigt:
                raise Abgelehnt("Die Erledigt-Spalte bleibt; mach erst eine andere Spalte zur Erledigt-Spalte")
            if len(b.spalten) < 2:
                raise Abgelehnt("Die letzte Spalte bleibt: ein Board braucht mindestens eine")
            ziel = spalte_von(b, nach) if nach else None
            if nach and (ziel is None or ziel.id == s.id):
                raise Abgelehnt("Die Karten können nur in eine andere Spalte dieses Boards")
            wandern = [c.id for c in karten_der_spalte(k, s.id)]
            verschoben = hinein(k, b, wandern, ziel, None) if ziel and wandern else ""
            karten = karten_der_spalte(k, s.id)
            gebucht = zeiterfassung.timer_beenden(k, karten)
            for c in karten:
                k.s.loesch("karten", c.id)
                vermerken(k, c, f"hat sie mit der Spalte {s.name} in den Papierkorb gelegt")
            ablegen(k, b.id, "spalte", karten, Stelle(platz=b.spalten.index(s)), spalte=s)
            gruppen_aufraeumen(k, b.id, {c.gruppe for c in karten if c.gruppe})
            b.spalten = [x for x in b.spalten if x.id != s.id]
            k.s.schreib("boards", b.json_daten())
            if verschoben:
                return f"Spalte {s.name} im Papierkorb; {verschoben}"
            return (f"Spalte {s.name} im Papierkorb" + (f" mit {anzahl(len(karten))}" if karten else "")
                    + zeiterfassung.gestoppt(gebucht))

        return await self.a.aendern(konto, arbeit)

    async def board_in_papierkorb(self, konto: Konto, board_id: Kennung) -> Antwort:
        """Das Board mit allem (Karten, Gruppen, Ordner) als ein Eintrag in den Papierkorb der App; seine Zeilen
        verschwinden, das Kürzel bleibt vergeben."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "board.verwalten")
            karten = [Karte.model_validate(d) for d in k.s.alle("karten", "board=?", (b.id,), "spalte, reihe")]
            gebucht = zeiterfassung.timer_beenden(k, karten)
            gruppen = [Gruppe.model_validate(d) for d in k.s.alle("gruppen", "board=?", (b.id,))]
            ordner = [d for d in k.s.alle("ordner") if b.id in d.get("boards", [])]
            for c in karten:
                k.s.loesch("karten", c.id)
            for g in gruppen:
                k.s.loesch("gruppen", g.id)
            for d in ordner:
                k.s.schreib("ordner", {**d, "boards": [x for x in d["boards"] if x != b.id]})
            k.s.loesch("boards", b.id)
            inhalt = BoardInhalt(board=b, gruppen=gruppen, ordner=[d["id"] for d in ordner])
            ablegen(k, b.id, "board", karten, Stelle(), inhalt=inhalt.json_daten())
            return (f"{b.name} mit {anzahl(len(karten))} im Papierkorb; wiederherstellen unter Einstellungen, Papierkorb"
                    + zeiterfassung.gestoppt(gebucht))

        return await self.a.aendern(konto, arbeit)

    async def wiederherstellen(self, konto: Konto, eintrag_id: Kennung) -> Antwort:
        """An die alte Stelle, mit demselben Schlüssel und allem, was daran hing."""

        def arbeit(k: Kontext) -> str:
            e = eintrag_lesen(k, eintrag_id)
            zurueck = {"karte": karte_zurueck, "spalte": spalte_zurueck, "board": board_zurueck}[e.art]
            text = zurueck(k, e)
            k.s.loesch("papierkorb", e.id)
            return text

        return await self.a.aendern(konto, arbeit)

    async def entfernen(self, konto: Konto, ids: list[Kennung]) -> Antwort:
        """Gewählte Einträge endgültig entfernen, alle oder keiner (Recht "Papierkorb leeren" in jedem ihrer Boards)."""

        def arbeit(k: Kontext) -> str:
            eintraege = [eintrag_lesen(k, i) for i in dict.fromkeys(ids)]
            if not eintraege:
                raise Abgelehnt("Nichts gewählt")
            for e in eintraege:
                mit_recht(k, board_inhalt(e).board if e.art == "board" else k.board(e.board), "papierkorb.leeren")
            for e in eintraege:
                endgueltig(k, e)
            return entfernt_text(eintraege)

        return await self.a.aendern(konto, arbeit, rueckgaengig=False)

    async def leeren(self, konto: Konto, board_id: Kennung) -> Antwort:
        """Den ganzen Papierkorb eines Boards endgültig leeren."""

        def arbeit(k: Kontext) -> str | None:
            b = k.board_mit_recht(board_id, "papierkorb.leeren")
            eintraege = [Geloescht.model_validate(d) for d in k.s.alle("papierkorb", "board=?", (b.id,))]
            if not eintraege:
                return None
            for e in eintraege:
                endgueltig(k, e)
            return f"Papierkorb von {b.name} geleert: {entfernt_text(eintraege)}"

        return await self.a.aendern(konto, arbeit, rueckgaengig=False)
