"""Datenverträge der Agenten-API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ZeitBuchung(BaseModel):
    karte: str  # Schlüssel (R3-130), Titel oder ID
    dauer: str  # "1:30", "90min", "1,5h", "2 Std"
    datum: str | None = None  # "heute", "gestern", "2026-06-19", "Montag"
    kommentar: str | None = None
    dry_run: bool = False
    idempotenz_schluessel: str | None = None


class Erledigung(BaseModel):
    karte: str
    dauer: str | None = None
    kommentar: str | None = None
    dry_run: bool = False
    idempotenz_schluessel: str | None = None


class KartenAnlage(BaseModel):
    board: str  # Kürzel (R3), Titel oder ID
    titel: str
    spalte: str | None = None
    beschreibung: str | None = None
    labels: list[str] = Field(default_factory=list)
    prioritaet: str | None = None
    faellig: str | None = None
    zustaendig: str | None = None
    schaetzung_min: int | None = None
    dry_run: bool = False
    idempotenz_schluessel: str | None = None


class Kommentierung(BaseModel):
    karte: str
    text: str
    dry_run: bool = False
    idempotenz_schluessel: str | None = None


class Freitext(BaseModel):
    text: str
    dry_run: bool = False
    idempotenz_schluessel: str | None = None


class TokenAnlage(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])


class WerkzeugAufruf(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)
    dry_run: bool = False
    idempotenz_schluessel: str | None = None
