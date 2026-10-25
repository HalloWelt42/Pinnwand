"""Anwendungsfälle an Anhängen einer Karte (E-15, Mechanik M-63): hochladen legt die Dateien in der Kellerwolke ab, in
der Ablage der Pinnwand mit einem Ordner je Board; aus der eigenen Kellerwolke wird nur verknüpft, die Datei bleibt, wo
sie ist, und der Anhang trägt ihre Kennung. Entfernen nimmt den Anhang von der Karte, mit Rückgängig. Jede Änderung steht
im Verlauf der Karte. Grenze 25 MB je Datei, leere Dateien werden abgelehnt. Ändern nur mit dem Recht, Karten zu
bearbeiten; öffnen darf jedes Mitglied des Boards.

Reihenfolge beim Hochladen: prüfen (Karte, Recht, Namen, Größen), alle Dateien ablegen, dann in einer Änderung festhalten
(ein Rückgängig für alle). Scheitert das Ablegen einer Datei oder das Festhalten, kommen die schon abgelegten Dateien in
den Papierkorb der Kellerwolke; geht auch das nicht, steht es im Protokoll der App. Keine Datei bleibt stillschweigend
ohne Anhang liegen.

Geht ein Anhang von der Karte (Entfernen, Rückgängig nach dem Hochladen, Papierkorb der Pinnwand), bleibt die Datei in der
Kellerwolke. Entfernen und Papierkorb lassen sich zurücknehmen, der Anhang zeigt dann wieder auf dieselbe Datei. Rückgängig
stellt nur Zeilen der Pinnwand in einer Transaktion her; ein Löschen in der Kellerwolke daneben ließe sich weder mit ihr
zurücknehmen noch sicher mit ihr zusammen ausführen. Die Datei liegt danach sichtbar im Ordner des Boards, wo sie sich in
der Kellerwolke ansehen und löschen lässt."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Collection
from pathlib import Path
from typing import Literal, Protocol

from ..modell import Anhang, AnhangArt, Board, Karte, Kennung, Konto, Modell
from ..regeln.board import mitglied
from .kartenbasis import karte_lesen, speichern, vermerken
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext

#: höchstens so groß darf eine Datei sein (wie in der alten App)
GRENZE_MB = 25
GRENZE = GRENZE_MB * 1024 * 1024
#: so viele Dateien gehen auf einmal, so viele hängen höchstens an einer Karte
AUF_EINMAL = 20
JE_KARTE = 200
#: längster Name einer Datei (wie in der Kellerwolke)
NAME_LAENGE = 255
#: Steuerzeichen und Zeichen, die einen Weg teilen, werden in Namen zu "-"
UNERLAUBT = re.compile(r"[\\/\x00-\x1f\x7f]")
INHALTSTYP = re.compile(r"^[\w.+-]+/[\w.+-]+$")
#: Endungen je Art (für das Symbol), wie in der alten App
ENDUNGEN = {"bild": {"png", "jpg", "jpeg", "gif", "webp", "svg", "heic"}, "ton": {"mp3", "wav", "ogg", "m4a", "flac"},
            "tabelle": {"ods", "xlsx", "xls", "csv"}}


class Eingang(Modell):
    """Eine Datei, die zum Hochladen hereinkommt: Name, Größe und Typ, wie gesendet; der Inhalt liegt vorläufig unter
    `inhalt`, sobald er angenommen ist."""

    name: str
    groesse: int
    inhaltstyp: str | None = None
    inhalt: Path | None = None


class Datei(Modell):
    """Eine Datei oder ein Ordner der Kellerwolke, wie die Ablage sie meldet."""

    kennung: str
    name: str
    #: Weg vom Konto aus, mit dem Namen ("Apps/Pinnwand/Haushalt/Skizze.png")
    pfad: str
    ordner: bool = False
    groesse: int = 0
    inhaltstyp: str | None = None


class Glied(Modell):
    """Ein Ordner auf dem Weg vom Konto bis zum gezeigten; ohne Kennung: Meine Dateien."""

    id: str | None = None
    name: str


class Ordnerinhalt(Modell):
    kette: list[Glied]
    eintraege: list[Datei]


class KellerwolkeDatei(Modell):
    """Ein Eintrag deiner Kellerwolke in der Dateiwahl, gleich frontend/src/modell.ts."""

    id: str
    typ: Literal["ordner", "datei"]
    name: str
    #: Ordner, in dem er liegt (ohne: Meine Dateien), und dessen Weg vom Konto aus ("Dokumente/Angebote")
    ordner: str | None = None
    pfad: str = ""
    groesse: str = ""
    art: AnhangArt = "text"


class KellerwolkeOrdner(Modell):
    id: str | None = None
    kette: list[Glied]
    eintraege: list[KellerwolkeDatei]


class Gewaehlt(Modell):
    """Eine in der Dateiwahl gewählte Datei und der Ordner, in dem die Person sie gesehen hat."""

    ordner: str | None = None
    datei: str


class Ablage(Protocol):
    """Wo die Dateien der Anhänge liegen: die Kellerwolke. Fehler kommen als `Abgelehnt` mit Grund (503: gerade nicht
    erreichbar)."""

    async def ablegen(self, ordner: str, name: str, inhalt: Path, inhaltstyp: str | None) -> Datei:
        """In den Ordner `ordner` der Ablage der Pinnwand (er entsteht, wenn er fehlt); ein dort belegter Name bekommt
        einen Zähler wie an der Karte ("Skizze (2).png")."""
        ...

    async def verwerfen(self, datei: Datei, grund: str) -> None:
        """Eine abgelegte Datei, die kein Anhang wurde, in den Papierkorb der Kellerwolke; geht das nicht, steht sie mit
        dem Grund im Protokoll der App. Scheitert nie."""
        ...

    async def ordnerinhalt(self, sitzung: str, ordner: str | None) -> Ordnerinhalt:
        """Was die Person mit ihrer Anmeldung `sitzung` in einem Ordner ihrer Kellerwolke sieht (ohne: Meine Dateien)."""
        ...


# --- Regeln -----------------------------------------------------------------------------------------------------

def dateiname(name: str) -> str:
    """Name, unter dem eine Datei abgelegt wird: ohne Zeichen, die einen Weg teilen, ohne Leerraum am Rand."""
    n = UNERLAUBT.sub("-", name).strip()
    if not n or n in (".", ".."):
        raise Abgelehnt("Eine Datei braucht einen Namen")
    if len(n) > NAME_LAENGE:
        raise Abgelehnt(f"Ein Dateiname hat höchstens {NAME_LAENGE} Zeichen")
    return n


def ablage_ordner(b: Board) -> str:
    """Ordner des Boards in der Ablage der Pinnwand: sein Name. Nach dem Umbenennen kommen neue Dateien in einen Ordner
    mit dem neuen Namen; die alten bleiben, wo sie sind, ihre Anhänge finden sie über die Kennung."""
    return UNERLAUBT.sub("-", b.name).strip().strip(".") or b.kuerzel


def freier_name(belegt: Collection[str], name: str) -> str:
    """Gleicher Name: wie in der Kellerwolke mit Zähler, "Skizze (2).png"."""
    if name not in belegt:
        return name
    punkt = name.rfind(".")
    stamm, endung = (name[:punkt], name[punkt:]) if punkt > 0 else (name, "")
    n = 2
    while f"{stamm} ({n}){endung}" in belegt:
        n += 1
    return f"{stamm} ({n}){endung}"


def groesse_text(n: int) -> str:
    """Größe wie in der alten App: B, KB, MB."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{int(n / 1024 + 0.5)} KB"
    return f"{n / 1024 / 1024:.1f} MB".replace(".", ",")


