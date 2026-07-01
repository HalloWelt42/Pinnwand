"""Kuerzel-Snapshot am Zeiteintrag: Karten-Uebergaben verschieben die
Zeit-Historie nicht mehr, und zwei Personen koennen auf derselben Karte
getrennte Zeiten erfassen.
"""
from __future__ import annotations

from datetime import date


def _person(client, name, kuerzel):
    r = client.post("/api/planung/personen", json={"name": name, "kuerzel": kuerzel, "wochenstunden": [8, 8, 8, 8, 8, 0, 0]})
    assert r.status_code == 201, r.text
    return r.json()


def _karte(client, zustaendig):
    m = client.post("/api/kanban/mappen", json={"titel": f"Snap {zustaendig}"}).json()
    b = client.get(f"/api/kanban/mappen/{m['id']}/boards").json()[0]
    bd = client.get(f"/api/kanban/boards/{b['id']}").json()
    r = client.post("/api/kanban/karten", json={"board_id": b["id"], "spalte": bd["spalten"][0]["id"], "titel": "Snap-Karte", "zustaendig": zustaendig})
    return r.json()


def _ist_heute(client, person_id):
    r = client.get(f"/api/planung/stunden-uebersicht?person={person_id}")
    assert r.status_code == 200, r.text
    return r.json()["heute"]["ist_sek"]


def test_uebergabe_verschiebt_historie_nicht(client):
    heute = date.today().isoformat()
    a = _person(client, "Snap A", "SNA")
    b = _person(client, "Snap B", "SNB")
    k = _karte(client, "SNA")
    # A arbeitet 2h (offener Modus: Snapshot faellt auf karte.zustaendig zurueck)
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": heute, "sekunden": 7200}).status_code == 201
    assert _ist_heute(client, a["id"]) == 7200

    # Uebergabe an B, danach bucht B 1h
    assert client.patch(f"/api/kanban/karten/{k['id']}", json={"zustaendig": "SNB"}).status_code == 200
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": heute, "sekunden": 3600}).status_code == 201

    # As Historie bleibt bei A (2h), B bekommt nur die eigene Stunde.
    assert _ist_heute(client, a["id"]) == 7200
    assert _ist_heute(client, b["id"]) == 3600


def test_kuerzel_umbenennung_zieht_zeit_snapshot_mit(client):
    heute = date.today().isoformat()
    p = _person(client, "Snap C", "SNC")
    k = _karte(client, "SNC")
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": heute, "sekunden": 1800}).status_code == 201
    assert _ist_heute(client, p["id"]) == 1800
    # Umbenennung: Kaskade muss auch den Eintrags-Snapshot mitziehen,
    # sonst verliert die Person ihr Ist.
    assert client.patch(f"/api/planung/personen/{p['id']}", json={"kuerzel": "SNC2"}).status_code == 200
    assert _ist_heute(client, p["id"]) == 1800
