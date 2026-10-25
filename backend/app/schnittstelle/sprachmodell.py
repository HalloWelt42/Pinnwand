"""Sprachmodell für KI an der Karte über die Leitstelle des Gerüsts; die Anwendung kennt nur den Anschluss
`Sprachmodell`. Das Modell kommt aus der Einstellung `ki_modell` (leer: die Kette der App), die Priorität ist hoch,
weil eine Person auf die Antwort wartet. Fehler der Leitstelle werden Ablehnungen mit Grund; nichts wartet still."""

from __future__ import annotations

import logging
from typing import Any

from appkern.app import Geruest
from appkern.leitstelle import LeitstellenFehler, Nachricht, antwortform, json_lesen

from ..anwendung.ki import Auftrag
from ..anwendung.rahmen import Abgelehnt

log = logging.getLogger("pinnwand.ki")
#: so frei formuliert das Modell (niedrig: nah an der Karte)
TEMPERATUR = 0.2


class LeitstellenModell:
    def __init__(self, geruest: Geruest) -> None:
        self.g = geruest

    def bereit(self) -> bool:
        return self.g.leitstelle is not None

    async def fragen(self, auftrag: Auftrag) -> dict[str, Any]:
        ls = self.g.leitstelle
        if ls is None:
            raise Abgelehnt("Die Leitstelle ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)
        try:
            antwort = await ls.chat([Nachricht.system(auftrag.anweisung), auftrag.text], modell=self.g.einstellungen.stand.ki_modell or None,
                                    titel=auftrag.titel, prioritaet="hoch", response_format=antwortform(auftrag.name, auftrag.schema),
                                    temperature=TEMPERATUR, max_tokens=auftrag.laenge)
        except LeitstellenFehler as f:
            raise Abgelehnt(f"Die Leitstelle kann gerade nicht: {f.meldung}", 503) from f
        if antwort.abgebrochen:
            raise Abgelehnt("Der Auftrag wurde in der Leitstelle abgebrochen", 503)
        if antwort.ende == "length":
            raise Abgelehnt("Die Antwort des Modells brach ab, bevor sie fertig war; noch einmal versuchen oder den Text kürzen", 502)
        try:
            daten = json_lesen(antwort.text)
        except ValueError:
            daten = None
        if not isinstance(daten, dict):
            log.warning("Antwort von %s auf %s nicht lesbar: %.300s", antwort.modell, auftrag.name, antwort.text)
            raise Abgelehnt("Die Antwort des Modells war nicht lesbar; noch einmal versuchen", 502)
        return daten
