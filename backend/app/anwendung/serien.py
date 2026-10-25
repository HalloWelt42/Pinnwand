"""Anwendungsfälle der Serien (Modul Serien und Termine): anlegen, ändern, pausieren, fortsetzen, löschen, einen Tag
auslassen, der Nachtrag am Folgetag; dazu die Vorbuchung, die der Server macht (beim Anlegen, Ändern und Fortsetzen in
derselben Änderung, sonst einmal je Tag über den Begleiter `Vorbuchung`). Die Regeln der Tage stehen in
regeln/serien.py; hier steht, was sich an Serien und Karten ändert.

Pause, Ändern und Urlaub fassen nur unberührte Vorbuchungen an: Karten der Serie in der Zielspalte, nicht erledigt, ohne
Zeit, mit nur der Zeile ihres Anlegens im Verlauf. Bewusst ausgelassene Tage kommen nie wieder (M-106 bis M-111)."""

from __future__ import annotations

import asyncio
import logging
import re

from pydantic import ValidationError

from appkern.app import Begleiter

from ..modell import (Abwesenheit, Auslass, Board, Ereignis, Karte, Kennung, Konto, Modell, Monatsregel, Rhythmus, Serie,
                      Stelle, Zeiteintrag, Zeitkonto)
from ..regeln.arbeitszeit import fassung_am, ganztags_abwesend
from ..regeln.board import erledigt_spalte, modul_an, spalte_von
from ..regeln.feiertage import feiertag
from ..regeln.serien import NACHTRAG_TAGE, TagKarte, Umfeld, karten_titel, vorkommen, vorlauf_ende
from ..regeln.tage import datum_kurz, ist_tag, plus_tage
from ..regeln.zeit import dauer_text, minuten, uhrzeit
from . import termine, zeiterfassung
from .hinweise import PINNWAND
from .karten import TITEL_LAENGE, einreihen, hinein
from .kartenbasis import karten_der_spalte, speichern, vermerken
from .papierkorb import ablegen
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

logger = logging.getLogger(__name__)

UHRZEIT = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
#: längster Vorlauf (Tage) und längste Dauer eines Serientags (Minuten)
VORLAUF_HOECHSTENS = 60
DAUER_HOECHSTENS = 24 * 60
#: so oft schaut der Begleiter, ob ein neuer Tag begonnen hat (Sekunden)
TAKT_S = 300.0


class Serienangaben(Modell):
    """Was eine Serie ausmacht; beim Anlegen braucht es Titel, Rhythmus, Dauer, Zielspalte, Teilnehmer und den ersten
    Tag, beim Ändern nur, was sich ändert."""

    titel: str | None = None
    beschreibung: str | None = None
    labels: list[Kennung] | None = None
    rhythmus: Rhythmus | None = None
    tage: list[int] | None = None
    monatsregel: Monatsregel | None = None
    monatstag: int | None = None
    uhrzeit: str | None = None
    dauer_min: int | None = None
    zielspalte: Kennung | None = None
    teilnehmer: list[Kennung] | None = None
    ab: str | None = None
    bis: str | None = None
    vorlauf_tage: int | None = None
    wochenenden_ueberspringen: bool | None = None
    feiertage_ueberspringen: bool | None = None

    def gesetzt(self) -> dict:
        return self.model_dump(exclude_unset=True)


# ═══ Lage: was die Regeln aus dem Verzeichnis brauchen ════════════════════════════════════════════════════════════════

