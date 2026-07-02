"""HTTP-Schnittstelle der Suche.

Lokale UI-Endpunkte (ohne Token, wie der Kanban-Kern). Die semantische Suche
ist optional; ohne KI-Dienste liefert /api/suche Stichworttreffer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from module.auth.akteur import Akteur, aktueller_akteur
from module.kanban_kern import persistence as kdb

from . import dienst, indexer

router = APIRouter(prefix="/api/suche", tags=["suche"])


@router.get("")
def suchen(q: str = Query(default=""), limit: int = Query(default=15),
           akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    ergebnis = dienst.suche(q, max(1, min(limit, 50)))
    # Projekt-Scoping: Treffer aus unsichtbaren Mappen fuer Nicht-Admins ausblenden.
    if not akteur.ist_admin:
        sichtbar = kdb.sichtbare_mappen_ids(akteur.person_id)
        treffer = [tr for tr in ergebnis.get("treffer", [])
                   if kdb.karte_mappe_id(tr.get("karte_id") if isinstance(tr, dict) else tr.karte_id) in sichtbar]
        ergebnis = {**ergebnis, "treffer": treffer, "anzahl": len(treffer)}
    return ergebnis


@router.get("/status")
def status() -> dict:
    return dienst.status()


@router.post("/reindex")
def reindex() -> dict:
    return indexer.reindex()


_MAX_AUDIO = 25 * 1024 * 1024  # 25 MB reichen für kurze Sprachaufnahmen.


@router.post("/sprache")
async def sprache(datei: UploadFile) -> dict:
    """Wandelt eine Audioaufnahme in Text (lokaler Whisper-Dienst). 503, wenn nicht verfügbar."""
    # Begrenzt einlesen, damit eine große Datei nicht den Speicher füllt.
    audio = await datei.read(_MAX_AUDIO + 1)
    if len(audio) > _MAX_AUDIO:
        raise HTTPException(status_code=413, detail="Audiodatei zu groß (max. 25 MB)")
    ergebnis = dienst.transkribiere(audio, datei.filename or "aufnahme.webm")
    if ergebnis is None:
        raise HTTPException(status_code=503, detail="Spracheingabe nicht verfügbar (kein Whisper-Dienst konfiguriert)")
    return ergebnis
