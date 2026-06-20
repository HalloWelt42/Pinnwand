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
