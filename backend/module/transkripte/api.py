"""HTTP-Schnittstelle der Transkriptions-Anbindung (lokale UI-Endpunkte).

Enthaelt neben der reinen Anzeige auch die Transkript-Marken: Verknuepfungen einer
Karte mit einer Stelle im Transkript samt editierbarer Zusammenfassung.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from . import dienst, marken

router = APIRouter(prefix="/api/transkripte", tags=["transkripte"])


class MarkeCreate(BaseModel):
    karte_id: str
    transkript_id: str
    transkript_name: str | None = None
    position_sek: float | None = None
    segment_text: str | None = None
    sprecher: str | None = None
    titel: str | None = None
    zusammenfassung: str | None = None


class MarkeUpdate(BaseModel):
    titel: str | None = None
    zusammenfassung: str | None = None
    position_sek: float | None = None
    segment_text: str | None = None
    sprecher: str | None = None


class VorschlagEingabe(BaseModel):
    transkript_id: str
    position_sek: float | None = None


@router.get("/status")
def status() -> dict:
    return {"erreichbar": dienst.erreichbar(), "konfiguriert": dienst.verfuegbar()}


@router.get("/suche")
def suche(q: str = Query(default=""), limit: int = Query(default=30)) -> dict:
    if not dienst.verfuegbar():
        raise HTTPException(status_code=503, detail="Transkriptionen nicht konfiguriert")
    return {"treffer": dienst.suche(q, max(1, min(limit, 100)))}


# -- Transkript-Marken (Karte <-> Transkript-Stelle) ----------------------
# WICHTIG: vor der Catch-all-Route /{tid} definieren, sonst faengt diese "marken".

@router.get("/marken")
def marken_liste(karte_id: str = Query(...)) -> dict:
    return {"marken": marken.liste(karte_id)}


@router.post("/marken", status_code=201)
def marke_anlegen(eingabe: MarkeCreate) -> dict:
    return marken.erstelle(eingabe.model_dump())


@router.patch("/marken/{mid}")
def marke_aendern(mid: str, eingabe: MarkeUpdate) -> dict:
    m = marken.aktualisiere(mid, eingabe.model_dump(exclude_unset=True))
    if m is None:
        raise HTTPException(status_code=404, detail="Marke nicht gefunden")
    return m


@router.delete("/marken/{mid}", status_code=204)
def marke_loeschen(mid: str) -> None:
    marken.loesche(mid)


@router.post("/zusammenfassung-vorschlag")
def zusammenfassung_vorschlag(eingabe: VorschlagEingabe) -> dict:
    txt = dienst.zusammenfassung_vorschlag(eingabe.transkript_id, eingabe.position_sek)
    if txt is None:
        raise HTTPException(status_code=503, detail="KI-Vorschlag nicht verfuegbar (kein Chat-Modell geladen)")
    return {"zusammenfassung": txt}


@router.get("/{tid}/marken")
def marken_je_transkript(tid: str) -> dict:
    return {"marken": marken.je_transkript(tid)}


@router.get("/{tid}")
def detail(tid: str) -> dict:
    d = dienst.detail(tid)
    if d is None:
        raise HTTPException(status_code=404, detail="Transkription nicht gefunden")
    return d
