"""HTTP-Schnittstelle der Transkriptions-Anbindung (lokale UI-Endpunkte)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from . import dienst

router = APIRouter(prefix="/api/transkripte", tags=["transkripte"])


@router.get("/status")
def status() -> dict:
    return {"erreichbar": dienst.erreichbar(), "konfiguriert": dienst.verfuegbar()}


@router.get("/suche")
def suche(q: str = Query(default=""), limit: int = Query(default=30)) -> dict:
    if not dienst.verfuegbar():
        raise HTTPException(status_code=503, detail="Transkriptionen nicht konfiguriert")
    return {"treffer": dienst.suche(q, max(1, min(limit, 100)))}


@router.get("/{tid}")
def detail(tid: str) -> dict:
    d = dienst.detail(tid)
    if d is None:
        raise HTTPException(status_code=404, detail="Transkription nicht gefunden")
    return d
