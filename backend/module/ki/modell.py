"""Generischer Zugang zum grossen lokalen Sprachmodell (LM Studio, OpenAI-kompatibel).

Das ist die eine zentrale Stelle, ueber die alle KI-Funktionen mit dem Modell
sprechen: ein einfacher Chat-Aufruf und ein Chat-Aufruf mit strukturierter
JSON-Antwort. Beide sind absichtlich fehlertolerant - bei jedem Problem (Dienst
aus, Timeout, kaputte Antwort) kommt None zurueck, nie eine Ausnahme. So bleibt
KI immer die optionale zweite Option und reisst nie den normalen Ablauf ab.
"""
from __future__ import annotations

import json
import re

import httpx

from app.config import einstellungen, erreichbar

# Modelle, die nicht zum Chatten/Strukturieren taugen (Embedding, Bild, Vision, Audio).
# Coder-Modelle meiden wir fuer deutsche Fachtexte ebenfalls, wenn es Alternativen gibt.
_UNGEEIGNET = ("embed", "image", "edit", "vl-", "-vl", "vision", "flux", "stable", "whisper", "tts")


def _geladene_modelle() -> list[str]:
    base = einstellungen.llm_url
    if not base:
        return []
    try:
        r = httpx.get(base.rstrip("/") + "/v1/models", timeout=3.0)
        return [m.get("id", "") for m in r.json().get("data", []) if m.get("id")]
    except Exception:
        return []


def _ist_text(modell: str) -> bool:
    s = modell.lower()
    return bool(modell) and not any(x in s for x in _UNGEEIGNET)


def waehle_modell() -> str | None:
    """Das zu nutzende Chat-Modell. Feste Vorgabe (PINNWAND_KI_MODELL) hat Vorrang;
    sonst automatische Auswahl unter den geladenen Modellen: echte Instruct-/Chat-
    Modelle bevorzugt, Coder-Modelle nachrangig."""
    if einstellungen.ki_modell:
        return einstellungen.ki_modell
    kandidaten = [m for m in _geladene_modelle() if _ist_text(m)]
    if not kandidaten:
        return None
    instruct = [m for m in kandidaten if "instruct" in m.lower() or "chat" in m.lower()]
    ohne_coder = [m for m in instruct if "coder" not in m.lower()] or instruct
    if ohne_coder:
        return ohne_coder[0]
    nicht_coder = [m for m in kandidaten if "coder" not in m.lower()] or kandidaten
    return nicht_coder[0]


def verfuegbar() -> bool:
    """True, wenn das LLM konfiguriert und erreichbar ist (mit kurzem Cache)."""
    return bool(einstellungen.llm_url) and erreichbar(einstellungen.llm_url, "/v1/models")


def status() -> dict:
    """Fuer die Oberflaeche: ob der Assistent nutzbar ist und welches Modell greift."""
    ok = verfuegbar()
    return {
        "verfuegbar": ok,
        "modell": (waehle_modell() if ok else None),
        "automatisch": not bool(einstellungen.ki_modell),
    }


def chat(
    system: str,
    nutzer: str,
    *,
    temperatur: float = 0.2,
    max_tokens: int = 800,
    timeout: float = 120.0,
) -> str | None:
    """Ein einfacher Chat-Aufruf. Gibt den Antworttext zurueck oder None bei Ausfall."""
    base = einstellungen.llm_url
    if not base:
        return None
    modell = waehle_modell()
    if not modell:
        return None
    try:
        r = httpx.post(
            base.rstrip("/") + "/v1/chat/completions",
            json={
                "model": modell,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": nutzer},
                ],
                "temperature": temperatur,
                "max_tokens": max_tokens,
                "stream": False,
            },
            timeout=timeout,
        )
        if r.status_code >= 400:
            return None
        return (r.json()["choices"][0]["message"]["content"] or "").strip() or None
    except Exception:
        return None


def chat_json(
    system: str,
    nutzer: str,
    *,
    temperatur: float = 0.1,
    max_tokens: int = 1200,
    timeout: float = 120.0,
) -> dict | None:
    """Wie chat(), erwartet aber eine JSON-Antwort und gibt das geparste Objekt zurueck.

    Robust gegen Modelle, die Text um das JSON herum schreiben: es wird das erste
    {...}-Objekt aus der Antwort herausgeschnitten. None bei jedem Problem.
    """
    antwort = chat(
        system + " Antworte ausschliesslich mit gueltigem JSON, ohne Einleitung und ohne Code-Zaun.",
        nutzer,
        temperatur=temperatur,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    if not antwort:
        return None
    roh = re.search(r"\{.*\}", antwort, re.S)
    if not roh:
        return None
    try:
        geparst = json.loads(roh.group(0))
        return geparst if isinstance(geparst, dict) else None
    except Exception:
        return None