def art_von(name: str, typ: str | None) -> AnhangArt:
    """Art der Datei nach Typ und Endung, für das Symbol."""
    endung = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    t = typ or ""
    if t.startswith("image/") or endung in ENDUNGEN["bild"]:
        return "bild"
    if t == "application/pdf" or endung == "pdf":
        return "pdf"
    if t.startswith("audio/") or endung in ENDUNGEN["ton"]:
        return "ton"
    return "tabelle" if endung in ENDUNGEN["tabelle"] else "text"


def ort_zum_lesen(pfad: str) -> str:
    """Ordner einer Datei zum Lesen, ohne den Zweig der Apps und ohne den Namen ("Pinnwand/Haushalt"); gleich ablageOrt
    in frontend/src/daten/anwendung/anhaenge.svelte.ts."""
    teile = pfad.split("/")[:-1]
    return "/".join(teile[1:] if teile[:1] == ["Apps"] else teile)


def anzahl(n: int) -> str:
    return "1 Datei" if n == 1 else f"{n} Dateien"


def eingaenge_pruefen(eingaenge: list[Eingang]) -> list[Eingang]:
    """Anzahl, Namen, Größen und Typen; Ergebnis: die Eingänge mit dem Namen, unter dem sie abgelegt werden."""
    if not eingaenge:
        raise Abgelehnt("Keine Datei gewählt")
    if len(eingaenge) > AUF_EINMAL:
        raise Abgelehnt(f"Höchstens {AUF_EINMAL} Dateien auf einmal")
    geprueft: list[Eingang] = []
    for e in eingaenge:
        name = dateiname(e.name)
        if e.groesse <= 0:
            raise Abgelehnt(f"Nicht angehängt: {name} ist leer")
        if e.groesse > GRENZE:
            raise Abgelehnt(f"Nicht angehängt: {name} ist größer als {GRENZE_MB} MB")
        typ = (e.inhaltstyp or "").split(";")[0].strip().lower()
        geprueft.append(e.model_copy(update={"name": name, "inhaltstyp": typ if INHALTSTYP.match(typ) else None}))
    return geprueft


