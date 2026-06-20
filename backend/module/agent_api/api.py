"""REST-Adapter der Agenten-API.

Dünne Hülle über der Aktionsschicht. Jede Schreibaktion läuft über einen
gemeinsamen Pfad mit Scope-Prüfung, Idempotenz, Trockenlauf und Audit-Log.
"""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query

from . import persistence as db
from . import werkzeuge
from .aktionen import Aktionen, AktionsFehler
from .auth import Akteur, aktueller_akteur, erfordere
from .models import (
    Erledigung,
    Freitext,
    KartenAnlage,
    Kommentierung,
    TokenAnlage,
    WerkzeugAufruf,
    ZeitBuchung,
)

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _ziel(ergebnis: dict) -> str | None:
    karte = ergebnis.get("karte")
    if isinstance(karte, dict):
        return karte.get("schluessel") or karte.get("id")
    return ergebnis.get("board_id")


def _schreibe(akteur: Akteur, aktion_name: str, idem: str | None, dry_run: bool, fn: Callable[[], dict]) -> dict:
    """Gemeinsamer Pfad für Schreibaktionen: Idempotenz, Trockenlauf, Audit."""
    if not dry_run:
        treffer = db.idempotenz_treffer(akteur.name, idem)
        if treffer is not None:
            return {**treffer, "wiederholt": True}
    try:
        ergebnis = fn()
    except AktionsFehler as e:
        db.protokolliere(akteur.name, aktion_name, None, "fehler", {"fehler": e.nachricht})
        raise HTTPException(status_code=e.status, detail=e.nachricht)
    if dry_run:
        db.protokolliere(akteur.name, aktion_name, _ziel(ergebnis), "vorschau", None)
        return ergebnis
    db.idempotenz_merke(akteur.name, idem, ergebnis)
    db.protokolliere(akteur.name, aktion_name, _ziel(ergebnis), "ok", None)
    return ergebnis


# -- Schreibaktionen (Scope write) ---------------------------------------

@router.post("/zeit")
def zeit_buchen(eingabe: ZeitBuchung, akteur: Akteur = Depends(erfordere("write"))) -> dict:
    a = Aktionen(akteur.name)
    return _schreibe(akteur, "zeit_buchen", eingabe.idempotenz_schluessel, eingabe.dry_run,
                     lambda: a.zeit_buchen(eingabe.karte, eingabe.dauer, eingabe.datum, eingabe.kommentar, eingabe.dry_run))


@router.post("/erledigt")
def erledigen(eingabe: Erledigung, akteur: Akteur = Depends(erfordere("write"))) -> dict:
    a = Aktionen(akteur.name)
    return _schreibe(akteur, "erledigen", eingabe.idempotenz_schluessel, eingabe.dry_run,
                     lambda: a.erledigen(eingabe.karte, eingabe.dauer, eingabe.kommentar, eingabe.dry_run))


@router.post("/karte")
def karte_anlegen(eingabe: KartenAnlage, akteur: Akteur = Depends(erfordere("write"))) -> dict:
    a = Aktionen(akteur.name)
    return _schreibe(akteur, "karte_anlegen", eingabe.idempotenz_schluessel, eingabe.dry_run,
                     lambda: a.karte_anlegen(
                         eingabe.board, eingabe.titel, eingabe.spalte, eingabe.beschreibung,
                         eingabe.labels, eingabe.prioritaet, eingabe.faellig, eingabe.zustaendig,
                         eingabe.schaetzung_min, eingabe.dry_run))


@router.post("/kommentar")
def kommentieren(eingabe: Kommentierung, akteur: Akteur = Depends(erfordere("write"))) -> dict:
    a = Aktionen(akteur.name)
    return _schreibe(akteur, "kommentieren", eingabe.idempotenz_schluessel, eingabe.dry_run,
                     lambda: a.kommentieren(eingabe.karte, eingabe.text, eingabe.dry_run))


@router.post("/erfassen")
def erfassen(eingabe: Freitext, akteur: Akteur = Depends(erfordere("write"))) -> dict:
    a = Aktionen(akteur.name)
    return _schreibe(akteur, "erfassen", eingabe.idempotenz_schluessel, eingabe.dry_run,
                     lambda: a.erfasse_freitext(eingabe.text, eingabe.dry_run))


# -- Leseaktionen (Scope read) -------------------------------------------

@router.get("/suche")
def suche(q: str = Query(default=""), limit: int = Query(default=10),
          akteur: Akteur = Depends(erfordere("read"))) -> dict:
    return Aktionen(akteur.name).suchen(q, limit)


@router.get("/briefing")
def briefing(datum: str | None = Query(default=None), akteur: Akteur = Depends(erfordere("read"))) -> dict:
    return Aktionen(akteur.name).briefing(datum)


@router.get("/info")
def info(akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    return {"akteur": akteur.name, "scopes": sorted(akteur.scopes)}


# -- Generische Werkzeuge (OpenAI-Function-Tools) -------------------------

@router.get("/tools")
def tools(akteur: Akteur = Depends(erfordere("read"))) -> dict:
    """Werkzeug-Definitionen im OpenAI-Function-Calling-Format."""
    return {"tools": werkzeuge.openai_schemas()}


@router.post("/tools/execute")
def tools_execute(eingabe: WerkzeugAufruf, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    """Führt ein Werkzeug generisch aus (Scope wird je Werkzeug geprüft)."""
    try:
        return werkzeuge.fuehre_aus(
            eingabe.name, eingabe.arguments, akteur, eingabe.dry_run, eingabe.idempotenz_schluessel
        )
    except AktionsFehler as e:
        raise HTTPException(status_code=e.status, detail=e.nachricht)


# -- Verwaltung (Scope admin) --------------------------------------------

@router.post("/token", status_code=201)
def token_anlegen(eingabe: TokenAnlage, akteur: Akteur = Depends(erfordere("admin"))) -> dict:
    gueltige = {"read", "write", "admin"}
    scopes = [s for s in eingabe.scopes if s in gueltige] or ["read"]
    ergebnis = db.erstelle_token(eingabe.name, scopes)
    db.protokolliere(akteur.name, "token_anlegen", ergebnis["id"], "ok", {"name": eingabe.name, "scopes": scopes})
    return ergebnis


@router.get("/token")
def token_liste(akteur: Akteur = Depends(erfordere("admin"))) -> list[dict]:
    return db.liste_token()


@router.delete("/token/{token_id}", status_code=204)
def token_widerrufen(token_id: str, akteur: Akteur = Depends(erfordere("admin"))) -> None:
    if not db.widerrufe_token(token_id):
        raise HTTPException(status_code=404, detail="Token nicht gefunden")
    db.protokolliere(akteur.name, "token_widerrufen", token_id, "ok", None)


@router.get("/audit")
def audit(limit: int = Query(default=100), akteur: Akteur = Depends(erfordere("admin"))) -> list[dict]:
    return db.liste_audit(limit)
