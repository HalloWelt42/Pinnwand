"""Ablage der Anhänge in der Kellerwolke über den Zugang des Gerüsts; die Anwendung kennt nur die Schnittstelle `Ablage`.
Hochgeladenes liegt im Zweig der App, ein Ordner je Board (Apps/Pinnwand/Haushalt); Dateien aus der eigenen Kellerwolke
sieht die Pinnwand nur mit der Anmeldung der Person (Dateiwahl). Dazu das Ausliefern einer Datei an den Browser. Fehler
der Kellerwolke werden Ablehnungen mit Grund."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import Response

from appkern.app import Geruest, herunterladen_kopf, inhalt_reichen
from appkern.kellerwolke import (
    Kellerwolke, KellerwolkeFehler, Knoten, Konflikt, NichtErreichbar, NichtGefunden, StandVeraltet, ZuGross, pfad_aus,
)

from ..anwendung.anhaenge import Datei, Glied, Ordnerinhalt, freier_name
from ..anwendung.rahmen import Abgelehnt

#: so lange wartet ein Aufruf auf eine nicht erreichbare Kellerwolke (eine Person wartet auf die Antwort)
GEDULD_S = 10.0
#: so oft wird ein inzwischen belegter Name durch den nächsten freien ersetzt
VERSUCHE = 5
#: was der Browser im Reiter zeigt; alles andere kommt als Download, damit nichts Ausführbares im Ursprung der App läuft
ZEIGEN = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/avif", "application/pdf", "text/plain"}
ZEIGEN_GRUPPEN = ("audio/", "video/")


def abgelehnt(f: KellerwolkeFehler) -> Abgelehnt:
    if isinstance(f, NichtErreichbar):
        return Abgelehnt("Die Kellerwolke ist gerade nicht erreichbar", 503)
    if isinstance(f, ZuGross):
        return Abgelehnt("Die Kellerwolke nimmt die Datei nicht an: sie ist zu groß", 413)
    if isinstance(f, NichtGefunden):
        return Abgelehnt("Das gibt es in der Kellerwolke nicht (mehr)", 404)
    return Abgelehnt(f"Die Kellerwolke lehnt ab: {f.meldung}", 502)


def datei_aus(k: Knoten) -> Datei:
    return Datei(kennung=str(k.id), name=k.name, pfad=k.pfad, ordner=k.ist_ordner, groesse=k.groesse or 0,
                 inhaltstyp=k.inhaltstyp)


class KellerwolkeAblage:
    def __init__(self, geruest: Geruest) -> None:
        self.g = geruest

    def _kw(self) -> Kellerwolke:
        """Der aktuelle Zugang (das Gerüst baut ihn nach geänderten Einstellungen neu), mit kurzer Geduld."""
        kw = self.g.kellerwolke
        if kw is None:
            raise Abgelehnt("Die Pinnwand ist noch mit keiner Kellerwolke verbunden", 503)
        return kw.mit_geduld(GEDULD_S)

    async def ablegen(self, ordner: str, name: str, inhalt: Path, inhaltstyp: str | None) -> Datei:
        kw = self._kw()
        try:
            ort = await kw.ordner(pfad_aus((await kw.ich()).zweig, ordner))
            belegt = {k.name async for k in kw.alle_kinder(ort.id)}
            for _ in range(VERSUCHE):
                ziel = freier_name(belegt, name)
                try:
                    return datei_aus(await kw.schreiben(pfad_aus(ort.pfad, ziel), inhalt, nur_neu=True, inhaltstyp=inhaltstyp))
                except (StandVeraltet, Konflikt):
                    belegt.add(ziel)                          # inzwischen belegt: der nächste freie Name
        except KellerwolkeFehler as f:
            raise abgelehnt(f) from f
        raise Abgelehnt(f"Im Ordner {ordner} der Kellerwolke ist gerade kein Name für {name} frei", 409)

    async def verwerfen(self, datei: Datei, grund: str) -> None:
        bezug = {"bezug_art": "datei", "bezug_id": datei.kennung, "bezug_name": datei.name}
        try:
            await self._kw().loeschen(datei.kennung)
        except (KellerwolkeFehler, Abgelehnt) as f:
            await self.g.protokoll.eintragen(
                "anhang.liegengeblieben", f"{datei.pfad} ist abgelegt, hängt aber an keiner Karte ({grund}); in den "
                f"Papierkorb der Kellerwolke ging sie nicht: {f.meldung}", stufe="warnung", **bezug)
            return
        await self.g.protokoll.eintragen("anhang.verworfen", f"{datei.pfad} in den Papierkorb der Kellerwolke ({grund})",
                                         **bezug)

    async def ordnerinhalt(self, sitzung: str, ordner: str | None) -> Ordnerinhalt:
        try:
            seite = await self._kw().wahl(sitzung, ordner)
        except NichtGefunden as f:
            raise Abgelehnt("Diesen Ordner gibt es in deiner Kellerwolke nicht (mehr)", 404) from f
        except KellerwolkeFehler as f:
            raise abgelehnt(f) from f
        weg = [o.name for o in seite.kette[1:]]
        return Ordnerinhalt(
            kette=[Glied(id=str(o.id) if o.id else None, name=o.name) for o in seite.kette],
            eintraege=[Datei(kennung=str(e.id), name=e.name, pfad="/".join([*weg, e.name]), ordner=e.typ == "ordner",
                             groesse=e.groesse or 0, inhaltstyp=e.inhaltstyp)
                       for e in seite.eintraege if e.typ in ("ordner", "datei")])

    async def ausliefern(self, datei: str, name: str, request: Request) -> Response:
        """Inhalt einer Datei an den Browser, mit Bereichen (Spulen im Spieler); was er gefahrlos zeigt, im Reiter, alles
        andere als Download."""
        kw = self._kw()
        try:
            knoten = await kw.knoten(datei)
        except NichtGefunden as f:
            raise Abgelehnt("Diese Datei kann die Pinnwand in der Kellerwolke nicht (mehr) lesen", 404) from f
        except KellerwolkeFehler as f:
            raise abgelehnt(f) from f
        antwort = await inhalt_reichen(kw, knoten, request)
        typ = (knoten.inhaltstyp or "").split(";")[0].strip().lower()
        if typ in ZEIGEN or typ.startswith(ZEIGEN_GRUPPEN):
            antwort.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{quote(name)}"
        else:
            antwort.headers.update(herunterladen_kopf(name))
        antwort.headers["X-Content-Type-Options"] = "nosniff"
        return antwort
