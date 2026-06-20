"""Werkzeug-Registry der Agenten-API.

Eine einzige Definition aller Agenten-Werkzeuge (Name, Beschreibung, Scope,
Parameter-Schema, Aufruf). Darüber setzen mehrere dünne Adapter auf:
die OpenAI-Function-Schemas, der Execute-Endpunkt und der MCP-Server. So bleibt
die Wahrheit an einer Stelle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from . import persistence as db
from .aktionen import Aktionen, AktionsFehler
from .auth import Akteur


@dataclass(frozen=True)
class Werkzeug:
    name: str
    beschreibung: str
    scope: str  # "read" oder "write"
    eigenschaften: dict
    pflicht: list[str]
    aufruf: Callable[[Aktionen, dict, bool], dict]


WERKZEUGE: list[Werkzeug] = [
    Werkzeug(
        "zeit_buchen", "Bucht Arbeitszeit auf eine Karte (per Schlüssel wie R3-130, Titel oder ID).",
        "write",
        {
            "karte": {"type": "string", "description": "Kartenschlüssel, Titel oder ID"},
            "dauer": {"type": "string", "description": "Dauer, z.B. '1:30', '90min', '1,5h', '2 Std'"},
            "datum": {"type": "string", "description": "Datum, z.B. 'heute', 'gestern', '2026-06-19'"},
            "kommentar": {"type": "string", "description": "Was wurde gemacht"},
        },
        ["karte", "dauer"],
        lambda a, x, dry: a.zeit_buchen(x["karte"], x["dauer"], x.get("datum"), x.get("kommentar"), dry),
    ),
    Werkzeug(
        "karte_anlegen", "Legt eine neue Karte/Aufgabe auf einem Board an.",
        "write",
        {
            "board": {"type": "string", "description": "Board-Kürzel (z.B. R3), Titel oder ID"},
            "titel": {"type": "string"},
            "spalte": {"type": "string", "description": "Spaltentitel oder ID; sonst erste Spalte"},
            "beschreibung": {"type": "string"},
            "labels": {"type": "array", "items": {"type": "string"}},
            "prioritaet": {"type": "string", "enum": ["hoch", "mittel", "niedrig"]},
            "faellig": {"type": "string", "description": "Fälligkeit JJJJ-MM-TT"},
            "zustaendig": {"type": "string"},
            "schaetzung_min": {"type": "integer", "description": "Schätzung in Minuten"},
        },
        ["board", "titel"],
        lambda a, x, dry: a.karte_anlegen(
            x["board"], x["titel"], x.get("spalte"), x.get("beschreibung"), x.get("labels"),
            x.get("prioritaet"), x.get("faellig"), x.get("zustaendig"), x.get("schaetzung_min"), dry),
    ),
    Werkzeug(
        "erledigen", "Markiert eine Karte als erledigt (verschiebt in die Erledigt-Spalte), optional mit Abschlusszeit.",
        "write",
        {
            "karte": {"type": "string"},
            "dauer": {"type": "string", "description": "Optionale Abschlusszeit, z.B. '0:30'"},
            "kommentar": {"type": "string"},
        },
        ["karte"],
        lambda a, x, dry: a.erledigen(x["karte"], x.get("dauer"), x.get("kommentar"), dry),
    ),
    Werkzeug(
        "kommentieren", "Hängt einen Kommentar an eine Karte.",
        "write",
        {"karte": {"type": "string"}, "text": {"type": "string"}},
        ["karte", "text"],
        lambda a, x, dry: a.kommentieren(x["karte"], x["text"], dry),
    ),
    Werkzeug(
        "erfassen", "Erfasst eine Zeitbuchung aus freiem Text (z.B. '2 Std an R3-130, Toleranzen geprüft').",
        "write",
        {"text": {"type": "string"}},
        ["text"],
        lambda a, x, dry: a.erfasse_freitext(x["text"], dry),
    ),
    Werkzeug(
        "suche", "Durchsucht Karteninhalte nach einem Begriff.",
        "read",
        {"q": {"type": "string"}, "limit": {"type": "integer"}},
        ["q"],
        lambda a, x, dry: a.suchen(x["q"], int(x.get("limit", 10))),
    ),
    Werkzeug(
        "briefing", "Was steht an: überfällige, heute/diese Woche fällige und laufende Aufgaben.",
        "read",
        {"datum": {"type": "string", "description": "Bezugsdatum, Standard heute"}},
        [],
        lambda a, x, dry: a.briefing(x.get("datum")),
    ),
]

_NACH_NAME = {w.name: w for w in WERKZEUGE}


def openai_schemas() -> list[dict]:
    """Werkzeuge im OpenAI-Function-Calling-Format."""
    schemas = []
    for w in WERKZEUGE:
        schemas.append({
            "type": "function",
            "function": {
                "name": w.name,
                "description": w.beschreibung,
                "parameters": {
                    "type": "object",
                    "properties": w.eigenschaften,
                    "required": w.pflicht,
                },
            },
        })
    return schemas


def _ziel(ergebnis: dict) -> str | None:
    karte = ergebnis.get("karte")
    if isinstance(karte, dict):
        return karte.get("schluessel") or karte.get("id")
    return ergebnis.get("board_id")


def fuehre_aus(name: str, argumente: dict, akteur: Akteur,
               dry_run: bool = False, idempotenz_schluessel: str | None = None) -> dict:
    """Führt ein Werkzeug aus: Scope-Prüfung, Idempotenz, Trockenlauf, Audit."""
    w = _NACH_NAME.get(name)
    if w is None:
        raise AktionsFehler(f"Unbekanntes Werkzeug '{name}'", status=404)
    if not akteur.hat(w.scope):
        raise AktionsFehler(f"Scope '{w.scope}' erforderlich", status=403)
    a = Aktionen(akteur.name)
    schreibt = w.scope == "write"

    if schreibt and not dry_run and idempotenz_schluessel:
        treffer = db.idempotenz_treffer(akteur.name, idempotenz_schluessel)
        if treffer is not None:
            return {**treffer, "wiederholt": True}

    try:
        ergebnis = w.aufruf(a, argumente or {}, dry_run)
    except AktionsFehler as e:
        db.protokolliere(akteur.name, name, None, "fehler", {"fehler": e.nachricht})
        raise
    except KeyError as e:
        fehlend = str(e).strip("'")
        db.protokolliere(akteur.name, name, None, "fehler", {"fehler": f"Pflichtfeld fehlt: {fehlend}"})
        raise AktionsFehler(f"Pflichtfeld fehlt: {fehlend}")

    if schreibt and dry_run:
        db.protokolliere(akteur.name, name, _ziel(ergebnis), "vorschau", None)
    elif schreibt:
        db.idempotenz_merke(akteur.name, idempotenz_schluessel, ergebnis)
        db.protokolliere(akteur.name, name, _ziel(ergebnis), "ok", None)
    else:
        db.protokolliere(akteur.name, name, None, "ok", None)
    return ergebnis
