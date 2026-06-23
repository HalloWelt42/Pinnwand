"""Gemeinsame Test-Grundlage.

Jede Test-Session laeuft gegen eine FRISCHE, temporaere SQLite-Datenbank, damit die
echten Nutzdaten (backend/pinnwand.db) niemals beruehrt werden. Die App baut beim
Start (Lifespan) das Schema aller Module auf; der TestClient als Context-Manager
loest diesen Start aus.

Wichtig: Die Umgebungsvariablen muessen GESETZT sein, BEVOR die App importiert wird,
weil app.db.DB_PFAD und app.config.einstellungen beim Import ausgewertet werden.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="pinnwand-test-")) / "test.db"
os.environ["PINNWAND_DB_PFAD"] = str(_TMP)
os.environ["PINNWAND_BACKUP_AUTO"] = "0"  # keine Snapshots ins echte data/ schreiben
os.environ["PINNWAND_MCP"] = ""
# Optionale externe Dienste im Test nicht ansprechen (kein LLM/Qdrant/TTS noetig).
for _k in ("PINNWAND_LLM_URL", "PINNWAND_QDRANT_URL", "PINNWAND_TTS_URL", "PINNWAND_TRANSCRIPTS_URL", "PINNWAND_STT_URL"):
    os.environ[_k] = ""

from fastapi.testclient import TestClient  # noqa: E402  (Import bewusst nach den env-Setzungen)
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """FastAPI-TestClient gegen die temporaere DB; Lifespan legt das Schema an."""
    with TestClient(app) as c:
        yield c
