"""Anbindung an die Transkription (eigene App auf dem Pi), optional.

Suche, Liste und Einzelabruf gehen an `GET /api/v1/transkripte` der Transkription, angemeldet mit dem App-Schlüssel
der Kellerwolke (Zugang "Pinnwand", `PINNWAND_TRANSCRIPTS_SCHLUESSEL`). Die Suche macht die Transkription selbst
(wörtlich, mit Fundstellen und Zeit); Pinnwand dünnt nur aus. Den Ton reicht Pinnwand durch (`/api/transkripte/<id>/ton`),
weil der Browser den Schlüssel nicht kennt. Ohne erreichbaren Dienst liefert alles leere Ergebnisse - die Ansicht
zeigt dann einen Hinweis.
"""
from __future__ import annotations

import time
from collections.abc import Iterator

import httpx

from app.config import einstellungen

_cache: dict = {"zeit": 0.0, "daten": []}
_TTL = 30.0
_SEITE = 100                 # mehr gibt die Transkription je Abruf nicht heraus
_HOECHSTENS = 2000           # so viele Transkripte zeigt die Liste


def _basis() -> str | None:
    return einstellungen.transcripts_url.rstrip("/") if einstellungen.transcripts_url else None


def verfuegbar() -> bool:
    return bool(einstellungen.transcripts_url and einstellungen.transcripts_schluessel)


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(base_url=_basis() or "", timeout=timeout, verify=einstellungen.transcripts_ca or True,
                        headers={"Authorization": f"Bearer {einstellungen.transcripts_schluessel}"})


def erreichbar() -> bool:
    if not verfuegbar():
        return False
    try:
        with _client(3.0) as c:
            return c.get("/api/v1/transkripte", params={"anzahl": 1}).status_code < 400
    except Exception:
        return False


def _leicht(e: dict) -> dict:
    """Ein Eintrag der Transkription in der Form, die Pinnwand zeigt."""
    return {
        "id": str(e.get("id")),
        "name": e.get("name") or "",
        "language": e.get("sprache") or "",
        "full_text": "",
        "speaker_names": e.get("sprecher") or [],
        "segment_count": e.get("segmente"),
        "status": "fertig",
    }


def _seiten(params: dict, bis: int) -> Iterator[dict]:
    """Einträge der Transkription seitenweise, höchstens `bis`."""
    ab = 0
    with _client(25.0) as c:
        while ab < bis:
            r = c.get("/api/v1/transkripte", params={**params, "ab": ab, "anzahl": min(_SEITE, bis - ab)})
            if r.status_code >= 400:
                return
            seite = r.json()
            eintraege = seite.get("eintraege") or []
            yield from eintraege
            ab += len(eintraege)
            if not eintraege or ab >= seite.get("gesamt", 0):
                return


def _liste() -> list[dict]:
    if not verfuegbar():
        return []
    jetzt = time.monotonic()
    if _cache["daten"] and (jetzt - _cache["zeit"]) < _TTL:
        return _cache["daten"]
    try:
        leicht = [_leicht(e) for e in _seiten({}, _HOECHSTENS) if e.get("id")]
    except Exception:
        leicht = []
    _cache.update(zeit=jetzt, daten=leicht)
    return leicht


def suche(q: str, limit: int = 30) -> list[dict]:
    q = (q or "").strip()
    if not q:
        return [{"id": t["id"], "name": t["name"], "snippet": "", "speaker_names": t["speaker_names"],
                 "language": t["language"], "start": None} for t in _liste()[:limit]]
    if not verfuegbar():
        return []
    try:
        treffer = list(_seiten({"suche": q}, limit))
    except Exception:
        return []
    out: list[dict] = []
    for e in treffer:
        fund = (e.get("fundstellen") or [None])[0] or {}
        out.append({"id": str(e["id"]), "name": e.get("name") or "", "snippet": fund.get("ausschnitt") or "",
                    "speaker_names": e.get("sprecher") or [], "language": e.get("sprache") or "",
                    "start": fund.get("zeit")})
    return out


