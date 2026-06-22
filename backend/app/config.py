"""Zentrale Konfiguration und Erkennung optionaler Dienste.

Leitprinzip: KI- und Integrationsdienste sind optional. Diese Schicht liest die
Konfiguration (Umgebungsvariablen, optional eine .env im Projektwurzelverzeichnis)
und stellt fest, welche optionalen Dienste konfiguriert und erreichbar sind. Ein
nicht erreichbarer Dienst führt nie zu einem Fehler, sondern nur zum dezenten
Abschalten der zugehörigen Funktion in der Oberfläche.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

# Zentrale Versionsangabe der Anwendung (Backend + Snapshots beziehen sich hierauf).
VERSION = "0.45.2"

# backend/app/config.py -> Projektwurzel (Pinnwand/)
_PROJEKT_WURZEL = Path(__file__).resolve().parents[2]


def _lade_dotenv() -> None:
    """Liest eine .env im Projektwurzelverzeichnis, ohne bereits gesetzte Variablen zu überschreiben."""
    pfad = _PROJEKT_WURZEL / ".env"
    if not pfad.is_file():
        return
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        schluessel, _, wert = zeile.partition("=")
        schluessel = schluessel.strip()
        wert = wert.strip().strip('"').strip("'")
        if schluessel and schluessel not in os.environ:
            os.environ[schluessel] = wert


_lade_dotenv()


def _env(name: str, standard: str = "") -> str:
    return os.environ.get(name, standard).strip()


def _port(name: str, standard: int) -> int:
    roh = _env(name)
    try:
        return int(roh) if roh else standard
    except ValueError:
        return standard


@dataclass(frozen=True)
class Einstellungen:
    """Aufgelöste Konfiguration. Leere Dienst-URLs bedeuten: Dienst ist abgeschaltet."""

    bind: str
    backend_port: int
    frontend_port: int
    llm_url: str
    embedding_model: str
    qdrant_url: str
    tts_url: str
    transcripts_url: str
    stt_url: str
    agent_token: str
    ui_token: str
    mcp_aktiv: bool
    backup_auto: bool
    backup_behalten: int


def _lese_einstellungen() -> Einstellungen:
    return Einstellungen(
        bind=_env("PINNWAND_BIND", "127.0.0.1"),
        backend_port=_port("PINNWAND_BACKEND_PORT", 8420),
        frontend_port=_port("PINNWAND_FRONTEND_PORT", 5198),
        llm_url=_env("PINNWAND_LLM_URL"),
        embedding_model=_env("PINNWAND_EMBEDDING_MODEL"),
        qdrant_url=_env("PINNWAND_QDRANT_URL"),
        tts_url=_env("PINNWAND_TTS_URL", "http://127.0.0.1:8765"),
        transcripts_url=_env("PINNWAND_TRANSCRIPTS_URL", "http://localhost:10031"),
        stt_url=_env("PINNWAND_STT_URL"),
        agent_token=_env("PINNWAND_AGENT_TOKEN"),
        ui_token=_env("PINNWAND_UI_TOKEN"),
        mcp_aktiv=_env("PINNWAND_MCP").lower() in ("1", "true", "yes", "an"),
        backup_auto=_env("PINNWAND_BACKUP_AUTO", "1").lower() not in ("0", "false", "no", "aus"),
        backup_behalten=_port("PINNWAND_BACKUP_BEHALTEN", 10),
    )


einstellungen = _lese_einstellungen()


def cors_origins() -> list[str]:
    """Erlaubte Browser-Herkünfte für die API.

    Die API ist unauthentifiziert und lokal gedacht. Ein offenes '*' würde es
    beliebigen Webseiten erlauben, im Browser des Nutzers auf die lokale API
    zuzugreifen. Deshalb sind nur die bekannte Oberfläche (localhost auf dem
    Frontend-Port) und ausdrücklich gesetzte Herkünfte erlaubt.
    """
    roh = _env("PINNWAND_CORS_ORIGINS")
    if roh:
        return [t.strip() for t in roh.split(",") if t.strip()]
    p = einstellungen.frontend_port
    herkuenfte: list[str] = []
    for host in ("localhost", "127.0.0.1"):
        herkuenfte.append(f"http://{host}:{p}")
        herkuenfte.append(f"https://{host}:{p}")
    return herkuenfte


# --- Optionale Dienste: Beschreibung + Erreichbarkeitsprüfung mit kurzem Cache ---


@dataclass(frozen=True)
class Dienst:
    schluessel: str
    name: str
    url: str
    pruef_pfad: str = "/"


def optionale_dienste() -> list[Dienst]:
    e = einstellungen
    return [
        Dienst("llm", "LLM und Embeddings", e.llm_url, "/v1/models"),
        Dienst("qdrant", "Vektor-Datenbank", e.qdrant_url, "/"),
        Dienst("tts", "Vorlesen", e.tts_url, "/health"),
        Dienst("transcripts", "Transkriptionen", e.transcripts_url, "/api/search/stats"),
        Dienst("stt", "Spracheingabe", e.stt_url, "/"),
    ]


_cache: dict[str, tuple[float, bool]] = {}
_CACHE_TTL = 10.0


def erreichbar(url: str, pfad: str = "/") -> bool:
    """Prüft, ob ein Dienst antwortet. Ergebnis wird kurz zwischengespeichert."""
    if not url:
        return False
    schluessel = url + pfad
    jetzt = time.monotonic()
    treffer = _cache.get(schluessel)
    if treffer and (jetzt - treffer[0]) < _CACHE_TTL:
        return treffer[1]
    ok = False
    try:
        antwort = httpx.get(url.rstrip("/") + pfad, timeout=1.5)
        ok = antwort.status_code < 500
    except Exception:
        ok = False
    _cache[schluessel] = (jetzt, ok)
    return ok


def dienste_status() -> list[dict]:
    """Status aller optionalen Dienste: ob konfiguriert und, falls ja, ob erreichbar."""
    ausgabe: list[dict] = []
    for d in optionale_dienste():
        konfiguriert = bool(d.url)
        ausgabe.append(
            {
                "schluessel": d.schluessel,
                "name": d.name,
                "konfiguriert": konfiguriert,
                "erreichbar": erreichbar(d.url, d.pruef_pfad) if konfiguriert else False,
            }
        )
    return ausgabe
