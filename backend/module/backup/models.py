"""Datenmodelle der Sicherung. Spiegeln die Felder im Frontend (types).

Ein Snapshot ist eine in sich geschlossene ZIP-Datei mit der Datenbank, dem
Berichts-Archiv, einer Kopie der Konfigurationsvorlage und einem Manifest, das
Version, Schema und Datensatz-Zähler festhält.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SnapshotInfo(BaseModel):
    """Kurzbeschreibung eines Snapshots für die Liste."""

    id: str
    dateiname: str
    erstellt_am: str
    groesse: int
    version: str
    art: str  # "manuell" | "automatisch" | "vor_wiederherstellung"
    notiz: str = ""


class ErzeugeAnfrage(BaseModel):
    notiz: str = Field(default="", max_length=200)


class ResetAnfrage(BaseModel):
    modus: str = "beispiel"  # 'beispiel' = neu seeden, 'leer' = ohne Beispieldaten


class SchemaTabelle(BaseModel):
    tabelle: str
    spalten: list[str]


class Zustand(BaseModel):
    """Inhaltlicher Umfang: Version, Zähler je Tabelle, Anzahl Berichte."""

    version: str
    zaehler: dict[str, int]
    berichte: int


class Vorschau(BaseModel):
    """Was eine Wiederherstellung bedeuten würde: Snapshot gegen aktuellen Stand."""

    info: SnapshotInfo
    snapshot: Zustand
    aktuell: Zustand
    schema_: list[SchemaTabelle] = Field(default_factory=list, alias="schema")
    warnungen: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class WiederherstellenErgebnis(BaseModel):
    ok: bool
    vorher_gesichert: str  # id des automatischen Sicherheits-Snapshots
    wiederhergestellt: Zustand
