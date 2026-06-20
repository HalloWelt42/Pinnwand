"""HTTP-Schnittstelle der Sicherung."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from . import dienst
from .models import (
    ErzeugeAnfrage,
    ResetAnfrage,
    SnapshotInfo,
    Vorschau,
    WiederherstellenErgebnis,
    Zustand,
)

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("")
def liste() -> list[SnapshotInfo]:
    from . import persistence as db

    return [SnapshotInfo(**r) for r in db.liste()]


@router.get("/zustand")
def zustand() -> Zustand:
    return Zustand(**dienst.aktueller_zustand())


@router.post("/erzeugen")
def erzeugen(e: ErzeugeAnfrage) -> SnapshotInfo:
    info = dienst.erzeuge(art="manuell", notiz=e.notiz)
    return SnapshotInfo(**info)


@router.get("/{sid}/vorschau")
def vorschau(sid: str) -> Vorschau:
    v = dienst.vorschau(sid)
    if v is None:
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    return Vorschau.model_validate(v)


@router.get("/{sid}/datei")
def datei(sid: str) -> FileResponse:
    treffer = dienst.hole_datei(sid)
    if treffer is None:
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    pfad, dateiname = treffer
    return FileResponse(path=pfad, media_type="application/zip", filename=dateiname)


@router.post("/{sid}/wiederherstellen")
def wiederherstellen(sid: str) -> WiederherstellenErgebnis:
    try:
        ergebnis = dienst.wiederherstellen(sid)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    if ergebnis is None:
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    return WiederherstellenErgebnis.model_validate(ergebnis)


@router.post("/zuruecksetzen")
def zuruecksetzen(e: ResetAnfrage) -> dict:
    if e.modus not in ("beispiel", "leer"):
        raise HTTPException(status_code=400, detail="Unbekannter Modus")
    return dienst.zuruecksetzen(e.modus)


@router.delete("/{sid}")
def loeschen(sid: str) -> dict:
    if not dienst.loesche(sid):
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    return {"ok": True}
