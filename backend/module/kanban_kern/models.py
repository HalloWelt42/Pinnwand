"""Datenverträge des Kanban-Moduls.

Liegen bewusst im Modul, nicht im Kern - so kann ein anderes Modul ein
eigenes Datenmodell mitbringen, ohne den Kern anzufassen.
Das Frontend spiegelt diese Typen in ``frontend/src/lib/types.ts``.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Prioritaet = Literal["hoch", "mittel", "niedrig"]


class ChecklistPunkt(BaseModel):
    text: str
    erledigt: bool = False


class Kommentar(BaseModel):
    autor: str
    text: str
    zeit: str


class Karte(BaseModel):
    id: str
    board_id: str
    spalte: str
    titel: str
    schluessel: str | None = None
    beschreibung: str | None = None
    notizen: str | None = None
    labels: list[str] = Field(default_factory=list)
    prioritaet: Prioritaet | None = None
    checkliste: list[ChecklistPunkt] = Field(default_factory=list)
    kommentare: list[Kommentar] = Field(default_factory=list)
    cover: str | None = None
    reihenfolge: int = 0
    start: date | None = None
    faellig: date | None = None
    zustaendig: str | None = None
    erstellt_am: str | None = None
    bewegt_am: str | None = None
    schaetzung_min: int | None = None
    erfasst_sek: int = 0
    laeuft_seit: str | None = None
    transkript_id: str | None = None
    transkript_name: str | None = None


class Spalte(BaseModel):
    id: str
    titel: str
    wip_limit: int | None = None
    reihenfolge: int = 0
    erledigt: bool = False


class Board(BaseModel):
    id: str
    mappe_id: str
    titel: str
    kuerzel: str | None = None
    spalten: list[Spalte] = Field(default_factory=list)


class BoardDetail(Board):
    karten: list[Karte] = Field(default_factory=list)


class Projektmappe(BaseModel):
    id: str
    titel: str
    beschreibung: str | None = None


class MappeCreate(BaseModel):
    titel: str
    beschreibung: str | None = None


class MappeUpdate(BaseModel):
    titel: str | None = None
    beschreibung: str | None = None


KontextTyp = Literal["karte", "mappe"]


class Dokument(BaseModel):
    id: str
    kontext: KontextTyp
    kontext_id: str
    titel: str
    inhalt: str = ""
    erstellt_am: str | None = None
    bewegt_am: str | None = None


class DokumentCreate(BaseModel):
    kontext: KontextTyp
    kontext_id: str
    titel: str


class DokumentUpdate(BaseModel):
    titel: str | None = None
    inhalt: str | None = None


class SchnellErfassen(BaseModel):
    text: str
    dry_run: bool = False


class KarteCreate(BaseModel):
    board_id: str
    spalte: str
    titel: str
    beschreibung: str | None = None
    labels: list[str] = Field(default_factory=list)
    prioritaet: Prioritaet | None = None
    cover: str | None = None
    start: date | None = None
    faellig: date | None = None
    zustaendig: str | None = None


class KarteUpdate(BaseModel):
    titel: str | None = None
    beschreibung: str | None = None
    notizen: str | None = None
    labels: list[str] | None = None
    prioritaet: Prioritaet | None = None
    checkliste: list[ChecklistPunkt] | None = None
    cover: str | None = None
    spalte: str | None = None
    reihenfolge: int | None = None
    start: date | None = None
    faellig: date | None = None
    zustaendig: str | None = None
    schaetzung_min: int | None = None
    transkript_id: str | None = None
    transkript_name: str | None = None


class KarteMove(BaseModel):
    spalte: str
    reihenfolge: int


class ErfasstSetzen(BaseModel):
    sekunden: int


class KommentarCreate(BaseModel):
    autor: str
    text: str


class SpalteCreate(BaseModel):
    titel: str
    wip_limit: int | None = None


class SpalteUpdate(BaseModel):
    titel: str | None = None
    wip_limit: int | None = None


class SpalteMove(BaseModel):
    richtung: int


class SpaltenReihenfolge(BaseModel):
    spalten: list[str]


class BoardCreate(BaseModel):
    titel: str


class BoardUpdate(BaseModel):
    titel: str | None = None


class Zeiteintrag(BaseModel):
    id: str
    karte_id: str
    board_id: str | None = None
    mappe_id: str | None = None
    datum: str
    start: str | None = None
    ende: str | None = None
    sekunden: int
    kommentar: str | None = None
    manuell: bool = False
    karte_titel: str | None = None
    karte_schluessel: str | None = None


class ZeiteintragCreate(BaseModel):
    karte_id: str
    datum: str
    sekunden: int
    kommentar: str | None = None


class ZeiteintragUpdate(BaseModel):
    datum: str | None = None
    sekunden: int | None = None
    kommentar: str | None = None
