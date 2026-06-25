"""Pydantic-Modelle des KI-Assistenten."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class KiStatus(BaseModel):
    verfuegbar: bool
    modell: str | None = None
    automatisch: bool = True


class KiAufgabeEingabe(BaseModel):
    typ: str
    kontext: dict[str, Any] = {}
    anweisung: str = ""


class KiVorschlag(BaseModel):
    id: str
    text: str
    begruendung: str = ""
    vorgewaehlt: bool = True


class KiAntwort(BaseModel):
    ok: bool
    modell: str | None = None
    vorschlaege: list[KiVorschlag] = []
    fehler: str | None = None


class KiTyp(BaseModel):
    """Ein registrierter KI-Aufgabentyp (fuer Doku/Diagnose)."""

    typ: str
    beschreibung: str
