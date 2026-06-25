"""HTTP-Schnittstelle der Berichte (erzeugen, Archiv)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from . import daten, render
from . import persistence as db
from .models import ArchivEintrag, BerichtAnfrage, TypenAntwort

router = APIRouter(prefix="/api/berichte", tags=["berichte"])

_EXT = {"pdf": "pdf", "csv": "csv", "markdown": "md", "md": "md"}


@router.get("/typen", response_model=TypenAntwort)
def typen() -> dict:
    return {"typen": [{"id": k, "titel": v} for k, v in daten.TYPEN.items()]}


@router.post("/erzeugen")
def erzeugen(e: BerichtAnfrage) -> Response:
    von = e.von or "2000-01-01"
    bis = e.bis or "2100-12-31"
    try:
        bericht = daten.erzeuge(e.typ, von, bis, e.person, e.board_id)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    try:
        inhalt, mime = render.rendere(bericht, e.format)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception:  # z.B. WeasyPrint nicht verfügbar - Details nicht nach außen geben
        raise HTTPException(status_code=500, detail="Bericht konnte nicht erzeugt werden (Render-Dienst nicht verfügbar).")
    if e.archivieren:
        db.archiviere(e.typ, bericht["titel"], bericht["zeitraum"], e.format, e.person, inhalt)
    dateiname = f"{e.typ}_{e.von or 'gesamt'}.{_EXT.get(e.format, 'bin')}"
    return Response(content=inhalt, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{dateiname}"'})


@router.get("/archiv", response_model=list[ArchivEintrag])
def archiv() -> list[dict]:
    return db.liste()


@router.get("/archiv/{bid}")
def archiv_datei(bid: str) -> Response:
    treffer = db.hole(bid)
    if treffer is None:
        raise HTTPException(status_code=404, detail="Bericht nicht gefunden")
    inhalt, dateiname, mime = treffer
    return Response(content=inhalt, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{dateiname}"'})
