"""Authentifizierung und Scopes der Agenten-API.

Bearer-Token je Client mit den Scopes read, write und admin. Ein optionales
Konfig-Token (PINNWAND_AGENT_TOKEN) gilt als Bootstrap mit Vollzugriff.
"""
from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException

from app.config import einstellungen

from . import persistence as db

SCOPES = ("read", "write", "admin")


class Akteur:
    """Ein authentifizierter Aufrufer mit seinen Scopes."""

    def __init__(self, name: str, scopes: set[str]) -> None:
        self.name = name
        self.scopes = scopes

    def hat(self, scope: str) -> bool:
        return "admin" in self.scopes or scope in self.scopes


def _token_aus_header(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip() or None


def aktueller_akteur(authorization: str | None = Header(default=None)) -> Akteur:
    token = _token_aus_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Token fehlt (Authorization: Bearer ...)")
    if einstellungen.agent_token and hmac.compare_digest(token, einstellungen.agent_token):
        return Akteur("konfig", {"admin"})
    treffer = db.pruefe_token(token)
    if treffer is None:
        raise HTTPException(status_code=401, detail="Token ungültig oder widerrufen")
    name, scopes = treffer
    return Akteur(name, scopes)


def erfordere(scope: str):
    """FastAPI-Abhängigkeit, die einen bestimmten Scope verlangt."""

    def pruefer(akteur: Akteur = Depends(aktueller_akteur)) -> Akteur:
        if not akteur.hat(scope):
            raise HTTPException(status_code=403, detail=f"Scope '{scope}' erforderlich")
        return akteur

    return pruefer
