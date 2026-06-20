"""Berechnet die Berichtsdaten als normalisierte Struktur.

Ein Bericht besteht aus Abschnitten mit Spalten, Zeilen und optionaler
Summenzeile - so kann er einheitlich als PDF, CSV oder Markdown gerendert werden.
Zeiten werden über die Zeiteinträge gerechnet (Single Source of Truth); die
Zuordnung zu Personen läuft über das Feld 'zustaendig' der Karte.
"""
from __future__ import annotations

from app.db import verbindung


def std(sekunden: int | float) -> str:
    sek = int(sekunden or 0)
    return f"{sek // 3600}:{(sek % 3600) // 60:02d}"


def _dt(iso: str) -> str:
    """ISO-Datum '2026-06-20' -> deutsches '20.06.2026'."""
    if not iso or len(iso) < 10:
        return iso or ""
    j, m, t = iso[:10].split("-")
    return f"{t}.{m}.{j}"


def _personen_namen() -> dict[str, str]:
    with verbindung() as conn:
        try:
            rows = conn.execute("SELECT kuerzel, name FROM person").fetchall()
        except Exception:
            return {}
    return {r["kuerzel"]: r["name"] for r in rows if r["kuerzel"]}


def stundenzettel(von: str, bis: str, person: str | None = None) -> dict:
    namen = _personen_namen()
    bedingung = "AND k.zustaendig = ?" if person else ""
    args: tuple = (von, bis, person) if person else (von, bis)
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT z.datum, z.sekunden, z.kommentar, k.schluessel, k.titel, k.zustaendig "
            "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
            f"WHERE z.datum >= ? AND z.datum <= ? {bedingung} "
            "ORDER BY k.zustaendig, z.datum, z.id",
            args,
        ).fetchall()
    gruppen: dict[str, list] = {}
    for r in rows:
        gruppen.setdefault(r["zustaendig"] or "(ohne)", []).append(r)
    abschnitte = []
    for kuerzel, eintraege in sorted(gruppen.items()):
        zeilen = [
            [_dt(r["datum"]), f'{r["schluessel"] or ""} {r["titel"] or ""}'.strip(), std(r["sekunden"]), r["kommentar"] or ""]
            for r in eintraege
        ]
        summe = sum(int(r["sekunden"] or 0) for r in eintraege)
        name = namen.get(kuerzel, kuerzel)
        abschnitte.append({
            "titel": name, "spalten": ["Datum", "Aufgabe", "Dauer", "Notiz"],
            "zeilen": zeilen, "summe": ["", "Summe", std(summe), ""],
        })
    return {
        "titel": "Wochen-Stundenzettel", "zeitraum": f"{_dt(von)} bis {_dt(bis)}", "abschnitte": abschnitte,
    }


def soll_ist(board_id: str | None = None) -> dict:
    bedingung = "WHERE board_id = ?" if board_id else ""
    args: tuple = (board_id,) if board_id else ()
    with verbindung() as conn:
        rows = conn.execute(
            f"SELECT schluessel, titel, schaetzung_min, erfasst_sek FROM karte {bedingung} ORDER BY erfasst_sek DESC",
            args,
        ).fetchall()
    zeilen = []
    for r in rows:
        soll = int(r["schaetzung_min"] or 0) * 60
        ist = int(r["erfasst_sek"] or 0)
        if not soll and not ist:
            continue
        pz = f"{round(ist / soll * 100)}%" if soll else "-"
        zeilen.append([r["schluessel"] or "", r["titel"] or "", std(soll), std(ist), pz])
    return {
        "titel": "Soll / Ist", "zeitraum": "Gesamtbestand",
        "abschnitte": [{"titel": "Karten", "spalten": ["Schlüssel", "Titel", "Soll", "Ist", "Auslastung"], "zeilen": zeilen, "summe": None}],
    }


