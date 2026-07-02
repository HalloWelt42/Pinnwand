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
KartenTyp = Literal["arbeit", "idee"]


class ChecklistPunkt(BaseModel):
    text: str
    erledigt: bool = False


class GruppenMitglied(BaseModel):
    """Eine andere Karte derselben Verknuepfungs-/Zeitgruppe (zur Anzeige)."""
    id: str
    schluessel: str | None = None
    titel: str


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
    # Abschlussdatum (YYYY-MM-DD) fuer den Fertig-Zeitfilter: bei Serien-/REKO-Karten
    # das feste geplante Datum (faellig), sonst der Erledigt-Zeitpunkt (bewegt_am).
    # Die erfassten Zeiten (zeiteintrag) spielen hier bewusst keine Rolle.
    abschluss_am: str | None = None
    # Karten-Typ: "arbeit" (mit Zeiterfassung) oder "idee" (Notiz, keine Zeiten, kein Play).
    typ: KartenTyp = "arbeit"
    # Verknuepfungs-/Zeitgruppe: Karten mit gleicher gruppe_id gehoeren zusammen.
    gruppe_id: str | None = None
    # Berechnet (board_detail): kombinierte Zeit der Gruppe, wenn die Gruppe die Zeit
    # teilt; sonst die eigene erfasst_sek. None, wenn die Karte in keiner Gruppe ist.
    gruppe_sek: int | None = None
    # Berechnet (board_detail): die anderen Karten der Gruppe.
    gruppe_mitglieder: list[GruppenMitglied] = Field(default_factory=list)
    # Berechnet (board_detail): teilt die Gruppe die Zeit (Spezialfall abschaltbar)?
    gruppe_zeit_geteilt: bool = True


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


class KartenSeite(BaseModel):
    """Eine gefensterte Seite Karten (fertige Spalte oder Archiv) mit Nachlade-Info."""
    karten: list[Karte] = Field(default_factory=list)
    gesamt: int = 0
    hat_mehr: bool = False


class KanbanEinstellungen(BaseModel):
    """Anzeige-/Ladegrenzen und Karten-Alterung - in der UI einstellbar."""
    fertig_seitengroesse: int = 50
    archiv_tage: int = 365
    aging_amber_tage: int = 4  # Verweildauer-Badge amber ab X Tagen (0 = aus)
    aging_rot_tage: int = 8    # rot ab Y Tagen (0 = aus)


class KanbanEinstellungenUpdate(BaseModel):
    fertig_seitengroesse: int = Field(ge=1, le=500)
    archiv_tage: int = Field(ge=1, le=100000)
    aging_amber_tage: int = Field(default=4, ge=0, le=365)
    aging_rot_tage: int = Field(default=8, ge=0, le=365)


# Eine Mappe ist zugleich ein Projekt (Board = Phase). Der Status steuert nur die
# Darstellung/Auswertung, nicht die Sichtbarkeit (die haengt an der Mitgliedschaft).
ProjektStatus = Literal["aktiv", "pausiert", "abgeschlossen"]


class Projektmappe(BaseModel):
    id: str
    titel: str
    beschreibung: str | None = None
    owner: str | None = None
    budget_min: int | None = None
    status: ProjektStatus = "aktiv"


class MappeCreate(BaseModel):
    titel: str
    beschreibung: str | None = None


class MappeUpdate(BaseModel):
    titel: str | None = None
    beschreibung: str | None = None
    owner: str | None = None
    budget_min: int | None = None
    status: ProjektStatus | None = None


class ProjektAufwand(BaseModel):
    """Aufwand je Projekt (Mappe). Ist = tatsaechlich erfasste Zeit (Sekunden, aus
    zeiteintrag als SSOT), Soll = Summe der Karten-Schaetzungen (Minuten), Budget =
    optionale Planungsobergrenze (Minuten). Ist/Soll/Budget bleiben bewusst getrennt."""
    mappe_id: str
    titel: str
    status: ProjektStatus = "aktiv"
    owner: str | None = None
    budget_min: int | None = None
    ist_sekunden: int = 0
    soll_minuten: int = 0
    karten: int = 0
    boards: int = 0


class ProjektBoardAufwand(BaseModel):
    board_id: str
    titel: str
    ist_sekunden: int = 0
    soll_minuten: int = 0
    karten: int = 0


class ProjektPersonAufwand(BaseModel):
    kuerzel: str | None = None
    ist_sekunden: int = 0


class ProjektDetail(BaseModel):
    mappe_id: str
    titel: str
    status: ProjektStatus = "aktiv"
    owner: str | None = None
    budget_min: int | None = None
    ist_sekunden: int = 0
    soll_minuten: int = 0
    boards: list[ProjektBoardAufwand] = []
    personen: list[ProjektPersonAufwand] = []


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
    typ: KartenTyp = "arbeit"


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
    typ: KartenTyp | None = None


class KarteVerknuepfen(BaseModel):
    ziel_karte_id: str


class GruppeUpdate(BaseModel):
    zeit_geteilt: bool


class KarteMove(BaseModel):
    spalte: str
    reihenfolge: int


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


# -- Label-Definitionen (zentrale Farbe je Label-Name) --------------------
# karte.labels bleibt eine Liste freier Namens-Strings; diese Definition liefert
# nur die zugewiesene Material-Farbe und die Verwaltung. Namen ohne Definition
# färbt das Frontend weiter über den Hash-Fallback (labels.ts).
class LabelDefinition(BaseModel):
    id: str
    name: str
    familie: str


class LabelCreate(BaseModel):
    name: str
    familie: str


class LabelUpdate(BaseModel):
    name: str | None = None
    familie: str | None = None


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
    kuerzel: str | None = None  # Person des Eintrags (Snapshot beim Buchen)
    karte_titel: str | None = None
    karte_schluessel: str | None = None
    karte_zustaendig: str | None = None


class ZeiteintragCreate(BaseModel):
    karte_id: str
    datum: str
    sekunden: int
    kommentar: str | None = None


class TicketzeitSetzen(BaseModel):
    sekunden: int = Field(ge=0)


class ZeiteintragUpdate(BaseModel):
    datum: str | None = None
    sekunden: int | None = None
    kommentar: str | None = None


class HeuteEintrag(BaseModel):
    """Eine Karte in der handlungsorientierten Heute-Uebersicht (knappe Felder)."""

    id: str
    board_id: str
    schluessel: str | None = None
    titel: str
    faellig: str | None = None


class HeuteUebersicht(BaseModel):
    datum: str
    ueberfaellig: list[HeuteEintrag] = []
    heute: list[HeuteEintrag] = []
    diese_woche: list[HeuteEintrag] = []
    laufend: list[HeuteEintrag] = []
    liegengeblieben: list[HeuteEintrag] = []
