"""Datenverträge der Planung."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Rolle = Literal["admin", "mitarbeiter"]


class Person(BaseModel):
    id: str
    name: str
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] = Field(default_factory=lambda: [8, 8, 8, 8, 8, 0, 0])
    bundesland: str | None = None
    urlaubsanspruch: float = 30
    resturlaub_vorjahr: float = 0
    aktiv: bool = True
    # Rolle steuert nur die sichtbaren Verwaltungsbereiche im UI (kein Login/Schutz).
    rolle: Rolle = "mitarbeiter"


class PersonCreate(BaseModel):
    name: str
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] | None = None
    bundesland: str | None = None
    urlaubsanspruch: float = 30
    resturlaub_vorjahr: float = 0


class PersonUpdate(BaseModel):
    name: str | None = None
    kuerzel: str | None = None
    farbe: str | None = None
    wochenstunden: list[float] | None = None
    bundesland: str | None = None
    urlaubsanspruch: float | None = None
    resturlaub_vorjahr: float | None = None
    aktiv: bool | None = None
    rolle: Rolle | None = None


class Urlaubskonto(BaseModel):
    person_id: str
    jahr: int
    anspruch: float
    uebertrag: float
    verfuegbar: float
    genommen: float
    verbleibend: float
    genommen_vorjahr: float


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


class AbwesenheitTyp(BaseModel):
    code: str
    name: str
    farbe: str
    reduziert_soll: bool = True
    anrechnen: bool = True
    anwesend: bool = False
    reihenfolge: int = 0


class AbwesenheitTypUpdate(BaseModel):
    name: str | None = None
    farbe: str | None = None
    reduziert_soll: bool | None = None
    anrechnen: bool | None = None
    anwesend: bool | None = None
    reihenfolge: int | None = None


class Tagesregel(BaseModel):
    id: str
    person_id: str | None = None
    art: str  # 'jahrestag' | 'wochentag' | 'brueckentag'
    monat: int | None = None
    tag: int | None = None
    wochentag: int | None = None
    anteil: float = 0.5
    notiz: str | None = None
    aktiv: bool = True


class TagesregelCreate(BaseModel):
    id: str | None = None
    person_id: str | None = None
    art: str
    monat: int | None = None
    tag: int | None = None
    wochentag: int | None = None
    anteil: float = 0.5
    notiz: str | None = None
    aktiv: bool = True


class TagLeeren(BaseModel):
    person_id: str
    datum: str


class WochenOverride(BaseModel):
    jahr: int
    kw: int
    wochenstunden: list[float]


class WochenOverrideSetzen(BaseModel):
    jahr: int
    kw: int
    wochenstunden: list[float]
