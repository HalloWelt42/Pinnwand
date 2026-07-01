"""Tests fuer den Karten-Lebenszyklus abseits des Drag-Pfads.

Kern: Ein Spaltenwechsel ist IMMER ein echtes Verschieben - auch ueber
PATCH /karten/{id} (Drawer-Status, Agenten-API). bewegt_am wird gesetzt,
Gruppenmitglieder ziehen mit, Erledigen stoppt laufende Timer, und
Ideentickets erfassen auf keinem Weg Zeit.
"""
from __future__ import annotations

from module.kanban_kern import persistence as kdb


def _board(client, titel="LZ Board"):
    m = client.post("/api/kanban/mappen", json={"titel": f"Mappe {titel}"}).json()
    b = client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": titel}).json()
    return b


def _spalte(client, board_id, titel, erledigt=False):
    s = client.post(f"/api/kanban/boards/{board_id}/spalten", json={"titel": titel}).json()
    if erledigt:
        s = client.post(f"/api/kanban/spalten/{s['id']}/erledigt").json()
    return s


def _karte(client, board_id, spalte, titel, typ="arbeit"):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel, "typ": typ})
    assert r.status_code == 201, r.text
    return r.json()


def test_patch_spalte_setzt_bewegt_am_und_zieht_gruppe_mit(client):
    b = _board(client, "Patch-Move")
    quelle = b["spalten"][0]["id"]
    ziel = _spalte(client, b["id"], "Ziel")["id"]
    k1 = _karte(client, b["id"], quelle, "Gruppe A")
    k2 = _karte(client, b["id"], quelle, "Gruppe B")
    assert client.post(f"/api/kanban/karten/{k1['id']}/verknuepfen", json={"ziel_karte_id": k2["id"]}).status_code == 200

    # bewegt_am kuenstlich altern lassen (minutengenaue Zeitstempel), damit der
    # Reset durch den PATCH-Move eindeutig messbar ist.
    alt = "2020-01-01T00:00"
    with kdb._verb() as conn:
        conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (alt, k1["id"]))
    r = client.patch(f"/api/kanban/karten/{k1['id']}", json={"spalte": ziel})
    assert r.status_code == 200, r.text
    neu = r.json()
    assert neu["spalte"] == ziel
    assert neu["bewegt_am"] is not None and neu["bewegt_am"] != alt
    # Gruppenmitglied zieht mit - wie beim Drag ueber den Move-Endpunkt.
    assert client.get(f"/api/kanban/karten/{k2['id']}").json()["spalte"] == ziel


def test_patch_ohne_spaltenwechsel_laesst_bewegt_am_stehen(client):
    b = _board(client, "Patch-Titel")
    spalte = b["spalten"][0]["id"]
    k = _karte(client, b["id"], spalte, "Nur Titel")
    alt = client.get(f"/api/kanban/karten/{k['id']}").json()["bewegt_am"]
    r = client.patch(f"/api/kanban/karten/{k['id']}", json={"titel": "Nur Titel neu", "spalte": spalte})
    assert r.status_code == 200
    assert client.get(f"/api/kanban/karten/{k['id']}").json()["bewegt_am"] == alt


def test_erledigen_stoppt_laufenden_timer(client):
    b = _board(client, "Erledigt-Stopp")
    quelle = b["spalten"][0]["id"]
    fertig = _spalte(client, b["id"], "Fertig", erledigt=True)["id"]
    k = _karte(client, b["id"], quelle, "Laeuft")
    assert client.post(f"/api/kanban/karten/{k['id']}/timer/start").status_code == 200
    r = client.post(f"/api/kanban/karten/{k['id']}/move", json={"spalte": fertig, "reihenfolge": 0})
    assert r.status_code == 200
    assert r.json()["laeuft_seit"] is None


def test_idee_wechsel_stoppt_timer_und_buchung_abgelehnt(client):
    b = _board(client, "Idee-Gating")
    spalte = b["spalten"][0]["id"]
    k = _karte(client, b["id"], spalte, "Wird Idee")
    assert client.post(f"/api/kanban/karten/{k['id']}/timer/start").status_code == 200
    r = client.patch(f"/api/kanban/karten/{k['id']}", json={"typ": "idee"})
    assert r.status_code == 200
    assert r.json()["laeuft_seit"] is None
    # Manuelle Buchung auf ein Ideenticket wird abgewiesen.
    z = client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": "2026-03-02", "sekunden": 600})
    assert z.status_code == 409


def test_spalte_loeschen_raeumt_dokumente_und_zeiten(client):
    b = _board(client, "Kaskade-Spalte")
    quelle = b["spalten"][0]["id"]
    ziel = _spalte(client, b["id"], "Wegwerf")["id"]
    k = _karte(client, b["id"], ziel, "Mit Anhang")
    d = client.post("/api/kanban/dokumente", json={"kontext": "karte", "kontext_id": k["id"], "titel": "Notiz"})
    assert d.status_code == 201
    z = client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": "2026-03-02", "sekunden": 600})
    assert z.status_code == 201

    assert client.delete(f"/api/kanban/spalten/{ziel}").status_code == 204
    assert client.get(f"/api/kanban/dokumente?kontext=karte&kontext_id={k['id']}").json() == []
    assert client.get(f"/api/kanban/zeiteintraege?karte_id={k['id']}").json() == []
    # Die Wegwerf-Spalte ist weg, die uebrigen Spalten bleiben bestehen.
    bd = client.get(f"/api/kanban/boards/{b['id']}").json()
    ids = [s["id"] for s in bd["spalten"]]
    assert ziel not in ids and quelle in ids


def test_board_loeschen_loescht_serien_mit(client):
    b = _board(client, "Kaskade-Serie")
    s = client.post("/api/serien", json={"board_id": b["id"], "titel": "Taegliche Runde", "typ": "taeglich"})
    assert s.status_code == 201, s.text
    sid = s.json()["id"]
    assert client.delete(f"/api/kanban/boards/{b['id']}").status_code == 204
    verbleibend = {x["id"] for x in client.get("/api/serien").json()}
    assert sid not in verbleibend
