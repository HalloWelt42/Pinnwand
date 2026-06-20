"""Datenvertraege fuer Termine (leichte Meeting-Zeiterfassung).

Termine sind keine Kanban-Karten: eine Termin-Serie beschreibt einen
wiederkehrenden Meeting-Rhythmus, jedes Vorkommen wird als Instanz materialisiert
und am Folgetag bestaetigt (oder abgelehnt). Erst eine bestaetigte Instanz zaehlt
als geleistete Zeit.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from module.serien.models import Monatsregel, SerienTyp

InstanzStatus = Literal["schwebend", "bestaetigt", "abgelehnt"]


class TerminSerie(BaseModel):
    id: str
    titel: str
    beschreibung: str | None = None
    kuerzel: str | None = None  # Person, der die Zeit gutgeschrieben wird
    typ: SerienTyp
    intervall: int = 1
    wochentage: list[int] = Field(default_factory=list)  # 0=Mo .. 6=So
    monatstag: int | None = None
    monatsregel: Monatsregel = "tag"
    uhrzeit: str | None = None  # HH:MM (nur Anzeige)
    dauer_min: int = 60  # geplante Dauer (Soll-Vorschlag bei Bestaetigung)
    wochenenden_ueberspringen: bool = False
    feiertage_ueberspringen: bool = False
    urlaub_ueberspringen: bool = True  # an Urlaubstagen der Person keine Instanz
    rueckblick_tage: int = 14  # Backfill-Grenze beim Materialisieren
    start: str | None = None
    ende: str | None = None
    aktiv: bool = True


class TerminSerieCreate(BaseModel):
    titel: str
    beschreibung: str | None = None
    kuerzel: str | None = None
    typ: SerienTyp = "taeglich"
    intervall: int = 1
    wochentage: list[int] = Field(default_factory=list)
    monatstag: int | None = None
    monatsregel: Monatsregel = "tag"
    uhrzeit: str | None = None
    dauer_min: int = 60
    wochenenden_ueberspringen: bool = False
    feiertage_ueberspringen: bool = False
    urlaub_ueberspringen: bool = True
    rueckblick_tage: int = 14
    start: str | None = None
    ende: str | None = None
    aktiv: bool = True


class TerminSerieUpdate(BaseModel):
    titel: str | None = None
    beschreibung: str | None = None
    kuerzel: str | None = None
    typ: SerienTyp | None = None
    intervall: int | None = None
    wochentage: list[int] | None = None
    monatstag: int | None = None
    monatsregel: Monatsregel | None = None
    uhrzeit: str | None = None
    dauer_min: int | None = None
    wochenenden_ueberspringen: bool | None = None
    feiertage_ueberspringen: bool | None = None
    urlaub_ueberspringen: bool | None = None
    rueckblick_tage: int | None = None
    start: str | None = None
    ende: str | None = None
    aktiv: bool | None = None


class TerminInstanz(BaseModel):
    id: str
    serie_id: str
    datum: str
    kuerzel: str | None = None
    titel: str
    uhrzeit: str | None = None
    geplant_min: int
    status: InstanzStatus
    effektiv_min: int | None = None
    bestaetigt_am: str | None = None


class BestaetigenEingabe(BaseModel):
    dauer_min: int | None = None  # None = wie geplant


class SammelBestaetigung(BaseModel):
    ids: list[str] | None = None  # None = alle schwebenden
