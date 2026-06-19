"""Optionaler MCP-Server der Agenten-API.

Stellt dieselben Werkzeuge wie die REST-/OpenAI-Schicht ueber das MCP-Protokoll
bereit (Streamable HTTP, eingehaengt unter /mcp). Strikt optional: nur aktiv,
wenn das mcp-Paket vorhanden ist UND PINNWAND_MCP gesetzt ist. Laeuft als
Dienst-Akteur 'mcp' (read+write); jeder Aufruf wird im Audit-Log festgehalten.
Die Erreichbarkeit folgt der Server-Bindung (Standard: nur localhost).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from app.config import einstellungen

from . import werkzeuge
from .aktionen import AktionsFehler
from .auth import Akteur

try:
    from mcp.server.fastmcp import FastMCP

    _VERFUEGBAR = True
except Exception:  # pragma: no cover - mcp ist optional
    _VERFUEGBAR = False


def _aktiviert() -> bool:
    return _VERFUEGBAR and einstellungen.mcp_aktiv


def _akteur() -> Akteur:
    return Akteur("mcp", {"read", "write"})


def _ruf(name: str, argumente: dict) -> dict:
    """Fuehrt ein Werkzeug aus und gibt fachliche Fehler als Feld zurueck (statt Exception)."""
    try:
        return werkzeuge.fuehre_aus(name, argumente, _akteur())
    except AktionsFehler as e:
        return {"fehler": e.nachricht}


def _baue() -> "FastMCP":
    # streamable_http_path='/' -> Endpunkt liegt direkt unter dem Mount-Pfad (/mcp),
    # sonst entstuende /mcp/mcp.
    mcp = FastMCP("Pinnwand", streamable_http_path="/")

    @mcp.tool()
    def zeit_buchen(karte: str, dauer: str, datum: str = "", kommentar: str = "") -> dict:
        """Bucht Arbeitszeit auf eine Karte (Schluessel wie R3-130, Titel oder ID)."""
        return _ruf("zeit_buchen", {"karte": karte, "dauer": dauer, "datum": datum or None, "kommentar": kommentar or None})

    @mcp.tool()
    def karte_anlegen(board: str, titel: str, spalte: str = "", beschreibung: str = "",
                      prioritaet: str = "", faellig: str = "", schaetzung_min: int = 0) -> dict:
        """Legt eine neue Karte/Aufgabe auf einem Board an."""
        return _ruf("karte_anlegen", {
            "board": board, "titel": titel, "spalte": spalte or None, "beschreibung": beschreibung or None,
            "prioritaet": prioritaet or None, "faellig": faellig or None,
            "schaetzung_min": schaetzung_min or None,
        })

    @mcp.tool()
    def erledigen(karte: str, dauer: str = "", kommentar: str = "") -> dict:
        """Markiert eine Karte als erledigt (verschiebt in die Erledigt-Spalte), optional mit Abschlusszeit."""
        return _ruf("erledigen", {"karte": karte, "dauer": dauer or None, "kommentar": kommentar or None})

    @mcp.tool()
    def kommentieren(karte: str, text: str) -> dict:
        """Haengt einen Kommentar an eine Karte."""
        return _ruf("kommentieren", {"karte": karte, "text": text})

    @mcp.tool()
    def erfassen(text: str) -> dict:
        """Erfasst eine Zeitbuchung aus freiem Text (z.B. '2 Std an R3-130, Toleranzen geprueft')."""
        return _ruf("erfassen", {"text": text})

    @mcp.tool()
    def suche(q: str, limit: int = 10) -> dict:
        """Durchsucht Karteninhalte nach einem Begriff."""
        return _ruf("suche", {"q": q, "limit": limit})

    @mcp.tool()
    def briefing(datum: str = "") -> dict:
        """Was steht an: ueberfaellige, heute/diese Woche faellige und laufende Aufgaben."""
        return _ruf("briefing", {"datum": datum or None})

    return mcp


mcp_instanz = _baue() if _aktiviert() else None
asgi_app = mcp_instanz.streamable_http_app() if mcp_instanz is not None else None


@asynccontextmanager
async def lebenszyklus():
    """Startet den MCP-Session-Manager, falls aktiv (sonst No-op)."""
    if mcp_instanz is not None:
        async with mcp_instanz.session_manager.run():
            yield
    else:
        yield
