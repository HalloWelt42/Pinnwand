"""Hinweise an Personen: was sie in ihren Boards betrifft (zugewiesen, erwähnt, Kommentar, verschoben, fällig), mit
Sprung zur Karte. Sie entstehen im Server in derselben Änderung wie ihr Anlass (Rückgängig nimmt sie mit), nie an die
handelnde Person, nur an Mitglieder des Boards und nur auf den Wegen, die die Person eingeschaltet hat. Fällige Karten
meldet der Begleiter `Faelligkeit` einmal am Tag. Gelesen gilt am Konto, auf allen Geräten."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Iterable

from appkern.app import Begleiter

from ..modell import MODULE_DA, Board, Hinweis, HinweisArt, HinweisWeg, Karte, Kennung, Konto, PersonEinstellungen, Spalte
from ..regeln.board import spalte_von
from ..regeln.tage import tage_zwischen
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

logger = logging.getLogger("pinnwand.hinweise")

#: Arten, die diese Fassung gibt; Termine gehören zum Modul Serien
ARTEN_DA: tuple[str, ...] = ("zugewiesen", "faellig", "erwaehnt", "kommentar", "verschoben") + (
    ("termin",) if "serien" in MODULE_DA else ())
#: Wege, die diese Fassung anbietet (die Oberfläche bekommt sie im Stand); der Assistent gehört zum Verbund
WEGE_DA: tuple[str, ...] = ("pinnwand", "push")
#: Push gilt, solange die Person nichts anderes schaltet, für das, was sie selbst betrifft; die übrigen kommen nur in
#: der Pinnwand (und Push erst, wenn ein Gerät eingerichtet ist)
PUSH_VORGABE = {"zugewiesen", "faellig", "erwaehnt", "termin"}


def vorgabe(art: str, weg: str) -> bool:
    """Was gilt, solange die Person einen Weg für eine Art nicht selbst geschaltet hat."""
    return weg == "pinnwand" or (weg == "push" and art in PUSH_VORGABE)
NAMEN_DER_ARTEN = {"zugewiesen": "Zugewiesen", "faellig": "Fällig", "erwaehnt": "Erwähnt", "termin": "Termin",
                   "kommentar": "Kommentar", "verschoben": "Verschoben"}
NAMEN_DER_WEGE = {"pinnwand": "In der Pinnwand", "push": "Push aufs Telefon", "assistent": "Über den Assistenten"}
#: wer handelt, wenn die Pinnwand selbst Hinweise gibt (fällig): steht im Journal, nie in einem Board
PINNWAND = Konto(id="pinnwand", name="Pinnwand", kuerzel="PW", kellerwolke="")
#: so oft schaut der Begleiter, ob ein neuer Tag begonnen hat (Sekunden)
TAKT_S = 300.0

#: Erwähnung mit @ wie in der Darstellung (teile/markdown.ts): nicht hinter Buchstabe, Ziffer, Punkt oder @
ERWAEHNUNG = re.compile(r"(?<![\w.@])@(\w(?:[\w.-]*\w)?)")
#: Zaun eines Codeblocks und, im Text, Code und Adressen: dort ist ein @ keine Erwähnung
ZAUN = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*[\w-]*\s*$")
CODE_ODER_ADRESSE = re.compile(r"(`+).+?\1|https?://[^\s<>\"]*")


# --- Wege ----------------------------------------------------------------------------------------------------------

def weg_an(einstellungen: dict | None, art: str, weg: str = "pinnwand") -> bool:
    """Ob eine Person Hinweise dieser Art auf diesem Weg bekommt: ihre Einstellung, sonst die Vorgabe."""
    je_art = ((einstellungen or {}).get("hinweise") or {}).get(art) or {}
    return bool(je_art.get(weg, vorgabe(art, weg)))


def will(k: Kontext, konto: Kennung, art: str) -> bool:
    return weg_an(k.s.lies("person_einstellungen", konto), art)


# --- Erwähnungen ---------------------------------------------------------------------------------------------------

def _lesbarer_text(text: str) -> str:
    """Der Text ohne Codeblöcke, Code und Adressen (wie die Darstellung ihn liest)."""
    aus: list[str] = []
    zaun: str | None = None
    for z in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if zaun:
            if z.strip().startswith(zaun):
                zaun = None
            continue
        m = ZAUN.match(z)
        if m:
            zaun = m.group(1)
            continue
        aus.append(z)
    return CODE_ODER_ADRESSE.sub(" ", "\n".join(aus))


def erwaehnte(k: Kontext, b: Board, text: str | None) -> set[Kennung]:
    """Wen ein Text mit @ erwähnt: Vorname, Kellerwolke-Name oder Kürzel eines Mitglieds, ohne Groß- und
    Kleinschreibung; bei mehreren passenden die erste Person, wie die Darstellung sie nennt."""
    if not text:
        return set()
    personen = [Konto.model_validate(d) for d in (k.s.lies("konten", m.konto) for m in b.mitglieder if m.konto) if d]
    gefunden: set[Kennung] = set()
    for wort in ERWAEHNUNG.findall(_lesbarer_text(text)):
        w = wort.lower()
        p = next((p for p in personen if w in (p.name.split(" ")[0].lower(), p.kellerwolke.lower(), p.kuerzel.lower())), None)
        if p:
            gefunden.add(p.id)
    return gefunden


# --- Anlässe (in der Transaktion der auslösenden Änderung) -----------------------------------------------------------

def melden(k: Kontext, b: Board, art: HinweisArt, an: Iterable[Kennung], karte: Karte | None, text: str) -> None:
    """Ein Hinweis je Person: nie an die handelnde, nur an Mitglieder des Boards, nur wenn die Person die Art in der
    Pinnwand bekommen will. Ohne Karte (ein Termin) führt der Hinweis zu den Serien und Terminen."""
    mitglieder = {m.konto for m in b.mitglieder if m.konto}
    for konto in dict.fromkeys(an):
        if konto == k.konto.id or konto not in mitglieder or not will(k, konto, art):
            continue
        h = Hinweis(id=neue_kennung("h"), konto=konto, art=art, zeit=k.jetzt, von=k.konto.id, board=b.id,
                    karte=karte.id if karte else None, schluessel=karte.schluessel if karte else None, text=text)
        k.s.schreib("hinweise", h.json_daten())


def zugewiesen(k: Kontext, b: Board, karte: Karte, personen: Iterable[Kennung]) -> None:
    melden(k, b, "zugewiesen", personen, karte, f"{k.konto.name} hat dir {karte.schluessel} zugewiesen")


def erwaehnt(k: Kontext, b: Board, karte: Karte, personen: Iterable[Kennung]) -> None:
    melden(k, b, "erwaehnt", personen, karte, f"{k.konto.name} hat dich in {karte.schluessel} erwähnt")


def nach_bearbeiten(k: Kontext, b: Board, alt: Karte, neu: Karte) -> None:
    """Wer neu zuständig ist, und wer in Beschreibung oder Notizen neu erwähnt ist (nicht bei jedem Speichern erneut)."""
    zugewiesen(k, b, neu, [x for x in neu.zustaendig if x not in alt.zustaendig])
    neu_erwaehnt: set[Kennung] = set()
    for feld in ("beschreibung", "notizen"):
        neu_erwaehnt |= erwaehnte(k, b, getattr(neu, feld)) - erwaehnte(k, b, getattr(alt, feld))
    erwaehnt(k, b, neu, sorted(neu_erwaehnt))


def nach_kommentar(k: Kontext, b: Board, karte: Karte, text: str) -> None:
    """Wer im Kommentar erwähnt ist, und die Zuständigen der Karte (wer erwähnt ist, nur einmal)."""
    genannt = erwaehnte(k, b, text)
    erwaehnt(k, b, karte, sorted(genannt))
    melden(k, b, "kommentar", [x for x in karte.zustaendig if x not in genannt], karte,
           f"{k.konto.name} hat {karte.schluessel} kommentiert")


def verschoben(k: Kontext, b: Board, karte: Karte, ziel: Spalte, mit: Karte | None = None) -> None:
    """An die Zuständigen einer Karte, die in eine andere Spalte kommt; `mit`: die Karte, mit der sie verknüpft mitzieht."""
    wie = f" mit {mit.schluessel}" if mit else ""
    was = "erledigt" if ziel.erledigt else f"nach {ziel.name} verschoben"
    melden(k, b, "verschoben", karte.zustaendig, karte, f"{k.konto.name} hat {karte.schluessel}{wie} {was}")


def faellig_text(karte: Karte, heute: str) -> str:
    tage = tage_zwischen(karte.faellig or heute, heute)
    if tage <= 0:
        return f"{karte.schluessel} ist heute fällig"
    return f"{karte.schluessel} ist {tage} {'Tag' if tage == 1 else 'Tage'} überfällig"


def _eigener(k: Kontext, hinweis_id: Kennung) -> Hinweis:
    d = k.s.lies("hinweise", hinweis_id)
    if d is None or d.get("konto") != k.konto.id:
        raise Abgelehnt("Diesen Hinweis gibt es nicht (mehr)", 404)
    return Hinweis.model_validate(d)


# --- Anwendungsfälle -----------------------------------------------------------------------------------------------

class Hinweise:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def gelesen(self, konto: Konto, hinweis_id: Kennung, gelesen: bool = True) -> Antwort:
        """Ein eigener Hinweis gelesen oder wieder ungelesen: still, ohne Rückweg."""

        def arbeit(k: Kontext) -> str | None:
            h = _eigener(k, hinweis_id)
            if h.gelesen == gelesen:
                return None
            h.gelesen = gelesen
            k.s.schreib("hinweise", h.json_daten())
            return "Hinweis gelesen" if gelesen else "Hinweis ungelesen"

        return await self.a.aendern(konto, arbeit, rueckgaengig=False, melden=False)

    async def alle_gelesen(self, konto: Konto) -> Antwort:
        def arbeit(k: Kontext) -> str | None:
            offen = [Hinweis.model_validate(d) for d in k.s.alle("hinweise", "konto=? AND gelesen=0", (konto.id,))]
            for h in offen:
                h.gelesen = True
                k.s.schreib("hinweise", h.json_daten())
            n = len(offen)
            return f"{n} {'Hinweis' if n == 1 else 'Hinweise'} als gelesen markiert" if n else None

        return await self.a.aendern(konto, arbeit)

    async def weg_setzen(self, konto: Konto, art: HinweisArt, weg: HinweisWeg, an: bool) -> Antwort:
        """Auf welchem Weg welche Hinweise kommen (gilt am Konto, auf allen Geräten)."""
        if weg not in WEGE_DA:
            raise Abgelehnt(f"Den Weg {NAMEN_DER_WEGE[weg]} bietet diese Pinnwand nicht an")
        if art not in ARTEN_DA:
            raise Abgelehnt(f"Hinweise der Art {NAMEN_DER_ARTEN[art]} bietet diese Pinnwand nicht an")
        await self._einstellungen_anlegen(konto)

        def arbeit(k: Kontext) -> str | None:
            d = k.s.lies("person_einstellungen", konto.id) or {"id": konto.id}
            if weg_an(d, art, weg) == an:
                return None
            e = PersonEinstellungen.model_validate(d)
            e.hinweise.setdefault(art, {})[weg] = an
            k.s.schreib("person_einstellungen", {**d, **e.json_daten(), "id": konto.id})
            return "Hinweise gespeichert"

        return await self.a.aendern(konto, arbeit)

    async def _einstellungen_anlegen(self, konto: Konto) -> None:
        """Die Einstellungen der Person als Zeile, angelegt ohne Rückweg: so stellt Rückgängig sie nur zurück und
        entfernt sie nie (die Oberfläche behielte sonst den Stand vor dem Rückgängig)."""

        def arbeit(k: Kontext) -> str | None:
            if k.s.lies("person_einstellungen", konto.id) is not None:
                return None
            k.s.schreib("person_einstellungen", {"id": konto.id, **PersonEinstellungen().json_daten()})
            return "Einstellungen angelegt"

        await self.a.aendern(konto, arbeit, rueckgaengig=False, melden=False)

    async def faellige_melden(self) -> Antwort:
        """Ein Hinweis je offener Karte, die heute fällig oder überfällig ist, an jede Person, die für sie zuständig ist.
        Je Karte und Person gibt es einen solchen Hinweis: ein neuer Tag erneuert ihn (neuer Text, wieder ungelesen),
        am selben Tag bleibt er, wie er ist. So entsteht kein Doppel, auch nicht nach einem Neustart."""

        def arbeit(k: Kontext) -> str | None:
            boards = {d["id"]: Board.model_validate(d) for d in k.s.alle("boards")}
            einstellungen = {d["id"]: d for d in k.s.alle("person_einstellungen")}
            bisher = {(d["konto"], d.get("karte")): d
                      for d in k.s.alle("hinweise", "json_extract(daten, '$.art') = 'faellig'")}
            n = 0
            for d in k.s.alle("karten", "json_extract(daten, '$.faellig') <= ?", (k.heute,), "schluessel"):
                c = Karte.model_validate(d)
                if c.serie:                                   # Serientage stehen in Heute unter Serien
                    continue
                b = boards.get(c.board)
                spalte = spalte_von(b, c.spalte) if b else None
                if b is None or spalte is None or spalte.erledigt:
                    continue
                mitglieder = {m.konto for m in b.mitglieder if m.konto}
                for konto in dict.fromkeys(c.zustaendig):
                    alt = bisher.get((konto, c.id))
                    if konto not in mitglieder or not weg_an(einstellungen.get(konto), "faellig") \
                            or (alt and alt["zeit"][:10] == k.heute):
                        continue
                    h = Hinweis(id=alt["id"] if alt else neue_kennung("h"), konto=konto, art="faellig", zeit=k.jetzt,
                                board=b.id, karte=c.id, schluessel=c.schluessel, text=faellig_text(c, k.heute))
                    k.s.schreib("hinweise", h.json_daten())
                    n += 1
            return f"{n} {'Hinweis' if n == 1 else 'Hinweise'} zu fälligen Karten" if n else None

        return await self.a.aendern(PINNWAND, arbeit, rueckgaengig=False, melden=False)


class Faelligkeit(Begleiter):
    """Meldet die fälligen Karten beim Start und danach bei jedem Tageswechsel (Ortszeit der Uhr). Ein Begleiter im
    Prozess, weil die Pinnwand als ein Prozess läuft und der Hinweis den Tag braucht, nicht die Minute: alle paar Minuten
    vergleicht er nur den Tag, so übersteht er Ruhezustand, Uhrsprünge und Neustarts; ein verpasster Tag wird beim
    nächsten Blick nachgeholt. Doppelte Läufe schaden nicht, weil `faellige_melden` je Tag nur einmal schreibt."""

    def __init__(self, hinweise: Hinweise, takt_s: float = TAKT_S) -> None:
        self.hinweise = hinweise
        self.takt_s = takt_s
        self._zuletzt: str | None = None
        self._aufgabe: asyncio.Task[None] | None = None

    async def starten(self) -> None:
        self._aufgabe = asyncio.create_task(self._laufen(), name="pinnwand-faellig")

    async def stoppen(self) -> None:
        if self._aufgabe:
            self._aufgabe.cancel()
            await asyncio.gather(self._aufgabe, return_exceptions=True)
            self._aufgabe = None

    async def pruefen(self) -> bool:
        """Meldet die fälligen Karten, wenn seit dem letzten Mal ein neuer Tag begonnen hat. True: gemeldet."""
        heute = self.hinweise.a.uhr.heute()
        if heute == self._zuletzt:
            return False
        await self.hinweise.faellige_melden()
        self._zuletzt = heute
        return True

    async def _laufen(self) -> None:
        while True:
            try:
                await self.pruefen()
            except Exception:  # noqa: BLE001 - der nächste Blick versucht es wieder
                logger.exception("Fällige Karten melden")
            await asyncio.sleep(self.takt_s)
