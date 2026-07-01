"""HTTP-Schnittstelle der Planung (Personen, Urlaub, Feiertage, Kapazität)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from module.auth import dienst as authdienst
from module.auth import persistence as authdb
from module.auth.akteur import Akteur, aktueller_akteur
from module.auth.rechte import darf_person_bearbeiten, verlange

from . import feiertage, kalender, kapazitaet
from . import persistence as db
from .models import (
    AbwesenheitTyp,
    AbwesenheitTypUpdate,
    FeiertageUebernehmen,
    PasswortEingabe,
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
def person_anlegen(e: PersonCreate, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    verlange(akteur.ist_admin, "Nur Admins dürfen Personen anlegen.")
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
def person_aendern(pid: str, e: PersonUpdate, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    daten = e.model_dump(exclude_unset=True)
    # Rechte-relevante Felder darf nur ein Admin aendern; persoenliche Felder (Bundesland,
    # Wochenstunden, Urlaubsanspruch, Farbe) darf die Person auch selbst pflegen.
    _ADMIN_FELDER = {"rolle", "aktiv", "name", "kuerzel"}
    if _ADMIN_FELDER & daten.keys():
        verlange(akteur.ist_admin, "Diese Felder darf nur ein Admin ändern.")
    else:
        verlange(darf_person_bearbeiten(akteur, pid), "Nur die eigene Person oder ein Admin.")
    # Aussperr-Schutz: bei aktiver Anmeldung den letzten Admin (mit Passwort) nicht
    # herabstufen oder deaktivieren.
    entzieht_admin = daten.get("rolle") == "mitarbeiter" or daten.get("aktiv") is False
    if authdienst.login_aktiv() and entzieht_admin and not db.admin_mit_passwort_existiert(ausser_pid=pid):
        raise HTTPException(
            status_code=409,
            detail="Der letzte Admin kann bei aktiver Anmeldung nicht herabgestuft oder deaktiviert werden.",
        )
    p = db.aktualisiere_person(pid, daten)
    if p is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    if daten.get("aktiv") is False:
        authdb.loesche_sitzungen_von(pid)  # Deaktivierte Person sofort abmelden
    return p


@router.delete("/personen/{pid}", status_code=204)
def person_loeschen(pid: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    verlange(akteur.ist_admin, "Nur Admins dürfen Personen löschen.")
    # Aussperr-Schutz: bei aktiver Anmeldung den letzten Admin mit Passwort nicht loeschen.
    if authdienst.login_aktiv() and not db.admin_mit_passwort_existiert(ausser_pid=pid):
        raise HTTPException(
            status_code=409, detail="Der letzte Admin kann bei aktiver Anmeldung nicht gelöscht werden.",
        )
    if not db.loesche_person(pid):
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    authdb.loesche_sitzungen_von(pid)  # verwaiste Sitzungen der geloeschten Person entfernen


@router.post("/personen/{pid}/passwort", response_model=Person)
def person_passwort(pid: str, eingabe: PasswortEingabe, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    """Setzt oder entfernt (leer) das Passwort einer Person. Nur fuer Admins."""
    verlange(akteur.ist_admin, "Nur Admins dürfen Passwörter setzen.")
    neu = eingabe.passwort.strip() or None
    # Aussperr-Schutz: bei aktiver Anmeldung das letzte Admin-Passwort nicht entfernen.
    if authdienst.login_aktiv() and neu is None and not db.admin_mit_passwort_existiert(ausser_pid=pid):
        raise HTTPException(
            status_code=409, detail="Das letzte Admin-Passwort kann bei aktiver Anmeldung nicht entfernt werden.",
        )
    p = db.setze_passwort(pid, neu)
    if p is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    # Passwortwechsel/-entfernung beendet bestehende Sitzungen dieser Person (CWE-613).
    authdb.loesche_sitzungen_von(pid)
    return p


# -- Urlaub ---------------------------------------------------------------

@router.get("/urlaub")
def urlaub(person: str | None = Query(default=None), von: str = Query(...), bis: str = Query(...)) -> list[dict]:
    return db.liste_urlaub(person, von, bis)


@router.post("/urlaub")
def urlaub_setzen(e: UrlaubSetzen, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    verlange(darf_person_bearbeiten(akteur, e.person_id), "Nur der eigene Urlaub oder ein Admin.")
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
def urlaub_loeschen(uid: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    eintrag = db.hole_urlaub(uid)
    if eintrag is None:
        raise HTTPException(status_code=404, detail="Urlaubseintrag nicht gefunden")
    verlange(darf_person_bearbeiten(akteur, eintrag["person_id"]), "Nur der eigene Urlaub oder ein Admin.")
    db.loesche_urlaub(uid)


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


@router.get("/stunden-uebersicht")
def stunden_uebersicht(person: str | None = Query(default=None)) -> dict:
    """Geleistete Stunden (Ist) gegen Soll je Heute/Woche/Monat/Jahr.

    Ohne person: Team-Gesamt. Mit person (Personen-ID): nur diese Person."""
    return kapazitaet.stunden_uebersicht(person_id=person)


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
def tagesregel_anlegen(e: TagesregelCreate, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    # Persoenliche Regel (person_id gesetzt) = self-or-admin; globale Regel (person_id None)
    # = admin-only. darf_person_bearbeiten deckt beides ab (None -> nur Admin).
    verlange(darf_person_bearbeiten(akteur, e.person_id), "Eigene Regel oder Admin (globale Regeln nur Admin).")
    return db.setze_tagesregel(e.model_dump(exclude_unset=True))


@router.delete("/tagesregeln/{rid}", status_code=204)
def tagesregel_loeschen(rid: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    regel = db.hole_tagesregel(rid)
    if regel is None:
        raise HTTPException(status_code=404, detail="Regel nicht gefunden")
    verlange(darf_person_bearbeiten(akteur, regel["person_id"]), "Eigene Regel oder Admin (globale Regeln nur Admin).")
    db.loesche_tagesregel(rid)


# -- Komfort: einen Tag einer Person leeren (alle Abwesenheiten entfernen) -

@router.post("/tag-leeren")
def tag_leeren(e: TagLeeren, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    verlange(darf_person_bearbeiten(akteur, e.person_id), "Nur den eigenen Tag oder ein Admin.")
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
def wochen_override_setzen(person_id: str, e: WochenOverrideSetzen, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    verlange(darf_person_bearbeiten(akteur, person_id), "Nur die eigenen Arbeitszeiten oder ein Admin.")
    if len(e.wochenstunden) != 7:
        raise HTTPException(status_code=400, detail="Sieben Werte (Mo-So) noetig")
    if not (1 <= e.kw <= 53):
        raise HTTPException(status_code=400, detail="Kalenderwoche ausserhalb 1-53")
    return db.setze_wochen_override(person_id, e.jahr, e.kw, [float(x) for x in e.wochenstunden])


@router.delete("/personen/{person_id}/wochen-override/{jahr}/{kw}", status_code=204)
def wochen_override_loeschen(person_id: str, jahr: int, kw: int, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    verlange(darf_person_bearbeiten(akteur, person_id), "Nur die eigenen Arbeitszeiten oder ein Admin.")
    if not db.loesche_wochen_override(person_id, jahr, kw):
        raise HTTPException(status_code=404, detail="Kein Override für diese Woche")
