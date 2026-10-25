"""Regeln des Moduls Arbeitszeit, soweit der Server sie braucht: Namen der Abwesenheiten für Meldungen, die
Bundesländer und die Prüfung eines Zeitkontos. Soll, Feiertage und Urlaubstage rechnet die Oberfläche mit denselben
Regeln (frontend/src/regeln/arbeitszeit.ts, feiertage.ts); Berichte bringen sie mit Stufe 4 auch hierher."""

from __future__ import annotations

from ..modell import Abwesenheit, Halbtagsregel, Kennung, Zeitkonto
from .tage import ist_tag

#: Namen der Arten wie ARTEN in frontend/src/regeln/arbeitszeit.ts (name und knapp)
ARTEN: dict[str, tuple[str, str]] = {
    "urlaub": ("Urlaub", "Urlaub"),
    "krank": ("Krank", "Krank"),
    "frei": ("Frei (Ausgleich)", "Ausgleich"),
    "fortbildung": ("Fortbildung", "Fortbildung"),
    "feiertag": ("Betrieblich frei", "Betrieb frei"),
}

BUNDESLAENDER = (
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern",
    "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
    "Schleswig-Holstein", "Thüringen",
)

#: Tage je Monat für die Prüfung einer Halbtagsregel (der 29. Februar ist erlaubt)
TAGE_IM_MONAT = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def art_name(a: Abwesenheit) -> str:
    """Name einer Abwesenheit mit ihrem Anteil: "Urlaub", "Halber Tag Urlaub"."""
    name, knapp = ARTEN[a.art]
    return f"Halber Tag {knapp}" if a.anteil == 0.5 else name


def abwesenheit_fehler(von: str, bis: str, anteil: float | None) -> str | None:
    """Grund, warum eine Abwesenheit so nicht geht, sonst None. Halbe Tage gelten für jeden Tag des Zeitraums."""
    if not ist_tag(von) or not ist_tag(bis):
        return "Von und bis müssen Tage sein"
    if bis < von:
        return "Bis liegt vor von"
    if anteil is not None and anteil != 0.5:
        return "Ein Tag zählt ganz oder halb"
    return None


def zeitkonto_fehler(ab: str, wochenstunden: float, tage: list[int], bundesland: str, urlaubsanspruch: float,
                     resturlaub: float, halbtage: list[Halbtagsregel]) -> str | None:
    """Grund, warum ein Zeitkonto so nicht geht, sonst None."""
    if not ist_tag(ab):
        return "Gilt ab muss ein Tag sein"
    if not 0 <= wochenstunden <= 80:
        return "Wochenstunden von 0 bis 80"
    if len(set(tage)) != len(tage) or any(t not in range(7) for t in tage):
        return "Arbeitstage sind Wochentage, jeder einmal"
    if bundesland not in BUNDESLAENDER:
        return "Unbekanntes Bundesland"
    if not 0 <= urlaubsanspruch <= 366 or not 0 <= resturlaub <= 366:
        return "Urlaubstage von 0 bis 366"
    for r in halbtage:
        if not 1 <= r.monat <= 12 or not 1 <= r.tag <= TAGE_IM_MONAT[r.monat - 1] or not r.name.strip():
            return "Ein halber Tag braucht Tag, Monat und Namen"
    return None


def fassung_am(fassungen: list[Zeitkonto], konto: Kennung, tag: str) -> Zeitkonto | None:
    """Die Fassung des Zeitkontos, die an einem Tag gilt: die jüngste mit ab bis zu diesem Tag, sonst die erste (für das
    Bundesland vor dem Beginn), wie fassungAm der Oberfläche."""
    eigene = sorted((z for z in fassungen if z.konto == konto), key=lambda z: z.ab)
    gueltig = [z for z in eigene if z.ab <= tag]
    return gueltig[-1] if gueltig else (eigene[0] if eigene else None)


def ganztags_abwesend(liste: list[Abwesenheit], konto: Kennung, tag: str) -> str | None:
    """Name einer ganztägigen Abwesenheit der Person an diesem Tag, sonst None."""
    a = next((x for x in liste if x.konto == konto and x.von <= tag <= x.bis), None)
    return art_name(a) if a and (a.anteil or 1) >= 1 else None
