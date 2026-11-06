"""Mitgelieferte Vorlagen neuer Boards (eigene speichert jede Person dazu), und die Start-Rollen jedes Boards."""

from __future__ import annotations

from .modell import Farbe, Rolle, Vorlage, VorlageSpalte
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


# Symbole der Spalten (HELF-165) aus der Auswahl der Oberfläche (SPALTENSYMBOLE in frontend/src/anzeige.ts)

def _erledigt(name: str = "Erledigt") -> VorlageSpalte:
    return VorlageSpalte(name=name, farbe="minze", erledigt=True, sortierung="erledigung", symbol="fa-circle-check")


def _offen(name: str, farbe: Farbe, symbol: str, grenze: int | None = None) -> VorlageSpalte:
    """Eine offene Spalte: höchste Priorität oben, bei gleicher die neueste (HELF-50)."""
    return VorlageSpalte(name=name, farbe=farbe, grenze=grenze, sortierung="prioritaet", symbol=symbol)


def _in_arbeit(name: str, farbe: Farbe = "honig", symbol: str = "fa-person-digging", grenze: int | None = None) -> VorlageSpalte:
    """Eine Spalte für Arbeit, die läuft: zuletzt begonnen oben (HELF-50)."""
    return VorlageSpalte(name=name, farbe=farbe, grenze=grenze, sortierung="arbeitsbeginn", symbol=symbol)


MITGELIEFERT: list[Vorlage] = [
    Vorlage(id="v-leer", name="Leer anfangen", beschreibung="Drei Spalten, ohne Module und Felder; alles Weitere stellst du selbst ein.",
            symbol="fa-square", spalten=[_offen("Offen", "stahl", "fa-inbox"), _in_arbeit("In Arbeit"), _erledigt()]),
    Vorlage(id="v-aufgaben", name="Aufgaben", beschreibung="Offen, Dran, Erledigt: für Aufgaben im Alltag", symbol="fa-list-check",
            spalten=[_offen("Offen", "stahl", "fa-inbox"), _in_arbeit("Dran"), _erledigt()],
            module=["zeiterfassung", "serien", "vorlesen"]),
    Vorlage(id="v-projekt", name="Projekt", beschreibung="Eingang bis Erledigt mit Grenzen in Arbeit und Prüfung",
            symbol="fa-diagram-project",
            spalten=[_offen("Eingang", "stahl", "fa-inbox"), _offen("Geplant", "himmel", "fa-calendar-days"),
                     _in_arbeit("In Arbeit", grenze=4), _in_arbeit("Prüfung", "flieder", "fa-magnifying-glass", grenze=3), _erledigt()],
            module=["zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki"]),
    Vorlage(id="v-ideen", name="Ideen", beschreibung="Gesammelt, Bewerten, Umsetzen; neue Karten sind Ideen", symbol="fa-lightbulb",
            spalten=[_offen("Gesammelt", "flieder", "fa-lightbulb"), _offen("Bewerten", "himmel", "fa-scale-balanced"),
                     _in_arbeit("Umsetzen", "tuerkis", "fa-hammer"), _erledigt("Umgesetzt")],
            kartenart="idee", module=["transkripte", "vorlesen", "ki"]),
]
