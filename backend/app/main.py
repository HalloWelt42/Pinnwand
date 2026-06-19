"""Pinnwand - Host-Anwendung.

Der Kern ist bewusst duenn und domaenenneutral: Module entdecken, ihre
Schemata initialisieren, ihre Router einbinden und ihre Erweiterungspunkte
bereitstellen. Die eigentliche Funktionalitaet liefern die Module.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import dienste_status, einstellungen
from app.modul_registry import (
    aggregiere_erweiterungen,
    init_fuer,
    lade_manifeste,
    router_fuer,
)


@asynccontextmanager
async def lebenszyklus(app: FastAPI):
    for manifest in lade_manifeste():
        init_fuer(manifest)
    yield


app = FastAPI(title="Pinnwand", version="0.9.0", lifespan=lebenszyklus)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/module")
def module() -> list[dict]:
    """Listet die geladenen Module samt Manifest."""
    return lade_manifeste()


@app.get("/api/erweiterungen")
def erweiterungen() -> dict[str, list[dict]]:
    """Aggregierte Erweiterungspunkte aller Module (views, cardFields, ...)."""
    return aggregiere_erweiterungen()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/dienste")
def dienste() -> dict:
    """Status der optionalen KI-/Integrationsdienste.

    Dient der Oberflaeche dazu, KI-Funktionen nur anzubieten, wenn der jeweilige
    Dienst konfiguriert und erreichbar ist. KI bleibt damit optional.
    """
    return {"bind": einstellungen.bind, "dienste": dienste_status()}


for _manifest in lade_manifeste():
    _router = router_fuer(_manifest)
    if _router is not None:
        app.include_router(_router)
