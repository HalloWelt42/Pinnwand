"""HTTP-Schnittstelle der Planung (Personen, Urlaub, Feiertage, Kapazität)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from . import feiertage, kalender, kapazitaet
from . import persistence as db
from .models import (
    AbwesenheitTyp,
    AbwesenheitTypUpdate,
    FeiertageUebernehmen,
    Person,
    PersonCreate,
    PersonUpdate,
    Tagesregel,
    TagesregelCreate,
    TagLeeren,
    Urlaubskonto,
    UrlaubSetzen,
    WochenOverride,
    WochenOverrideSetzen,
)

router = APIRouter(prefix="/api/planung", tags=["planung"])


# -- Personen -------------------------------------------------------------

@router.get("/personen", response_model=list[Person])
def personen() -> list[dict]:
    return db.liste_personen()


@router.post("/personen", response_model=Person, status_code=201)
def person_anlegen(e: PersonCreate) -> dict:
    return db.erstelle_person(
        e.name, e.kuerzel, e.wochenstunden, e.farbe,
        bundesland=e.bundesland, urlaubsanspruch=e.urlaubsanspruch, resturlaub_vorjahr=e.resturlaub_vorjahr,
    )


@router.get("/urlaubskonten", response_model=list[Urlaubskonto])
def urlaubskonten(jahr: int = Query(...)) -> list[dict]:
    return db.urlaubskonten(jahr)


@router.get("/urlaubskonto", response_model=Urlaubskonto)
def urlaubskonto(person: str = Query(...), jahr: int = Query(...)) -> dict:
    k = db.urlaubskonto(person, jahr)
    if k is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    return k


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
    p = db.hole_person(e.person_id)
    ws = p["wochenstunden"] if p else [8, 8, 8, 8, 8, 0, 0]
    feier: set[str] = set()
    if e.feiertage_ueberspringen:
        feier = {f["datum"] for f in db.feiertage_relevant(e.von, bis, p.get("bundesland") if p else None)}
    cur = date.fromisoformat(e.von)
    ende = date.fromisoformat(bis)
    erzeugt = 0
    uebersprungen = 0
    while cur <= ende:
        iso = cur.isoformat()
        wd = cur.weekday()
        # Arbeitstag = die Person hat an diesem Wochentag überhaupt Soll-Stunden.
        arbeitstag = wd < len(ws) and float(ws[wd]) > 0
        kein_arbeitstag = e.wochenenden_ueberspringen and not arbeitstag
        ist_feiertag = e.feiertage_ueberspringen and iso in feier
        if kein_arbeitstag or ist_feiertag:
            uebersprungen += 1
        else:
            db.setze_urlaub(e.person_id, iso, e.anteil, e.typ, e.notiz)
            erzeugt += 1
        cur += timedelta(days=1)
    return {"gesetzt": erzeugt, "uebersprungen": uebersprungen}


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
        raise HTTPException(status_code=400, detail="Keine Feiertage für diese Auswahl gefunden")
    # Jeder Eintrag trägt bereits seine korrekte Region (None = bundesweit, sonst Code).
    return {"uebernommen": db.uebernehme_feiertage(eintraege)}


@router.delete("/feiertage")
def feiertage_loeschen(jahr: int = Query(...), region: str | None = Query(default=None)) -> dict:
    return {"geloescht": db.loesche_feiertage(jahr, region)}


# -- Kapazität / Kalender-Overlay ---------------------------------------

@router.get("/kapazitaet")
def kapazitaet_abruf(person: str = Query(...), von: str = Query(...), bis: str = Query(...)) -> dict:
    k = kapazitaet.kapazitaet(person, von, bis)
    if k is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    return k


@router.get("/tage")
def tage(von: str = Query(...), bis: str = Query(...), person: str | None = Query(default=None)) -> list[dict]:
    return kapazitaet.tage_overlay(von, bis, person)


# -- Jahreskalender (Aggregation über alle Personen) --------------------

@router.get("/kalender")
def kalender_abruf(jahr: int = Query(...)) -> dict:
    return kalender.kalender(jahr)


# -- Abwesenheits-Arten ---------------------------------------------------

@router.get("/abwesenheitstypen", response_model=list[AbwesenheitTyp])
def abwesenheitstypen() -> list[dict]:
    return db.liste_abwesenheitstypen()


@router.patch("/abwesenheitstypen/{code}", response_model=AbwesenheitTyp)
def abwesenheitstyp_aendern(code: str, e: AbwesenheitTypUpdate) -> dict:
    t = db.aktualisiere_abwesenheitstyp(code, e.model_dump(exclude_unset=True))
    if t is None:
        raise HTTPException(status_code=404, detail="Abwesenheits-Art nicht gefunden")
    return t


# -- Tagesregeln (halbe Tage / Sonderregeln) ------------------------------

@router.get("/tagesregeln", response_model=list[Tagesregel])
def tagesregeln(person: str | None = Query(default=None)) -> list[dict]:
    return db.liste_tagesregeln(person)


@router.post("/tagesregeln", response_model=Tagesregel, status_code=201)
def tagesregel_anlegen(e: TagesregelCreate) -> dict:
    return db.setze_tagesregel(e.model_dump(exclude_unset=True))


@router.delete("/tagesregeln/{rid}", status_code=204)
def tagesregel_loeschen(rid: str) -> None:
    if not db.loesche_tagesregel(rid):
        raise HTTPException(status_code=404, detail="Regel nicht gefunden")


# -- Komfort: einen Tag einer Person leeren (alle Abwesenheiten entfernen) -

@router.post("/tag-leeren")
def tag_leeren(e: TagLeeren) -> dict:
    geloescht = 0
    for u in db.liste_urlaub(e.person_id, e.datum, e.datum):
        if db.loesche_urlaub(u["id"]):
            geloescht += 1
    return {"geloescht": geloescht}


# -- Wochen-Override (abweichende Wochenstunden einzelner Wochen) ----------

@router.get("/personen/{person_id}/wochen-override", response_model=list[WochenOverride])
def wochen_override(person_id: str) -> list[dict]:
    return db.liste_wochen_override(person_id)


@router.post("/personen/{person_id}/wochen-override", response_model=WochenOverride)
def wochen_override_setzen(person_id: str, e: WochenOverrideSetzen) -> dict:
    if len(e.wochenstunden) != 7:
        raise HTTPException(status_code=400, detail="Sieben Werte (Mo-So) noetig")
    if not (1 <= e.kw <= 53):
        raise HTTPException(status_code=400, detail="Kalenderwoche ausserhalb 1-53")
    return db.setze_wochen_override(person_id, e.jahr, e.kw, [float(x) for x in e.wochenstunden])


@router.delete("/personen/{person_id}/wochen-override/{jahr}/{kw}", status_code=204)
def wochen_override_loeschen(person_id: str, jahr: int, kw: int) -> None:
    if not db.loesche_wochen_override(person_id, jahr, kw):
        raise HTTPException(status_code=404, detail="Kein Override fuer diese Woche")
