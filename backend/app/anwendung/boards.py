"""Anwendungsfälle an Boards: ein Board aus einer Vorlage anlegen (wer anlegt, ist Besitzer), Personen einladen und das
Board einstellen (Name, Farbe, Kartenart, Einstellungen, Module), als eigene Vorlage speichern; dazu die Prüfung eines
Kürzels beim Anlegen. Das Kürzel ist über alle Boards eindeutig und bleibt beim Umbenennen fest. Eingeladen wird per
Kontoname der Kellerwolke; wer noch nie angemeldet war, wartet als Mitglied ohne Kennung, bis er sich das erste Mal
anmeldet. Damit er sich anmelden darf, schaltet der `Zugang` den Namen in der App frei. Hier stehen auch die kleinen
Hilfen, die alle Anwendungsfälle der Verwaltung teilen (Namen, Reihenfolgen, Zählen, eine Änderung am Board)."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from typing import Literal, Protocol, TypeVar

from ..modell import (MODULE, MODULE_DA, Board, BoardEinstellungen, Farbe, Feld, Kartenart, Kennung, Konto, Label, Mitglied,
                      Modell, Ordner, Spalte, Vorlage, VorlageFeld, VorlageLabel, VorlageSpalte)
from ..regeln.board import einstellung_fehler
from ..regeln.kuerzel import KUERZEL_MUSTER, Inhaber, abwandlungen, kuerzel_fehler
from ..verzeichnis import Schreiber
from ..vorlagen import start_rollen
from .papierkorb import geloeschtes_board
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: Farben neuer Boards: die erste, die noch kein Board trägt (unterscheidbar in der Seitenleiste)
NEU_FARBEN: list[Farbe] = ["tuerkis", "himmel", "honig", "violett", "rose", "sand", "stahl", "koralle", "petrol", "minze", "flieder"]
#: Vorgabe des Zeitfensters neuer Erledigt-Spalten (wie in der alten App)
ZEITFENSTER_VORGABE = "heute"
#: Kontonamen der Kellerwolke: Buchstaben, Ziffern, Punkt, Bindestrich, Unterstrich, @
KONTONAME = re.compile(r"^[\w.@-]{1,64}$")
#: Längster Name eines Boards, einer Spalte, eines Labels, Feldes, einer Option, Rolle, Vorlage oder eines Ordners
NAME_LAENGE = 100
#: Namen der Module für Meldungen, gleich MODULE in frontend/src/anzeige.ts
MODUL_NAMEN = {
    "zeiterfassung": "Zeiterfassung", "arbeitszeit": "Arbeitszeit und Urlaub", "serien": "Serien und Termine",
    "berichte": "Berichte", "transkripte": "Transkripte", "vorlesen": "Vorlesen", "ki": "KI an der Karte",
}


class Zugang(Protocol):
    """Wer die App nutzen darf. Eingeladene Kontonamen werden freigeschaltet; entzogen wird nie selbsttätig."""

    async def freischalten(self, namen: Iterable[str]) -> None: ...


class Einladung(Modell):
    kellerwolke: str
    rolle: Kennung = "mitglied"


def kuerzel_inhaber(k: Kontext):
    """Wem ein Kürzel gehört: Name des Boards, wenn ich es sehe, sonst "" (fremdes Board), None: frei. Ein Board im
    Papierkorb behält sein Kürzel, damit es sich wiederherstellen lässt."""
    def inhaber(kuerzel: str) -> str | None:
        d = k.s.alle("boards", "kuerzel=?", (kuerzel,))
        if d:
            b = Board.model_validate(d[0])
            return b.name if any(m.konto == k.konto.id for m in b.mitglieder) else ""
        g = geloeschtes_board(k, kuerzel)
        if g is None:
            return None
        return f"{g.name} im Papierkorb" if any(m.konto == k.konto.id for m in g.mitglieder) else ""
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


# --- Hilfen der Verwaltung ---------------------------------------------------------------------------------------

class HatKennung(Protocol):
    id: Kennung


E = TypeVar("E", bound=HatKennung)


def name_pruefen(name: str, wer: str) -> str:
    """Ein Name ohne Leerraum am Rand; abgelehnt, wenn er leer oder zu lang ist. `wer`: "Ein Board", "Eine Spalte" ..."""
    n = name.strip()
    if not n:
        raise Abgelehnt(f"{wer} braucht einen Namen")
    if len(n) > NAME_LAENGE:
        raise Abgelehnt(f"Ein Name hat höchstens {NAME_LAENGE} Zeichen")
    return n


def vergeben(eintraege: Iterable[tuple[Kennung, str]], name: str, ausser: Kennung = "") -> str | None:
    """Der schon vergebene Name, der ohne Beachtung von Groß und klein gleich ist (außer dem Eintrag `ausser`)."""
    gesucht = name.strip().casefold()
    return next((n for i, n in eintraege if i != ausser and n.casefold() == gesucht), None)


def neue_reihenfolge(alle: Sequence[E], ids: list[Kennung], was: str) -> list[E] | None:
    """Die Einträge in der Reihenfolge von `ids`; None, wenn sie gleich bleibt. Abgelehnt, wenn `ids` nicht jeden Eintrag
    genau einmal nennt. `was`: "jede Spalte des Boards" und so weiter."""
    nach_id = {e.id: e for e in alle}
    if len(ids) != len(alle) or set(ids) != set(nach_id):
        raise Abgelehnt(f"Die Reihenfolge muss {was} genau einmal nennen")
    if ids == [e.id for e in alle]:
        return None
    return [nach_id[i] for i in ids]


def anzahl(n: int, eins: str, viele: str) -> str:
    return f"{n} {eins if n == 1 else viele}"


async def am_board(a: Anwendung, konto: Konto, board_id: Kennung, recht: str,
                   tun: Callable[[Kontext, Board], str | None]) -> Antwort:
    """Eine Änderung am Board mit dem Recht: `tun` ändert das gelesene Board (und was daran hängt) und gibt den Text der
    Meldung zurück; danach wird das Board gespeichert. None: es ändert sich nichts."""

    def arbeit(k: Kontext) -> str | None:
        b = k.board_mit_recht(board_id, recht)
        text = tun(k, b)
        if text is not None:
            k.s.schreib("boards", b.json_daten())
        return text

    return await a.aendern(konto, arbeit)


# --- Einstellungen, Vorlagen, Kürzel -----------------------------------------------------------------------------

class Einstellungsteil(Modell):
    """Geänderte Einstellungen eines Boards; nur die gesendeten gelten."""

    alterung_warnung: int | None = None
    alterung_gefahr: int | None = None
    ladeschritt: int | None = None
    archiv_tage: int | None = None

    def gesendet(self) -> dict[str, int]:
        return {n: getattr(self, n) for n in self.model_fields_set if getattr(self, n) is not None}


class KuerzelPruefung(Modell):
    """Ob ein Kürzel frei ist, in der Form von frontend/src/regeln/kuerzel.ts; vergeben mit bis zu drei freien
    Abwandlungen. Der Server kennt alle Boards, auch fremde."""

    kuerzel: str
    stand: Literal["leer", "form", "vergeben", "frei"]
    text: str
    frei: list[str] = []


def kuerzel_pruefung(kuerzel: str, inhaber: Inhaber) -> KuerzelPruefung:
    fehler = kuerzel_fehler(kuerzel, inhaber)
    if fehler is None:
        return KuerzelPruefung(kuerzel=kuerzel, stand="frei", text=f"Frei. Karten heißen {kuerzel}-1, {kuerzel}-2 und so weiter.")
    if not kuerzel:
        return KuerzelPruefung(kuerzel=kuerzel, stand="leer", text=fehler)
    if not KUERZEL_MUSTER.match(kuerzel):
        return KuerzelPruefung(kuerzel=kuerzel, stand="form", text=fehler)
    return KuerzelPruefung(kuerzel=kuerzel, stand="vergeben", text=fehler, frei=abwandlungen(kuerzel, inhaber))


def vorlage_aus(b: Board, name: str, konto: Kennung) -> Vorlage:
    """Aufbau eines Boards als eigene Vorlage: Spalten, Kartenart, Felder, Labels, Module; ohne Karten und Mitglieder."""
    return Vorlage(
        id=neue_kennung("v"), name=name, beschreibung=f"Eigene Vorlage aus {b.name}", symbol="fa-copy", eigen=True, konto=konto,
        spalten=[VorlageSpalte(name=s.name, farbe=s.farbe, erledigt=s.erledigt, grenze=s.grenze) for s in b.spalten],
        kartenart=b.kartenart,
        felder=[VorlageFeld(name=f.name, art=f.art, optionen=f.optionen, auf_karte=f.auf_karte) for f in b.felder],
        labels=[VorlageLabel(name=l.name, farbe=l.farbe) for l in b.labels],
        module=[m for m in MODULE if b.module.get(m)],
    )


class Boards:
    def __init__(self, anwendung: Anwendung, zugang: Zugang) -> None:
        self.a = anwendung
        self.zugang = zugang

    async def anlegen(self, konto: Konto, vorlage_id: Kennung, name: str, kuerzel: str, ordner: Kennung | None = None,
                      einladungen: list[Einladung] | None = None) -> Antwort:
        einladungen = einladungen or []

        def arbeit(k: Kontext) -> str:
            n = name_pruefen(name, "Ein Board")
            fehler = kuerzel_fehler(kuerzel, kuerzel_inhaber(k))
            if fehler:
                raise Abgelehnt(fehler, 409 if "vergeben" in fehler else 400)
            d = k.s.lies("vorlagen", vorlage_id)
            if d is None or (d.get("konto") and d["konto"] != konto.id):
                raise Abgelehnt("Diese Vorlage gibt es nicht", 404)
            v = Vorlage.model_validate(d)
            farben = {b.get("farbe") for b in k.s.alle("boards")}
            b = Board(
                id=neue_kennung("b"), name=n, kuerzel=kuerzel, kartenart=v.kartenart,
                farbe=next((f for f in NEU_FARBEN if f not in farben), NEU_FARBEN[0]),
                spalten=[Spalte(id=neue_kennung("s"), name=s.name, farbe=s.farbe, erledigt=s.erledigt, grenze=s.grenze,
                                zeitfenster=ZEITFENSTER_VORGABE if s.erledigt else None) for s in v.spalten],
                labels=[Label(id=neue_kennung("l"), name=l.name, farbe=l.farbe) for l in v.labels],
                felder=[Feld(id=neue_kennung("f"), **f.model_dump()) for f in v.felder],
                rollen=start_rollen(),
                mitglieder=[Mitglied(konto=konto.id, kellerwolke=konto.kellerwolke, rolle="besitzer", seit=k.heute)],
                module={m: m in v.module and m in MODULE_DA for m in MODULE},
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
            return f"Board {n} angelegt, Karten heißen {kuerzel}-1 und so weiter"

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

    async def kuerzel_pruefen(self, konto: Konto, kuerzel: str) -> KuerzelPruefung:
        """Ist das Kürzel frei? Über alle Boards; bei einem fremden ohne seinen Namen. Liest nur."""
        uhr = self.a.uhr

        def lesen(s: Schreiber) -> KuerzelPruefung:
            return kuerzel_pruefung(kuerzel, kuerzel_inhaber(Kontext(s, konto, uhr)))

        ergebnis, _ = await self.a.v.transaktion(lesen)
        return ergebnis

    # --- Allgemein (Recht "Board verwalten") ---------------------------------------------------------------------

    async def umbenennen(self, konto: Konto, board_id: Kennung, name: str) -> Antwort:
        """Umbenennen ändert das Kürzel nie (Kartenschlüssel und Adressen bleiben)."""

        def tun(k: Kontext, b: Board) -> str | None:
            n = name_pruefen(name, "Ein Board")
            if n == b.name:
                return None
            alt, b.name = b.name, n
            return f"{alt} heißt jetzt {n}; das Kürzel {b.kuerzel} bleibt"

        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    async def farbe_setzen(self, konto: Konto, board_id: Kennung, farbe: Farbe) -> Antwort:
        def tun(k: Kontext, b: Board) -> str | None:
            if b.farbe == farbe:
                return None
            b.farbe = farbe
            return f"Farbe von {b.name} geändert"

        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    async def kartenart_setzen(self, konto: Konto, board_id: Kennung, art: Kartenart) -> Antwort:
        """Art neuer Karten, wenn beim Anlegen keine gewählt ist; bestehende Karten bleiben, wie sie sind."""

        def tun(k: Kontext, b: Board) -> str | None:
            if b.kartenart == art:
                return None
            b.kartenart = art
            return f"Neue Karten in {b.name} sind ab jetzt {'Ideen' if art == 'idee' else 'Arbeit'}"

        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    async def einstellungen_setzen(self, konto: Konto, board_id: Kennung, teil: Einstellungsteil) -> Antwort:
        """Alterung, Ladeschritt und Archiv; ganze Zahlen in ihren Grenzen, 0 schaltet eine Alterungsstufe aus."""
        neu = teil.gesendet()

        def tun(k: Kontext, b: Board) -> str | None:
            for feld, wert in neu.items():
                fehler = einstellung_fehler(feld, wert)
                if fehler:
                    raise Abgelehnt(fehler)
            if all(getattr(b.einstellungen, f) == w for f, w in neu.items()):
                return None
            b.einstellungen = b.einstellungen.model_copy(update=neu)
            return f"Einstellungen von {b.name} gespeichert"

        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    async def modul_schalten(self, konto: Konto, board_id: Kennung, modul: str, an: bool) -> Antwort:
        """Modul an oder aus: aus blendet es in Board, Karten und Rollen aus, seine Daten bleiben. Nur Module, die diese
        Fassung anbietet."""
        if modul not in MODULE_DA:
            raise Abgelehnt("Dieses Modul bietet diese Pinnwand nicht an")

        def tun(k: Kontext, b: Board) -> str | None:
            if b.module.get(modul, False) == an:
                return None
            b.module[modul] = an
            name = MODUL_NAMEN[modul]
            return f"{name} in {b.name} eingeschaltet" if an else f"{name} in {b.name} ausgeblendet; die Daten bleiben"

        return await am_board(self.a, konto, board_id, "board.verwalten", tun)

    async def als_vorlage(self, konto: Konto, board_id: Kennung, name: str) -> Antwort:
        """Als eigene Vorlage speichern; sie steht danach beim Anlegen unter den eigenen Vorlagen (nur für dich)."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "board.verwalten")
            v = vorlage_aus(b, name_pruefen(name, "Eine Vorlage"), konto.id)
            k.s.schreib("vorlagen", v.json_daten())
            return (f"Vorlage {v.name} gespeichert: {anzahl(len(v.spalten), 'Spalte', 'Spalten')}, "
                    f"{anzahl(len(v.felder), 'Feld', 'Felder')}, {anzahl(len(v.labels), 'Label', 'Labels')}; "
                    "sie steht beim Anlegen unter den eigenen Vorlagen")

        return await self.a.aendern(konto, arbeit)
