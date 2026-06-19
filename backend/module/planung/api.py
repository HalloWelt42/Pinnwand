"""HTTP-Schnittstelle der Planung (Personen, Urlaub, Feiertage, Kapazitaet)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from . import feiertage, kapazitaet
from . import persistence as db
from .models import FeiertageUebernehmen, Person, PersonCreate, PersonUpdate, UrlaubSetzen

router = APIRouter(prefix="/api/planung", tags=["planung"])


# -- Personen -------------------------------------------------------------

@router.get("/personen", response_model=list[Person])
def personen() -> list[dict]:
    return db.liste_personen()


@router.post("/personen", response_model=Person, status_code=201)
def person_anlegen(e: PersonCreate) -> dict:
    return db.erstelle_person(e.name, e.kuerzel, e.wochenstunden, e.farbe)


@router.patch("/personen/{pid}", response_model=Person)
def person_aendern(pid: str, e: PersonUpdate) -> dict:
    p = db.aktualisiere_person(pid, e.model_dump(exclude_unset=True))
    if p is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    return p


@router.delete("/personen/{pid}", status_code=204)
def person_loeschen(pid: str) -> None:
    if not db.loesche_person(pid):
        raise HTTPException(status_code=404, detail="Person nicht gefunden")


# -- Urlaub ---------------------------------------------------------------

@router.get("/urlaub")
def urlaub(person: str | None = Query(default=None), von: str = Query(...), bis: str = Query(...)) -> list[dict]:
    return db.liste_urlaub(person, von, bis)


@router.post("/urlaub")
def urlaub_setzen(e: UrlaubSetzen) -> dict:
    bis = e.bis or e.von
    feier = {f["datum"] for f in db.liste_feiertage(e.von, bis)} if e.feiertage_ueberspringen else set()
    cur = date.fromisoformat(e.von)
    ende = date.fromisoformat(bis)
    erzeugt = 0
    while cur <= ende:
        iso = cur.isoformat()
        ueberspringen = (e.wochenenden_ueberspringen and cur.weekday() >= 5) or (iso in feier)
        if not ueberspringen:
            db.setze_urlaub(e.person_id, iso, e.anteil, e.typ, e.notiz)
            erzeugt += 1
        cur += timedelta(days=1)
    return {"gesetzt": erzeugt}


@router.delete("/urlaub/{uid}", status_code=204)
def urlaub_loeschen(uid: str) -> None:
    if not db.loesche_urlaub(uid):
        raise HTTPException(status_code=404, detail="Urlaubseintrag nicht gefunden")


# -- Feiertage ------------------------------------------------------------

@router.get("/laender")
def laender() -> dict:
    return {"verfuegbar": feiertage.verfuegbar(), "laender": feiertage.laender()}


@router.get("/feiertage")
def feiertage_liste(von: str = Query(...), bis: str = Query(...)) -> list[dict]:
    return db.liste_feiertage(von, bis)


@router.get("/feiertage/vorschau")
def feiertage_vorschau(land: str = Query("DE"), region: str | None = Query(default=None), jahr: int = Query(...)) -> dict:
    return {"eintraege": feiertage.vorschau(land, region, jahr)}


@router.post("/feiertage/uebernehmen")
def feiertage_uebernehmen(e: FeiertageUebernehmen) -> dict:
    eintraege = feiertage.vorschau(e.land, e.region, e.jahr)
    if not eintraege:
        raise HTTPException(status_code=400, detail="Keine Feiertage fuer diese Auswahl gefunden")
    region = f"{e.land}-{e.region}" if e.region else e.land
    return {"uebernommen": db.uebernehme_feiertage(eintraege, region)}


@router.delete("/feiertage")
def feiertage_loeschen(jahr: int = Query(...), region: str | None = Query(default=None)) -> dict:
    return {"geloescht": db.loesche_feiertage(jahr, region)}


# -- Kapazitaet / Kalender-Overlay ---------------------------------------

@router.get("/kapazitaet")
def kapazitaet_abruf(person: str = Query(...), von: str = Query(...), bis: str = Query(...)) -> dict:
    k = kapazitaet.kapazitaet(person, von, bis)
    if k is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    return k


@router.get("/tage")
def tage(von: str = Query(...), bis: str = Query(...), person: str | None = Query(default=None)) -> list[dict]:
    return kapazitaet.tage_overlay(von, bis, person)
