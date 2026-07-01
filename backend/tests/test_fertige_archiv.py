"""Tests fuer gefenstertes Laden fertiger Karten + Archiv.

Geprueft wird:
- board_detail liefert KEINE Karten aus Erledigt-Spalten (die kommen gefenstert).
- fertige_seite: Anzahl-Deckel + Nachladen (offset), gesamt/hat_mehr korrekt.
- Zeitfenster (heute vs. alle) wirkt serverseitig.
- Archiv: Karten aelter als die Schwelle verschwinden aus dem Board und tauchen im Archiv auf.
- Einstellungen (Seitengroesse/Archiv-Tage) sind les- und setzbar und wirken.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.db import verbindung


def _board_mit_fertig(client):
    m = client.post("/api/kanban/mappen", json={"titel": "FA-Mappe"}).json()
    b = client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": "FA-Board"}).json()
    spalten = b["spalten"]
    offen = spalten[0]["id"]
    done = spalten[-1]["id"]
    r = client.post(f"/api/kanban/spalten/{done}/erledigt")
    assert r.status_code == 200, r.text
    return b["id"], offen, done


def _karte(client, board_id, spalte, titel):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _setze_abschluss(karte_id: str, tage_zurueck: int) -> None:
    tag = (date.today() - timedelta(days=tage_zurueck)).isoformat()
    with verbindung() as conn:
        conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (tag + "T10:00", karte_id))


def test_board_detail_ohne_fertige(client):
    board_id, offen, done = _board_mit_fertig(client)
    k_offen = _karte(client, board_id, offen, "offene Karte")
    k_done = _karte(client, board_id, done, "fertige Karte")
    ids = {k["id"] for k in client.get(f"/api/kanban/boards/{board_id}").json()["karten"]}
    assert k_offen in ids
    assert k_done not in ids  # Erledigt-Karten kommen NICHT ueber board_detail


def test_fertige_deckel_und_nachladen(client):
    board_id, _offen, done = _board_mit_fertig(client)
    for i in range(3):
        _karte(client, board_id, done, f"fertig {i}")
    s1 = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "heute", "limit": 2}).json()
    assert s1["gesamt"] == 3
    assert len(s1["karten"]) == 2
    assert s1["hat_mehr"] is True
    s2 = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "heute", "limit": 2, "offset": 2}).json()
    assert len(s2["karten"]) == 1
    assert s2["hat_mehr"] is False


def test_zeitfenster_wirkt(client):
    board_id, _offen, done = _board_mit_fertig(client)
    _karte(client, board_id, done, "heute fertig")
    alt = _karte(client, board_id, done, "vorige Woche fertig")
    _setze_abschluss(alt, 8)
    heute = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "heute"}).json()
    assert heute["gesamt"] == 1
    alle = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "alle"}).json()
    assert alle["gesamt"] == 2


def test_archiv_ab_einem_jahr(client):
    board_id, _offen, done = _board_mit_fertig(client)
    _karte(client, board_id, done, "neu fertig")
    alt = _karte(client, board_id, done, "sehr alt fertig")
    _setze_abschluss(alt, 400)  # aelter als 365 Tage -> Archiv
    alle = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "alle"}).json()
    ids = {k["id"] for k in alle["karten"]}
    assert alt not in ids  # archivierte Karte NICHT im Board
    arch = client.get(f"/api/kanban/boards/{board_id}/archiv").json()
    assert alt in {k["id"] for k in arch["karten"]}


def test_einstellungen_les_und_setzbar(client):
    vorher = client.get("/api/kanban/einstellungen").json()
    assert vorher["fertig_seitengroesse"] == 50
    assert vorher["archiv_tage"] == 365
    try:
        gesetzt = client.put(
            "/api/kanban/einstellungen", json={"fertig_seitengroesse": 10, "archiv_tage": 30}
        )
        assert gesetzt.status_code == 200, gesetzt.text
        assert gesetzt.json() == {"fertig_seitengroesse": 10, "archiv_tage": 30}
        # Archiv-Schwelle 30 Tage: eine 40 Tage alte Fertig-Karte muss ins Archiv wandern.
        board_id, _offen, done = _board_mit_fertig(client)
        alt = _karte(client, board_id, done, "40 Tage alt")
        _setze_abschluss(alt, 40)
        alle = client.get(f"/api/kanban/spalten/{done}/fertige", params={"zeitraum": "alle"}).json()
        assert alt not in {k["id"] for k in alle["karten"]}
        arch = client.get(f"/api/kanban/boards/{board_id}/archiv").json()
        assert alt in {k["id"] for k in arch["karten"]}
    finally:
        client.put("/api/kanban/einstellungen", json={"fertig_seitengroesse": 50, "archiv_tage": 365})