def _ist_je_person(conn, von: str, bis: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT k.zustaendig AS p, COALESCE(SUM(z.sekunden),0) AS s "
        "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
        "WHERE z.datum >= ? AND z.datum <= ? GROUP BY k.zustaendig",
        (von, bis),
    ).fetchall()
    out = {r["p"]: int(r["s"]) for r in rows if r["p"]}
    # Bestaetigte Termine als zweite Ist-Quelle hinzurechnen (Modul optional -> defensiv).
    try:
        from module.termine import dienst as _td
        for (kuerzel, _d), minuten in _td.ist_minuten_je_tag_person(von, bis).items():
            if kuerzel:
                out[kuerzel] = out.get(kuerzel, 0) + int(minuten) * 60
    except Exception:
        pass
    return out


def kapazitaet_auslastung(von: str, bis: str) -> dict:
    from module.planung import kapazitaet as kap
    from module.planung import persistence as pdb

    with verbindung() as conn:
        ist = _ist_je_person(conn, von, bis)
    zeilen = []
    for p in pdb.liste_personen():
        kuerzel = p["kuerzel"] or ""
        k = kap.kapazitaet(p["id"], von, bis)
        kap_sek = int((k["summe_std"] if k else 0) * 3600)
        ist_sek = ist.get(kuerzel, 0)
        pz = f"{round(ist_sek / kap_sek * 100)}%" if kap_sek else "-"
        zeilen.append([p["name"], std(kap_sek), std(ist_sek), pz])
    return {
        "titel": "Kapazität und Auslastung", "zeitraum": f"{_dt(von)} bis {_dt(bis)}",
        "abschnitte": [{"titel": "Personen", "spalten": ["Person", "Kapazität", "Ist", "Auslastung"], "zeilen": zeilen, "summe": None}],
    }


def zeit_je_person(von: str, bis: str) -> dict:
    namen = _personen_namen()
    with verbindung() as conn:
        ist = _ist_je_person(conn, von, bis)
    zeilen = [[namen.get(p, p), std(s)] for p, s in sorted(ist.items(), key=lambda x: -x[1])]
    summe = sum(ist.values())
    return {
        "titel": "Zeit je Person", "zeitraum": f"{_dt(von)} bis {_dt(bis)}",
        "abschnitte": [{"titel": "Personen", "spalten": ["Person", "Stunden"], "zeilen": zeilen, "summe": ["Summe", std(summe)]}],
    }


def zeit_je_karte(von: str, bis: str) -> dict:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT k.schluessel, k.titel, COALESCE(SUM(z.sekunden),0) AS s "
            "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
            "WHERE z.datum >= ? AND z.datum <= ? GROUP BY z.karte_id ORDER BY s DESC",
            (von, bis),
        ).fetchall()
    zeilen = [[r["schluessel"] or "", r["titel"] or "", std(r["s"])] for r in rows]
    summe = sum(int(r["s"]) for r in rows)
    return {
        "titel": "Zeit je Karte", "zeitraum": f"{_dt(von)} bis {_dt(bis)}",
        "abschnitte": [{"titel": "Karten", "spalten": ["Schlüssel", "Titel", "Stunden"], "zeilen": zeilen, "summe": ["", "Summe", std(summe)]}],
    }


TYPEN = {
    "stundenzettel": "Wochen-Stundenzettel",
    "soll_ist": "Soll / Ist",
    "kapazitaet": "Kapazität und Auslastung",
    "zeit_person": "Zeit je Person",
    "zeit_karte": "Zeit je Karte",
}


def erzeuge(typ: str, von: str, bis: str, person: str | None = None, board_id: str | None = None) -> dict:
    if typ == "stundenzettel":
        return stundenzettel(von, bis, person)
    if typ == "soll_ist":
        return soll_ist(board_id)
    if typ == "kapazitaet":
        return kapazitaet_auslastung(von, bis)
    if typ == "zeit_person":
        return zeit_je_person(von, bis)
    if typ == "zeit_karte":
        return zeit_je_karte(von, bis)
    raise ValueError(f"Unbekannter Berichtstyp: {typ}")
