"""Serien-Haertung: stabiler Startdatum-Anker, Auslass-Marker, Monatstag-Clamp,
Pause/Reaktivieren ohne Rueckwirkung, Verlauf-Schutz beim Loeschen und
Nachziehen offener Vorbuchungen.
"""
from __future__ import annotations

from datetime import date, timedelta

from module.kanban_kern import persistence as kdb
from module.serien import wiederholung


class _Regel:
    def __init__(self, **kw):
        self.typ = kw.get("typ", "taeglich")
        self.intervall = kw.get("intervall", 1)
        self.wochentage = kw.get("wochentage", [])
        self.monatstag = kw.get("monatstag")
        self.monatsregel = kw.get("monatsregel", "tag")
        self.start = kw.get("start")
        self.ende = kw.get("ende")
        self.wochenenden_ueberspringen = kw.get("we", False)
        self.feiertage_ueberspringen = kw.get("ft", False)


def test_intervall_anker_bleibt_stabil_bei_wanderndem_fenster():
    """'alle 2 Tage' mit festem Start: auch wenn das Abfragefenster wandert,
    bleiben die Abstaende exakt 2 Tage (kein Kollaps zu taeglich)."""
    start = date(2026, 3, 2)
    r = _Regel(typ="taeglich", intervall=2, start=start.isoformat())
    gesamt: list[date] = []
    fenster_von = start
    for _ in range(5):
        fenster_bis = fenster_von + timedelta(days=3)
        gesamt.extend(wiederholung.termine(r, fenster_von, fenster_bis))
        fenster_von = fenster_bis + timedelta(days=1)
    abstaende = {(b - a).days for a, b in zip(gesamt, gesamt[1:])}
    assert abstaende == {2}


def test_monatstag_31_klemmt_auf_monatsende():
    r = _Regel(typ="monatlich", monatstag=31, start="2026-01-31")
    treffer = wiederholung.termine(r, date(2026, 1, 1), date(2026, 6, 30))
    monate = [(d.month, d.day) for d in treffer]
    assert (2, 28) in monate  # Februar faellt nicht mehr aus
    assert (4, 30) in monate
    assert (1, 31) in monate and (3, 31) in monate


def _serie(client, board_id, **extra):
    daten = {"board_id": board_id, "titel": "Haertung", "typ": "taeglich", "vorlauf_tage": 3}
    daten.update(extra)
    r = client.post("/api/serien", json=daten)
    assert r.status_code == 201, r.text
    return r.json()


def _board(client, titel):
    m = client.post("/api/kanban/mappen", json={"titel": f"SH {titel}"}).json()
    return client.get(f"/api/kanban/mappen/{m['id']}/boards").json()[0]


def _serienkarten(client, sid):
    # serie_id ist kein API-Feld - direkt in der Test-DB nachsehen.
    with kdb._verb() as conn:
        rows = conn.execute(
            "SELECT id, faellig, titel, zustaendig, spalte, serie_id FROM karte WHERE serie_id = ?", (sid,)
        ).fetchall()
    return [dict(r) for r in rows]


def test_start_default_wird_gesetzt(client):
    b = _board(client, "Startdefault")
    s = _serie(client, b["id"])
    assert s["start"] == date.today().isoformat()


def test_geloeschte_instanz_kommt_nicht_wieder(client):
    b = _board(client, "Auslass")
    s = _serie(client, b["id"])
    karten = _serienkarten(client, s["id"])
    assert karten, "Vorbuchung fehlt"
    heute = date.today().isoformat()
    ziel = next((k for k in karten if k["faellig"] == heute), karten[0])
    assert client.delete(f"/api/kanban/karten/{ziel['id']}").status_code == 204
    # Erneutes Vorbuchen legt die bewusst geloeschte Instanz NICHT neu an.
    client.post(f"/api/serien/{s['id']}/vorbuchen")
    daten = {k["faellig"] for k in _serienkarten(client, s["id"])}
    assert ziel["faellig"] not in daten


def test_pause_raeumt_und_reaktivieren_ohne_rueckwirkung(client):
    b = _board(client, "Pause")
    s = _serie(client, b["id"], vorlauf_tage=5)
    vorher = _serienkarten(client, s["id"])
    assert len(vorher) >= 3
    # Pausieren entfernt offene Zukunfts-Vorbuchungen.
    assert client.patch(f"/api/serien/{s['id']}", json={"aktiv": False}).status_code == 200
    uebrig = [k for k in _serienkarten(client, s["id"]) if k["faellig"] >= date.today().isoformat()]
    assert uebrig == []
    # Reaktivieren materialisiert ab heute (kein rueckwirkender Stapel).
    assert client.patch(f"/api/serien/{s['id']}", json={"aktiv": True}).status_code == 200
    neu = _serienkarten(client, s["id"])
    assert all(k["faellig"] >= date.today().isoformat() for k in neu)
    assert neu, "Reaktivieren sollte wieder vorbuchen"


def test_patch_zieht_offene_vorbuchungen_nach(client):
    b = _board(client, "Nachziehen")
    s = _serie(client, b["id"], zustaendig="ALT1")
    r = client.patch(f"/api/serien/{s['id']}", json={"zustaendig": "NEU1", "titel": "Haertung neu"})
    assert r.status_code == 200
    karten = _serienkarten(client, s["id"])
    assert karten and all(k["zustaendig"] == "NEU1" for k in karten)
    assert all(k["titel"] == "Haertung neu" for k in karten)


def test_serie_loeschen_schont_erledigte_instanzen(client):
    b = _board(client, "Verlauf")
    bd = client.get(f"/api/kanban/boards/{b['id']}").json()
    fertig = client.post(f"/api/kanban/boards/{b['id']}/spalten", json={"titel": "Fertig"}).json()
    client.post(f"/api/kanban/spalten/{fertig['id']}/erledigt")
    s = _serie(client, b["id"])
    karten = _serienkarten(client, s["id"])
    assert karten
    # Eine Instanz per Move erledigen (ohne Zeit) - sie ist Verlauf, keine Vorbuchung.
    erledigt = karten[0]
    client.post(f"/api/kanban/karten/{erledigt['id']}/move", json={"spalte": fertig["id"], "reihenfolge": 0})
    assert client.delete(f"/api/serien/{s['id']}").status_code == 204
    # Die erledigte Karte existiert weiter (abgekoppelt), offene Vorbuchungen sind weg.
    assert client.get(f"/api/kanban/karten/{erledigt['id']}").status_code == 200
    with kdb._verb() as conn:
        r = conn.execute("SELECT serie_id FROM karte WHERE id = ?", (erledigt["id"],)).fetchone()
    assert r["serie_id"] is None
