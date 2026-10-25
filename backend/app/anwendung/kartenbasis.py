"""Lesen und Schreiben einer Karte für alle Bereiche: lesen (oder abgelehnt, wenn es sie nicht gibt), die Karten einer
Spalte in ihrer Reihe, eine Zeile im Verlauf, speichern. Liegt für sich, damit Karten und Zeiterfassung einander nutzen
können."""

from __future__ import annotations

from ..modell import Auslass, Ereignis, Karte, Kennung, Serie
from .rahmen import Abgelehnt, Kontext


def karte_lesen(k: Kontext, karte_id: Kennung) -> Karte:
    d = k.s.lies("karten", karte_id)
    if d is None:
        raise Abgelehnt("Diese Karte gibt es nicht (mehr)", 404)
    return Karte.model_validate(d)


def karten_der_spalte(k: Kontext, spalte_id: Kennung) -> list[Karte]:
    return [Karte.model_validate(d) for d in k.s.alle("karten", "spalte=?", (spalte_id,), "reihe")]


def vermerken(k: Kontext, karte: Karte, text: str) -> None:
    """Eine Zeile im Verlauf der Karte (M-64)."""
    karte.verlauf.append(Ereignis(zeit=k.jetzt, von=k.konto.id, text=text))


def speichern(k: Kontext, karte: Karte) -> Karte:
    return Karte.model_validate(k.s.schreib("karten", karte.json_daten()))


def gruppen_aufraeumen(k: Kontext, board_id: Kennung, gruppen: set[Kennung]) -> None:
    """Gruppen, aus denen Karten gingen (Papierkorb, anderes Board): bleibt nur eine Karte übrig, endet die Gruppe (wie
    beim Lösen)."""
    for g in gruppen:
        rest = [Karte.model_validate(d) for d in k.s.alle("karten", "board=?", (board_id,)) if d.get("gruppe") == g]
        if len(rest) < 2:
            for x in rest:
                x.gruppe = None
                speichern(k, x)
            k.s.loesch("gruppen", g)


def serientag_auslassen(k: Kontext, c: Karte) -> None:
    """Geht die Karte eines Serientags (Papierkorb, anderes Board), kommt der Tag nicht wieder (M-108)."""
    d = k.s.lies("serien", c.serie) if c.serie else None
    if d is None or not c.faellig:
        return
    s = Serie.model_validate(d)
    if not any(a.tag == c.faellig for a in s.auslass):
        s.auslass = [*s.auslass, Auslass(tag=c.faellig, von=k.konto.id, am=k.jetzt)]
        k.s.schreib("serien", s.json_daten())


def serientag_zurueck(k: Kontext, c: Karte) -> None:
    """Kommt die Karte eines Serientags aus dem Papierkorb zurück, nimmt das den Auslass ihres Tags zurück."""
    d = k.s.lies("serien", c.serie) if c.serie else None
    if d is None:
        return
    s = Serie.model_validate(d)
    if any(a.tag == c.faellig for a in s.auslass):
        s.auslass = [a for a in s.auslass if a.tag != c.faellig]
        k.s.schreib("serien", s.json_daten())
