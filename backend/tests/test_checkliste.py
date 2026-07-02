"""Tests fuer die Checklisten-Einzeloperationen.

Kern: Punkte werden atomar in SQL angehaengt/geaendert/entfernt statt die
ganze Liste zu ersetzen - und ein veralteter Index meldet 409 (Konflikt)
statt still an der falschen Stelle zu schreiben.
"""
from __future__ import annotations


def _karte(client, titel="Checkliste"):
    m = client.post("/api/kanban/mappen", json={"titel": f"Mappe {titel}"}).json()
    b = client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": titel}).json()
    r = client.post("/api/kanban/karten", json={
        "board_id": b["id"], "spalte": b["spalten"][0]["id"], "titel": titel,
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_checkliste_einzeloperationen(client):
    k = _karte(client, "CL-Ops")
    kid = k["id"]

    # Anhaengen
    r = client.post(f"/api/kanban/karten/{kid}/checkliste", json={"text": "Erster Punkt"})
    assert r.status_code == 201, r.text
    r = client.post(f"/api/kanban/karten/{kid}/checkliste", json={"text": "Zweiter Punkt"})
    liste = r.json()["checkliste"]
    assert [p["text"] for p in liste] == ["Erster Punkt", "Zweiter Punkt"]
    assert all(p["erledigt"] is False for p in liste)

    # Abhaken + Text aendern
    r = client.patch(f"/api/kanban/karten/{kid}/checkliste/0", json={"erledigt": True})
    assert r.status_code == 200 and r.json()["checkliste"][0]["erledigt"] is True
    r = client.patch(f"/api/kanban/karten/{kid}/checkliste/1", json={"text": "Zweiter Punkt neu"})
    assert r.json()["checkliste"][1]["text"] == "Zweiter Punkt neu"
    # Der andere Punkt bleibt unberuehrt
    assert r.json()["checkliste"][0] == {"text": "Erster Punkt", "erledigt": True}

    # Entfernen
    r = client.delete(f"/api/kanban/karten/{kid}/checkliste/0")
    assert r.status_code == 200
    assert [p["text"] for p in r.json()["checkliste"]] == ["Zweiter Punkt neu"]

    # Veralteter Index -> 409 Konflikt
    assert client.patch(f"/api/kanban/karten/{kid}/checkliste/5", json={"erledigt": True}).status_code == 409
    assert client.delete(f"/api/kanban/karten/{kid}/checkliste/5").status_code == 409

    # Leerer Text -> 400
    assert client.post(f"/api/kanban/karten/{kid}/checkliste", json={"text": "  "}).status_code == 400
    assert client.patch(f"/api/kanban/karten/{kid}/checkliste/0", json={"text": " "}).status_code == 400
