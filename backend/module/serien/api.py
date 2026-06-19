"""HTTP-Schnittstelle der Serien (wiederkehrende Termine/Aufgaben)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from . import dienst, wiederholung
from . import persistence as db
from .models import Serie, SerieCreate, SerieUpdate

router = APIRouter(prefix="/api/serien", tags=["serien"])


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
    if not db.loesche(sid):
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")


@router.get("/{sid}/vorschau")
def vorschau(sid: str, tage: int = Query(default=30)) -> dict:
    serie = db.hole(sid)
    if serie is None:
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")
    heute = date.today()
    termine = wiederholung.termine(serie, heute, heute + timedelta(days=max(1, min(tage, 365))))
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
