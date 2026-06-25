"""Datenvertraege der Anmeldung."""
from __future__ import annotations

from pydantic import BaseModel


class LoginEingabe(BaseModel):
    kennung: str  # Name oder Kuerzel der Person
    passwort: str


class LoginModusEingabe(BaseModel):
    erforderlich: bool


class AuthStatus(BaseModel):
    erforderlich: bool  # Ist eine Anmeldung erforderlich?
    angemeldet: bool
    person_id: str | None = None
    name: str | None = None
    kuerzel: str | None = None
    rolle: str | None = None
