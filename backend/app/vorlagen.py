"""Mitgelieferte Vorlagen neuer Boards (eigene speichert jede Person dazu), und die Start-Rollen jedes Boards."""

from __future__ import annotations

from .modell import Rolle, Vorlage, VorlageSpalte
from .regeln.board import RECHTE_DER_MODULE

ALLE_RECHTE = [r for rechte in RECHTE_DER_MODULE.values() for r in rechte]


def start_rollen() -> list[Rolle]:
    """Start-Rollen jedes Boards: Besitzer, Mitglied, Leser (umbenennbar, nicht löschbar)."""
    return [
        Rolle(id="besitzer", name="Besitzer", vorgabe=True, rechte=list(ALLE_RECHTE)),
        Rolle(id="mitglied", name="Mitglied", vorgabe=True, rechte=[
            "karten.anlegen", "karten.bearbeiten", "karten.verschieben", "karten.loeschen", "kommentieren", "zeit.buchen",
            "zeit.andere.sehen", "abwesenheit.sehen", "serien.verwalten", "berichte.erstellen"]),
        Rolle(id="leser", name="Leser", vorgabe=True, rechte=["kommentieren"]),
    ]


def _erledigt(name: str = "Erledigt") -> VorlageSpalte:
    return VorlageSpalte(name=name, farbe="minze", erledigt=True)


MITGELIEFERT: list[Vorlage] = [
    Vorlage(id="v-aufgaben", name="Aufgaben", beschreibung="Offen, Dran, Erledigt; mit Zeiterfassung und Serien", symbol="fa-list-check",
            spalten=[VorlageSpalte(name="Offen", farbe="stahl"), VorlageSpalte(name="Dran", farbe="honig"), _erledigt()],
            module=["zeiterfassung", "serien", "vorlesen"]),
    Vorlage(id="v-projekt", name="Projekt", beschreibung="Eingang bis Erledigt mit Prüfung, Zeiterfassung, Arbeitszeit und Berichten",
            symbol="fa-diagram-project",
            spalten=[VorlageSpalte(name="Eingang", farbe="stahl"), VorlageSpalte(name="Geplant", farbe="himmel"),
                     VorlageSpalte(name="In Arbeit", farbe="honig", grenze=4), VorlageSpalte(name="Prüfung", farbe="flieder", grenze=3),
                     _erledigt()],
            module=["zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki"]),
    Vorlage(id="v-ideen", name="Ideen", beschreibung="Gesammelt, Bewerten, Umsetzen; Karten sind Ideen ohne Zeiten", symbol="fa-lightbulb",
            spalten=[VorlageSpalte(name="Gesammelt", farbe="flieder"), VorlageSpalte(name="Bewerten", farbe="himmel"),
                     VorlageSpalte(name="Umsetzen", farbe="tuerkis"), _erledigt("Umgesetzt")],
            module=["transkripte", "vorlesen", "ki"]),
]
