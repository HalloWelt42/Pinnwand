"""Tests fuer das Aktivitaetsprotokoll je Karte und die Benachrichtigungs-Sicht.

Kern: Jede nachvollziehenswerte Aenderung (Anlegen, Verschieben, Blockade,
Zustaendigkeit, Kommentar, Zeitbuchung) landet als Eintrag am Protokoll der
Karte; die Glocke liefert nur FREMDE Ereignisse auf den eigenen Karten und
das Loeschen der Karte raeumt ihr Protokoll mit ab.
"""
from __future__ import annotations

from module.kanban_kern import persistence as kdb


def _board(client, titel="Akt Board"):
    m = client.post("/api/kanban/mappen", json={"titel": f"Mappe {titel}"}).json()
    return client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": titel}).json()


def _karte(client, board_id, spalte, titel, zustaendig=None):
    r = client.post("/api/kanban/karten", json={
        "board_id": board_id, "spalte": spalte, "titel": titel, "zustaendig": zustaendig,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _protokoll(client, karte_id):
    r = client.get(f"/api/kanban/karten/{karte_id}/aktivitaet")
    assert r.status_code == 200, r.text
    return r.json()


def test_lebenszyklus_landet_im_protokoll(client):
    b = _board(client, "Verlauf")
    quelle = b["spalten"][0]["id"]
    ziel = client.post(f"/api/kanban/boards/{b['id']}/spalten", json={"titel": "Akt-Ziel"}).json()

    k = _karte(client, b["id"], quelle, "Mit Verlauf")
    arten = [a["art"] for a in _protokoll(client, k["id"])]
    assert arten == ["angelegt"]

    # Verschieben (ueber den Move-Endpunkt) und Feld-Aenderungen
    client.post(f"/api/kanban/karten/{k['id']}/move", json={"spalte": ziel["id"], "reihenfolge": 0})
    client.patch(f"/api/kanban/karten/{k['id']}", json={"zustaendig": "AA", "faellig": "2026-07-10"})
    client.patch(f"/api/kanban/karten/{k['id']}", json={"blockiert_grund": "wartet auf Zulieferung"})
    client.patch(f"/api/kanban/karten/{k['id']}", json={"blockiert_grund": None})
    client.post(f"/api/kanban/karten/{k['id']}/kommentare", json={"autor": "BB", "text": "Hallo"})
    client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": "2026-07-01", "sekunden": 1800})

    eintraege = _protokoll(client, k["id"])
    arten = {a["art"] for a in eintraege}
    assert {"angelegt", "verschoben", "zustaendig", "faellig", "blockiert", "kommentar", "zeit"} <= arten
    blockade = [a["text"] for a in eintraege if a["art"] == "blockiert"]
    assert "Blockade aufgehoben" in blockade
    assert any("wartet auf Zulieferung" in x for x in blockade)
    # Reine Titel-/Beschreibungs-Aenderungen fluten das Protokoll nicht.
    vorher = len(eintraege)
    client.patch(f"/api/kanban/karten/{k['id']}", json={"titel": "Umbenannt", "beschreibung": "Text"})
    assert len(_protokoll(client, k["id"])) == vorher


def test_glocke_liefert_nur_fremde_ereignisse_auf_eigenen_karten(client):
    b = _board(client, "Glocke")
    spalte = b["spalten"][0]["id"]
    eigene = _karte(client, b["id"], spalte, "Glocke eigene", zustaendig="GA")
    fremde = _karte(client, b["id"], spalte, "Glocke fremde", zustaendig="GB")

    # Fremder Kommentar auf der eigenen Karte -> Ereignis fuer GA
    client.post(f"/api/kanban/karten/{eigene['id']}/kommentare", json={"autor": "GB", "text": "fremd"})
    # Eigener Kommentar -> KEIN Ereignis fuer GA
    client.post(f"/api/kanban/karten/{eigene['id']}/kommentare", json={"autor": "GA", "text": "selbst"})
    # Ereignis auf einer fremden Karte -> nicht in GAs Glocke
    client.post(f"/api/kanban/karten/{fremde['id']}/kommentare", json={"autor": "GA", "text": "woanders"})

    r = client.get("/api/kanban/aktivitaet", params={"kuerzel": "GA"})
    assert r.status_code == 200, r.text
    meine = [a for a in r.json() if a["karte_id"] in (eigene["id"], fremde["id"])]
    assert all(a["karte_id"] == eigene["id"] for a in meine)
    texte = {(a["art"], a["kuerzel"]) for a in meine}
    assert ("kommentar", "GB") in texte
    assert ("kommentar", "GA") not in texte
    # Angereicherte Kartendaten fuer die Anzeige
    assert all(a["karte_titel"] and a["board_id"] for a in meine)

    # seit-Filter: ein Zeitstempel weit in der Zukunft blendet alles aus
    r = client.get("/api/kanban/aktivitaet", params={"kuerzel": "GA", "seit": "9999-01-01T00:00:00"})
    assert [a for a in r.json() if a["karte_id"] == eigene["id"]] == []


def test_loeschen_raeumt_protokoll_ab(client):
    b = _board(client, "Akt-Loeschen")
    spalte = b["spalten"][0]["id"]
    k = _karte(client, b["id"], spalte, "Wird geloescht")
    assert _protokoll(client, k["id"])
    assert client.delete(f"/api/kanban/karten/{k['id']}").status_code == 204
    with kdb._verb() as conn:
        rest = conn.execute("SELECT COUNT(*) FROM aktivitaet WHERE karte_id = ?", (k["id"],)).fetchone()[0]
    assert rest == 0


def test_faellig_kalender_liefert_zeitraum_mit_erledigt_flag(client):
    b = _board(client, "Faellig-Kal")
    offen_sp = b["spalten"][0]["id"]
    fertig_sp = client.post(f"/api/kanban/boards/{b['id']}/spalten", json={"titel": "FK-Fertig"}).json()
    client.post(f"/api/kanban/spalten/{fertig_sp['id']}/erledigt")

    r = client.post("/api/kanban/karten", json={
        "board_id": b["id"], "spalte": offen_sp, "titel": "FK offen", "faellig": "2026-08-10",
    })
    offen = r.json()
    fertig = client.post("/api/kanban/karten", json={
        "board_id": b["id"], "spalte": offen_sp, "titel": "FK fertig", "faellig": "2026-08-20",
    }).json()
    client.post(f"/api/kanban/karten/{fertig['id']}/move", json={"spalte": fertig_sp["id"], "reihenfolge": 0})
    # Ausserhalb des Zeitraums
    client.post("/api/kanban/karten", json={
        "board_id": b["id"], "spalte": offen_sp, "titel": "FK September", "faellig": "2026-09-01",
    })

    r = client.get("/api/kanban/faellig", params={"von": "2026-08-01", "bis": "2026-08-31"})
    assert r.status_code == 200, r.text
    eintraege = {e["id"]: e for e in r.json() if e["board_id"] == b["id"]}
    assert set(eintraege) == {offen["id"], fertig["id"]}
    assert eintraege[offen["id"]]["erledigt"] is False
    assert eintraege[fertig["id"]]["erledigt"] is True
    # Sortiert nach Datum
    daten = [e["faellig"] for e in r.json()]
    assert daten == sorted(daten)
