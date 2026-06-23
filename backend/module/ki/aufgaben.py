"""Aufgaben-Registry des KI-Assistenten (Dispatcher).

Jede KI-Aufgabe ist eine austauschbare Einheit hinter einer klaren Schnittstelle:
sie baut aus Kontext + Anweisung des Nutzers einen Prompt und deutet die
JSON-Antwort des Modells in eine Liste korrigierbarer Vorschlaege. Neue
datenreiche Stellen docken an, indem sie eine vorhandene Aufgabe nutzen oder eine
neue hier registrieren - der Rest (HTTP, Modellaufruf, Oberflaeche) bleibt gleich.

Ein Vorschlag ist immer gleich geformt, damit die Oberflaeche ihn einheitlich als
Checkliste zeigen kann: {id, text, begruendung, vorgewaehlt}. Die aufrufende
Stelle entscheidet selbst, was "Uebernehmen" konkret tut - die KI schlaegt nur vor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import modell

# Schutz vor Riesen-Prompts: grosse Listen werden gekappt, lange Texte gekuerzt.
_MAX_ELEMENTE = 300
_MAX_TEXT = 240


def _kurz(text: object, grenze: int = _MAX_TEXT) -> str:
    s = str(text or "").strip().replace("\n", " ")
    return s[:grenze]


@dataclass(frozen=True)
class Aufgabe:
    typ: str
    beschreibung: str
    baue: Callable[[dict, str], tuple[str, str]]   # (kontext, anweisung) -> (system, nutzer)
    deute: Callable[[dict, dict], list[dict]]      # (roh_json, kontext) -> Vorschlaege


# --- auswahl: aus einer grossen Liste die zur Anweisung passenden Eintraege waehlen ---

def _auswahl_baue(kontext: dict, anweisung: str) -> tuple[str, str]:
    elemente = (kontext.get("elemente") or [])[:_MAX_ELEMENTE]
    zeilen = [f"{e.get('id')}\t{_kurz(e.get('text'))}" for e in elemente]
    system = (
        "Du hilfst, aus einer Liste die zur Anweisung passenden Eintraege auszuwaehlen. "
        "Waehle nur wirklich passende; im Zweifel weglassen. "
        'Form: {"auswahl": [{"id": "<id aus der Liste>", "begruendung": "<kurz, deutsch>"}]}.'
    )
    nutzer = (
        f"Anweisung: {anweisung or 'Die wahrscheinlich relevanten Eintraege.'}\n\n"
        f"Liste (je Zeile: id<TAB>Text):\n" + "\n".join(zeilen)
    )
    return system, nutzer


def _auswahl_deute(roh: dict, kontext: dict) -> list[dict]:
    nach_id = {str(e.get("id")): _kurz(e.get("text")) for e in (kontext.get("elemente") or [])}
    ergebnis: list[dict] = []
    for eintrag in (roh.get("auswahl") or []):
        eid = str(eintrag.get("id"))
        if eid in nach_id and not any(v["id"] == eid for v in ergebnis):
            ergebnis.append({
                "id": eid,
                "text": nach_id[eid],
                "begruendung": _kurz(eintrag.get("begruendung"), 200),
                "vorgewaehlt": True,
            })
    return ergebnis


# --- labels: aus Titel/Beschreibung einer Karte Schlagworte vorschlagen ---

def _labels_baue(kontext: dict, anweisung: str) -> tuple[str, str]:
    vorhanden = ", ".join(_kurz(x, 40) for x in (kontext.get("vorhandene_labels") or [])) or "(keine)"
    system = (
        "Du schlaegst kurze, treffende Schlagworte (Labels) fuer eine Aufgabenkarte vor. "
        "Bevorzuge bereits vorhandene Labels, wenn sie passen; sonst praegnante neue (ein bis zwei Worte, kleingeschrieben). "
        'Form: {"labels": [{"name": "<label>", "begruendung": "<kurz, deutsch>"}]}. Hoechstens 6.'
    )
    nutzer = (
        f"Titel: {_kurz(kontext.get('titel'), 200)}\n"
        f"Beschreibung: {_kurz(kontext.get('beschreibung'), 600)}\n"
        f"Vorhandene Labels im Board: {vorhanden}\n"
        f"Zusatz-Anweisung: {anweisung or '(keine)'}"
    )
    return system, nutzer


def _labels_deute(roh: dict, kontext: dict) -> list[dict]:
    schon = {str(x).lower() for x in (kontext.get("bereits_an_karte") or [])}
    ergebnis: list[dict] = []
    for eintrag in (roh.get("labels") or []):
        name = _kurz(eintrag.get("name"), 40)
        if not name or name.lower() in schon or any(v["id"].lower() == name.lower() for v in ergebnis):
            continue
        ergebnis.append({
            "id": name,
            "text": name,
            "begruendung": _kurz(eintrag.get("begruendung"), 200),
            "vorgewaehlt": True,
        })
    return ergebnis


# --- filter: aus einer Wunsch-Beschreibung eine Filter-Kombination vorschlagen ---

def _filter_baue(kontext: dict, anweisung: str) -> tuple[str, str]:
    labels = ", ".join(_kurz(x, 40) for x in (kontext.get("labels") or [])) or "(keine)"
    prioritaeten = ", ".join(kontext.get("prioritaeten") or ["hoch", "mittel", "niedrig"])
    sortierungen = ", ".join(kontext.get("sortierungen") or [])
    system = (
        "Du schlaegst eine Filter-Kombination fuer ein Aufgaben-Board vor. "
        "Nutze nur vorhandene Labels und gueltige Werte. Felder duerfen null sein. "
        'Form: {"labels": ["<label>"], "prioritaet": "<wert|null>", '
        '"sortierung": "<wert|null>", "begruendung": "<kurz, deutsch>"}.'
    )
    nutzer = (
        f"Wunsch: {anweisung or 'Sinnvolle Ansicht.'}\n"
        f"Verfuegbare Labels: {labels}\n"
        f"Prioritaeten: {prioritaeten}\n"
        f"Sortierungen: {sortierungen or '(Standard)'}"
    )
    return system, nutzer


def _filter_deute(roh: dict, kontext: dict) -> list[dict]:
    erlaubte_labels = {str(x).lower(): str(x) for x in (kontext.get("labels") or [])}
    erlaubte_prio = {str(x).lower() for x in (kontext.get("prioritaeten") or ["hoch", "mittel", "niedrig"])}
    erlaubte_sort = {str(x).lower() for x in (kontext.get("sortierungen") or [])}
    grund = _kurz(roh.get("begruendung"), 200)
    ergebnis: list[dict] = []
    for lab in (roh.get("labels") or []):
        key = str(lab).lower()
        if key in erlaubte_labels:
            ergebnis.append({"id": f"label:{erlaubte_labels[key]}", "text": f"Label: {erlaubte_labels[key]}",
                             "begruendung": grund, "vorgewaehlt": True})
    prio = roh.get("prioritaet")
    if prio and str(prio).lower() in erlaubte_prio:
        ergebnis.append({"id": f"prioritaet:{str(prio).lower()}", "text": f"Prioritaet: {prio}",
                         "begruendung": grund, "vorgewaehlt": True})
    sort = roh.get("sortierung")
    if sort and (not erlaubte_sort or str(sort).lower() in erlaubte_sort):
        ergebnis.append({"id": f"sortierung:{str(sort).lower()}", "text": f"Sortierung: {sort}",
                         "begruendung": grund, "vorgewaehlt": True})
    return ergebnis


AUFGABEN: dict[str, Aufgabe] = {
    a.typ: a
    for a in [
        Aufgabe("auswahl", "Aus einer grossen Liste die passenden Eintraege waehlen", _auswahl_baue, _auswahl_deute),
        Aufgabe("labels", "Schlagworte fuer eine Karte vorschlagen", _labels_baue, _labels_deute),
        Aufgabe("filter", "Eine Filter-Kombination fuer ein Board vorschlagen", _filter_baue, _filter_deute),
    ]
}


def typen() -> list[dict]:
    return [{"typ": a.typ, "beschreibung": a.beschreibung} for a in AUFGABEN.values()]


def fuehre_aus(typ: str, kontext: dict, anweisung: str) -> dict:
    """Fuehrt eine KI-Aufgabe aus und liefert korrigierbare Vorschlaege.

    Wirft nie wegen Modellproblemen: bei nicht erreichbarem/leerem Modell kommt
    ok=False mit leeren Vorschlaegen zurueck. ValueError nur bei unbekanntem Typ.
    """
    aufgabe = AUFGABEN.get(typ)
    if aufgabe is None:
        raise ValueError(f"Unbekannter KI-Aufgabentyp '{typ}'")
    kontext = kontext or {}
    system, nutzer = aufgabe.baue(kontext, anweisung or "")
    roh = modell.chat_json(system, nutzer)
    if roh is None:
        return {"ok": False, "modell": None, "vorschlaege": [], "fehler": "kein-modell"}
    vorschlaege = aufgabe.deute(roh, kontext)
    return {"ok": True, "modell": modell.waehle_modell(), "vorschlaege": vorschlaege, "fehler": None}