class Lage:
    """Abwesenheiten, Zeitkonten, die Karten der Serientage und wer auf ihnen Zeit gebucht hat, einmal je Änderung
    gelesen. Neue und zurückgenommene Karten trägt die Änderung hier mit ein."""

    def __init__(self, k: Kontext) -> None:
        self.k = k
        self.abwesenheiten = [Abwesenheit.model_validate(d) for d in k.s.alle("abwesenheiten")]
        self.zeitkonten = [Zeitkonto.model_validate(d) for d in k.s.alle("zeitkonten")]
        self.karten: dict[tuple[Kennung, str], Karte] = {}
        for d in k.s.alle("karten", "json_extract(daten, '$.serie') IS NOT NULL"):
            c = Karte.model_validate(d)
            if c.serie and c.faellig:
                self.karten[(c.serie, c.faellig)] = c
        self.gebucht: dict[Kennung, set[Kennung]] = {}
        ids = [c.id for c in self.karten.values()]
        if ids:
            for e in k.s.alle("zeiteintraege", f"karte IN ({','.join('?' * len(ids))})", tuple(ids)):
                self.gebucht.setdefault(e["karte"], set()).add(e["konto"])

    def angefasst(self, s: Serie, c: Karte) -> bool:
        """Nicht mehr in der Zielspalte, erledigt, mit Zeit oder mit mehr als der Zeile ihres Anlegens im Verlauf."""
        return c.spalte != s.zielspalte or bool(c.abgeschlossen) or bool(self.gebucht.get(c.id)) or len(c.verlauf) > 1

    def unberuehrte(self, s: Serie, ab: str) -> list[Karte]:
        return sorted((c for (sid, tag), c in self.karten.items() if sid == s.id and tag >= ab and not self.angefasst(s, c)),
                      key=lambda c: c.faellig or "")

    def weg(self, c: Karte) -> None:
        self.karten.pop((c.serie or "", c.faellig or ""), None)

    def umfeld(self, s: Serie, ohne: frozenset[Kennung] = frozenset()) -> Umfeld:
        """Das Umfeld der Regeln für eine Serie; Karten in `ohne` gelten als nicht da (beim Ändern neu bewertet)."""

        def tag_karte(serie_id: Kennung, tag: str) -> TagKarte | None:
            c = self.karten.get((serie_id, tag))
            if c is None or c.id in ohne:
                return None
            return TagKarte(c.id, list(c.zustaendig), sorted(self.gebucht.get(c.id, ())), self.angefasst(s, c))

        def feiertag_von(konto: Kennung, tag: str) -> str | None:
            z = fassung_am(self.zeitkonten, konto, tag)
            return feiertag(tag, z.bundesland) if z else None

        return Umfeld(heute=self.k.heute, jetzt=self.k.jetzt[11:16],
                      abwesend=lambda konto, tag: ganztags_abwesend(self.abwesenheiten, konto, tag),
                      feiertag=feiertag_von, tag_karte=tag_karte)


# ═══ Regeln am Board ══════════════════════════════════════════════════════════════════════════════════════════════════

def serie_lesen(k: Kontext, serie_id: Kennung) -> Serie:
    d = k.s.lies("serien", serie_id)
    if d is None:
        raise Abgelehnt("Diese Serie gibt es nicht (mehr)", 404)
    return Serie.model_validate(d)


def schreiben(k: Kontext, s: Serie) -> None:
    k.s.schreib("serien", s.json_daten())


