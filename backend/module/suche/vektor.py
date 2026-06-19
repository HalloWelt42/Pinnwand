"""Vektor-Speicher-Adapter (optional) ueber die Qdrant-REST-API.

Bewusst ohne zusaetzliche Client-Bibliothek - reines HTTP. Ohne konfigurierte
oder erreichbare Qdrant-Instanz liefern alle Funktionen leere/negative Ergebnisse,
sodass die Suche sauber auf Stichwortsuche zurueckfaellt.
"""
from __future__ import annotations

import httpx

from app.config import einstellungen

COLLECTION = "pinnwand_karten"


def _basis() -> str | None:
    return einstellungen.qdrant_url.rstrip("/") if einstellungen.qdrant_url else None


def verfuegbar() -> bool:
    return bool(einstellungen.qdrant_url)


def erreichbar() -> bool:
    basis = _basis()
    if not basis:
        return False
    try:
        return httpx.get(basis + "/collections", timeout=2.0).status_code < 500
    except Exception:
        return False


def sicherstellen_collection(dim: int, name: str = COLLECTION) -> bool:
    basis = _basis()
    if not basis:
        return False
    try:
        vorhanden = httpx.get(f"{basis}/collections/{name}", timeout=3.0)
        if vorhanden.status_code == 200:
            return True
        r = httpx.put(
            f"{basis}/collections/{name}",
            json={"vectors": {"size": dim, "distance": "Cosine"}},
            timeout=10.0,
        )
        return r.status_code < 400
    except Exception:
        return False


def upsert(punkte: list[dict], name: str = COLLECTION) -> bool:
    """punkte: [{id, vector, payload}]."""
    basis = _basis()
    if not basis or not punkte:
        return False
    try:
        r = httpx.put(f"{basis}/collections/{name}/points", json={"points": punkte}, timeout=30.0)
        return r.status_code < 400
    except Exception:
        return False


def suche(vektor: list[float], limit: int = 10, name: str = COLLECTION) -> list[dict]:
    """Gibt Treffer als [{score, payload}] zurueck, leer bei Ausfall."""
    basis = _basis()
    if not basis:
        return []
    try:
        r = httpx.post(
            f"{basis}/collections/{name}/points/search",
            json={"vector": vektor, "limit": limit, "with_payload": True},
            timeout=10.0,
        )
        if r.status_code >= 400:
            return []
        return [{"score": t.get("score", 0.0), "payload": t.get("payload", {})} for t in r.json().get("result", [])]
    except Exception:
        return []
