"""Anwendungsfälle der Termine (Modul Serien und Termine): einen Termin anlegen, vorher zusagen oder absagen, nach dem
Termin die eigene Zeit bestätigen oder verwerfen. Ein Termin hat keine Karte; bestätigte Zeit ist ein Zeiteintrag mit
Herkunft `termin` und zählt ins Ist (Entscheidung des Nutzers). Die übrigen Teilnehmer bekommen beim Anlegen einen
Hinweis."""

from __future__ import annotations

import re

from ..modell import Board, Kennung, Konto, Termin, Zeiteintrag
from ..regeln.board import hat_recht, modul_an
from ..regeln.tage import datum_kurz, ist_tag
from ..regeln.zeit import minuten
from . import hinweise
from .rahmen import NAMEN_DER_RECHTE, Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

UHRZEIT = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
#: längster Titel und Ort eines Termins (Zeichen)
TEXT_LAENGE = 200


def termin_lesen(k: Kontext, termin_id: Kennung) -> Termin:
    d = k.s.lies("termine", termin_id)
    if d is None:
        raise Abgelehnt("Diesen Termin gibt es nicht (mehr)", 404)
    return Termin.model_validate(d)


def teilnehmend(k: Kontext, t: Termin) -> Board:
    """Das Board des Termins, wenn die handelnde Person teilnimmt und dort Mitglied ist."""
    b = k.board(t.board)
    if k.konto.id not in t.teilnehmer or not any(m.konto == k.konto.id for m in b.mitglieder):
        raise Abgelehnt("Du nimmst an diesem Termin nicht teil", 403)
    if not modul_an(b, "serien"):
        raise Abgelehnt(f"Im Board {b.name} sind Serien und Termine aus")
    return b


def speichern(k: Kontext, t: Termin) -> None:
    k.s.schreib("termine", t.json_daten())


def zeit_text(t: Termin) -> str:
    return f"{t.titel}, {datum_kurz(t.datum)} {t.von}"


def bestaetigen(k: Kontext, t: Termin) -> str | None:
    """Die eigene Zeit nach dem Termin bestätigen: ein Zeiteintrag von bis, erst dann zählt sie. Recht: "Eigene Zeit
    buchen" im Board des Termins (dafür muss die Zeiterfassung an sein)."""
    b = teilnehmend(k, t)
    if k.konto.id in t.bestaetigt:
        return None
    if t.datum >= k.heute:
        raise Abgelehnt("Die Zeit eines Termins bestätigst du nach dem Termin")
    if not hat_recht(b, "zeit.buchen", k.konto.id):
        raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE['zeit.buchen']}", 403)
    sek = (minuten(t.bis) - minuten(t.von)) * 60
    k.s.schreib("zeiteintraege", Zeiteintrag(id=neue_kennung("z"), termin=t.id, board=t.board, konto=k.konto.id,
                                             datum=t.datum, von=t.von, bis=t.bis, sekunden=sek, herkunft="termin").json_daten())
    t.bestaetigt = [*t.bestaetigt, k.konto.id]
    speichern(k, t)
    return f"Zeit bestätigt: {zeit_text(t)} bis {t.bis}"


def verwerfen(k: Kontext, t: Termin) -> str:
    """Fand für die Person nicht statt: sie ist nicht mehr Teilnehmer, es zählt keine Zeit."""
    teilnehmend(k, t)
    ich = k.konto.id
    t.teilnehmer = [x for x in t.teilnehmer if x != ich]
    t.zugesagt = [x for x in t.zugesagt if x != ich]
    t.bestaetigt = [x for x in t.bestaetigt if x != ich]
    speichern(k, t)
    for d in k.s.alle("zeiteintraege", "konto=? AND json_extract(daten, '$.termin')=?", (ich, t.id)):
        k.s.loesch("zeiteintraege", d["id"])
    return f"{t.titel} am {datum_kurz(t.datum)}: fand für dich nicht statt, es zählt keine Zeit"


class Termine:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def anlegen(self, konto: Konto, board_id: Kennung, titel: str, datum: str, von: str, bis: str,
                      teilnehmer: list[Kennung], ort: str = "") -> Antwort:
        """Neuer Termin; wer ihn anlegt und teilnimmt, hat zugesagt, die übrigen bekommen einen Hinweis."""
        titel, ort = titel.strip(), ort.strip()
        if not titel or len(titel) > TEXT_LAENGE or len(ort) > TEXT_LAENGE:
            raise Abgelehnt(f"Ein Termin braucht einen Titel (höchstens {TEXT_LAENGE} Zeichen)")
        if not ist_tag(datum):
            raise Abgelehnt("Das ist kein gültiger Tag")
        if not (UHRZEIT.match(von) and UHRZEIT.match(bis)) or bis <= von:
            raise Abgelehnt("Von und bis als Uhrzeit wie 09:30, bis nach von")

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "serien.verwalten")
            mitglieder = [m.konto for m in b.mitglieder if m.konto]
            leute = [x for x in dict.fromkeys(teilnehmer) if x in mitglieder]
            if not leute or len(leute) != len(set(teilnehmer)):
                raise Abgelehnt("Teilnehmer sind Mitglieder des Boards, mindestens eines")
            t = Termin(id=neue_kennung("t"), board=b.id, titel=titel, datum=datum, von=von, bis=bis, teilnehmer=leute,
                       ort=ort or None, zugesagt=[k.konto.id] if k.konto.id in leute else [])
            speichern(k, t)
            hinweise.melden(k, b, "termin", leute, None, f"Termin {zeit_text(t)}" + (f" ({t.ort})" if t.ort else ""))
            return f"Termin {zeit_text(t)} angelegt"

        return await self.a.aendern(konto, arbeit)

    async def zusagen(self, konto: Konto, termin_id: Kennung, ja: bool = True) -> Antwort:
        def arbeit(k: Kontext) -> str | None:
            t = termin_lesen(k, termin_id)
            teilnehmend(k, t)
            if (k.konto.id in t.zugesagt) == ja:
                return None
            t.zugesagt = [*t.zugesagt, k.konto.id] if ja else [x for x in t.zugesagt if x != k.konto.id]
            speichern(k, t)
            return f"Zugesagt: {zeit_text(t)}" if ja else f"Abgesagt: {t.titel}"

        return await self.a.aendern(konto, arbeit)

    async def bestaetigen(self, konto: Konto, termin_id: Kennung) -> Antwort:
        return await self.a.aendern(konto, lambda k: bestaetigen(k, termin_lesen(k, termin_id)))

    async def verwerfen(self, konto: Konto, termin_id: Kennung) -> Antwort:
        return await self.a.aendern(konto, lambda k: verwerfen(k, termin_lesen(k, termin_id)))
