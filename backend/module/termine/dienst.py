"""Materialisierung und Bestaetigung von Terminen.

Erzeugt aus Termin-Serien die Vorkommen-Instanzen (nur fuer Tage bis gestern,
damit am Folgetag bestaetigt werden kann), bestaetigt/lehnt sie ab und liefert
die bestaetigte Zeit als zweite Ist-Quelle.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.db import verbindung
from module.serien import wiederholung

from . import persistence as db
from .models import TerminInstanz, TerminSerie

# Ist-Quelle fuer planung/berichte: (kuerzel, datum) -> bestaetigte Minuten.
ist_minuten_je_tag_person = db.ist_minuten_je_tag_person


def _feiertage(von: date, bis: date) -> set[str]:
    """Feiertags-Datumswerte im Bereich. Logik zentral in planung (feiertage_set)."""
    from module.planung import persistence as pdb
    return pdb.feiertage_set(von.isoformat(), bis.isoformat())


def _urlaubstage(kuerzel: str | None, von: date, bis: date) -> set[str]:
    """Urlaubs-Datumswerte der Person. Logik zentral in planung (urlaubstage_set)."""
    from module.planung import persistence as pdb
    return pdb.urlaubstage_set(kuerzel, von.isoformat(), bis.isoformat())


def materialisiere(serie: TerminSerie, heute: date | None = None) -> int:
    """Legt fehlende Instanzen bis gestern an. Gibt die Anzahl neu erzeugter zurueck."""
    if not serie.aktiv:
        return 0
    heute = heute or date.today()
    gestern = heute - timedelta(days=1)
    rueckblick = max(0, int(serie.rueckblick_tage or 14))
    von = gestern - timedelta(days=rueckblick)
    if serie.start:
        try:
            von = max(von, date.fromisoformat(serie.start))
        except ValueError:
            pass
    if von > gestern:
        return 0
    feiertage = _feiertage(von, gestern) if serie.feiertage_ueberspringen else None
    urlaub = _urlaubstage(serie.kuerzel, von, gestern) if serie.urlaub_ueberspringen else set()
    erzeugt = 0
    for d in wiederholung.termine(serie, von, gestern, feiertage):
        iso = d.isoformat()
        if iso in urlaub:
            continue
        if db.instanz_existiert(serie.id, iso):
            continue
        db.erstelle_instanz(serie, iso)
        erzeugt += 1
    return erzeugt


def materialisiere_alle(heute: date | None = None) -> int:
    return sum(materialisiere(s, heute) for s in db.liste_serien())


def bestaetige(iid: str, dauer_min: int | None = None) -> TerminInstanz | None:
    inst = db.hole_instanz(iid)
    if inst is None:
        return None
    dauer = int(dauer_min) if dauer_min is not None else int(inst.geplant_min)
    return db.bestaetige(iid, max(0, dauer))


def lehne_ab(iid: str) -> TerminInstanz | None:
    if db.hole_instanz(iid) is None:
        return None
    return db.lehne_ab(iid)


def bestaetige_alle(ids: list[str] | None = None) -> int:
    """Bestaetigt schwebende Instanzen wie geplant. ids=None -> alle schwebenden."""
    if ids is None:
        ziele = [i.id for i in db.liste_instanzen(status="schwebend")]
    else:
        ziele = ids
    anzahl = 0
    for iid in ziele:
        inst = db.hole_instanz(iid)
        if inst and inst.status == "schwebend":
            db.bestaetige(iid, int(inst.geplant_min))
            anzahl += 1
    return anzahl


def init() -> None:
    """Schema anlegen und beim Start die faelligen Instanzen materialisieren."""
    db.init_db()
    try:
        materialisiere_alle()
    except Exception:
        # Materialisierung darf den Start nie verhindern.
        pass
