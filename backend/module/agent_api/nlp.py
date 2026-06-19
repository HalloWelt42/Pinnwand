"""Natuerlichsprachige Erfassung - hybrid und KI-optional.

Die deterministische Auswertung (Dauer, Datum, Kartenbezug) funktioniert immer.
Ist ein LLM konfiguriert, darf es zusaetzlich Felder vorschlagen; das Ergebnis
wird anschliessend deterministisch validiert. Faellt das LLM aus, bleibt die
regelbasierte Auswertung bestehen.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta

import httpx

from app.config import einstellungen

_WOCHENTAGE = {
    "montag": 0, "mo": 0,
    "dienstag": 1, "di": 1,
    "mittwoch": 2, "mi": 2,
    "donnerstag": 3, "do": 3,
    "freitag": 4, "fr": 4,
    "samstag": 5, "sa": 5,
    "sonntag": 6, "so": 6,
}

# Kartenschluessel wie R3-130, ABC-7
_SCHLUESSEL = re.compile(r"\b([A-Za-z][A-Za-z0-9]*-\d+)\b")


def parse_dauer(text: str) -> int | None:
    """Wandelt eine Dauerangabe in Sekunden. Versteht '1:30', '1,5h', '90min', '2 Std', '45m'."""
    if not text:
        return None
    s = text.strip().lower().replace(",", ".")

    m = re.search(r"(\d{1,3}):([0-5]?\d)", s)
    if m:
        return (int(m.group(1)) * 60 + int(m.group(2))) * 60

    m = re.search(r"(\d+(?:\.\d+)?)\s*(h|std|stunde|stunden)\b", s)
    if m:
        sek = int(round(float(m.group(1)) * 3600))
        rest = re.search(r"(\d+)\s*(m|min|minute|minuten)\b", s)
        if rest:
            sek += int(rest.group(1)) * 60
        return sek

    m = re.search(r"(\d+)\s*(m|min|minute|minuten)\b", s)
    if m:
        return int(m.group(1)) * 60

    # Reine Zahl: als Stunden interpretieren (z.B. '1.5').
    m = re.fullmatch(r"\d+(?:\.\d+)?", s)
    if m:
        return int(round(float(s) * 3600))
    return None


def parse_datum(text: str | None, heute: date | None = None) -> str:
    """Wandelt eine Datumsangabe in ISO (JJJJ-MM-TT). Standard: heute."""
    heute = heute or date.today()
    if not text:
        return heute.isoformat()
    s = text.strip().lower()

    if s in ("heute", "today"):
        return heute.isoformat()
    if s in ("gestern", "yesterday"):
        return (heute - timedelta(days=1)).isoformat()
    if s == "vorgestern":
        return (heute - timedelta(days=2)).isoformat()

    if s in _WOCHENTAGE:
        ziel = _WOCHENTAGE[s]
        delta = (heute.weekday() - ziel) % 7
        return (heute - timedelta(days=delta)).isoformat()

    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", s)
    if m:
        return m.group(0)

    m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", s)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.?\b", s)
    if m:
        return f"{heute.year:04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    return heute.isoformat()


def _datum_stichwort(text: str) -> str | None:
    s = text.lower()
    for w in ("vorgestern", "gestern", "heute"):
        if w in s:
            return w
    for name in _WOCHENTAGE:
        if re.search(rf"\b{name}\b", s):
            return name
    m = re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\.\d{1,2}\.(?:\d{4})?\b", s)
    return m.group(0) if m else None


def extrahiere_regelbasiert(text: str, heute: date | None = None) -> dict:
    """Deterministische Auswertung: Kartenbezug, Dauer, Datum, Restkommentar."""
    rest = text.strip()

    schluessel = None
    m = _SCHLUESSEL.search(rest)
    if m:
        schluessel = m.group(1)
        rest = (rest[: m.start()] + rest[m.end() :]).strip()

    dauer_sek = None
    dm = re.search(r"\d{1,3}:[0-5]?\d|\d+(?:[.,]\d+)?\s*(?:h|std|stunde|stunden|m|min|minute|minuten)\b", rest, re.I)
    if dm:
        dauer_sek = parse_dauer(dm.group(0))
        rest = (rest[: dm.start()] + rest[dm.end() :]).strip()

    datum_wort = _datum_stichwort(rest)
    datum = parse_datum(datum_wort, heute)
    if datum_wort:
        rest = re.sub(re.escape(datum_wort), "", rest, count=1, flags=re.I).strip()

    kommentar = re.sub(r"^[\s,;:\-]+|[\s,;:\-]+$", "", rest)
    kommentar = re.sub(r"\b(an|fuer|für|auf|am|um|von|std|stunden)\b", "", kommentar, flags=re.I).strip()
    kommentar = re.sub(r"\s{2,}", " ", kommentar).strip(" ,;:-")

    return {
        "karte": schluessel,
        "dauer_sek": dauer_sek,
        "datum": datum,
        "kommentar": kommentar or None,
        "quelle": "regel",
    }


def _llm_extraktion(text: str) -> dict | None:
    """Optionaler LLM-Vorschlag. Liefert None, wenn kein LLM konfiguriert/erreichbar ist."""
    if not einstellungen.llm_url:
        return None
    system = (
        "Extrahiere aus der Notiz strukturierte Felder fuer eine Zeitbuchung. "
        "Antworte ausschliesslich mit JSON: {\"karte\": string|null, \"dauer\": string|null, "
        "\"datum\": string|null, \"kommentar\": string|null}. dauer als '1:30' oder '90min'."
    )
    try:
        antwort = httpx.post(
            einstellungen.llm_url.rstrip("/") + "/v1/chat/completions",
            json={
                "model": einstellungen.embedding_model or "local-model",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
                "stream": False,
            },
            timeout=20.0,
        )
        if antwort.status_code >= 400:
            return None
        inhalt = antwort.json()["choices"][0]["message"]["content"]
        roh = re.search(r"\{.*\}", inhalt, re.S)
        if not roh:
            return None
        return json.loads(roh.group(0))
    except Exception:
        return None


def erfasse(text: str, heute: date | None = None) -> dict:
    """Hybride Auswertung: LLM-Vorschlag (falls vorhanden), deterministisch validiert."""
    basis = extrahiere_regelbasiert(text, heute)
    vorschlag = _llm_extraktion(text)
    if not vorschlag:
        return basis

    # LLM-Felder uebernehmen, aber deterministisch validieren/normalisieren.
    ergebnis = dict(basis)
    ergebnis["quelle"] = "hybrid"
    if vorschlag.get("karte"):
        ergebnis["karte"] = str(vorschlag["karte"]).strip()
    if vorschlag.get("dauer"):
        sek = parse_dauer(str(vorschlag["dauer"]))
        if sek:
            ergebnis["dauer_sek"] = sek
    if vorschlag.get("datum"):
        ergebnis["datum"] = parse_datum(str(vorschlag["datum"]), heute)
    if vorschlag.get("kommentar"):
        ergebnis["kommentar"] = str(vorschlag["kommentar"]).strip() or ergebnis["kommentar"]
    return ergebnis