def angenommen(e: Eingang) -> Path:
    """Der vorläufig angenommene Inhalt, vollständig wie angegeben."""
    if e.inhalt is None or e.inhalt.stat().st_size != e.groesse:
        raise Abgelehnt("Die Dateien kamen nicht vollständig an")
    return e.inhalt


def platz_pruefen(c: Karte, neu: int) -> None:
    if len(c.anhaenge) + neu > JE_KARTE:
        raise Abgelehnt(f"Eine Karte hat höchstens {JE_KARTE} Anhänge")


def anhaengen(k: Kontext, c: Karte, d: Datei, name: str, verknuepft: bool) -> str:
    """Hängt die Datei an, unter `name` oder, wenn er an dieser Karte belegt ist, mit Zähler; Ergebnis: der Name an der
    Karte. In der Kellerwolke kann die Datei anders heißen (dort zählt der Ordner des Boards)."""
    name = freier_name({a.name for a in c.anhaenge}, name)
    c.anhaenge.append(Anhang(name=name, groesse=groesse_text(d.groesse), art=art_von(d.name, d.inhaltstyp),
                             verknuepft=verknuepft or None, datei=d.kennung, pfad=d.pfad, von=k.konto.id))
    return name


# --- Anwendungsfälle --------------------------------------------------------------------------------------------

