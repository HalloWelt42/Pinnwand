"""Tests fuer den Projekt-Aufwand (Mappe = Projekt).

Ist = tatsaechlich erfasste Zeit (zeiteintrag.sekunden als SSOT), Soll = Summe der
Karten-Schaetzungen (schaetzung_min), Budget = optionale Planungsobergrenze. Die drei
bleiben getrennt; keine Doppelzaehlung. Sichtbarkeit folgt der Mitgliedschaft.
"""
from __future__ import annotations

import pytest

from module.auth import persistence as adb


@pytest.fixture(autouse=True)
def _login_danach_aus(client):
    yield
    adb.setze_einstellung("login_erforderlich", "0")


def _mappe(client, titel):
    m = client.post("/api/kanban/mappen", json={"titel": titel})
    assert m.status_code == 201, m.text
    return m.json()


def _board_erste_spalte(client, mappe_id):
    boards = client.get(f"/api/kanban/mappen/{mappe_id}/boards").json()
    bd = client.get(f"/api/kanban/boards/{boards[0]['id']}").json()
    return bd["id"], bd["spalten"][0]["id"]


def _karte(client, board_id, spalte, titel, schaetzung_min=None, zustaendig=None):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel, "zustaendig": zustaendig})
    assert r.status_code == 201, r.text
    k = r.json()
    if schaetzung_min is not None:
        p = client.patch(f"/api/kanban/karten/{k['id']}", json={"schaetzung_min": schaetzung_min})
        assert p.status_code == 200, p.text
    return k


def _buche(client, karte_id, sekunden, datum="2026-03-02"):
    r = client.post("/api/kanban/zeiteintraege", json={"karte_id": karte_id, "datum": datum, "sekunden": sekunden})
    assert r.status_code == 201, r.text
    return r.json()


def _projekt(client, mappe_id):
    liste = client.get("/api/kanban/projekte").json()
    treffer = [p for p in liste if p["mappe_id"] == mappe_id]
    assert treffer, f"Projekt {mappe_id} nicht in Liste"
    return treffer[0]


def test_aufwand_ist_und_soll_getrennt(client):
    m = _mappe(client, "Aufwand Alpha")
    board_id, spalte = _board_erste_spalte(client, m["id"])
    k1 = _karte(client, board_id, spalte, "K1", schaetzung_min=60)
    k2 = _karte(client, board_id, spalte, "K2", schaetzung_min=30)
    _buche(client, k1["id"], 3600)
    _buche(client, k2["id"], 1800)

    p = _projekt(client, m["id"])
    assert p["ist_sekunden"] == 5400          # 1h + 0,5h tatsaechlich
    assert p["soll_minuten"] == 90            # 60 + 30 geschaetzt
    assert p["karten"] == 2
    assert p["boards"] >= 1
    assert p["status"] == "aktiv"


def test_keine_doppelzaehlung_bei_mehreren_eintraegen(client):
    m = _mappe(client, "Aufwand Beta")
    board_id, spalte = _board_erste_spalte(client, m["id"])
    k = _karte(client, board_id, spalte, "K", schaetzung_min=120)
    _buche(client, k["id"], 1000, datum="2026-03-02")
    _buche(client, k["id"], 500, datum="2026-03-03")

    p = _projekt(client, m["id"])
    assert p["ist_sekunden"] == 1500          # genau die Summe, nichts doppelt
    assert p["soll_minuten"] == 120


def test_budget_owner_status_editierbar(client):
    m = _mappe(client, "Aufwand Gamma")
    r = client.patch(f"/api/kanban/mappen/{m['id']}", json={"budget_min": 240, "owner": "CHF", "status": "pausiert"})
    assert r.status_code == 200, r.text
    p = _projekt(client, m["id"])
    assert p["budget_min"] == 240
    assert p["owner"] == "CHF"
    assert p["status"] == "pausiert"


def test_detail_bricht_auf_boards_und_personen_herunter(client):
    m = _mappe(client, "Aufwand Delta")
    board_id, spalte = _board_erste_spalte(client, m["id"])
    k = _karte(client, board_id, spalte, "K", schaetzung_min=45, zustaendig="ZZ")
    _buche(client, k["id"], 2700)

    d = client.get(f"/api/kanban/projekte/{m['id']}").json()
    assert d["ist_sekunden"] == 2700
    assert d["soll_minuten"] == 45
    board = [b for b in d["boards"] if b["board_id"] == board_id][0]
    assert board["ist_sekunden"] == 2700
    assert board["soll_minuten"] == 45
    assert any(pp["kuerzel"] == "ZZ" and pp["ist_sekunden"] == 2700 for pp in d["personen"])


def _person(client, name, kuerzel, rolle="mitarbeiter"):
    p = client.post("/api/planung/personen", json={"name": name, "kuerzel": kuerzel}).json()
    if rolle == "admin":
        client.patch(f"/api/planung/personen/{p['id']}", json={"rolle": "admin"})
    return p


def test_projekt_liste_folgt_der_mitgliedschaft(client):
    admin = _person(client, "Prj Chefin", "PJC", "admin")
    ich = _person(client, "Prj Ich", "PJI", "mitarbeiter")
    for p, pw in ((admin, "pjc-geheim-1"), (ich, "pji-geheim-1")):
        assert client.post(f"/api/planung/personen/{p['id']}/passwort", json={"passwort": pw}).status_code == 200
    offen = _mappe(client, "Prj Offen")             # ohne Mitglieder -> geteilt
    privat = _mappe(client, "Prj Privat Admin")     # nur Admin -> fuer Mitarbeiter unsichtbar
    assert client.put(f"/api/kanban/mappen/{privat['id']}/mitglieder/{admin['id']}").status_code == 204

    assert client.put("/api/auth/login-modus", json={"erforderlich": True}).status_code == 200
    login = client.post("/api/auth/login", json={"kennung": "PJI", "passwort": "pji-geheim-1"})
    assert login.status_code == 200, login.text
    kopf = {"X-Pinnwand-Sitzung": login.json()["token"]}

    sichtbar = {p["mappe_id"] for p in client.get("/api/kanban/projekte", headers=kopf).json()}
    assert offen["id"] in sichtbar
    assert privat["id"] not in sichtbar
    # Direkter Zugriff auf ein fremdes Projekt-Detail wird verweigert.
    assert client.get(f"/api/kanban/projekte/{privat['id']}", headers=kopf).status_code == 403
