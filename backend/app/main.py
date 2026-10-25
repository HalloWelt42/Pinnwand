"""Pinnwand: plant Arbeit auf Boards. Backend auf dem Gerüst des Appkerns.

    uvicorn app.main:app --port 8420
"""

import os
from pathlib import Path

import httpx
from fastapi import FastAPI

from appkern.app import Geruest

from .anwendung import Dienste, Start
from .anwendung.hinweise import Faelligkeit
from .einstellungen import AppEinstellungen
from .fassung import FASSUNG, WURZEL
from .schnittstelle.rest import router
from .schnittstelle.zugang import GeruestZugang
from .uhr import Uhr


def app_bauen(daten: Path, transport: httpx.AsyncBaseTransport | None = None, uhr: Uhr | None = None) -> FastAPI:
    """`transport` und `uhr` nur für Tests (Kellerwolke und Leitstelle nachgestellt, feste Uhr)."""
    geruest = Geruest(name="Pinnwand", kennung="pinnwand", rolle="plant Arbeit auf Boards", symbol="fa-thumbtack", farbe="#2f8f86", fassung=FASSUNG,
                      daten=daten, einstellungen=AppEinstellungen, oberflaeche=WURZEL / "frontend" / "dist",
                      transport=transport)
    dienste = Dienste.bauen(geruest.db, GeruestZugang(geruest), uhr)
    geruest.begleiter_anmelden(Start(geruest.db), Faelligkeit(dienste.hinweise))
    app = geruest.fastapi()
    app.state.geruest = geruest
    app.state.dienste = dienste
    app.include_router(router(geruest, dienste))
    geruest.oberflaeche_ausliefern(app)
    return app


def daten_ordner() -> Path:
    """Wo die App ihre Daten hält: `PINNWAND_DATEN` (im Container /app/daten), sonst daten/ im Repo."""
    return Path(os.environ.get("PINNWAND_DATEN") or WURZEL / "daten")


app = app_bauen(daten_ordner())
