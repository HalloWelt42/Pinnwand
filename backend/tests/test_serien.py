"""Tests fuer Serien (wiederkehrende Aufgaben) - getypte Modelle (P5).

Deckt den Lese-/Rechen-/Vorbuchungspfad ab, der nach der Umstellung der
Persistenz von rohen Dicts auf Pydantic-Modelle (Serie) korrekt bleiben muss.
"""
from __future__ import annotations


def _board(client):
    m = client.post("/api/kanban/mappen", json={"titel": "SE-Mappe"}).json()
    return client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": "SE-Board"}).json()


def test_serie_crud_vorschau_vorbuchen(client):
    b = _board(client)
    spalte = b["spalten"][0]["id"]
    r = client.post("/api/serien", json={
        "board_id": b["id"], "spalte_id": spalte, "titel": "Daily",
        "typ": "taeglich", "intervall": 1, "dauer_min": 30,
    })
    assert r.status_code == 201, r.text
    s = r.json()
    # getypte Felder: Listen/Booleans korrekt geformt
    assert s["typ"] == "taeglich"
    assert s["aktiv"] is True
    assert isinstance(s["wochentage"], list)
    sid = s["id"]

    lst = client.get(f"/api/serien?board_id={b['id']}").json()
    assert any(x["id"] == sid for x in lst)

    # Vorschau nutzt die geteilte Wiederholungsberechnung (Protocol)
    vs = client.get(f"/api/serien/{sid}/vorschau?tage=7").json()
    assert len(vs["termine"]) >= 1

    # Das Anlegen hat ueber dienst.materialisiere(Serie) bereits Karten erzeugt
    # (waere die Attribut-Umstellung kaputt, haette POST schon 500 geliefert).
    # Vorbuchen ist daher idempotent (0 neue), aber muss fehlerfrei laufen.
    vb = client.post(f"/api/serien/{sid}/vorbuchen").json()
    assert vb["erzeugt"] >= 0
    # Es existieren Serien-Karten auf dem Board (Materialisierung wirkte).
    karten = client.get(f"/api/kanban/boards/{b['id']}").json()["karten"]
    assert any(k.get("schluessel") for k in karten)

    r = client.patch(f"/api/serien/{sid}", json={"titel": "Daily geaendert"})
    assert r.status_code == 200, r.text
    assert r.json()["titel"] == "Daily geaendert"

    assert client.delete(f"/api/serien/{sid}").status_code == 204
    assert all(x["id"] != sid for x in client.get(f"/api/serien?board_id={b['id']}").json())


def test_nachtraege_typisiert(client):
    """Der Nachtraege-Endpunkt liefert getypte Eintraege (leere Liste ist gueltig)."""
    r = client.get("/api/serien/nachtraege")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
