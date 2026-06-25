"""HTTP-Schnittstelle der Anmeldung: Login, Logout, Status, Login-Modus."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from . import dienst
from .models import AuthStatus, LoginEingabe, LoginModusEingabe

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token(kopf: str | None) -> str:
    return (kopf or "").strip()


@router.post("/login")
def login(eingabe: LoginEingabe) -> dict:
    token = dienst.login(eingabe.kennung.strip(), eingabe.passwort)
    if token is None:
        raise HTTPException(status_code=401, detail="Name oder Passwort ist falsch")
    return {"token": token}


@router.post("/logout", status_code=204)
def logout(x_pinnwand_sitzung: str | None = Header(default=None)) -> None:
    dienst.logout(_token(x_pinnwand_sitzung))


@router.get("/status", response_model=AuthStatus)
def status(x_pinnwand_sitzung: str | None = Header(default=None)) -> AuthStatus:
    return dienst.status(_token(x_pinnwand_sitzung))


@router.put("/login-modus", response_model=AuthStatus)
def login_modus(eingabe: LoginModusEingabe, x_pinnwand_sitzung: str | None = Header(default=None)) -> AuthStatus:
    ok, fehler = dienst.setze_login_modus(eingabe.erforderlich)
    if not ok:
        raise HTTPException(status_code=400, detail=fehler)
    return dienst.status(_token(x_pinnwand_sitzung))
