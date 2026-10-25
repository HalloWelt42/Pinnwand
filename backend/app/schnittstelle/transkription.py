"""Die Transkription über den Verbund des Gerüsts; die Anwendung kennt nur den Anschluss `Transkription`. Gefragt wird
mit dem App-Schlüssel der Pinnwand im Auftrag der Person (ihre Sitzung), die Adresse steht in der Einstellung
`transkription_adresse`. Fehler der Transkription werden Ablehnungen mit Grund."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import Response

from appkern.app import Geruest
from appkern.verbund import ABFRAGE, VerbundFehler

from ..anwendung.rahmen import Abgelehnt
from ..anwendung.transkripte import Abschnitt, Fundstelle, Transkriptinhalt, Treffer, Trefferseite


def abgelehnt(f: VerbundFehler) -> Abgelehnt:
    if f.status is None:
        if f.meldung == "nicht eingerichtet":
            return Abgelehnt("Die Transkription ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)
        return Abgelehnt(f"Die Transkription ist gerade nicht erreichbar ({f.meldung})", 503)
    if f.status in (401, 403):
        return Abgelehnt(f"Die Transkription lässt dich nicht zu: {f.meldung}", 403)
    if f.status == 404:
        return Abgelehnt("Dieses Transkript gibt es in der Transkription nicht (mehr)", 404)
    if f.status == 413:
        return Abgelehnt(f.meldung, 413)
    return Abgelehnt(f"Die Transkription meldet: {f.meldung}", 502)


class VerbundTranskription:
    def __init__(self, geruest: Geruest) -> None:
        self.g = geruest

    def adresse(self) -> str:
        return self.g.einstellungen.stand.transkription_adresse.strip().rstrip("/")

    async def suchen(self, sitzung: str, text: str, ab: int, anzahl: int) -> Trefferseite:
        try:
            antwort = await self.g.verbund.anfrage("GET", self.adresse(), "/api/v1/transkripte", sitzung=sitzung,
                                                   timeout=ABFRAGE, params={"suche": text, "ab": ab, "anzahl": anzahl})
        except VerbundFehler as f:
            raise abgelehnt(f) from f
        seite = antwort.json()
        return Trefferseite(gesamt=seite.get("gesamt", 0), ab=seite.get("ab", ab), treffer=[
            Treffer(transkript=str(e["id"]), name=e["name"], dauer_s=e.get("dauer_s") or 0.0,
                    fundstellen=[Fundstelle(zeit=s["zeit"], ausschnitt=s.get("ausschnitt") or "")
                                 for s in e.get("fundstellen") or []])
            for e in seite.get("eintraege") or []])

    async def lesen(self, sitzung: str, transkript: str) -> Transkriptinhalt:
        try:
            antwort = await self.g.verbund.anfrage("GET", self.adresse(), f"/api/v1/transkripte/{transkript}",
                                                   sitzung=sitzung, timeout=ABFRAGE)
        except VerbundFehler as f:
            raise abgelehnt(f) from f
        daten = antwort.json()
        t = daten["transkript"]
        namen = {s["kennung"]: s["name"] for s in t.get("sprecher") or []}
        return Transkriptinhalt(id=str(daten["id"]), name=t["name"], dauer_s=t.get("dauer_s") or 0.0, abschnitte=[
            Abschnitt(start=s["start"], ende=s["ende"], sprecher=namen.get(s.get("sprecher") or "", s.get("sprecher")),
                      text=s["text"])
            for s in t.get("segmente") or []])

    async def hoeren(self, sitzung: str, inhalt: bytes, dateiname: str, typ: str) -> str:
        try:
            antwort = await self.g.verbund.anfrage("POST", self.adresse(), "/api/v1/hoeren", sitzung=sitzung,
                                                   files={"datei": (dateiname, inhalt, typ)})
        except VerbundFehler as f:
            raise abgelehnt(f) from f
        return str(antwort.json().get("text") or "")

    async def ton(self, transkript: str, request: Request, sitzung: str) -> Response:
        """Die Abspielfassung der Aufnahme, mit Bereichen durchgereicht."""
        try:
            return await self.g.verbund.durchreichen(self.adresse(), f"/api/v1/inhalt/transkripte/{transkript}/ton",
                                                     request, sitzung=sitzung)
        except VerbundFehler as f:
            raise abgelehnt(f) from f
