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
from .anwendung.serien import Vorbuchung
from .einstellungen import AppEinstellungen
from .fassung import FASSUNG, WURZEL
from .schnittstelle import anhaenge, transkripte
from .schnittstelle.ablage import KellerwolkeAblage
from .schnittstelle.rest import router
from .schnittstelle.sprachmodell import LeitstellenModell
from .schnittstelle.transkription import VerbundTranskription
from .schnittstelle.vertonung import VerbundVertonung
from .schnittstelle.zugang import GeruestZugang
from .sicherung import Nachtsicherung
from .uhr import Uhr


def app_bauen(daten: Path, transport: httpx.AsyncBaseTransport | None = None, uhr: Uhr | None = None,
              sicherungen: Path | None = None) -> FastAPI:
    """`transport` und `uhr` nur für Tests (Kellerwolke und Leitstelle nachgestellt, feste Uhr). Die Nachtsicherung
    schreibt nach `sicherungen` (ohne Angabe neben den Daten: im Container /app/sicherungen)."""
    geruest = Geruest(name="Pinnwand", kennung="pinnwand", rolle="plant Arbeit auf Boards", symbol="fa-thumbtack", farbe="#2f8f86", fassung=FASSUNG,
                      daten=daten, einstellungen=AppEinstellungen, oberflaeche=WURZEL / "frontend" / "dist",
                      push=True, transport=transport)
    ablage = KellerwolkeAblage(geruest)
    transkription = VerbundTranskription(geruest)
    vertonung = VerbundVertonung(geruest)
    dienste = Dienste.bauen(geruest.db, GeruestZugang(geruest), ablage, uhr, push=geruest.push,
                            sprachmodell=LeitstellenModell(geruest), transkription=transkription,
                            vertonung=vertonung)
    geruest.einstellungen.anbieten("ki_modell", geruest.leitstelle_angebot("text", leer="Kette der App"))
    geruest.einstellungen.anbieten("transkription_adresse", geruest.verbund.angebot("Transkription", "transkription", transkription.adresse))
    geruest.verbund.anmelden("Transkription", transkription.adresse)
    geruest.einstellungen.anbieten("vertonung_adresse", geruest.verbund.angebot("Vertonung", "vertonung", vertonung.adresse))
    geruest.einstellungen.anbieten("vorlesen_stimme", vertonung.stimmen_angebot())
    geruest.verbund.anmelden("Vertonung", vertonung.adresse)
    geruest.begleiter_anmelden(Start(geruest.db), Vorbuchung(dienste.serien), Faelligkeit(dienste.hinweise), dienste.mitteilungen,
                               Nachtsicherung(Path(geruest.db.pfad), sicherungen or daten.parent / "sicherungen", "pinnwand",
                                              dienste.anwendung.uhr))
    app = geruest.fastapi()
    app.state.geruest = geruest
    app.state.dienste = dienste
    app.include_router(router(geruest, dienste))
    app.include_router(anhaenge.inhalt(geruest, dienste, ablage))
    app.include_router(transkripte.inhalt(geruest, dienste, transkription))
    geruest.oberflaeche_ausliefern(app)
    return app


def daten_ordner() -> Path:
    """Wo die App ihre Daten hält: `PINNWAND_DATEN` (im Container /app/daten), sonst daten/ im Repo."""
    return Path(os.environ.get("PINNWAND_DATEN") or WURZEL / "daten")


app = app_bauen(daten_ordner())
