"""Embedding-Adapter (optional).

Spricht einen OpenAI-kompatiblen Endpunkt (z.B. lokaler Modell-Host) an. Ohne
Konfiguration oder bei Ausfall liefert er None - die Suche faellt dann auf
Stichwortsuche zurueck. KI bleibt optional.
"""
from __future__ import annotations

import httpx

from app.config import einstellungen

_modell_cache: str | None = None


def verfuegbar() -> bool:
    return bool(einstellungen.llm_url)


def _ermittle_modell() -> str | None:
    global _modell_cache
    if _modell_cache:
        return _modell_cache
    if einstellungen.embedding_model:
        _modell_cache = einstellungen.embedding_model
        return _modell_cache
    try:
        r = httpx.get(einstellungen.llm_url.rstrip("/") + "/v1/models", timeout=3.0)
        modelle = [m.get("id", "") for m in r.json().get("data", [])]
        treffer = next((m for m in modelle if "embed" in m.lower()), None) or (modelle[0] if modelle else None)
        _modell_cache = treffer
        return treffer
    except Exception:
        return None


def einbetten(texte: list[str]) -> tuple[list[list[float]], str] | None:
    """Bettet Texte ein. Gibt (Vektoren, Modellname) zurueck oder None."""
    if not einstellungen.llm_url or not texte:
        return None
    modell = _ermittle_modell()
    if not modell:
        return None
    try:
        r = httpx.post(
            einstellungen.llm_url.rstrip("/") + "/v1/embeddings",
            json={"model": modell, "input": texte},
            timeout=60.0,
        )
        if r.status_code >= 400:
            return None
        daten = r.json().get("data", [])
        vektoren = [d["embedding"] for d in daten]
        if len(vektoren) != len(texte):
            return None
        return vektoren, modell
    except Exception:
        return None
