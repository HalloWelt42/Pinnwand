"""HTTP-Schnittstelle der Termine (leichte Meeting-Zeiterfassung)."""
from __future__ import annotations

from datetime import date, timedelta

from module.auth.akteur import Akteur, aktueller_akteur
from module.auth.rechte import darf_zeiteintrag_bearbeiten, verlange
from fastapi import APIRouter, Depends, HTTPException, Query

from module.serien import wiederholung

from . import dienst
from . import persistence as db
from .models import (
    BestaetigenEingabe,
    SammelBestaetigung,
    TerminInstanz,
    TerminSerie,
    TerminSerieCreate,
    TerminSerieUpdate,
)

router = APIRouter(prefix="/api/termine", tags=["termine"])


# -- Serien ---------------------------------------------------------------

@router.get("/serien", response_model=list[TerminSerie])
def serien() -> list[dict]:
    return db.liste_serien()


@router.post("/serien", response_model=TerminSerie, status_code=201)
def serie_anlegen(eingabe: TerminSerieCreate) -> dict:
    if not eingabe.titel.strip():
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")
    serie = db.erstelle_serie(eingabe.model_dump())
    dienst.materialisiere(serie)
    return serie


@router.patch("/serien/{sid}", response_model=TerminSerie)
def serie_aendern(sid: str, eingabe: TerminSerieUpdate) -> dict:
    serie = db.aktualisiere_serie(sid, eingabe.model_dump(exclude_unset=True))
    if serie is None:
        raise HTTPException(status_code=404, detail="Termin-Serie nicht gefunden")
    dienst.materialisiere(serie)
    return serie


@router.delete("/serien/{sid}", status_code=204)
def serie_loeschen(sid: str) -> None:
    if not db.loesche_serie(sid):
        raise HTTPException(status_code=404, detail="Termin-Serie nicht gefunden")


@router.get("/serien/{sid}/vorschau")
def serie_vorschau(sid: str, tage: int = Query(default=30)) -> dict:
    serie = db.hole_serie(sid)
    if serie is None:
        raise HTTPException(status_code=404, detail="Termin-Serie nicht gefunden")
    heute = date.today()
    bis = heute + timedelta(days=max(1, min(tage, 365)))
    return {"termine": [d.isoformat() for d in wiederholung.termine(serie, heute, bis)]}


# -- Instanzen ------------------------------------------------------------

@router.get("/instanzen", response_model=list[TerminInstanz])
def instanzen(
    status: str | None = Query(default=None),
    von: str | None = Query(default=None),
    bis: str | None = Query(default=None),
    kuerzel: str | None = Query(default=None),
) -> list[dict]:
    return db.liste_instanzen(status=status, von=von, bis=bis, kuerzel=kuerzel)


@router.get("/offen/anzahl")
def offen_anzahl() -> dict:
    return {"anzahl": db.zaehle_offen(date.today().isoformat())}


@router.post("/instanzen/{iid}/bestaetigen", response_model=TerminInstanz)
def instanz_bestaetigen(iid: str, eingabe: BestaetigenEingabe, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    # Bestaetigte Termine sind eine Ist-Quelle: nur die eigene Person oder ein Admin.
    vorhanden = db.hole_instanz(iid)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, vorhanden.kuerzel), "Nur eigene Termine bestätigen.")
    inst = dienst.bestaetige(iid, eingabe.dauer_min)
    if inst is None:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    return inst


@router.post("/instanzen/{iid}/ablehnen", response_model=TerminInstanz)
def instanz_ablehnen(iid: str, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    vorhanden = db.hole_instanz(iid)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, vorhanden.kuerzel), "Nur eigene Termine ablehnen.")
    inst = dienst.lehne_ab(iid)
    if inst is None:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    return inst


@router.post("/instanzen/bestaetigen-alle")
def instanzen_bestaetigen_alle(eingabe: SammelBestaetigung, akteur: Akteur = Depends(aktueller_akteur)) -> dict:
    # Sammel-Bestaetigung nur fuer die eigenen Instanzen (Admin: alle uebergebenen).
    ids = eingabe.ids
    if not akteur.ist_admin:
        offene = {i.id: i for i in db.liste_instanzen(status="schwebend")}
        ids = [i for i in (ids or []) if (inst := offene.get(i)) and darf_zeiteintrag_bearbeiten(akteur, inst.kuerzel)]
    return {"bestaetigt": dienst.bestaetige_alle(ids)}


@router.post("/materialisieren")
def materialisieren() -> dict:
    return {"erzeugt": dienst.materialisiere_alle()}
