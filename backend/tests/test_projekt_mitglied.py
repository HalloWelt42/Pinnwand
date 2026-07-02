"""Tests fuer Projekt-Mitgliedschaft + Sichtbarkeits-Scoping (Mappe = Projekt).

Regel: eine Mappe OHNE Mitglieder ist fuer alle sichtbar (geteilt); sobald Mitglieder
hinterlegt sind, sehen nur diese (plus Admin) das Projekt und seine Boards.
"""
from __future__ import annotations

import pytest

from module.auth import persistence as adb


@pytest.fixture(autouse=True)
def _login_danach_aus(client):
    yield
    adb.setze_einstellung("login_erforderlich", "0")


def _person(client, name, kuerzel, rolle="mitarbeiter"):
    p = client.post(
        "/api/planung/personen",
        json={"name": name, "kuerzel": kuerzel, "wochenstunden": [8, 8, 8, 8, 8, 0, 0]},
    ).json()
    if rolle == "admin":
        client.patch(f"/api/planung/personen/{p['id']}", json={"rolle": "admin"})
    return p


def _login(client, kennung, passwort):
    r = client.post("/api/auth/login", json={"kennung": kennung, "passwort": passwort})
    assert r.status_code == 200, r.text
    return {"X-Pinnwand-Sitzung": r.json()["token"]}


def test_mappe_ohne_mitglieder_bleibt_geteilt(client):
    a = client.post("/api/kanban/mappen", json={"titel": "Geteilt A"}).json()
    # ohne Mitglieder ist sie fuer jede (auch memberlose) Sicht sichtbar
    sichtbar = {m["id"] for m in client.get("/api/kanban/mappen").json()}
    assert a["id"] in sichtbar


def test_projekt_scoping_und_verwaltung(client):
    admin = _person(client, "PM Chefin", "PMC", "admin")
    ich = _person(client, "PM Ich", "PMI", "mitarbeiter")
    for p, pw in ((admin, "pmc-geheim-1"), (ich, "pmi-geheim-1")):
        assert client.post(f"/api/planung/personen/{p['id']}/passwort", json={"passwort": pw}).status_code == 200

    a = client.post("/api/kanban/mappen", json={"titel": "PM Projekt A"}).json()
    b = client.post("/api/kanban/mappen", json={"titel": "PM Projekt B"}).json()
    # A dem Mitarbeiter zuordnen, B nur dem Admin (Mitarbeiter also NICHT Mitglied von B)
    assert client.put(f"/api/kanban/mappen/{a['id']}/mitglieder/{ich['id']}").status_code == 204
    assert client.put(f"/api/kanban/mappen/{b['id']}/mitglieder/{admin['id']}").status_code == 204
    b_board_id = client.get(f"/api/kanban/mappen/{b['id']}/boards").json()[0]["id"]

    assert client.put("/api/auth/login-modus", json={"erforderlich": True}).status_code == 200
    kopf = _login(client, "PMI", "pmi-geheim-1")

    sichtbar = {m["id"] for m in client.get("/api/kanban/mappen", headers=kopf).json()}
    assert a["id"] in sichtbar          # Mitglied -> sichtbar
    assert b["id"] not in sichtbar      # nur Admin Mitglied -> fuer Mitarbeiter unsichtbar

    # Board-Zugriff: B verboten, A erlaubt
    assert client.get(f"/api/kanban/mappen/{b['id']}/boards", headers=kopf).status_code == 403
    assert client.get(f"/api/kanban/boards/{b_board_id}", headers=kopf).status_code == 403
    assert client.get(f"/api/kanban/mappen/{a['id']}/boards", headers=kopf).status_code == 200

    # Admin sieht beide Projekte
    kopf_admin = _login(client, "PMC", "pmc-geheim-1")
    sichtbar_admin = {m["id"] for m in client.get("/api/kanban/mappen", headers=kopf_admin).json()}
    assert a["id"] in sichtbar_admin and b["id"] in sichtbar_admin

    # Mitglieder-Verwaltung: ein Mitglied pflegt die Mitglieder der EIGENEN Mappe
    # (Self-Service des Erstellers) - fuer eine fremde Mappe bleibt es verboten.
    assert client.put(f"/api/kanban/mappen/{a['id']}/mitglieder/{admin['id']}", headers=kopf).status_code == 204
    assert client.delete(f"/api/kanban/mappen/{a['id']}/mitglieder/{admin['id']}", headers=kopf).status_code == 204
    assert client.put(f"/api/kanban/mappen/{b['id']}/mitglieder/{ich['id']}", headers=kopf).status_code == 403
