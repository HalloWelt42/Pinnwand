"""Datenvertraege der Planung."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str
    name: str
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] = Field(default_factory=lambda: [8, 8, 8, 8, 8, 0, 0])
    aktiv: bool = True


class PersonCreate(BaseModel):
    name: str
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] | None = None


class PersonUpdate(BaseModel):
    name: str | None = None
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] | None = None
    aktiv: bool | None = None


class UrlaubSetzen(BaseModel):
    person_id: str
    von: str
    bis: str | None = None  # None = einzelner Tag
    anteil: float = 1.0  # 1.0 ganzer Tag, 0.5 halber Tag
    typ: str = "urlaub"
    notiz: str | None = None
    wochenenden_ueberspringen: bool = True
    feiertage_ueberspringen: bool = True


class FeiertageUebernehmen(BaseModel):
    land: str = "DE"
    region: str | None = None
    jahr: int
