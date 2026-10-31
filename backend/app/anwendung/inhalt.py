"""Anwendungsfälle am Inhalt von Karten: Felder bearbeiten, Art umschalten, kommentieren, Sammelaktionen (zuweisen,
Label, Priorität). Der Server prüft jeden Wert gegen das Board (Mitglieder, Labels, eigene Felder) und schreibt die
Verlaufszeilen selbst. Einen Hinweis bekommt, wer neu zuständig ist, wer mit @ erwähnt wird und wer für eine Karte
zuständig ist, die einen Kommentar bekommt. Ein Konflikt entsteht nur, wenn genau ein geändertes Feld inzwischen anders
ist als die Oberfläche es kannte (M-55); dann wird nichts still überschrieben."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ..modell import Board, Farbe, Karte, Kennung, Kommentar, Konto, Modell, Prioritaet, Punkt
from ..regeln.tage import datum_text, ist_tag
from . import hinweise
from . import zeiterfassung
from .kartenbasis import (
    FELD_LAENGE, KOMMENTAR_LAENGE, KURZ_LAENGE, PUNKTE_HOECHSTENS, TEXT_LAENGE, TITEL_LAENGE, karte_lesen, speichern, vermerken,
)
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext

#: so viele Bilder hat ein Kommentar höchstens (HELF-56)
BILDER_JE_KOMMENTAR = 10

PRIORITAETEN = {"keine": "Keine", "niedrig": "Niedrig", "mittel": "Mittel", "hoch": "Hoch", "dringend": "Dringend"}
SCHAETZUNG_HOECHSTENS = 100_000


class Kartenfelder(Modell):
    """Die bearbeitbaren Felder einer Karte; nur die gesendeten gelten (null entfernt einen Wert)."""

    titel: str | None = None
    beschreibung: str | None = None
    notizen: str | None = None
    zustaendig: list[Kennung] | None = None
    prioritaet: Prioritaet | None = None
    start: str | None = None
    faellig: str | None = None
    labels: list[Kennung] | None = None
    checkliste: list[Punkt] | None = None
    cover: Farbe | None = None
    blockiert: str | None = None
    schaetzung_min: int | None = Field(None, ge=0, le=SCHAETZUNG_HOECHSTENS)
    felder: dict[Kennung, str] | None = None

    def gesendet(self) -> dict[str, Any]:
        return {n: getattr(self, n) for n in self.model_fields_set}


def _mitglieder(b: Board) -> dict[Kennung, str]:
    return {m.konto: m.kellerwolke for m in b.mitglieder if m.konto}


def _name(k: Kontext, konto: Kennung) -> str:
    d = k.s.lies("konten", konto)
    return d["name"] if d else konto


def pruefen(k: Kontext, b: Board, f: dict[str, Any]) -> None:
    """Jeden gesendeten Wert gegen Regeln und Board prüfen; abgelehnt mit dem ersten Grund."""
    if "titel" in f:
        t = (f["titel"] or "").strip()
        if not t:
            raise Abgelehnt("Eine Karte braucht einen Titel")
        if len(t) > TITEL_LAENGE:
            raise Abgelehnt(f"Der Titel ist länger als {TITEL_LAENGE} Zeichen")
        f["titel"] = t
    for name in ("beschreibung", "notizen"):
        if f.get(name) and len(f[name]) > TEXT_LAENGE:
            raise Abgelehnt(f"Der Text ist länger als {TEXT_LAENGE} Zeichen")
    if f.get("blockiert") is not None:
        f["blockiert"] = f["blockiert"].strip()[:KURZ_LAENGE] or None
    for name in ("start", "faellig"):
        if f.get(name) and not ist_tag(f[name]):
            raise Abgelehnt(f"{f[name]} ist kein Tag (JJJJ-MM-TT)")
    if "zustaendig" in f:
        f["zustaendig"] = list(dict.fromkeys(f["zustaendig"] or []))
        fremd = [x for x in f["zustaendig"] if x not in _mitglieder(b)]
        if fremd:
            raise Abgelehnt("Zuständig kann nur sein, wer im Board Mitglied ist")
    if "labels" in f:
        f["labels"] = list(dict.fromkeys(f["labels"] or []))
        if any(x not in {l.id for l in b.labels} for x in f["labels"]):
            raise Abgelehnt("Dieses Label gibt es in diesem Board nicht")
    if "checkliste" in f:
        punkte = f["checkliste"] or []
        if len(punkte) > PUNKTE_HOECHSTENS:
            raise Abgelehnt(f"Eine Checkliste hat höchstens {PUNKTE_HOECHSTENS} Punkte")
        for p in punkte:
            p.text = p.text.strip()
            if not p.text or len(p.text) > KURZ_LAENGE:
                raise Abgelehnt(f"Ein Punkt der Checkliste braucht Text (höchstens {KURZ_LAENGE} Zeichen)")
    if f.get("felder") is not None:
        felder = {x.id: x for x in b.felder}
        for fid, wert in f["felder"].items():
            feld = felder.get(fid)
            if feld is None:
                raise Abgelehnt("Dieses Feld gibt es in diesem Board nicht")
            if len(wert) > FELD_LAENGE:
                raise Abgelehnt(f"{feld.name}: höchstens {FELD_LAENGE} Zeichen")
            if wert and feld.art == "auswahl" and wert not in (feld.optionen or []):
                raise Abgelehnt(f"{feld.name}: {wert} steht nicht zur Wahl")
            if wert and feld.art == "datum" and not ist_tag(wert):
                raise Abgelehnt(f"{feld.name}: {wert} ist kein Tag (JJJJ-MM-TT)")
            if wert and feld.art == "zahl":
                try:
                    float(wert.replace(",", "."))
                except ValueError:
                    raise Abgelehnt(f"{feld.name}: {wert} ist keine Zahl") from None
        f["felder"] = {fid: w for fid, w in f["felder"].items() if w != ""}


def verlaufszeilen(k: Kontext, c: Karte, f: dict[str, Any]) -> list[str]:
    """Was im Verlauf steht (Titel, Beschreibung, Notizen, Checkliste bewusst nicht)."""
    zeilen: list[str] = []
    if "zustaendig" in f:
        for x in f["zustaendig"]:
            if x not in c.zustaendig:
                zeilen.append(f"hat {_name(k, x)} zugewiesen")
        for x in c.zustaendig:
            if x not in f["zustaendig"]:
                zeilen.append(f"hat {_name(k, x)} als zuständig entfernt")
    if "faellig" in f and f["faellig"] != c.faellig:
        zeilen.append(f"hat fällig auf {datum_text(f['faellig'])} gesetzt" if f["faellig"] else "hat die Fälligkeit entfernt")
    if "start" in f and f["start"] != c.start:
        zeilen.append(f"hat den Start auf {datum_text(f['start'])} gesetzt" if f["start"] else "hat den Start entfernt")
    if "prioritaet" in f and f["prioritaet"] != c.prioritaet:
        zeilen.append(f"hat die Priorität auf {PRIORITAETEN[f['prioritaet']]} gesetzt")
    if "blockiert" in f and f["blockiert"] != c.blockiert:
        zeilen.append(f"hat sie blockiert: {f['blockiert']}" if f["blockiert"] else "hat die Blockade aufgehoben")
    return zeilen


def gleiche_karten(k: Kontext, ids: list[Kennung], recht: str) -> tuple[Board, list[Karte]]:
    """Karten einer Sammelaktion: alle aus einem Board, in dem die Person das Recht hat."""
    if not ids:
        raise Abgelehnt("Keine Karten gewählt")
    karten = [karte_lesen(k, i) for i in dict.fromkeys(ids)]
    if len({c.board for c in karten}) > 1:
        raise Abgelehnt("Sammelaktionen gehen nur mit Karten eines Boards")
    return k.board_mit_recht(karten[0].board, recht), karten


def anzahl(n: int) -> str:
    return f"{n} {'Karte' if n == 1 else 'Karten'}"


class Inhalte:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def bearbeiten(self, konto: Konto, karte_id: Kennung, felder: Kartenfelder, vorher: Kartenfelder | None = None,
                         text: str | None = None) -> Antwort:
        """Felder ändern. `vorher`: wie die Oberfläche die geänderten Felder kannte; ist eines inzwischen anders, wird
        abgelehnt (409). `text`: Meldung der Oberfläche ("fällig Di 27.10."), sonst "Gespeichert"."""
        neu = felder.gesendet()
        bekannt = vorher.gesendet() if vorher else {}

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            b = k.board_mit_recht(c.board, "karten.bearbeiten")
            jetzt = c.model_dump(include=set(neu))
            for name, alt in bekannt.items():
                if name in neu and _normal(jetzt.get(name)) != _normal(alt):
                    raise Abgelehnt(f"{c.schluessel} wurde inzwischen geändert ({name}); deine Änderung ist nicht gespeichert", 409)
            pruefen(k, b, neu)
            # nur, wer Start oder Fällig setzt, muss sie stimmig setzen; der Timer setzt den Start einer überfälligen Karte
            # zu Recht nach den Fälligkeitstag, und dann bleiben alle anderen Felder bearbeitbar
            start = neu.get("start", c.start)
            faellig = neu.get("faellig", c.faellig)
            if ("start" in neu or "faellig" in neu) and start and faellig and start > faellig:
                raise Abgelehnt("Der Start liegt nach dem Fälligkeitstag")
            if all(_normal(jetzt.get(n)) == _normal(_roh(w)) for n, w in neu.items()):
                return None
            alt = c.model_copy(deep=True)
            for zeile in verlaufszeilen(k, c, neu):
                vermerken(k, c, zeile)
            for name, wert in neu.items():
                setattr(c, name, wert)
            speichern(k, c)
            hinweise.nach_bearbeiten(k, b, alt, c)
            return f"{c.schluessel}: {(text or '').strip()[:200] or 'Gespeichert'}"

        return await self.a.aendern(konto, arbeit)

    async def art_setzen(self, konto: Konto, karte_id: Kennung, art: Literal["arbeit", "idee"]) -> Antwort:
        """Arbeit oder Idee: eine Idee hat keine Zeiterfassung."""

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            k.board_mit_recht(c.board, "karten.bearbeiten")
            if c.art == art:
                return None
            c.art = art
            vermerken(k, c, "hat sie zur Idee gemacht" if art == "idee" else "hat sie zur Arbeit gemacht")
            gebucht = zeiterfassung.timer_beenden(k, [c]) if art == "idee" else 0
            speichern(k, c)
            return f"{c.schluessel} ist jetzt {'eine Idee' if art == 'idee' else 'Arbeit'}" + zeiterfassung.gestoppt(gebucht)

        return await self.a.aendern(konto, arbeit)

    async def kommentieren(self, konto: Konto, karte_id: Kennung, text: str, bilder: list[str] | None = None) -> Antwort:
        """Ein Kommentar, auf Wunsch mit Bildern (HELF-56): Namen von Bild-Anhängen der Karte, die hochgeladen sind (sie
        liegen in der Kellerwolke und jedes Mitglied darf sie öffnen; verknüpfte aus einer fremden Kellerwolke nicht)."""
        t = text.strip()
        namen = list(dict.fromkeys(bilder or []))

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            b = k.board_mit_recht(c.board, "kommentieren")
            if not t:
                raise Abgelehnt("Ein Kommentar braucht Text")
            if len(t) > KOMMENTAR_LAENGE:
                raise Abgelehnt(f"Ein Kommentar hat höchstens {KOMMENTAR_LAENGE} Zeichen")
            if len(namen) > BILDER_JE_KOMMENTAR:
                raise Abgelehnt(f"Ein Kommentar hat höchstens {BILDER_JE_KOMMENTAR} Bilder")
            vorhanden = {a.name: a for a in c.anhaenge}
            for n in namen:
                a = vorhanden.get(n)
                if a is None or a.art != "bild" or a.verknuepft:
                    raise Abgelehnt(f"{n} ist kein hochgeladenes Bild an {c.schluessel}")
            c.kommentare.append(Kommentar(von=konto.id, zeit=k.jetzt, text=t, bilder=namen))
            vermerken(k, c, "hat kommentiert")
            speichern(k, c)
            hinweise.nach_kommentar(k, b, c, t)
            return f"Kommentar an {c.schluessel} gespeichert"

        return await self.a.aendern(konto, arbeit)

    async def kommentar_bearbeiten(self, konto: Konto, karte_id: Kennung, nr: int, text: str) -> Antwort:
        """Eigenen Kommentar ändern (HELF-94). `nr` zählt die Kommentare der Karte in der Reihenfolge ihres Entstehens ab 1
        (sie werden nur angehängt, die Nummer bleibt). Nur wer ihn schrieb, darf ihn ändern; die alte Fassung steht im
        Verlauf, der Kommentar trägt die Zeit der Bearbeitung. Hinweise gehen nur an neu Erwähnte."""
        t = text.strip()

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            b = k.board_mit_recht(c.board, "kommentieren")
            if not 1 <= nr <= len(c.kommentare):
                raise Abgelehnt(f"{c.schluessel} hat keinen Kommentar {nr}", 404)
            alt = c.kommentare[nr - 1]
            if alt.von != konto.id:
                raise Abgelehnt("Nur eigene Kommentare lassen sich bearbeiten", 403)
            if not t:
                raise Abgelehnt("Ein Kommentar braucht Text")
            if len(t) > KOMMENTAR_LAENGE:
                raise Abgelehnt(f"Ein Kommentar hat höchstens {KOMMENTAR_LAENGE} Zeichen")
            if t == alt.text:
                return f"Kommentar an {c.schluessel} unverändert"
            c.kommentare[nr - 1] = alt.model_copy(update={"text": t, "bearbeitet": k.jetzt})
            vermerken(k, c, "hat einen Kommentar bearbeitet", vorher=alt.text)
            speichern(k, c)
            hinweise.erwaehnt(k, b, c, sorted(hinweise.erwaehnte(k, b, t) - hinweise.erwaehnte(k, b, alt.text)))
            return f"Kommentar an {c.schluessel} bearbeitet"

        return await self.a.aendern(konto, arbeit)

    async def sammel_zuweisen(self, konto: Konto, ids: list[Kennung], person: Kennung) -> Antwort:
        def arbeit(k: Kontext) -> str:
            b, karten = gleiche_karten(k, ids, "karten.bearbeiten")
            if person not in _mitglieder(b):
                raise Abgelehnt("Zuständig kann nur sein, wer im Board Mitglied ist")
            name = _name(k, person)
            for c in karten:
                if person not in c.zustaendig:
                    c.zustaendig.append(person)
                    vermerken(k, c, f"hat {name} zugewiesen")
                    speichern(k, c)
                    hinweise.zugewiesen(k, b, c, [person])
            return f"{anzahl(len(karten))} {name} zugewiesen"

        return await self.a.aendern(konto, arbeit)

    async def sammel_label(self, konto: Konto, ids: list[Kennung], label: Kennung) -> Antwort:
        def arbeit(k: Kontext) -> str:
            b, karten = gleiche_karten(k, ids, "karten.bearbeiten")
            if label not in {l.id for l in b.labels}:
                raise Abgelehnt("Dieses Label gibt es in diesem Board nicht")
            for c in karten:
                if label not in c.labels:
                    c.labels.append(label)
                    speichern(k, c)
            return f"Label an {anzahl(len(karten))} gesetzt"

        return await self.a.aendern(konto, arbeit)

    async def sammel_prioritaet(self, konto: Konto, ids: list[Kennung], p: Prioritaet) -> Antwort:
        def arbeit(k: Kontext) -> str:
            _, karten = gleiche_karten(k, ids, "karten.bearbeiten")
            for c in karten:
                if c.prioritaet != p:
                    c.prioritaet = p
                    vermerken(k, c, f"hat die Priorität auf {PRIORITAETEN[p]} gesetzt")
                    speichern(k, c)
            return f"Priorität von {anzahl(len(karten))} gesetzt"

        return await self.a.aendern(konto, arbeit)


def _roh(w: Any) -> Any:
    if isinstance(w, list):
        return [x.model_dump() if isinstance(x, Modell) else x for x in w]
    return w


def _normal(w: Any) -> Any:
    """Zum Vergleich: leer und fehlend sind gleich, Modelle als Daten."""
    w = _roh(w)
    return None if w in ("", [], {}) else w
