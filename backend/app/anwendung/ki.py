"""KI an der Karte (Modul ki): Vorschläge über ein Sprachmodell. Die KI schlägt nur vor, geschrieben wird hier nichts;
übernommen wird nur, was die Person in der Vorschau bestätigt, über die gewohnten Anwendungsfälle mit Rückgängig.

Vier Vorschläge: eine Zusammenfassung der Karte (jedes Mitglied), neue Punkte für die Checkliste und Labels des Boards
(mit "Karten bearbeiten"), Karten aus einem Text (mit "Karten anlegen"); dazu mit dem Modul Transkripte eine Notiz zu
einer verknüpften Stelle aus den Abschnitten um sie herum. Jede Anfrage verlangt eine feste Antwortform,
die Begründung steht vor den Listen; Labels wählt das Modell über Kennungen der Anfrage (L1, L2, ...), die der Server
auf die echten abbildet. Alles vom Modell Geschriebene geht durch die Säuberung des Appkerns (nur gerade Zeichen); Punkte
und Titel werden gekürzt, Doppeltes und Vorhandenes fällt weg. Gerechnet wird hinter dem Anschluss `Sprachmodell`."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from appkern.leitstelle import gerade

from ..modell import Board, Karte, Kennung, Konto, Modell
from ..regeln.board import hat_recht, mitglied, modul_an, spalte_von
from ..regeln.tage import datum_text
from .karten import Kartenentwurf
from .kartenbasis import FELD_LAENGE, KURZ_LAENGE, TITEL_LAENGE
from .rahmen import NAMEN_DER_RECHTE, Abgelehnt, Anwendung
from .transkripte import KeineTranskription, Transkription, board_pruefen, marke_von, stelle_text

#: so viel Text je Feld der Karte geht höchstens an das Modell (Zeichen); die jüngsten Kommentare zuerst
FELD_HOECHSTENS = 12_000
KOMMENTARE_HOECHSTENS = 30
#: so lang darf ein Text sein, aus dem Karten werden
AUS_TEXT_HOECHSTENS = 20_000
#: so viel schlägt die KI höchstens vor
PUNKTE_VORSCHLAG = 10
KARTEN_VORSCHLAG = 20
ZUSAMMENFASSUNG_HOECHSTENS = 4_000
#: so viel Gespräch um eine Stelle liest das Modell für ihre Notiz (Sekunden davor und danach; ohne Stelle der Anfang)
STELLE_DAVOR, STELLE_DANACH, ANFANG = 30, 90, 600
#: Aufzählungszeichen, Nummern und Kästchen vor einem Punkt, wie Modelle sie gern mitliefern
_VORSATZ = re.compile(r"^\s*(?:[-*•]+|\d+[.)]|\[[ xX]?\])\s*")
_LEERRAUM = re.compile(r"\s+")
_WORT = re.compile(r"\w+")

GERADE = "Schreibe auf Deutsch mit echten Umlauten (ä, ö, ü, ß) und nur geraden Anführungszeichen und einfachen Bindestrichen."


@dataclass(frozen=True)
class Auftrag:
    """Eine Frage an das Sprachmodell: `anweisung` (Rolle system), `text` (Rolle user), die verlangte Antwortform als
    JSON-Schema und eine Obergrenze der Länge (Tokens). `titel` erscheint in der Leitstelle."""

    name: str
    titel: str
    anweisung: str
    text: str
    schema: dict[str, Any]
    laenge: int


class Sprachmodell(Protocol):
    def bereit(self) -> bool:
        """Ist ein Modell erreichbar eingerichtet? Sonst zeigt die Oberfläche keine Vorschläge."""
        ...

    async def fragen(self, auftrag: Auftrag) -> dict[str, Any]:
        """Die Antwort in der verlangten Form; abgelehnt mit Grund, wenn das Modell nicht kann (503) oder seine Antwort
        nicht lesbar ist (502)."""
        ...


class KeinModell:
    """Ohne Anschluss (etwa in Tests ohne Leitstelle): nichts bereit, jede Frage abgelehnt."""

    def bereit(self) -> bool:
        return False

    async def fragen(self, auftrag: Auftrag) -> dict[str, Any]:
        raise Abgelehnt("Die Leitstelle ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)


class Zusammenfassung(Modell):
    text: str


class Punktvorschlag(Modell):
    punkte: list[str]


class Labelvorschlag(Modell):
    labels: list[Kennung]


class Kartenvorschlag(Modell):
    karten: list[Kartenentwurf]


# --- Was das Modell liest -----------------------------------------------------------------------------------------

def gekuerzt(text: str, hoechstens: int = FELD_HOECHSTENS) -> str:
    return text if len(text) <= hoechstens else text[:hoechstens] + " [gekürzt]"


def kartentext(c: Karte, b: Board, namen: dict[Kennung, str]) -> str:
    """Die Karte als Text für das Modell: Angaben, Beschreibung, Notizen, Checkliste und die jüngsten Kommentare."""
    spalte = spalte_von(b, c.spalte)
    teile = [f"Board: {b.name}", f"Karte {c.schluessel}: {c.titel}"]
    if spalte:
        teile.append(f"Status: {spalte.name}")
    if c.faellig:
        teile.append(f"Fällig: {datum_text(c.faellig)}")
    if c.blockiert:
        teile.append(f"Blockiert: {c.blockiert}")
    if c.beschreibung:
        teile.append("Beschreibung:\n" + gekuerzt(c.beschreibung))
    if c.notizen:
        teile.append("Notizen:\n" + gekuerzt(c.notizen))
    if c.checkliste:
        teile.append("Checkliste:\n" + "\n".join(f"- [{'x' if p.erledigt else ' '}] {p.text}" for p in c.checkliste))
    if c.kommentare:
        juengste = c.kommentare[-KOMMENTARE_HOECHSTENS:]
        teile.append("Kommentare:\n" + "\n".join(
            f"- {namen.get(m.von, 'Jemand')} am {datum_text(m.zeit[:10])}: {gekuerzt(m.text, 2_000)}" for m in juengste))
    return "\n\n".join(teile)


# --- Was vom Modell kommt -----------------------------------------------------------------------------------------

def zeile(text: Any, hoechstens: int) -> str:
    """Ein Punkt oder Titel vom Modell: gerade Zeichen, ohne Aufzählungszeichen davor, Leerraum zusammengezogen, gekürzt."""
    if not isinstance(text, str):
        return ""
    t = _LEERRAUM.sub(" ", _VORSATZ.sub("", gerade(text))).strip()
    return t[:hoechstens].rstrip()


def woerter(text: str) -> set[str]:
    """Die tragenden Wörter eines Punkts (ab drei Buchstaben, Groß- und Kleinschreibung egal)."""
    return {w for w in _WORT.findall(text.casefold()) if len(w) >= 3}


def gleich(a: str, b: str) -> bool:
    """Sagen zwei Punkte dasselbe? Gleich geschrieben, oder einer enthält alle tragenden Wörter des anderen (mindestens
    zwei), etwa "Beton beim Baustoffhandel bestellen" und "Beton bestellen". Modelle wiederholen Vorhandenes gern mit
    mehr Worten, auch wenn die Anweisung es verbietet."""
    if a.casefold() == b.casefold():
        return True
    wa, wb = woerter(a), woerter(b)
    kurz, lang = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return len(kurz) >= 2 and kurz <= lang


def neue_punkte(roh: Any, vorhanden: list[str], hoechstens: int) -> list[str]:
    """Punkte vom Modell ohne Leeres und ohne, was dasselbe sagt wie ein vorhandener oder ein früherer Punkt."""
    gesehen = list(vorhanden)
    punkte: list[str] = []
    for r in roh if isinstance(roh, list) else []:
        t = zeile(r, KURZ_LAENGE)
        if t and not any(gleich(t, g) for g in gesehen):
            gesehen.append(t)
            punkte.append(t)
    return punkte[:hoechstens]


def _objekt(eigenschaften: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": eigenschaften, "required": list(eigenschaften), "additionalProperties": False}


TEXTE = {"type": "array", "items": {"type": "string"}}


class Ki:
    def __init__(self, anwendung: Anwendung, modell: Sprachmodell, transkription: Transkription | None = None) -> None:
        self.a = anwendung
        self.modell = modell
        self.transkription = transkription or KeineTranskription()

    def bereit(self) -> bool:
        return self.modell.bereit()

    async def _board(self, konto: Konto, board_id: Kennung, recht: str | None) -> Board:
        d = await self.a.v.lies("boards", board_id)
        if d is None:
            raise Abgelehnt("Dieses Board gibt es nicht (mehr)", 404)
        b = Board.model_validate(d)
        if mitglied(b, konto.id) is None:
            raise Abgelehnt(f"Im Board {b.name} bist du nicht Mitglied", 403)
        if not modul_an(b, "ki"):
            raise Abgelehnt(f"KI an der Karte ist im Board {b.name} aus", 403)
        if recht and not hat_recht(b, recht, konto.id):
            raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE[recht]}", 403)
        return b

    async def _karte(self, konto: Konto, karte_id: Kennung, recht: str | None) -> tuple[Board, Karte, str]:
        """Board, Karte und die Karte als Text, wenn die Person sie mit diesem Recht sehen darf."""
        d = await self.a.v.lies("karten", karte_id)
        if d is None:
            raise Abgelehnt("Diese Karte gibt es nicht (mehr)", 404)
        c = Karte.model_validate(d)
        b = await self._board(konto, c.board, recht)
        namen = {k["id"]: k["name"] for k in await self.a.v.alle("konten")} | {"pinnwand": "Pinnwand"}
        return b, c, kartentext(c, b, namen)

    async def zusammenfassen(self, konto: Konto, karte_id: Kennung) -> Zusammenfassung:
        _, c, text = await self._karte(konto, karte_id, None)
        antwort = await self.modell.fragen(Auftrag(
            name="zusammenfassung", titel=f"Zusammenfassung {c.schluessel}", laenge=2_000, text=text,
            anweisung="Du fasst eine Karte eines Boards für die Menschen zusammen, die an ihr arbeiten. Schreibe zwei bis "
                      "vier Sätze: worum es geht, was schon geschehen ist und was offen ist, mit den Namen, Tagen und "
                      "Zahlen aus der Karte. Nur, was in der Karte steht; nichts erfinden, nichts vermuten. Keine "
                      "Überschrift, keine Aufzählung, kein Markdown. " + GERADE,
            schema=_objekt({"text": {"type": "string"}})))
        zusammenfassung = gerade(str(antwort.get("text") or "")).strip()[:ZUSAMMENFASSUNG_HOECHSTENS]
        if not zusammenfassung:
            raise Abgelehnt("Das Modell hat keine Zusammenfassung geliefert; noch einmal versuchen", 502)
        return Zusammenfassung(text=zusammenfassung)

    async def checkliste(self, konto: Konto, karte_id: Kennung) -> Punktvorschlag:
        _, c, text = await self._karte(konto, karte_id, "karten.bearbeiten")
        antwort = await self.modell.fragen(Auftrag(
            name="checkliste", titel=f"Checkliste {c.schluessel}", laenge=2_000, text=text,
            anweisung="Du schlägst für eine Karte eines Boards die nächsten Schritte als Checkliste vor. Erst eine kurze "
                      "Begründung (ein Satz), dann die Punkte: drei bis acht kurze, konkrete Schritte in sinnvoller "
                      "Reihenfolge, je höchstens 80 Zeichen, etwa \"Angebot an Brandt schicken\". Was die Checkliste "
                      "schon hat, erledigt oder offen, auch nicht mit anderen Worten wiederholen. Nur Schritte, die sich "
                      "aus der Karte ergeben, ohne Werkzeug, Material oder Personen, die sie nicht nennt. " + GERADE,
            schema=_objekt({"begruendung": {"type": "string"}, "punkte": {**TEXTE, "minItems": 1, "maxItems": PUNKTE_VORSCHLAG}})))
        return Punktvorschlag(punkte=neue_punkte(antwort.get("punkte"), [p.text for p in c.checkliste], PUNKTE_VORSCHLAG))

    async def labels(self, konto: Konto, karte_id: Kennung) -> Labelvorschlag:
        b, c, text = await self._karte(konto, karte_id, "karten.bearbeiten")
        frei = [lab for lab in b.labels if lab.id not in c.labels]
        if not frei:
            return Labelvorschlag(labels=[])
        kennungen = {f"L{i}": lab for i, lab in enumerate(frei, 1)}
        liste = "\n".join(f"{k}: {lab.name}" for k, lab in kennungen.items())
        antwort = await self.modell.fragen(Auftrag(
            name="labels", titel=f"Labels {c.schluessel}", laenge=1_000, text=f"{text}\n\nLabels zur Wahl:\n{liste}",
            anweisung="Du wählst für eine Karte eines Boards passende Labels aus einer festen Liste. Erst eine kurze "
                      "Begründung (ein Satz), dann die Kennungen der Labels aus der Liste, etwa \"L2\". Wähle nur, was "
                      "der Inhalt der Karte klar trägt; lieber keins als ein falsches. " + GERADE,
            schema=_objekt({"begruendung": {"type": "string"},
                            "labels": {"type": "array", "items": {"type": "string", "enum": list(kennungen)}}})))
        nach_name = {lab.name.casefold(): lab for lab in frei}
        gewaehlt: list[Kennung] = []
        for roh in antwort.get("labels") or []:
            if not isinstance(roh, str):
                continue
            kennung = roh.split(":")[0].strip().upper()
            lab = kennungen.get(kennung) or nach_name.get(roh.strip().casefold())
            if lab and lab.id not in gewaehlt:
                gewaehlt.append(lab.id)
        return Labelvorschlag(labels=gewaehlt)

    async def karten_aus_text(self, konto: Konto, board_id: Kennung, text: str) -> Kartenvorschlag:
        b = await self._board(konto, board_id, "karten.anlegen")
        text = text.strip()
        if not text:
            raise Abgelehnt("Aus einem leeren Text werden keine Karten")
        if len(text) > AUS_TEXT_HOECHSTENS:
            raise Abgelehnt(f"Der Text ist länger als {AUS_TEXT_HOECHSTENS} Zeichen")
        antwort = await self.modell.fragen(Auftrag(
            name="karten", titel=f"Karten aus Text für {b.kuerzel}", laenge=6_000, text=f"Board: {b.name}\n\nText:\n{text}",
            anweisung="Du machst aus einem Text (Notiz, Nachricht, Protokoll, Liste) Karten für ein Board. Jede Karte ist "
                      "eine eigene Aufgabe oder Idee aus dem Text. Titel kurz und konkret, höchstens 80 Zeichen, ohne "
                      "Nummer davor. Beschreibung nur, wenn der Text dazu mehr sagt (ein bis drei Sätze), sonst leer. "
                      "Checkliste nur, wenn der Text Teilschritte nennt, sonst leer. Nur aufnehmen, was der Text nennt; "
                      f"nichts erfinden. Höchstens {KARTEN_VORSCHLAG} Karten. " + GERADE,
            schema=_objekt({"karten": {"type": "array", "maxItems": KARTEN_VORSCHLAG, "items": _objekt({
                "titel": {"type": "string"}, "beschreibung": {"type": "string"}, "checkliste": TEXTE})}})))
        karten: list[Kartenentwurf] = []
        gesehen: set[str] = set()
        for roh in antwort.get("karten") or []:
            if not isinstance(roh, dict):
                continue
            titel = zeile(roh.get("titel"), TITEL_LAENGE)
            if not titel or titel.casefold() in gesehen:
                continue
            gesehen.add(titel.casefold())
            beschreibung = gerade(roh["beschreibung"]).strip() if isinstance(roh.get("beschreibung"), str) else ""
            karten.append(Kartenentwurf(titel=titel, beschreibung=gekuerzt(beschreibung) or None,
                                        checkliste=neue_punkte(roh.get("checkliste"), [], PUNKTE_VORSCHLAG)))
        return Kartenvorschlag(karten=karten[:KARTEN_VORSCHLAG])

    async def notiz_vorschlagen(self, konto: Konto, karte_id: Kennung, marke_id: Kennung, sitzung: str) -> Zusammenfassung:
        """Eine Notiz zu einer verknüpften Stelle aus den Abschnitten um sie herum (das Transkript liest die Pinnwand im
        Auftrag der Person)."""
        b, c, _ = await self._karte(konto, karte_id, "karten.bearbeiten")
        board_pruefen(b, konto, None)
        m = marke_von(c, marke_id)
        t = await self.transkription.lesen(sitzung, m.transkript)
        von, bis = (m.sekunde - STELLE_DAVOR, m.sekunde + STELLE_DANACH) if m.sekunde is not None else (0, ANFANG)
        teile = [a for a in t.abschnitte if a.ende >= von and a.start <= bis]
        if not teile:
            raise Abgelehnt("An dieser Stelle steht im Transkript kein Text", 422)
        gespraech = "\n".join(f"[{stelle_text(a.start)}] {a.sprecher or 'Jemand'}: {a.text}" for a in teile)
        antwort = await self.modell.fragen(Auftrag(
            name="notiz", titel=f"Notiz zu einer Stelle an {c.schluessel}", laenge=1_000,
            text=f"Karte {c.schluessel}: {c.titel}\nTranskript: {t.name}\nMarkierte Stelle: {stelle_text(m.sekunde)}\n\n"
                 f"Gespräch:\n{gekuerzt(gespraech)}",
            anweisung="Du schreibst eine kurze Notiz zu einer Stelle aus einem Gespräch, die an einer Karte eines Boards "
                      "hängt. Ein bis zwei Sätze: was an der markierten Stelle gesagt oder entschieden wird, mit Namen, "
                      "Tagen und Zahlen aus dem Gespräch, soweit es die Karte betrifft. Nur, was im Gespräch steht; "
                      "nichts erfinden. Kein Markdown. " + GERADE,
            schema=_objekt({"text": {"type": "string"}})))
        notiz = gerade(str(antwort.get("text") or "")).strip()[:FELD_LAENGE]
        if not notiz:
            raise Abgelehnt("Das Modell hat keine Notiz geliefert; noch einmal versuchen", 502)
        return Zusammenfassung(text=notiz)
