"""HTTP-Schnittstelle der Serien (wiederkehrende Termine/Aufgaben)."""
from __future__ import annotations

from datetime import date, timedelta

from module.auth.akteur import Akteur, aktueller_akteur
from module.auth.rechte import darf_zeiteintrag_bearbeiten, verlange
from module.kanban_kern import persistence as k
from fastapi import APIRouter, Depends, HTTPException, Query

from . import dienst, wiederholung
from . import persistence as db
from .models import NachtragEingabe, Serie, SerieCreate, SerienNachtrag, SerieUpdate

router = APIRouter(prefix="/api/serien", tags=["serien"])


@router.get("/nachtraege", response_model=list[SerienNachtrag])
def nachtraege() -> list[SerienNachtrag]:
    """Ignorierte Serien-Karten vergangener Tage (nicht erfasst, nicht erledigt)."""
    return dienst.offene_nachtraege()


@router.post("/nachtraege/{karte_id}")
def nachtragen(karte_id: str, eingabe: NachtragEingabe, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    """Traegt die Stunden einer ignorierten Serien-Karte nach und erledigt sie."""
    vorhanden = k.hole_karte(karte_id)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, vorhanden.zustaendig), "Nur eigene Serien-Karten nachtragen.")
    karte = dienst.nachtragen(karte_id, eingabe.dauer_min)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte.model_dump() if hasattr(karte, "model_dump") else karte


@router.get("", response_model=list[Serie])
def liste(board_id: str | None = Query(default=None)) -> list[dict]:
    return db.liste(board_id)


@router.post("", response_model=Serie, status_code=201)
def anlegen(eingabe: SerieCreate) -> dict:
    serie = db.erstelle(eingabe.model_dump())
    dienst.materialisiere(serie)
    return serie


@router.patch("/{sid}", response_model=Serie)
def aendern(sid: str, eingabe: SerieUpdate) -> dict:
    serie = db.aktualisiere(sid, eingabe.model_dump(exclude_unset=True))
    if serie is None:
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")
    dienst.materialisiere(serie)
    return serie


@router.delete("/{sid}", status_code=204)
def loeschen(sid: str) -> None:
    if not dienst.loesche(sid):
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")


@router.get("/{sid}/vorschau")
def vorschau(sid: str, tage: int = Query(default=30)) -> dict:
    serie = db.hole(sid)
    if serie is None:
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")
    heute = date.today()
    bis = heute + timedelta(days=max(1, min(tage, 365)))
    feiertage = dienst._feiertage(heute, bis) if serie.feiertage_ueberspringen else None
    termine = wiederholung.termine(serie, heute, bis, feiertage)
    return {"termine": [d.isoformat() for d in termine]}


@router.post("/{sid}/vorbuchen")
def vorbuchen(sid: str) -> dict:
    serie = db.hole(sid)
    if serie is None:
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")
    return {"erzeugt": dienst.materialisiere(serie)}


@router.post("/vorbuchen")
def vorbuchen_alle() -> dict:
    return {"erzeugt": dienst.materialisiere_alle()}
