"""Such-Dienst: hybride Suche und optionale Sprach-Transkription.

Hybrid = semantische Treffer (Vektor) plus Stichworttreffer, zusammengefuehrt.
Sind die KI-Dienste nicht verfuegbar, bleibt reine Stichwortsuche. Die
Sprach-Transkription leitet Audio an einen lokalen Whisper-Dienst weiter.
"""
from __future__ import annotations

import httpx

from app.config import einstellungen
from app.db import verbindung

from . import embeddings, vektor


def status() -> dict:
    semantisch = embeddings.verfuegbar() and vektor.verfuegbar()
    return {
        "embeddings": embeddings.verfuegbar(),
        "vektor_konfiguriert": vektor.verfuegbar(),
        "vektor_erreichbar": vektor.erreichbar() if vektor.verfuegbar() else False,
        "mikrofon": bool(einstellungen.stt_url),
        "modus": "hybrid" if semantisch else "stichwort",
    }


def _stichwort(q: str, limit: int) -> list[dict]:
    muster = f"%{q}%"
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT id, board_id, spalte, schluessel, titel FROM karte "
            "WHERE titel LIKE ? OR beschreibung LIKE ? OR schluessel LIKE ? "
            "OR labels LIKE ? OR checkliste LIKE ? OR kommentare LIKE ? "
            "ORDER BY bewegt_am DESC LIMIT ?",
            (muster, muster, muster, muster, muster, muster, limit),
        ).fetchall()
    return [
        {"karte_id": r["id"], "schluessel": r["schluessel"], "titel": r["titel"],
         "board_id": r["board_id"], "spalte": r["spalte"], "quelle": "stichwort"}
        for r in rows
    ]


def suche(q: str, limit: int = 15) -> dict:
    q = (q or "").strip()
    semantisch_aktiv = embeddings.verfuegbar() and vektor.verfuegbar()
    if not q:
        return {"treffer": [], "anzahl": 0, "modus": "hybrid" if semantisch_aktiv else "stichwort"}

    treffer: dict[str, dict] = {}
    if semantisch_aktiv:
        eingebettet = embeddings.einbetten([q])
        if eingebettet is not None:
            vektoren, _ = eingebettet
            for t in vektor.suche(vektoren[0], limit):
                p = t["payload"]
                kid = p.get("karte_id")
                if kid:
                    treffer[kid] = {
                        "karte_id": kid, "schluessel": p.get("schluessel"), "titel": p.get("titel"),
                        "board_id": p.get("board_id"), "score": round(float(t["score"]), 3),
                        "quelle": "semantisch",
                    }
    for r in _stichwort(q, limit):
        treffer.setdefault(r["karte_id"], r)

    liste = list(treffer.values())[:limit]
    return {"treffer": liste, "anzahl": len(liste), "modus": "hybrid" if semantisch_aktiv else "stichwort"}


def transkribiere(audio: bytes, dateiname: str = "aufnahme.webm") -> dict | None:
    """Leitet Audio an einen lokalen Whisper-Dienst weiter. None, wenn nicht konfiguriert/fehlerhaft."""
    if not einstellungen.stt_url or not audio:
        return None
    ziel = einstellungen.stt_url.rstrip("/")
    if not ziel.endswith(("/transcribe", "/transcribe_file")):
        ziel += "/transcribe_file"
    try:
        r = httpx.post(ziel, files={"file": (dateiname, audio)}, timeout=120.0)
        if r.status_code >= 400:
            return None
        daten = r.json()
        text = daten.get("text") or daten.get("full_text") or ""
        return {"text": text.strip()}
    except Exception:
        return None
