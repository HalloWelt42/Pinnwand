"""HTTP-Schnittstelle des Vorlese-Dienstes (lokale UI-Endpunkte)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from . import dienst

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TtsEingabe(BaseModel):
    text: str
    stimme: str | None = None


@router.get("/status")
def status() -> dict:
    return {"verfuegbar": dienst.erreichbar()}


@router.get("/stimmen")
def stimmen() -> dict:
    return {"stimmen": dienst.stimmen() or []}


@router.post("")
def vorlesen(eingabe: TtsEingabe) -> Response:
    audio = dienst.synthese(eingabe.text, eingabe.stimme)
    if audio is None:
        raise HTTPException(status_code=503, detail="Vorlesen nicht verfügbar (kein TTS-Dienst konfiguriert)")
    return Response(content=audio, media_type="audio/wav")
