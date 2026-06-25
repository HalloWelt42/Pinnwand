"""HTTP-Schicht des KI-Assistenten.

Duenne Adapter: Status abfragen und eine KI-Aufgabe ausfuehren. Die Logik liegt
in modell.py (Modellzugang) und aufgaben.py (Aufgaben-Registry).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import aufgaben, modell, persistence
from .models import KiAntwort, KiAufgabeEingabe, KiStatus, KiTyp

router = APIRouter(prefix="/api/ki", tags=["ki"])


@router.get("/status", response_model=KiStatus)
def status() -> KiStatus:
    """Ob der Assistent nutzbar ist und welches Modell greift (zum Ausgrauen der UI)."""
    return KiStatus(**modell.status())


@router.get("/typen", response_model=list[KiTyp])
def typen() -> list[KiTyp]:
    """Die registrierten Aufgabentypen (fuer Doku/Diagnose)."""
    return aufgaben.typen()


@router.post("/aufgabe", response_model=KiAntwort)
def aufgabe(eingabe: KiAufgabeEingabe) -> KiAntwort:
    """Fuehrt eine KI-Aufgabe aus und liefert korrigierbare Vorschlaege.

    Die KI schlaegt nur vor - angewendet wird nichts. Ist kein Modell erreichbar,
    kommt ok=False (die Oberflaeche bietet dann den manuellen Weg)."""
    try:
        ergebnis = aufgaben.fuehre_aus(eingabe.typ, eingabe.kontext, eingabe.anweisung)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    persistence.protokolliere(eingabe.typ, ergebnis.modell, len(ergebnis.vorschlaege), ergebnis.ok)
    return ergebnis
