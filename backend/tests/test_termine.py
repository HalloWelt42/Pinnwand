"""Tests fuer Termine (Meeting-Zeiterfassung) - getypte Modelle (P5).

Deckt Serie-CRUD, Materialisierung der Instanzen und Bestaetigung ab, die nach
der Umstellung von rohen Dicts auf TerminSerie/TerminInstanz korrekt bleiben.
"""
from __future__ import annotations


def test_termin_serie_materialisieren_bestaetigen(client):
    r = client.post("/api/termine/serien", json={
        "titel": "Standup", "typ": "taeglich", "dauer_min": 15, "rueckblick_tage": 5,
    })
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["typ"] == "taeglich"
    assert s["dauer_min"] == 15
    assert isinstance(s["wochentage"], list)
    sid = s["id"]

    # Das Anlegen hat ueber dienst.materialisiere(TerminSerie) bereits Instanzen
    # bis gestern erzeugt (waere die Umstellung kaputt, haette POST 500 geliefert);
    # ein erneutes Materialisieren ist daher idempotent, muss aber fehlerfrei laufen.
    m = client.post("/api/termine/materialisieren").json()
    assert m["erzeugt"] >= 0

    insts = client.get("/api/termine/instanzen").json()
    assert insts, "es sollte mindestens eine Instanz geben"
    iid = insts[0]["id"]
    assert insts[0]["status"] == "schwebend"

    rb = client.post(f"/api/termine/instanzen/{iid}/bestaetigen", json={})
    assert rb.status_code == 200, rb.text
    assert rb.json()["status"] == "bestaetigt"
    assert rb.json()["effektiv_min"] == 15  # Soll uebernommen

    # Vorschau nutzt die geteilte Wiederholungsberechnung (Protocol)
    vs = client.get(f"/api/termine/serien/{sid}/vorschau?tage=7").json()
    assert "termine" in vs

    assert client.delete(f"/api/termine/serien/{sid}").status_code == 204
