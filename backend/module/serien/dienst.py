"""Vorbuchung: erzeugt aus Serien die kommenden Karten-Instanzen.

Idempotent: pro Serie und Datum entsteht höchstens eine Karte (Markierung an
der Karte). Die Instanzen sind normale Karten - mit Fälligkeit, geplanter Zeit
(Soll) und damit Timer-fähig.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db import verbindung
from module.kanban_kern import persistence as k

from . import persistence as db, wiederholung


def _zielspalte(serie: dict) -> str | None:
    if serie.get("spalte_id"):
        return serie["spalte_id"]
    with verbindung() as conn:
        r = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge LIMIT 1", (serie["board_id"],)
        ).fetchone()
    return r["id"] if r else None


def materialisiere(serie: dict, heute: date | None = None) -> int:
    """Legt fehlende Instanzen der Serie im Vorlauf-Zeitraum an. Gibt die Anzahl zurück."""
    if not serie.get("aktiv"):
        return 0
    heute = heute or date.today()
    bis = heute + timedelta(days=max(0, int(serie.get("vorlauf_tage") or 14)))
    spalte = _zielspalte(serie)
    if not spalte:
        return 0
    erzeugt = 0
    for d in wiederholung.termine(serie, heute, bis):
        iso = d.isoformat()
        if k.serien_instanz_existiert(serie["id"], iso):
            continue
        titel = serie["titel"]
        if serie.get("uhrzeit"):
            titel = f"{serie['uhrzeit']} {titel}"
        karte = k.erstelle_karte(
            karte_id="k_" + uuid4().hex[:8], board_id=serie["board_id"], spalte=spalte,
            titel=titel, beschreibung=serie.get("beschreibung"), labels=serie.get("labels") or [],
            prioritaet=None, cover=None, start=None, faellig=iso, zustaendig=serie.get("zustaendig"),
        )
        if serie.get("dauer_min"):
            k.aktualisiere_karte(karte.id, {"schaetzung_min": serie["dauer_min"]})
        k.markiere_serie(karte.id, serie["id"], iso)
        erzeugt += 1
    return erzeugt


def materialisiere_alle(heute: date | None = None) -> int:
    return sum(materialisiere(s, heute) for s in db.liste())


def init() -> None:
    """Schema anlegen und beim Start die anstehenden Instanzen vorbuchen."""
    db.init_db()
    try:
        materialisiere_alle()
    except Exception:
        # Vorbuchung darf den Start nie verhindern.
        pass
