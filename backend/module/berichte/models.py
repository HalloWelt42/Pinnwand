"""Datenverträge für Berichte."""
from __future__ import annotations

from pydantic import BaseModel


class BerichtAnfrage(BaseModel):
    typ: str
    format: str = "pdf"  # pdf | csv | markdown
    von: str | None = None
    bis: str | None = None
    person: str | None = None  # Kürzel (zustaendig)
    board_id: str | None = None
    archivieren: bool = False


class BerichtTyp(BaseModel):
    id: str
    titel: str


class TypenAntwort(BaseModel):
    typen: list[BerichtTyp]


class ArchivEintrag(BaseModel):
    """Ein archivierter Bericht (Metadaten; die Datei liegt separat)."""

    id: str
    typ: str
    titel: str
    zeitraum: str
    format: str
    person: str | None = None
    erstellt_am: str
    groesse: int
