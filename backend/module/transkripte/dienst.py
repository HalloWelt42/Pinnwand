"""Anbindung an den Transkriptions-Dienst (txt2voice), optional.

Holt die Transkriptions-Liste, dünnt sie aus (Embeddings und Roh-Segmente raus)
und durchsucht sie zuverlässig in Pinnwand (Wort/Phrase, mit Trefferausschnitt).
Das Original-Audio spielt der Browser direkt vom Dienst. Ohne erreichbaren Dienst
liefert alles leere Ergebnisse - die Ansicht zeigt dann einen Hinweis.
"""
from __future__ import annotations

import json
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


def _basisname(name: str) -> str:
    """Dateiname ohne Endung, normalisiert (Join FTS-Titel <-> Transkript-Name)."""
    return (name or "").rsplit(".", 1)[0].strip().lower()


def _ohne_mark(s: str) -> str:
    return (s or "").replace("<mark>", "").replace("</mark>", "")


def _fts(q: str, limit: int) -> list[dict] | None:
    """Volltextsuche ueber die FTS5-API des Dienstes (Trefferausschnitt + Segment-Zeitstempel).

    Gibt None zurueck, wenn der Dienst nicht erreichbar ist (dann lokaler Fallback).
    """
    b = _basis()
    if not b:
        return None
    try:
        r = httpx.get(b + "/api/search", params={"q": q, "limit": limit}, timeout=10.0)
        if r.status_code >= 400:
            return None
        treffer = r.json().get("results") or []
    except Exception:
        return None
    nach_name = {_basisname(t["name"]): t for t in _liste()}
    out: list[dict] = []
    for hit in treffer:
        titel = hit.get("title") or ""
        if not titel.lower().endswith(".transcript"):
            continue
        t = nach_name.get(_basisname(titel))
        if not t:
            continue
        segmente = hit.get("match_segments") or []
        start = segmente[0].get("start") if segmente and isinstance(segmente[0], dict) else None
        out.append({
            "id": t["id"], "name": t["name"], "snippet": _ohne_mark(hit.get("snippet") or ""),
            "speaker_names": t["speaker_names"], "language": t["language"],
            "start": float(start) if start is not None else None,
        })
        if len(out) >= limit:
            break
    return out


def suche(q: str, limit: int = 30) -> list[dict]:
    liste = _liste()
    q = (q or "").strip()
    if not q:
        return [
            {"id": t["id"], "name": t["name"], "snippet": t["full_text"][:140],
             "speaker_names": t["speaker_names"], "language": t["language"], "start": None}
            for t in liste[:limit]
        ]
    # Bevorzugt die FTS5-Suche des Dienstes; faellt bei Ausfall auf lokale Suche zurueck.
    ueber_fts = _fts(q, limit)
    if ueber_fts is not None:
        return ueber_fts
    ql = q.lower()
    out: list[dict] = []
    for t in liste:
        if ql in (t["name"] or "").lower() or ql in t["full_text"].lower():
            out.append({
                "id": t["id"], "name": t["name"], "snippet": _snippet(t["full_text"], q),
                "speaker_names": t["speaker_names"], "language": t["language"], "start": None,
            })
        if len(out) >= limit:
            break
    return out


def _segmente(roh: dict) -> list[dict]:
    """Normalisiert die Segmente eines Transkripts auf {start, text, speaker}."""
    rohsegmente = roh.get("segments") or roh.get("segmente") or []
    if isinstance(rohsegmente, str):
        # Manche Dienste liefern die Segmente als JSON-String.
        try:
            rohsegmente = json.loads(rohsegmente)
        except (ValueError, TypeError):
            return []
    if not isinstance(rohsegmente, list):
        return []
    out: list[dict] = []
    for s in rohsegmente:
        if not isinstance(s, dict):
            continue
        start = s.get("start", s.get("begin", s.get("start_time", s.get("offset", 0))))
        try:
            start_f = float(start or 0)
        except (TypeError, ValueError):
            start_f = 0.0
        text = (s.get("text") or s.get("content") or "").strip()
        if not text:
            continue
        out.append({"start": round(start_f, 2), "text": text, "speaker": s.get("speaker") or s.get("speaker_name")})
    return out


def detail(tid: str) -> dict | None:
    b = _basis()
    grund = next((t for t in _liste() if t["id"] == tid), None)
    if grund is None and b is None:
        return None
    audio = f"{b}/api/transcribe/{tid}/audio" if b else None
    segmente: list[dict] = []
    if b:
        # Volltext-Detail (inkl. Segmente) direkt vom Dienst holen.
        try:
            r = httpx.get(f"{b}/api/transcribe/{tid}", timeout=25.0)
            if r.status_code < 400:
                roh = r.json()
                segmente = _segmente(roh if isinstance(roh, dict) else {})
                if grund is None and isinstance(roh, dict):
                    grund = {
                        "id": tid, "name": roh.get("name"), "language": roh.get("language"),
                        "full_text": roh.get("full_text") or "", "speaker_names": roh.get("speaker_names") or [],
                        "segment_count": roh.get("segment_count"),
                    }
        except Exception:
            segmente = []
    if grund is None:
        return None
    return {**grund, "audio_url": audio, "segmente": segmente}
