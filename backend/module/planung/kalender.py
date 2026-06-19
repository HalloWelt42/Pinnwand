"""Kalender-Engine: Soll je Tag und Jahres-Aggregation ueber alle Personen.

Zentrale, testbare Logik fuer den Jahreskalender. Das Tages-Soll einer Person
ergibt sich aus den Wochenstunden, reduziert in klarer Reihenfolge:

  1. Nicht-Arbeitstag (Wochenstunden am Wochentag = 0)  -> Soll 0, frei
  2. Feiertag (fuer das Bundesland der Person)           -> Soll 0, feiertag
  3. Sonderregel (Tagesregel: Jahrestag/Wochentag/       -> Soll * anteil
     Brueckentag; personenbezogen schlaegt global)
  4. Abwesenheit (Urlaub/Krankheit/...; nur wenn die     -> Soll * (1 - anteil)
     Art das Soll reduziert; Homeoffice bleibt anwesend)

Die Reports (kapazitaet.py) nutzen dieselbe Tageslogik, damit Anzeige und
Auswertung konsistent sind.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.db import verbindung

from . import persistence as db


def _ist_sek_je_tag(von: str, bis: str) -> dict[tuple[str, str], int]:
    """Geleistete Sekunden je (Person-Kuerzel, Datum). Person ueber karte.zustaendig."""
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT z.datum AS datum, k.zustaendig AS kuerzel, COALESCE(SUM(z.sekunden), 0) AS sek "
            "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
            "WHERE z.datum >= ? AND z.datum <= ? GROUP BY z.datum, k.zustaendig",
            (von, bis),
        ).fetchall()
    out: dict[tuple[str, str], int] = {}
    for r in rows:
        if r["kuerzel"]:
            out[(r["kuerzel"], r["datum"])] = int(r["sek"] or 0)
    return out


def _regeln_aufbereiten(regeln: list[dict]) -> dict:
    """Sortiert aktive Tagesregeln in schnelle Nachschlage-Strukturen."""
    jt_global: dict[tuple[int, int], float] = {}
    jt_person: dict[str, dict[tuple[int, int], float]] = {}
    wt_global: dict[int, float] = {}
    wt_person: dict[str, dict[int, float]] = {}
    brueck_aktiv = False
    brueck_anteil = 0.0
    for r in regeln:
        if not r["aktiv"]:
            continue
        if r["art"] == "brueckentag":
            if r["person_id"] is None:
                brueck_aktiv = True
                brueck_anteil = float(r["anteil"])
            continue
        if r["art"] == "jahrestag" and r["monat"] and r["tag"]:
            ziel = jt_person.setdefault(r["person_id"], {}) if r["person_id"] else jt_global
            ziel[(r["monat"], r["tag"])] = float(r["anteil"])
        elif r["art"] == "wochentag" and r["wochentag"] is not None:
            ziel = wt_person.setdefault(r["person_id"], {}) if r["person_id"] else wt_global
            ziel[r["wochentag"]] = float(r["anteil"])
    return {
        "jt_global": jt_global, "jt_person": jt_person,
        "wt_global": wt_global, "wt_person": wt_person,
        "brueck_aktiv": brueck_aktiv, "brueck_anteil": brueck_anteil,
    }


def _ist_nicht_arbeit(d: date, ws: list, feier_set: set[str]) -> bool:
    wd = d.weekday()
    if wd >= len(ws) or float(ws[wd]) == 0:
        return True
    return d.isoformat() in feier_set


def _ist_brueckentag(d: date, ws: list, feier_set: set[str]) -> bool:
    """Arbeitstag, dessen beide Nachbartage nicht gearbeitet wird (zwischen Feiertag/Wochenende)."""
    wd = d.weekday()
    if wd >= len(ws) or float(ws[wd]) == 0 or d.isoformat() in feier_set:
        return False
    return _ist_nicht_arbeit(d - timedelta(days=1), ws, feier_set) and _ist_nicht_arbeit(d + timedelta(days=1), ws, feier_set)


def _person_kontext(person: dict, all_feier: list[dict], regelinfo: dict, urlaub_je_person: dict) -> dict:
    bl = person.get("bundesland")
    feier = [f for f in all_feier if f["region"] is None or f["region"] == bl]
    return {
        "ws": person["wochenstunden"],
        "feier_set": {f["datum"] for f in feier},
        "feier_name": {f["datum"]: f["name"] for f in feier},
        "jt": regelinfo["jt_person"].get(person["id"], {}),
        "jt_global": regelinfo["jt_global"],
        "wt": regelinfo["wt_person"].get(person["id"], {}),
        "wt_global": regelinfo["wt_global"],
        "brueck_aktiv": regelinfo["brueck_aktiv"],
        "brueck_anteil": regelinfo["brueck_anteil"],
        "urlaub": urlaub_je_person.get(person["id"], {}),
    }


def _regel_anteil(d: date, ctx: dict) -> float | None:
    """Wirksamer Sonderregel-Anteil fuer den Tag (None = keine Regel). Person schlaegt global, Jahrestag schlaegt Wochentag."""
    key = (d.month, d.day)
    wd = d.weekday()
    if key in ctx["jt"]:
        return ctx["jt"][key]
    if key in ctx["jt_global"]:
        return ctx["jt_global"][key]
    if wd in ctx["wt"]:
        return ctx["wt"][wd]
    if wd in ctx["wt_global"]:
        return ctx["wt_global"][wd]
    if ctx["brueck_aktiv"] and _ist_brueckentag(d, ctx["ws"], ctx["feier_set"]):
        return ctx["brueck_anteil"]
    return None


def zelle(d: date, ctx: dict, typ_map: dict, ist_sek: int) -> dict:
    """Berechnet eine Tageszelle einer Person."""
    iso = d.isoformat()
    wd = d.weekday()
    ws = ctx["ws"]
    basis = float(ws[wd]) if wd < len(ws) else 0.0
    feier_name = ctx["feier_name"].get(iso)
    abw = ctx["urlaub"].get(iso)  # (typ, anteil) oder None
    typ = typ_map.get(abw[0]) if abw else None
    regel = None

    if feier_name is not None:
        basis = 0.0
        status = "feiertag"
    elif basis == 0:
        status = "frei"
    else:
        regel = _regel_anteil(d, ctx)
        if regel is not None:
            basis = round(basis * regel, 2)
        if abw:
            if typ and typ["reduziert_soll"]:
                basis = round(basis * (1 - float(abw[1])), 2)
            status = "anwesend" if (typ and typ["anwesend"]) else "abwesend"
        elif regel is not None and basis == 0:
            status = "frei"
        else:
            status = "anwesend"

    return {
        "datum": iso,
        "soll": round(basis, 2),
        "ist_sek": int(ist_sek or 0),
        "abw": {"typ": abw[0], "anteil": float(abw[1])} if abw else None,
        "feiertag": feier_name,
        "regel": regel,
        "status": status,
    }


def _urlaub_je_person(von: str, bis: str) -> dict[str, dict[str, tuple[str, float]]]:
    out: dict[str, dict[str, tuple[str, float]]] = {}
    for u in db.liste_urlaub(None, von, bis):
        out.setdefault(u["person_id"], {})[u["datum"]] = (u["typ"], float(u["anteil"]))
    return out


def _feiertage_gepuffert(von: str, bis: str) -> list[dict]:
    """Feiertage inkl. je einem Tag davor/danach - noetig fuer die Brueckentag-Nachbarpruefung am Rand."""
    v = (date.fromisoformat(von) - timedelta(days=1)).isoformat()
    b = (date.fromisoformat(bis) + timedelta(days=1)).isoformat()
    return db.liste_feiertage(v, b)


def tageszellen(person: dict, von: str, bis: str) -> list[dict]:
    """Tageszellen einer Person ueber einen Zeitraum (fuer Kapazitaet/Overlay)."""
    all_feier = _feiertage_gepuffert(von, bis)
    regelinfo = _regeln_aufbereiten(db.liste_tagesregeln())
    typ_map = {t["code"]: t for t in db.liste_abwesenheitstypen()}
    ctx = _person_kontext(person, all_feier, regelinfo, _urlaub_je_person(von, bis))
    ist = _ist_sek_je_tag(von, bis)
    kuerzel = person.get("kuerzel")
    out: list[dict] = []
    cur = date.fromisoformat(von)
    ende = date.fromisoformat(bis)
    while cur <= ende:
        out.append(zelle(cur, ctx, typ_map, ist.get((kuerzel, cur.isoformat()), 0)))
        cur += timedelta(days=1)
    return out


def kalender(jahr: int) -> dict:
    """Jahresaggregation ueber alle aktiven Personen je Tag (fuer den Jahreskalender)."""
    von, bis = f"{jahr}-01-01", f"{jahr}-12-31"
    personen = [p for p in db.liste_personen() if p["aktiv"]]
    all_feier = _feiertage_gepuffert(von, bis)
    regelinfo = _regeln_aufbereiten(db.liste_tagesregeln())
    typ_map = {t["code"]: t for t in db.liste_abwesenheitstypen()}
    urlaub = _urlaub_je_person(von, bis)
    ist = _ist_sek_je_tag(von, bis)

    tage: list[str] = []
    cur = date.fromisoformat(von)
    ende = date.fromisoformat(bis)
    while cur <= ende:
        tage.append(cur.isoformat())
        cur += timedelta(days=1)

    zellen: dict[str, dict[str, dict]] = {}
    for p in personen:
        ctx = _person_kontext(p, all_feier, regelinfo, urlaub)
        kuerzel = p.get("kuerzel")
        prow: dict[str, dict] = {}
        for iso in tage:
            d = date.fromisoformat(iso)
            z = zelle(d, ctx, typ_map, ist.get((kuerzel, iso), 0))
            prow[iso] = {
                "soll": z["soll"], "ist_sek": z["ist_sek"], "abw": z["abw"],
                "feiertag": z["feiertag"], "regel": z["regel"], "status": z["status"],
            }
        zellen[p["id"]] = prow

    return {
        "jahr": jahr,
        "personen": [{"id": p["id"], "name": p["name"], "kuerzel": p["kuerzel"], "farbe": p["farbe"]} for p in personen],
        "tage": tage,
        "zellen": zellen,
    }
