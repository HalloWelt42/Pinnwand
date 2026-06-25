"""Datenmodelle der Transkript-Anbindung.

Entitaeten: Transkript-Marke (verbindet eine Karte mit einer Stelle im Transkript)
und Arbeitspool-Eintrag. Eingabe-DTOs und Antwort-Huellen halten den bestehenden
JSON-Vertrag der UI-Endpunkte (siehe api.py).
"""
from __future__ import annotations

from pydantic import BaseModel


class TranskriptMarke(BaseModel):
    id: str
    karte_id: str
    transkript_id: str
    transkript_name: str | None = None
    position_sek: float | None = None
    segment_text: str | None = None
    sprecher: str | None = None
    titel: str | None = None
    zusammenfassung: str | None = None
    reihenfolge: int = 0
    erstellt_am: str | None = None


class TranskriptMarkeMitKarte(TranskriptMarke):
    """Marke mit denormalisierter Karten-Info (fuer die Transkript-Ansicht)."""

    karte_schluessel: str | None = None
    karte_titel: str | None = None
    karte_board: str | None = None


class PoolEintrag(BaseModel):
    transkript_id: str
    transkript_name: str | None = None


# -- Eingabe-DTOs --
class MarkeCreate(BaseModel):
    karte_id: str
    transkript_id: str
    transkript_name: str | None = None
    position_sek: float | None = None
    segment_text: str | None = None
    sprecher: str | None = None
    titel: str | None = None
    zusammenfassung: str | None = None


class MarkeUpdate(BaseModel):
    titel: str | None = None
    zusammenfassung: str | None = None
    position_sek: float | None = None
    segment_text: str | None = None
    sprecher: str | None = None


class VorschlagEingabe(BaseModel):
    transkript_id: str
    position_sek: float | None = None


class PoolEingabe(BaseModel):
    transkript_id: str
    transkript_name: str | None = None


# -- Antwort-Huellen (bewahren die bestehende JSON-Form {marken:[...]} / {pool:[...]}) --
class MarkenAntwort(BaseModel):
    marken: list[TranskriptMarke]


class MarkenJeTranskriptAntwort(BaseModel):
    marken: list[TranskriptMarkeMitKarte]


class PoolAntwort(BaseModel):
    pool: list[PoolEintrag]
