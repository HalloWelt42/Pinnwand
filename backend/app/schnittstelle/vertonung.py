"""Die Vertonung über den Verbund des Gerüsts; die Anwendung kennt nur den Anschluss `Vertonung`. Gesprochen wird mit
der Stimme und dem Tempo aus den Einstellungen (`vorlesen_stimme`, `vorlesen_tempo`), deutsch, Zahlen und Abkürzungen
ausgeschrieben. Zur Wahl stehen nur Stimmen aus dem Katalog der Vertonung und private, die sie der Pinnwand freigibt;
gesammelte fremde Stimmen bietet die Pinnwand nicht an."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from appkern.app import Geruest
from appkern.einstellungen import Angebot, Option
from appkern.verbund import ABFRAGE, VerbundFehler

from ..anwendung.rahmen import Abgelehnt


def abgelehnt(f: VerbundFehler) -> Abgelehnt:
    if f.status is None:
        if f.meldung == "nicht eingerichtet":
            return Abgelehnt("Die Vertonung ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)
        return Abgelehnt(f"Die Vertonung ist gerade nicht erreichbar ({f.meldung})", 503)
    if f.status in (401, 403):
        return Abgelehnt(f"Die Vertonung lässt das nicht zu: {f.meldung}", 403)
    return Abgelehnt(f"Die Vertonung meldet: {f.meldung}", 502)


def stimmwahl(stimme: str) -> dict[str, str] | None:
    """Die Wahl im Format der Vertonung; leer: ihre Vorgabe."""
    if not stimme:
        return None
    if stimme.startswith("katalog:"):
        return {"art": "katalog", "name": stimme.removeprefix("katalog:")}
    return {"art": "klon", "knoten_id": stimme}


class VerbundVertonung:
    def __init__(self, geruest: Geruest) -> None:
        self.g = geruest

    def adresse(self) -> str:
        return self.g.einstellungen.stand.vertonung_adresse.strip().rstrip("/")

    async def strom(self, sitzung: str, text: str) -> AsyncIterator[dict[str, Any]]:
        e = self.g.einstellungen.stand
        koerper: dict[str, Any] = {"text": text, "tempo": e.vorlesen_tempo, "sprache": "de", "ausschreiben": True}
        if (wahl := stimmwahl(e.vorlesen_stimme)) is not None:
            koerper["stimme"] = wahl
        try:
            async with self.g.verbund.strom("POST", self.adresse(), "/api/v1/sprechen/strom", sitzung=sitzung,
                                            json=koerper) as antwort:
                async for z in antwort.aiter_lines():
                    if z.strip():
                        yield json.loads(z)
        except VerbundFehler as f:
            raise abgelehnt(f) from f

    def stimmen_angebot(self):
        """Anbieter für das Feld der Stimme: Katalog und für die Pinnwand freigegebene private Stimmen."""

        async def anbieter() -> Angebot:
            optionen = [Option(wert="", titel="Vorgabe der Vertonung", hinweis="die Stimme ab Werk")]
            for bereich, hinweis in (("privat", "private Stimme, freigegeben"), ("katalog", "Katalog")):
                try:
                    antwort = await self.g.verbund.anfrage("GET", self.adresse(), "/api/v1/stimmen", timeout=ABFRAGE,
                                                           params={"bereich": bereich})
                except VerbundFehler as f:
                    if f.status in (401, 403):          # private Stimmen sind der Pinnwand nicht freigegeben
                        continue
                    return Angebot(optionen=optionen, stand=f"Vertonung antwortet nicht: {f.meldung}")
                optionen += [Option(wert=s["id"], titel=s["name"], hinweis=hinweis) for s in antwort.json()]
            return Angebot(optionen=optionen, eigener_wert=False, stand=f"{len(optionen) - 1} Stimmen")

        return anbieter