def pruefen(b: Board, s: Serie) -> Serie:
    """Eine Serie, wie sie im Board gehen kann; sonst abgelehnt mit Grund. Ergebnis: die Serie mit bereinigtem Text."""
    titel = s.titel.strip()
    if not titel or len(titel) > TITEL_LAENGE:
        raise Abgelehnt(f"Eine Serie braucht einen Titel (höchstens {TITEL_LAENGE} Zeichen)")
    if s.rhythmus == "woechentlich" and s.tage is not None and (not s.tage or any(t not in range(7) for t in s.tage)):
        raise Abgelehnt("Wöchentlich braucht mindestens einen Wochentag")
    if s.monatstag is not None and not 1 <= s.monatstag <= 31:
        raise Abgelehnt("Der Tag im Monat liegt zwischen 1 und 31")
    if s.uhrzeit is not None and not UHRZEIT.match(s.uhrzeit):
        raise Abgelehnt("Uhrzeit wie 09:30")
    if not 1 <= s.dauer_min <= DAUER_HOECHSTENS:
        raise Abgelehnt("Die Dauer liegt zwischen einer Minute und 24 Stunden")
    ziel = spalte_von(b, s.zielspalte)
    if ziel is None or ziel.erledigt:
        raise Abgelehnt("Die Zielspalte ist eine offene Spalte dieses Boards")
    mitglieder = {m.konto for m in b.mitglieder if m.konto}
    if not s.teilnehmer or any(t not in mitglieder for t in s.teilnehmer):
        raise Abgelehnt("Teilnehmer sind Mitglieder des Boards, mindestens eines")
    if not ist_tag(s.ab) or (s.bis is not None and (not ist_tag(s.bis) or s.bis < s.ab)):
        raise Abgelehnt("Ab und bis sind Tage, bis nicht vor ab")
    if not 0 <= s.vorlauf_tage <= VORLAUF_HOECHSTENS:
        raise Abgelehnt(f"Der Vorlauf liegt zwischen 0 und {VORLAUF_HOECHSTENS} Tagen")
    labels = {l.id for l in b.labels}
    return s.model_copy(update={"titel": titel, "beschreibung": (s.beschreibung or "").strip() or None,
                                "teilnehmer": list(dict.fromkeys(s.teilnehmer)),
                                "labels": [l for l in dict.fromkeys(s.labels) if l in labels]})


def anwesende(s: Serie, b: Board, ohne: list[tuple[Kennung, str]]) -> list[Kennung]:
    fehlen = {k for k, _ in ohne}
    mitglieder = {m.konto for m in b.mitglieder if m.konto}
    return [t for t in s.teilnehmer if t not in fehlen and t in mitglieder]


def vorbuchen(k: Kontext, lage: Lage, s: Serie, b: Board) -> int:
    """Karten für die Tage von heute bis zum Ende des Vorlaufs anlegen, die noch keine haben (je Serie und Tag eine).
    Ergebnis: wie viele."""
    ziel = spalte_von(b, s.zielspalte)
    if not modul_an(b, "serien") or ziel is None or ziel.erledigt:
        return 0
    n = 0
    for v in vorkommen(s, k.heute, vorlauf_ende(s, k.heute), lage.umfeld(s)):
        if v.stand not in ("heute", "vorgebucht") or v.karte:
            continue
        c = Karte(id=neue_kennung("c"), board=b.id, schluessel=f"{b.kuerzel}-{k.naechste_nummer(b.id)}", spalte=ziel.id,
                  titel=karten_titel(s), beschreibung=s.beschreibung, labels=list(s.labels),
                  zustaendig=anwesende(s, b, v.ohne), faellig=v.tag, schaetzung_min=s.dauer_min, serie=s.id,
                  bewegt_am=k.jetzt, erstellt_am=k.jetzt,
                  verlauf=[Ereignis(zeit=k.jetzt, von=k.konto.id, text=f"aus der Serie {s.titel} angelegt")])
        einreihen(k, ziel, [c], None)
        lage.karten[(s.id, v.tag)] = speichern(k, c)
        n += 1
    return n


def zuruecknehmen(k: Kontext, lage: Lage, karten: list[Karte]) -> None:
    """Unberührte Vorbuchungen entfallen ohne Papierkorb; die Vorbuchung legt sie bei Bedarf neu an."""
    for c in karten:
        k.s.loesch("karten", c.id)
        lage.weg(c)


def in_den_papierkorb(k: Kontext, c: Karte, text: str, lage: Lage | None = None) -> None:
    """Eine Karte der Serie in den Papierkorb des Boards, an ihrer Stelle."""
    platz = [x.id for x in karten_der_spalte(k, c.spalte)].index(c.id)
    k.s.loesch("karten", c.id)
    if lage:
        lage.weg(c)
    vermerken(k, c, text)
    ablegen(k, c.board, "karte", [c], Stelle(spalte=c.spalte, platz=platz))


