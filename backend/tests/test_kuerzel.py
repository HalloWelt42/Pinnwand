"""Tests fuer die Kuerzel-Haertung: Eindeutigkeit, Umbenennungs-Kaskade,
Rollen-Default und Personen-Loesch-Kaskade (keine Mitglieds-Waisen).
"""
from __future__ import annotations

from module.planung import persistence as pdb


def _person(client, name, kuerzel):
    r = client.post("/api/planung/personen", json={"name": name, "kuerzel": kuerzel})
    assert r.status_code == 201, r.text
    return r.json()


def test_kuerzel_eindeutig_auch_case_insensitive(client):
    _person(client, "Kuerzel Eins", "KE1")
    r = client.post("/api/planung/personen", json={"name": "Kuerzel Zwei", "kuerzel": "ke1"})
    assert r.status_code == 409
    # Auch per PATCH kann man kein fremdes Kuerzel uebernehmen.
    p3 = _person(client, "Kuerzel Drei", "KE3")
    r = client.patch(f"/api/planung/personen/{p3['id']}", json={"kuerzel": "KE1"})
    assert r.status_code == 409


def test_neue_person_hat_rolle(client):
    p = _person(client, "Rollen Test", "RT1")
    assert p["rolle"] in ("admin", "mitarbeiter")
    with pdb.verbindung() as conn:
        r = conn.execute("SELECT rolle FROM person WHERE id = ?", (p["id"],)).fetchone()
    assert r["rolle"] is not None


def test_kuerzel_umbenennung_kaskadiert(client):
    p = _person(client, "Kaskade", "KAS")
    m = client.post("/api/kanban/mappen", json={"titel": "Kaskaden-Mappe"}).json()
    board = client.get(f"/api/kanban/mappen/{m['id']}/boards").json()[0]
    bd = client.get(f"/api/kanban/boards/{board['id']}").json()
    spalte = bd["spalten"][0]["id"]
    k = client.post("/api/kanban/karten", json={"board_id": board["id"], "spalte": spalte, "titel": "KAS-Karte", "zustaendig": "KAS"}).json()
    client.patch(f"/api/kanban/mappen/{m['id']}", json={"owner": "KAS"})

    r = client.patch(f"/api/planung/personen/{p['id']}", json={"kuerzel": "KA2"})
    assert r.status_code == 200, r.text
    assert client.get(f"/api/kanban/karten/{k['id']}").json()["zustaendig"] == "KA2"
    mappen = {x["id"]: x for x in client.get("/api/kanban/mappen").json()}
    assert mappen[m["id"]]["owner"] == "KA2"


def test_person_loeschen_raeumt_mitgliedschaft_auf(client):
    p = _person(client, "Mitglied Weg", "MW1")
    m = client.post("/api/kanban/mappen", json={"titel": "MW-Projekt"}).json()
    assert client.put(f"/api/kanban/mappen/{m['id']}/mitglieder/{p['id']}").status_code == 204
    assert client.delete(f"/api/planung/personen/{p['id']}").status_code == 204
    # Keine Waise: die Mappe ist wieder geteilt (Mitgliederliste leer).
    assert client.get(f"/api/kanban/mappen/{m['id']}/mitglieder").json() == []