def detail(tid: str) -> dict | None:
    if not verfuegbar():
        return None
    try:
        with _client(25.0) as c:
            r = c.get(f"/api/v1/transkripte/{tid}")
        if r.status_code >= 400:
            return None
        t = r.json()["transkript"]
    except Exception:
        return None
    namen = {s["kennung"]: s.get("name") or s["kennung"] for s in t.get("sprecher") or []}
    segmente = [{"start": round(float(s.get("start") or 0), 2), "text": (s.get("text") or "").strip(),
                 "speaker": namen.get(s.get("sprecher"), s.get("sprecher"))}
                for s in t.get("segmente") or [] if (s.get("text") or "").strip()]
    return {
        "id": tid,
        "name": t.get("name") or "",
        "language": t.get("sprache") or "",
        "full_text": " ".join(s["text"] for s in segmente),
        "speaker_names": [n for n in namen.values()],
        "segment_count": len(segmente),
        "status": "fertig",
        "audio_url": f"/api/transkripte/{tid}/ton",
        "segmente": segmente,
    }


def ton_oeffnen(tid: str, bereich: str | None) -> tuple[httpx.Client, httpx.Response] | None:
    """Öffnet den Ton (Abspielfassung) bei der Transkription als Strom; der Aufrufer schließt beides."""
    if not verfuegbar():
        return None
    c = _client(60.0)
    kopf = {"Range": bereich} if bereich else {}
    r = c.send(c.build_request("GET", f"/api/v1/inhalt/transkripte/{tid}/ton", headers=kopf), stream=True)
    if r.status_code >= 400:
        r.close()
        c.close()
        return None
    return c, r


def _chat_modell() -> str | None:
    """Erstes geladenes Nicht-Embedding-Modell von LM Studio (JIT laedt nur geladene)."""
    base = einstellungen.llm_url
    if not base:
        return None
    try:
        r = httpx.get(base.rstrip("/") + "/v1/models", timeout=3.0)
        modelle = [m.get("id", "") for m in r.json().get("data", [])]
    except Exception:
        return None

    def _ist_text(m: str) -> bool:
        s = m.lower()
        # Embedding-, Bild-, Vision- und Audio-Modelle taugen nicht zum Zusammenfassen.
        return bool(m) and not any(
            x in s for x in ("embed", "image", "edit", "vl-", "-vl", "vision", "flux", "stable", "whisper", "tts")
        )

    kandidaten = [m for m in modelle if _ist_text(m)]
    if not kandidaten:
        return None
    # Echte Instruct-/Chat-Modelle bevorzugen (Vision-/Flash-Varianten meiden).
    return next((m for m in kandidaten if "instruct" in m.lower() or "chat" in m.lower()), kandidaten[0])


def zusammenfassung_vorschlag(transkript_id: str, position_sek: float | None) -> str | None:
    """Erzeugt aus dem Abschnitt ab der Position einen Zusammenfassungs-Vorschlag
    (nur Vorschau, wird nicht gespeichert). None, wenn kein Chat-Modell verfuegbar."""
    base = einstellungen.llm_url
    if not base:
        return None
    d = detail(transkript_id)
    if not d:
        return None
    segmente = d.get("segmente") or []
    if position_sek is not None and segmente:
        idx = min(range(len(segmente)), key=lambda i: abs((segmente[i].get("start") or 0) - position_sek))
        abschnitt = segmente[idx: idx + 8]
        text = " ".join(s.get("text", "") for s in abschnitt)
    else:
        text = d.get("full_text") or " ".join(s.get("text", "") for s in segmente)
    text = (text or "").strip()[:4000]
    if not text:
        return None
    modell = _chat_modell()
    if not modell:
        return None
    try:
        r = httpx.post(
            base.rstrip("/") + "/v1/chat/completions",
            json={
                "model": modell,
                "messages": [
                    {"role": "system", "content": "Du fasst Transkript-Abschnitte praegnant auf Deutsch zusammen."},
                    {"role": "user", "content": "Fasse den folgenden Transkript-Abschnitt in 1 bis 3 Saetzen auf Deutsch zusammen. Gib nur die Zusammenfassung aus, ohne Einleitung:\n\n" + text},
                ],
                "temperature": 0.3,
                "max_tokens": 220,
            },
            timeout=120.0,
        )
        if r.status_code >= 400:
            return None
        return (r.json()["choices"][0]["message"]["content"] or "").strip() or None
    except Exception:
        return None
