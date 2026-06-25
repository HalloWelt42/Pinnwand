"""Tests fuer die Label-Verwaltung (zentrale Farbe je Label-Name).

Geprueft wird:
- CRUD: Anlegen, Auflisten, Farbe aendern, Loeschen.
- Doppelte Namen werden case-insensitiv abgewiesen (409).
- Umbenennen propagiert auf die Label-Strings aller Karten.
- Loeschen entfernt NUR die Definition; die Strings an Karten bleiben erhalten.
"""
from __future__ import annotations


def _board(client):
    m = client.post("/api/kanban/mappen", json={"titel": "LB-Mappe"})
    b = client.post(f"/api/kanban/mappen/{m.json()['id']}/boards", json={"titel": "LB-Board"})
    return b.json()


def _karte(client, board_id, spalte, titel, labels):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel, "labels": labels})
    assert r.status_code == 201, r.text
    return r.json()


def _karte_aus_board(client, board_id, karte_id):
    d = client.get(f"/api/kanban/boards/{board_id}").json()
    return next(k for k in d["karten"] if k["id"] == karte_id)


def test_label_crud(client):
    r = client.post("/api/kanban/labels", json={"name": "Backend", "familie": "blue"})
    assert r.status_code == 201, r.text
    lid = r.json()["id"]
    assert r.json()["name"] == "Backend"
    assert r.json()["familie"] == "blue"

    liste = client.get("/api/kanban/labels").json()
    assert any(x["id"] == lid for x in liste)

    r = client.patch(f"/api/kanban/labels/{lid}", json={"familie": "teal"})
    assert r.status_code == 200, r.text
    assert r.json()["familie"] == "teal"

    r = client.delete(f"/api/kanban/labels/{lid}")
    assert r.status_code == 204, r.text
    assert all(x["id"] != lid for x in client.get("/api/kanban/labels").json())


def test_doppelter_name_abgewiesen(client):
    assert client.post("/api/kanban/labels", json={"name": "Doku", "familie": "amber"}).status_code == 201
    # Gleicher Name in anderer Schreibweise -> Konflikt.
    r = client.post("/api/kanban/labels", json={"name": "doku", "familie": "red"})
    assert r.status_code == 409, r.text


def test_umbenennen_propagiert_auf_karten(client):
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Mit Label", ["backend", "wichtig"])
    r = client.post("/api/kanban/labels", json={"name": "backend", "familie": "blue"})
    lid = r.json()["id"]

    r = client.patch(f"/api/kanban/labels/{lid}", json={"name": "server"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "server"

    labels = _karte_aus_board(client, board["id"], k["id"])["labels"]
    assert "server" in labels
    assert "backend" not in labels
    assert "wichtig" in labels  # andere Labels unberuehrt


def test_loeschen_laesst_karten_labels_stehen(client):
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Bleibt", ["design"])
    lid = client.post("/api/kanban/labels", json={"name": "design", "familie": "deepPurple"}).json()["id"]

    assert client.delete(f"/api/kanban/labels/{lid}").status_code == 204
    # Label-Definition weg, aber der String an der Karte bleibt.
    assert _karte_aus_board(client, board["id"], k["id"])["labels"] == ["design"]


def test_umbenennen_dedupliziert(client):
    """Wird ein Label auf einen bereits vorhandenen Namen umbenannt, entsteht kein Duplikat."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Doppelt", ["alt", "neu"])
    lid = client.post("/api/kanban/labels", json={"name": "alt", "familie": "green"}).json()["id"]

    r = client.patch(f"/api/kanban/labels/{lid}", json={"name": "neu"})
    assert r.status_code == 200, r.text
    assert _karte_aus_board(client, board["id"], k["id"])["labels"] == ["neu"]


def test_umbenennen_dedupliziert_case_insensitiv(client):
    """Umbenennen darf keine zwei nur in der Schreibweise verschiedenen Labels
    auf derselben Karte erzeugen."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Mischfall", ["fehler", "Bug"])
    lid = client.post("/api/kanban/labels", json={"name": "Bug", "familie": "red"}).json()["id"]

    r = client.patch(f"/api/kanban/labels/{lid}", json={"name": "Fehler"})
    assert r.status_code == 200, r.text
    labels = _karte_aus_board(client, board["id"], k["id"])["labels"]
    # Genau ein Label uebrig (case-insensitiv eindeutig).
    assert len(labels) == 1
    assert labels[0].lower() == "fehler"
