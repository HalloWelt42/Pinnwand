"""Berechtigungs-Politik: reine Entscheidungsfunktionen ueber einen Akteur.

Bewusst klein und ohne DB-Zugriff (nur der Akteur-Wert + primitive Zielwerte) -
so ist die Politik ohne TestClient unit-testbar und es entstehen keine Import-Zyklen.
Endpunkte rufen die darf_*-Funktionen und setzen das Ergebnis mit verlange() durch.
"""
from __future__ import annotations

from fastapi import HTTPException

from .akteur import Akteur


def darf_person_bearbeiten(akteur: Akteur, ziel_person_id: str | None) -> bool:
    """Persoenliche Planungsdaten darf nur die Person selbst oder ein Admin aendern."""
    return akteur.ist_admin or (
        akteur.person_id is not None and akteur.person_id == ziel_person_id
    )


def darf_zeiteintrag_bearbeiten(akteur: Akteur, karte_zustaendig: str | None) -> bool:
    """Zeiteintraege gehoeren der zustaendigen Person (ueber ihr Kuerzel) - oder Admin.

    Fail-closed: ohne Kuerzel am Akteur begruendet auch ein None-Ziel kein Eigentum.
    """
    return akteur.ist_admin or (
        akteur.kuerzel is not None and akteur.kuerzel == karte_zustaendig
    )


def darf_zeit_buchen(akteur: Akteur, karte_zustaendig: str | None) -> bool:
    """Zeit BUCHEN darf: Admin ueberall, die zustaendige Person auf ihrer Karte -
    und jede Person mit Kuerzel auch auf fremden/gemeinsamen Karten, weil der
    Eintrag ihr selbst zugeschrieben wird (Kuerzel-Snapshot am Eintrag).
    Fail-closed: ohne Kuerzel keine Fremd-Buchung."""
    return akteur.ist_admin or akteur.kuerzel is not None


def verlange(erlaubt: bool, detail: str = "Keine Berechtigung für diese Aktion.") -> None:
    """Wirft 403, wenn die Aktion nicht erlaubt ist. Haelt die Endpunkte einzeilig."""
    if not erlaubt:
        raise HTTPException(status_code=403, detail=detail)
