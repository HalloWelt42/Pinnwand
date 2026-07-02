"""Datenverträge für wiederkehrende Termine/Aufgaben (Serien)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SerienTyp = Literal["taeglich", "woechentlich", "monatlich"]
# Monatsregel: fester Tag, erster oder letzter Werktag (Mo-Fr) des Monats.
Monatsregel = Literal["tag", "erster_werktag", "letzter_werktag"]


class NachtragEingabe(BaseModel):
    dauer_min: int | None = None  # None -> Serien-Soll als Vorschlag


class Serie(BaseModel):
    id: str
    board_id: str
    spalte_id: str | None = None
    titel: str
    beschreibung: str | None = None
    labels: list[str] = Field(default_factory=list)
    zustaendig: str | None = None
    typ: SerienTyp
    intervall: int = 1
    wochentage: list[int] = Field(default_factory=list)  # 0=Mo .. 6=So
    monatstag: int | None = None
    monatsregel: Monatsregel = "tag"
    uhrzeit: str | None = None  # HH:MM (Sprechzeit)
    dauer_min: int | None = None  # geplante Zeit (Soll)
    wochenenden_ueberspringen: bool = False
    feiertage_ueberspringen: bool = False
    vorlauf_tage: int = 14
    start: str | None = None
    ende: str | None = None
    aktiv: bool = True
    reaktiviert_am: str | None = None


class SerieCreate(BaseModel):
    board_id: str
    spalte_id: str | None = None
    titel: str
    beschreibung: str | None = None
    labels: list[str] = Field(default_factory=list)
    zustaendig: str | None = None
    typ: SerienTyp = "woechentlich"
    intervall: int = 1
    wochentage: list[int] = Field(default_factory=list)
    monatstag: int | None = None
    monatsregel: Monatsregel = "tag"
    uhrzeit: str | None = None
    dauer_min: int | None = None
    wochenenden_ueberspringen: bool = False
    feiertage_ueberspringen: bool = False
    vorlauf_tage: int = 14
    start: str | None = None
    ende: str | None = None
    aktiv: bool = True


class SerienNachtrag(BaseModel):
    """Eine ignorierte Serien-Karte vergangener Tage (Folgetag-Nachfrage)."""
    karte_id: str
    schluessel: str | None = None
    titel: str
    datum: str | None = None
    serie_titel: str | None = None
    soll_min: int | None = None


class SerieUpdate(BaseModel):
    titel: str | None = None
    beschreibung: str | None = None
    labels: list[str] | None = None
    zustaendig: str | None = None
    spalte_id: str | None = None
    typ: SerienTyp | None = None
    intervall: int | None = None
    wochentage: list[int] | None = None
    monatstag: int | None = None
    monatsregel: Monatsregel | None = None
    uhrzeit: str | None = None
    dauer_min: int | None = None
    wochenenden_ueberspringen: bool | None = None
    feiertage_ueberspringen: bool | None = None
    vorlauf_tage: int | None = None
    start: str | None = None
    ende: str | None = None
    aktiv: bool | None = None
    reaktiviert_am: str | None = None