def tage(n: int) -> str:
    return "1 Tag" if n == 1 else f"{n} Tage"


def karte_des_tags(k: Kontext, s: Serie, tag: str) -> Karte:
    d = k.s.alle("karten", "json_extract(daten, '$.serie')=? AND json_extract(daten, '$.faellig')=?", (s.id, tag))
    if not d:
        raise Abgelehnt(f"Für {datum_kurz(tag)} gibt es keine Karte der Serie {s.titel}", 404)
    return Karte.model_validate(d[0])


def nachtrag_pruefen(k: Kontext, c: Karte, tag: str) -> None:
    if k.konto.id not in c.zustaendig:
        raise Abgelehnt(f"Du bist am {datum_kurz(tag)} nicht eingeplant", 403)
    if not plus_tage(k.heute, -NACHTRAG_TAGE) <= tag < k.heute:
        raise Abgelehnt(f"Nachtragen geht für die vergangenen {NACHTRAG_TAGE} Tage")


def serienzeit_buchen(k: Kontext, s: Serie, tag: str, sek: int) -> str | None:
    """Die eigene Zeit eines Serientags bestätigen: ein Zeiteintrag mit Herkunft Serie auf der Karte des Tags; die Karte
    geht nach Erledigt und behält den Tag als Abschluss (M-23, M-111)."""
    c = karte_des_tags(k, s, tag)
    nachtrag_pruefen(k, c, tag)
    b = k.board(c.board)
    zeiterfassung.buchen_pruefen(b, c, k.konto.id)
    zeiterfassung.dauer_pruefen(sek)
    if k.s.alle("zeiteintraege", "konto=? AND karte=? AND datum=?", (k.konto.id, c.id, tag)):
        return None
    von = s.uhrzeit
    bis = uhrzeit(min(24 * 60, minuten(von) + sek // 60)) if von else None
    k.s.schreib("zeiteintraege", Zeiteintrag(id=neue_kennung("z"), karte=c.id, board=c.board, konto=k.konto.id, datum=tag,
                                             von=von, bis=bis, sekunden=sek, herkunft="serie").json_daten())
    ziel = erledigt_spalte(b)
    erledigt = ziel is not None and c.spalte != ziel.id
    if erledigt:
        hinein(k, b, [c.id], ziel, None)
    return f"{dauer_text(sek)} auf {c.schluessel} gebucht ({datum_kurz(tag)})" + (", Karte erledigt" if erledigt else "")


def serientag_verwerfen(k: Kontext, s: Serie, tag: str) -> str:
    """Fand für die Person nicht statt. Waren andere eingeplant, fällt nur sie aus der Karte; war sie allein, geht die
    Karte in den Papierkorb und der Tag gilt als verworfen (es zählt keine Zeit)."""
    c = karte_des_tags(k, s, tag)
    nachtrag_pruefen(k, c, tag)
    andere = [x for x in c.zustaendig if x != k.konto.id]
    if andere:
        c.zustaendig = andere
        vermerken(k, c, f"war am {datum_kurz(tag)} nicht dabei")
        speichern(k, c)
        return f"{c.schluessel}: für dich verworfen, die Karte bleibt für die anderen"
    in_den_papierkorb(k, c, f"hat den {datum_kurz(tag)} verworfen")
    s.verworfen = [*s.verworfen, tag]
    schreiben(k, s)
    return f"{s.titel} am {datum_kurz(tag)} verworfen; {c.schluessel} im Papierkorb, es zählt keine Zeit"


def ohne_person(k: Kontext, konto: Kennung, von: str, bis: str) -> int:
    """Eine ganztägige Abwesenheit nimmt die Person aus unberührten Vorbuchungen dieser Tage; bleibt niemand, entfällt
    die Karte (M-109). Ergebnis: wie viele Vorbuchungen."""
    lage = Lage(k)
    n = 0
    for d in k.s.alle("serien"):
        s = Serie.model_validate(d)
        if konto not in s.teilnehmer:
            continue
        for c in lage.unberuehrte(s, max(von, k.heute)):
            if (c.faellig or "") > bis or konto not in c.zustaendig:
                continue
            c.zustaendig = [x for x in c.zustaendig if x != konto]
            if c.zustaendig:
                speichern(k, c)
            else:
                zuruecknehmen(k, lage, [c])
            n += 1
    return n


# ═══ Anwendungsfälle ══════════════════════════════════════════════════════════════════════════════════════════════════

class Serien:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def anlegen(self, konto: Konto, board_id: Kennung, angaben: Serienangaben) -> Antwort:
        """Neue Serie; der Server legt im Vorlauf ihre Karten in die Zielspalte."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "serien.verwalten")
            try:
                s = Serie.model_validate({**angaben.gesetzt(), "id": neue_kennung("se"), "board": b.id})
            except ValidationError:
                raise Abgelehnt("Eine Serie braucht Titel, Rhythmus, Dauer, Zielspalte, Teilnehmer und den ersten Tag") from None
            s = pruefen(b, s)
            schreiben(k, s)
            n = vorbuchen(k, Lage(k), s, b)
            return f"Serie {s.titel} angelegt; {tage(n)} vorgebucht"

        return await self.a.aendern(konto, arbeit)

    async def aendern(self, konto: Konto, serie_id: Kennung, angaben: Serienangaben) -> Antwort:
        """Unberührte Vorbuchungen ab morgen ziehen nach (Titel, Beschreibung, Labels, Teilnehmer, Dauer, Zielspalte);
        ein Tag, der nach den neuen Regeln entfällt, wird zurückgenommen, neue Tage im Vorlauf kommen dazu. Angefasste,
        vergangene und ausgelassene Tage bleiben."""

        def arbeit(k: Kontext) -> str | None:
            alt = serie_lesen(k, serie_id)
            b = k.board_mit_recht(alt.board, "serien.verwalten")
            try:
                neu = Serie.model_validate({**alt.model_dump(), **angaben.gesetzt()})
            except ValidationError:
                raise Abgelehnt("Diese Angaben passen nicht zu einer Serie") from None
            neu = pruefen(b, neu)
            if neu == alt:
                return None
            lage = Lage(k)
            morgen = plus_tage(k.heute, 1)
            vorher = lage.unberuehrte(alt, morgen)
            u = lage.umfeld(neu, ohne=frozenset(c.id for c in vorher))
            bleiben = {v.tag: v for v in vorkommen(neu, morgen, vorlauf_ende(neu, k.heute), u) if v.stand == "vorgebucht"}
            ziel = spalte_von(b, neu.zielspalte)
            weg = [c for c in vorher if c.faellig not in bleiben]
            zuruecknehmen(k, lage, weg)
            for c in (c for c in vorher if c.faellig in bleiben):
                c.titel, c.beschreibung, c.labels = karten_titel(neu), neu.beschreibung, list(neu.labels)
                c.zustaendig, c.schaetzung_min = anwesende(neu, b, bleiben[c.faellig or ""].ohne), neu.dauer_min
                if ziel and c.spalte != ziel.id:
                    einreihen(k, ziel, [c], None)
                    c.spalte = ziel.id
                speichern(k, c)
            schreiben(k, neu)
            n = vorbuchen(k, lage, neu, b)
            teile = [f"Serie {neu.titel} gespeichert"]
            if len(vorher) - len(weg):
                teile.append(f"{tage(len(vorher) - len(weg))} angepasst")
            if weg:
                teile.append(f"{tage(len(weg))} zurückgenommen")
            if n:
                teile.append(f"{tage(n)} neu vorgebucht")
            return "; ".join(teile) + "; angefasste und vergangene Tage bleiben"

        return await self.a.aendern(konto, arbeit)

    async def pausieren(self, konto: Konto, serie_id: Kennung) -> Antwort:
        """Keine neuen Vorbuchungen; unberührte ab morgen werden zurückgenommen, angefasste bleiben (M-109)."""

        def arbeit(k: Kontext) -> str | None:
            s = serie_lesen(k, serie_id)
            k.board_mit_recht(s.board, "serien.verwalten")
            if s.pausiert_seit and not s.fortgesetzt:
                return None
            lage = Lage(k)
            weg = lage.unberuehrte(s, plus_tage(k.heute, 1))
            zuruecknehmen(k, lage, weg)
            s.pausiert_seit, s.fortgesetzt = k.heute, None
            schreiben(k, s)
            return f"Serie {s.titel} pausiert; {tage(len(weg))} zurückgenommen, angefasste Karten bleiben"

        return await self.a.aendern(konto, arbeit)

    async def fortsetzen(self, konto: Konto, serie_id: Kennung) -> Antwort:
        """Ab heute wird wieder vorgebucht; die Tage der Pause bleiben ohne Karte, ausgelassene bleiben ausgelassen."""

        def arbeit(k: Kontext) -> str | None:
            s = serie_lesen(k, serie_id)
            b = k.board_mit_recht(s.board, "serien.verwalten")
            if not s.pausiert_seit or s.fortgesetzt:
                return None
            s.fortgesetzt = k.heute
            schreiben(k, s)
            n = vorbuchen(k, Lage(k), s, b)
            return f"Serie {s.titel} fortgesetzt; {tage(n)} ab heute vorgebucht"

        return await self.a.aendern(konto, arbeit)

    async def loeschen(self, konto: Konto, serie_id: Kennung) -> Antwort:
        """Unberührte Vorbuchungen ab morgen in den Papierkorb; Karten mit Zeit, angefasste und vergangene bleiben als
        Verlauf und werden von der Serie gelöst (M-110); bestätigte Zeiten zählen weiter."""

        def arbeit(k: Kontext) -> str:
            s = serie_lesen(k, serie_id)
            k.board_mit_recht(s.board, "serien.verwalten")
            lage = Lage(k)
            weg = lage.unberuehrte(s, plus_tage(k.heute, 1))
            geloest = [c for (sid, _), c in lage.karten.items() if sid == s.id and c not in weg]
            for c in weg:
                c.serie = None
                in_den_papierkorb(k, c, f"hat die Serie {s.titel} gelöscht")
            for c in geloest:
                c.serie = None
                vermerken(k, c, f"aus der gelöschten Serie {s.titel} gelöst")
                speichern(k, c)
            k.s.loesch("serien", s.id)
            return (f"Serie {s.titel} gelöscht; {tage(len(weg))} im Papierkorb, "
                    f"{len(geloest)} {'Karte bleibt' if len(geloest) == 1 else 'Karten bleiben'} als Verlauf")

        return await self.a.aendern(konto, arbeit)

    async def auslassen(self, konto: Konto, serie_id: Kennung, tag: str) -> Antwort:
        """Einen Tag bewusst auslassen: er kommt nie wieder (M-108); eine unberührte Karte des Tags geht in den
        Papierkorb (Wiederherstellen nimmt den Auslass zurück)."""
        if not ist_tag(tag):
            raise Abgelehnt("Das ist kein gültiger Tag")

        def arbeit(k: Kontext) -> str | None:
            s = serie_lesen(k, serie_id)
            k.board_mit_recht(s.board, "serien.verwalten")
            if any(a.tag == tag for a in s.auslass):
                return None
            s.auslass = [*s.auslass, Auslass(tag=tag, von=k.konto.id, am=k.jetzt)]
            schreiben(k, s)
            lage = Lage(k)
            c = next((x for x in lage.unberuehrte(s, tag) if x.faellig == tag), None)
            if c:
                in_den_papierkorb(k, c, f"hat den {datum_kurz(tag)} der Serie ausgelassen", lage)
            return (f"{s.titel} am {datum_kurz(tag)} ausgelassen; der Tag kommt nicht wieder"
                    + (f", {c.schluessel} im Papierkorb" if c else ""))

        return await self.a.aendern(konto, arbeit)

    async def bestaetigen(self, konto: Konto, serie_id: Kennung, tag: str, sek: int) -> Antwort:
        return await self.a.aendern(konto, lambda k: serienzeit_buchen(k, serie_lesen(k, serie_id), tag, sek))

    async def verwerfen(self, konto: Konto, serie_id: Kennung, tag: str) -> Antwort:
        return await self.a.aendern(konto, lambda k: serientag_verwerfen(k, serie_lesen(k, serie_id), tag))

    async def nachtrag(self, konto: Konto, posten: list[tuple[str, Kennung, str, int | None]]) -> Antwort:
        """Mehrere vorgebuchte Zeiten in einer Änderung bestätigen: (Art, Bezug, Tag, Sekunden); eine Serie ohne
        Sekunden mit ihrer geplanten Dauer."""

        def arbeit(k: Kontext) -> str | None:
            n = 0
            for art, bezug, tag, sek in posten:
                if art == "serie":
                    s = serie_lesen(k, bezug)
                    n += serienzeit_buchen(k, s, tag, sek or s.dauer_min * 60) is not None
                else:
                    n += termine.bestaetigen(k, termine.termin_lesen(k, bezug)) is not None
            return f"{n} {'Zeit' if n == 1 else 'Zeiten'} bestätigt" if n else None

        return await self.a.aendern(konto, arbeit)

    async def alle_vorbuchen(self) -> Antwort:
        """Die Vorbuchung des Tages für alle Serien, als die Pinnwand selbst (still, ohne Rückweg)."""

        def arbeit(k: Kontext) -> str | None:
            lage = Lage(k)
            n = 0
            for d in k.s.alle("serien"):
                s = Serie.model_validate(d)
                b = k.s.lies("boards", s.board)
                if b:
                    n += vorbuchen(k, lage, s, Board.model_validate(b))
            return f"{tage(n)} von Serien vorgebucht" if n else None

        return await self.a.aendern(PINNWAND, arbeit, rueckgaengig=False, melden=False)


class Vorbuchung(Begleiter):
    """Legt beim Start und bei jedem Tageswechsel die Karten der Serien im Vorlauf an. Wie die Fälligkeit: alle paar
    Minuten ein Blick auf den Tag, so übersteht er Ruhezustand und Neustarts; doppelte Läufe legen nichts doppelt an."""

    def __init__(self, serien: Serien, takt_s: float = TAKT_S) -> None:
        self.serien = serien
        self.takt_s = takt_s
        self._zuletzt: str | None = None
        self._aufgabe: asyncio.Task[None] | None = None

    async def starten(self) -> None:
        self._aufgabe = asyncio.create_task(self._laufen(), name="pinnwand-vorbuchung")

    async def stoppen(self) -> None:
        if self._aufgabe:
            self._aufgabe.cancel()
            await asyncio.gather(self._aufgabe, return_exceptions=True)
            self._aufgabe = None

    async def pruefen(self) -> bool:
        heute = self.serien.a.uhr.heute()
        if heute == self._zuletzt:
            return False
        await self.serien.alle_vorbuchen()
        self._zuletzt = heute
        return True

    async def _laufen(self) -> None:
        while True:
            try:
                await self.pruefen()
            except Exception:  # noqa: BLE001 - der nächste Blick versucht es wieder
                logger.exception("Serien vorbuchen")
            await asyncio.sleep(self.takt_s)
