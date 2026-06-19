"""Vorlese-Dienst (optional): Proxy zu einem lokalen TTS-Dienst.

Holt vom TTS-Dienst einen rohen PCM-Strom (16-Bit, mono, 24 kHz) und verpackt
ihn in eine WAV-Datei, damit der Browser ihn direkt abspielen kann. Ohne
konfigurierten Dienst liefert alles None - die Oberflaeche nutzt dann die
Browser-Sprachausgabe oder blendet das Vorlesen aus.
"""
from __future__ import annotations

import struct

import httpx

from app.config import einstellungen

_RATE = 24000
_KANAELE = 1
_BITS = 16


def verfuegbar() -> bool:
    return bool(einstellungen.tts_url)


def _wav(pcm: bytes) -> bytes:
    byte_rate = _RATE * _KANAELE * _BITS // 8
    block_align = _KANAELE * _BITS // 8
    kopf = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    kopf += b"fmt " + struct.pack("<IHHIIHH", 16, 1, _KANAELE, _RATE, byte_rate, block_align, _BITS)
    kopf += b"data" + struct.pack("<I", len(pcm))
    return kopf + pcm


def synthese(text: str, stimme: str | None = None) -> bytes | None:
    """Erzeugt WAV-Audio aus Text. None, wenn kein Dienst konfiguriert oder bei Fehler."""
    if not einstellungen.tts_url or not text.strip():
        return None
    rumpf: dict = {"text": text}
    if stimme:
        rumpf["voice"] = stimme
    try:
        r = httpx.post(einstellungen.tts_url.rstrip("/") + "/synthesize", json=rumpf, timeout=120.0)
        if r.status_code >= 400 or not r.content:
            return None
        return _wav(r.content)
    except Exception:
        return None


def stimmen() -> list | None:
    if not einstellungen.tts_url:
        return None
    try:
        r = httpx.get(einstellungen.tts_url.rstrip("/") + "/voices", timeout=5.0)
        return r.json() if r.status_code < 400 else None
    except Exception:
        return None
