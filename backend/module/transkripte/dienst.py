"""Anbindung an den Transkriptions-Dienst (txt2voice), optional.

Holt die Transkriptions-Liste, dünnt sie aus (Embeddings und Roh-Segmente raus)
und durchsucht sie zuverlässig in Pinnwand (Wort/Phrase, mit Trefferausschnitt).
Das Original-Audio spielt der Browser direkt vom Dienst. Ohne erreichbaren Dienst
liefert alles leere Ergebnisse - die Ansicht zeigt dann einen Hinweis.
"""
from __future__ import annotations

import time

import httpx

from app.config import einstellungen

_cache: dict = {"zeit": 0.0, "daten": []}
_TTL = 30.0


def _basis() -> str | None:
    return einstellungen.transcripts_url.rstrip("/") if einstellungen.transcripts_url else None


def verfuegbar() -> bool:
    return bool(einstellungen.transcripts_url)


def erreichbar() -> bool:
    b = _basis()
    if not b:
        return False
    try:
        return httpx.get(b + "/api/search/stats", timeout=2.0).status_code < 500
    except Exception:
        return False


def _liste() -> list[dict]:
    b = _basis()
    if not b:
        return []
    jetzt = time.monotonic()
    if _cache["daten"] and (jetzt - _cache["zeit"]) < _TTL:
        return _cache["daten"]
    try:
        r = httpx.get(b + "/api/transcribe", timeout=25.0)
        roh = r.json() if r.status_code < 400 else []
    except Exception:
        roh = []
    if not isinstance(roh, list):
        roh = roh.get("items", []) if isinstance(roh, dict) else []
    leicht = [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "language": t.get("language"),
            "full_text": t.get("full_text") or "",
            "speaker_names": t.get("speaker_names") or [],
            "segment_count": t.get("segment_count"),
            "status": t.get("status"),
        }
        for t in roh
        if t.get("id")
    ]
    _cache.update(zeit=jetzt, daten=leicht)
    return leicht


def _snippet(text: str, q: str, laenge: int = 180) -> str:
    i = text.lower().find(q.lower())
    if i < 0:
        return text[:laenge]
    a = max(0, i - 60)
    teil = text[a:a + laenge]
    return ("..." if a > 0 else "") + teil + ("..." if a + laenge < len(text) else "")


def suche(q: str, limit: int = 30) -> list[dict]:
    liste = _liste()
    q = (q or "").strip()
    if not q:
        return [
            {"id": t["id"], "name": t["name"], "snippet": t["full_text"][:140],
             "speaker_names": t["speaker_names"], "language": t["language"]}
            for t in liste[:limit]
        ]
    ql = q.lower()
    out: list[dict] = []
    for t in liste:
        if ql in (t["name"] or "").lower() or ql in t["full_text"].lower():
            out.append({
                "id": t["id"], "name": t["name"], "snippet": _snippet(t["full_text"], q),
                "speaker_names": t["speaker_names"], "language": t["language"],
            })
        if len(out) >= limit:
            break
    return out


def detail(tid: str) -> dict | None:
    for t in _liste():
        if t["id"] == tid:
            audio = None
            b = _basis()
            if b:
                audio = f"{b}/api/transcribe/{tid}/audio"
            return {**t, "audio_url": audio}
    return None
