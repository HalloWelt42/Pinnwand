"""HTTP-Schnittstelle der Suche.

Lokale UI-Endpunkte (ohne Token, wie der Kanban-Kern). Die semantische Suche
ist optional; ohne KI-Dienste liefert /api/suche Stichworttreffer.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, UploadFile

from . import dienst, indexer

router = APIRouter(prefix="/api/suche", tags=["suche"])


@router.get("")
def suchen(q: str = Query(default=""), limit: int = Query(default=15)) -> dict:
    return dienst.suche(q, max(1, min(limit, 50)))


@router.get("/status")
def status() -> dict:
    return dienst.status()


@router.post("/reindex")
def reindex() -> dict:
    return indexer.reindex()


@router.post("/sprache")
async def sprache(datei: UploadFile) -> dict:
    """Wandelt eine Audioaufnahme in Text (lokaler Whisper-Dienst). 503, wenn nicht verfuegbar."""
    audio = await datei.read()
    ergebnis = dienst.transkribiere(audio, datei.filename or "aufnahme.webm")
    if ergebnis is None:
        raise HTTPException(status_code=503, detail="Spracheingabe nicht verfuegbar (kein Whisper-Dienst konfiguriert)")
    return ergebnis