class Anhaenge:
    def __init__(self, anwendung: Anwendung, ablage: Ablage) -> None:
        self.a = anwendung
        self.ablage = ablage

    async def _zum_bearbeiten(self, konto: Konto, karte_id: Kennung) -> Board:
        """Vor der Arbeit mit der Kellerwolke: gibt es die Karte, und darf die Person sie bearbeiten? Dieselbe Prüfung im
        selben Rahmen wie beim Festhalten; geschrieben wird nichts. Ergebnis: das Board der Karte."""
        board: list[Board] = []

        def pruefen(k: Kontext) -> None:
            board.append(k.board_mit_recht(karte_lesen(k, karte_id).board, "karten.bearbeiten"))

        await self.a.aendern(konto, pruefen)
        return board[0]

    async def pruefen(self, konto: Konto, karte_id: Kennung, eingaenge: list[Eingang]) -> list[Eingang]:
        """Bevor die Inhalte angenommen werden: Karte, Recht, Anzahl, Namen und Größen."""
        await self._zum_bearbeiten(konto, karte_id)
        return eingaenge_pruefen(eingaenge)

    async def hochladen(self, konto: Konto, karte_id: Kennung, eingaenge: list[Eingang]) -> Antwort:
        """Die angenommenen Dateien in den Ordner des Boards legen und in einer Änderung an die Karte hängen."""
        eingaenge = eingaenge_pruefen(eingaenge)
        inhalte = [angenommen(e) for e in eingaenge]
        ordner = ablage_ordner(await self._zum_bearbeiten(konto, karte_id))
        abgelegt: list[Datei] = []

        def festhalten(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            k.board_mit_recht(c.board, "karten.bearbeiten")
            platz_pruefen(c, len(abgelegt))
            namen = [anhaengen(k, c, d, e.name, verknuepft=False) for e, d in zip(eingaenge, abgelegt)]
            for name in namen:
                vermerken(k, c, f"hat den Anhang {name} hochgeladen")
            speichern(k, c)
            was = namen[0] if len(namen) == 1 else anzahl(len(namen))
            return f"{was} an {c.schluessel} angehängt, abgelegt in der Kellerwolke unter {ort_zum_lesen(abgelegt[0].pfad)}"

        try:
            for e, inhalt in zip(eingaenge, inhalte):
                try:
                    abgelegt.append(await self.ablage.ablegen(ordner, e.name, inhalt, e.inhaltstyp))
                except Abgelehnt as f:
                    raise Abgelehnt(f"Nicht angehängt: {f.meldung}", f.status) from f
            return await self.a.aendern(konto, festhalten)
        except BaseException as f:
            grund = f.meldung if isinstance(f, Abgelehnt) else "das Anhängen an die Karte ist gescheitert"
            if abgelegt:                                     # auch wenn die Anfrage abbricht: das Aufräumen läuft zu Ende
                await asyncio.shield(self._verwerfen(abgelegt, grund))
            raise

    async def _verwerfen(self, dateien: list[Datei], grund: str) -> None:
        for d in dateien:
            await self.ablage.verwerfen(d, grund)

    async def aus_kellerwolke(self, konto: Konto, karte_id: Kennung, sitzung: str, gewaehlt: list[Gewaehlt]) -> Antwort:
        """In der Dateiwahl gewählte Dateien verknüpfen. Name und Größe fragt die Pinnwand mit der Anmeldung der Person bei
        der Kellerwolke nach (nur was sie dort sieht, lässt sich verknüpfen); schon verknüpfte kommen nicht doppelt."""
        gewaehlt = list({g.datei: g for g in gewaehlt}.values())
        if not gewaehlt:
            raise Abgelehnt("Keine Datei gewählt")
        if len(gewaehlt) > AUF_EINMAL:
            raise Abgelehnt(f"Höchstens {AUF_EINMAL} Dateien auf einmal")
        await self._zum_bearbeiten(konto, karte_id)
        dateien = await self._gewaehlte(sitzung, gewaehlt)

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            k.board_mit_recht(c.board, "karten.bearbeiten")
            da = {a.datei for a in c.anhaenge if a.datei}
            neu = [d for d in dateien if d.kennung not in da]
            if not neu:
                return None
            platz_pruefen(c, len(neu))
            for d in neu:
                vermerken(k, c, f"hat {anhaengen(k, c, d, d.name, verknuepft=True)} aus der Kellerwolke verknüpft")
            speichern(k, c)
            was = neu[0].name if len(neu) == 1 else anzahl(len(neu))
            bleibt = "die Datei bleibt" if len(neu) == 1 else "die Dateien bleiben"
            return f"{was} an {c.schluessel} verknüpft; {bleibt} in deiner Kellerwolke"

        return await self.a.aendern(konto, arbeit)

    async def _gewaehlte(self, sitzung: str, gewaehlt: list[Gewaehlt]) -> list[Datei]:
        """Die gewählten Dateien, wie die Kellerwolke sie der Person in ihrem Ordner zeigt (je Ordner eine Frage)."""
        inhalte: dict[str | None, Ordnerinhalt] = {}
        for g in gewaehlt:
            if g.ordner not in inhalte:
                inhalte[g.ordner] = await self.ablage.ordnerinhalt(sitzung, g.ordner)
        dateien: list[Datei] = []
        for g in gewaehlt:
            d = next((e for e in inhalte[g.ordner].eintraege if e.kennung == g.datei and not e.ordner), None)
            if d is None:
                raise Abgelehnt("Diese Datei gibt es in deiner Kellerwolke nicht (mehr)", 404)
            dateien.append(d)
        return dateien

    async def entfernen(self, konto: Konto, karte_id: Kennung, name: str) -> Antwort:
        """Nimmt den Anhang von der Karte, mit Rückgängig; die Datei bleibt in der Kellerwolke."""

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            k.board_mit_recht(c.board, "karten.bearbeiten")
            a = next((x for x in c.anhaenge if x.name == name), None)
            if a is None:
                raise Abgelehnt(f"Den Anhang {name} gibt es an {c.schluessel} nicht (mehr)", 404)
            c.anhaenge = [x for x in c.anhaenge if x.name != name]
            vermerken(k, c, f"hat den Anhang {name} entfernt")
            speichern(k, c)
            if not a.verknuepft:
                return f"{name} von {c.schluessel} entfernt"
            besitzer = k.s.lies("konten", a.von) if a.von and a.von != k.konto.id else None
            wo = f"der Kellerwolke von {besitzer['name']}" if besitzer else "deiner Kellerwolke"
            return f"Verknüpfung zu {name} gelöst; die Datei bleibt in {wo}"

        return await self.a.aendern(konto, arbeit)

    async def kellerwolke(self, sitzung: str, ordner: str | None) -> KellerwolkeOrdner:
        """Ein Ordner deiner Kellerwolke für die Dateiwahl (ohne: Meine Dateien), in der Ordnung der Kellerwolke."""
        inhalt = await self.ablage.ordnerinhalt(sitzung, ordner)
        weg = "/".join(g.name for g in inhalt.kette[1:])
        return KellerwolkeOrdner(id=ordner, kette=inhalt.kette, eintraege=[
            KellerwolkeDatei(id=e.kennung, typ="ordner" if e.ordner else "datei", name=e.name, ordner=ordner, pfad=weg,
                             groesse="" if e.ordner else groesse_text(e.groesse), art=art_von(e.name, e.inhaltstyp))
            for e in inhalt.eintraege])

    async def oeffnen(self, konto: Konto, karte_id: Kennung, datei: str) -> Anhang:
        """Der Anhang zum Öffnen; sehen darf ihn jedes Mitglied des Boards."""
        d = await self.a.v.lies("karten", karte_id)
        if d is None:
            raise Abgelehnt("Diese Karte gibt es nicht (mehr)", 404)
        c = Karte.model_validate(d)
        b = await self.a.v.lies("boards", c.board)
        if b is None or mitglied(Board.model_validate(b), konto.id) is None:
            raise Abgelehnt(f"Die Karte {c.schluessel} liegt in einem Board, in dem du nicht Mitglied bist", 403)
        a = next((x for x in c.anhaenge if x.datei == datei), None)
        if a is None:
            raise Abgelehnt(f"Diesen Anhang gibt es an {c.schluessel} nicht (mehr)", 404)
        return a
