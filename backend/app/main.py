"""Pinnwand - Host-Anwendung.

Der Kern ist bewusst dünn und domänenneutral: Module entdecken, ihre
Schemata initialisieren, ihre Router einbinden und ihre Erweiterungspunkte
bereitstellen. Die eigentliche Funktionalität liefern die Module.
"""
from __future__ import annotations

import hmac
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import VERSION, cors_origins, dienste_status, einstellungen
from app.modul_registry import (
    aggregiere_erweiterungen,
    init_fuer,
    lade_manifeste,
    lifespan_fuer,
    mount_fuer,
    router_fuer,
)
# Querschnittsbelang Anmeldung: der Kern ruft nur die Prüffunktion des auth-Moduls auf.
from module.auth import dienst as authdienst


@asynccontextmanager
async def lebenszyklus(app: FastAPI):
    for manifest in lade_manifeste():
        init_fuer(manifest)
    # Optionale Modul-Lebenszyklen (z.B. MCP-Session-Manager) sauber starten/stoppen.
    async with AsyncExitStack() as stack:
        for manifest in lade_manifeste():
            cm = lifespan_fuer(manifest)
            if cm is not None:
                await stack.enter_async_context(cm)
        yield


app = FastAPI(title="Pinnwand", version=VERSION, lifespan=lebenszyklus)


@app.middleware("http")
async def ui_token_schutz(request: Request, call_next):
    """Optionaler Schutz der Haupt-API und von /mcp per UI-Token (PINNWAND_UI_TOKEN).

    Ohne gesetztes Token bleibt alles offen (lokaler Standard, unveraendert). Mit
    Token muessen geschuetzte Pfade den Header X-Pinnwand-Token mitschicken. Die
    Agenten-API (/api/agent/*) hat ihre eigene Bearer-Pruefung und ist ausgenommen;
    /api/health bleibt frei fuer Erreichbarkeits-Checks."""
    token = einstellungen.ui_token
    if token and request.method != "OPTIONS":
        pfad = request.url.path
        geschuetzt = (
            (pfad.startswith("/api/") and not pfad.startswith("/api/agent/") and pfad != "/api/health")
            or pfad.startswith("/mcp")
        )
        if geschuetzt and not hmac.compare_digest(request.headers.get("x-pinnwand-token", ""), token):
            return JSONResponse({"detail": "UI-Token erforderlich"}, status_code=401)
    # Anmeldung (Modul auth): bei aktivem Login Sitzung + Admin-Rechte serverseitig durchsetzen.
    status = authdienst.zugriff_pruefen(
        request.method, request.url.path, request.headers.get("x-pinnwand-sitzung", "")
    )
    if status == 401:
        return JSONResponse({"detail": "Anmeldung erforderlich"}, status_code=401)
    if status == 403:
        return JSONResponse({"detail": "Nur für Admins"}, status_code=403)
    return await call_next(request)


# CORS zuletzt registrieren = aeusserste Schicht, damit auch die 401-Antwort des
# Token-Schutzes die noetigen CORS-Header traegt.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
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

    Dient der Oberfläche dazu, KI-Funktionen nur anzubieten, wenn der jeweilige
    Dienst konfiguriert und erreichbar ist. KI bleibt damit optional.
    """
    return {"bind": einstellungen.bind, "dienste": dienste_status()}


for _manifest in lade_manifeste():
    _router = router_fuer(_manifest)
    if _router is not None:
        app.include_router(_router)

# Optionale Sub-Apps einhängen (z.B. MCP-Server unter /mcp).
for _manifest in lade_manifeste():
    _mount = mount_fuer(_manifest)
    if _mount is not None:
        app.mount(_mount[0], _mount[1])
