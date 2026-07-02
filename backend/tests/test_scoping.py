"""Projekt-Scoping und Eigentum auf den NEBENWEGEN (bei aktivem Login).

Das Sichtbarkeitsversprechen gilt nicht nur fuer die Board-Navigation:
Mutationen, Deep-Links, Heute, Zeitliste, Suche und Timer respektieren
Mitgliedschaft bzw. Eigentum.
"""
from __future__ import annotations

import pytest

from module.auth import persistence as adb


# Ein Szenario fuer das ganze Modul (UNIQUE-Kuerzel erlaubt kein mehrfaches
# Anlegen von SCA/SCM); der Login wird am Modulende wieder deaktiviert.


def _person(client, name, kuerzel, rolle="mitarbeiter"):
    p = client.post("/api/planung/personen", json={"name": name, "kuerzel": kuerzel}).json()
    if rolle == "admin":
        client.patch(f"/api/planung/personen/{p['id']}", json={"rolle": "admin"})
    return p


def _login(client, kennung, passwort):
    r = client.post("/api/auth/login", json={"kennung": kennung, "passwort": passwort})
    assert r.status_code == 200, r.text
    return {"X-Pinnwand-Sitzung": r.json()["token"]}


@pytest.fixture(scope="module")
def szenario(client):
    """Privates Projekt des Admins (SCA) + Mitarbeiter SCM ohne Mitgliedschaft."""
    admin = _person(client, "Scope Chefin", "SCA", "admin")
    ich = _person(client, "Scope Ich", "SCM", "mitarbeiter")
    for p, pw in ((admin, "sca-geheim-1"), (ich, "scm-geheim-1")):
        assert client.post(f"/api/planung/personen/{p['id']}/passwort", json={"passwort": pw}).status_code == 200
    m = client.post("/api/kanban/mappen", json={"titel": "Scope Geheim"}).json()
    assert client.put(f"/api/kanban/mappen/{m['id']}/mitglieder/{admin['id']}").status_code == 204
    board = client.get(f"/api/kanban/mappen/{m['id']}/boards").json()[0]
    bd = client.get(f"/api/kanban/boards/{board['id']}").json()
    spalte = bd["spalten"][0]["id"]
    k = client.post("/api/kanban/karten", json={"board_id": board["id"], "spalte": spalte, "titel": "Geheime Aufgabe Xyzzy", "zustaendig": "SCA"}).json()
    z = client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": "2026-03-02", "sekunden": 600}).json()
    assert client.put("/api/auth/login-modus", json={"erforderlich": True}).status_code == 200
    kopf = _login(client, "SCM", "scm-geheim-1")
    yield {"mappe": m, "board": board, "spalte": spalte, "karte": k, "zeit": z, "kopf": kopf}
    adb.setze_einstellung("login_erforderlich", "0")


def test_mappe_mutationen_gescoped(client, szenario):
    s = szenario
    assert client.patch(f"/api/kanban/mappen/{s['mappe']['id']}", json={"titel": "Gekapert"}, headers=s["kopf"]).status_code == 403
    assert client.delete(f"/api/kanban/mappen/{s['mappe']['id']}", headers=s["kopf"]).status_code == 403


def test_karten_wege_gescoped(client, szenario):
    s = szenario
    kid = s["karte"]["id"]
    assert client.get(f"/api/kanban/karten/{kid}", headers=s["kopf"]).status_code == 403
    assert client.patch(f"/api/kanban/karten/{kid}", json={"titel": "Umbenannt"}, headers=s["kopf"]).status_code == 403
    assert client.delete(f"/api/kanban/karten/{kid}", headers=s["kopf"]).status_code == 403
    assert client.post("/api/kanban/karten", json={"board_id": s["board"]["id"], "spalte": s["spalte"], "titel": "Einschleusen"}, headers=s["kopf"]).status_code == 403
    assert client.post(f"/api/kanban/karten/{kid}/move", json={"spalte": s["spalte"], "reihenfolge": 0}, headers=s["kopf"]).status_code == 403


def test_lese_nebenwege_gescoped(client, szenario):
    s = szenario
    kid = s["karte"]["id"]
    heute = client.get("/api/kanban/heute", headers=s["kopf"]).json()
    alle_ids = {e["id"] for liste in heute.values() if isinstance(liste, list) for e in liste}
    assert kid not in alle_ids
    zeiten = client.get("/api/kanban/zeiteintraege", headers=s["kopf"]).json()
    assert all(z["karte_id"] != kid for z in zeiten)
    treffer = client.get("/api/suche?q=Xyzzy", headers=s["kopf"]).json()["treffer"]
    assert all(t["karte_id"] != kid for t in treffer)


def test_timer_eigentum(client, szenario):
    s = szenario
    kid = s["karte"]["id"]
    # Fremde Karte in unsichtbarem Projekt: schon das Scoping blockt.
    assert client.post(f"/api/kanban/karten/{kid}/timer/start", headers=s["kopf"]).status_code == 403


def test_timer_fremde_karte_in_geteilter_mappe(client, szenario):
    s = szenario
    # Geteilte Mappe, Karte gehoert SCA: SCM darf den Timer dort nicht starten.
    m = client.post("/api/kanban/mappen", json={"titel": "Scope Geteilt"}, headers=s["kopf"]).json()
    # SCM ist als Ersteller Mitglied - Mappe fuer SCA per Admin sichtbar machen ist egal;
    # die Karte gehoert SCA:
    board = client.get(f"/api/kanban/mappen/{m['id']}/boards", headers=s["kopf"]).json()[0]
    bd = client.get(f"/api/kanban/boards/{board['id']}", headers=s["kopf"]).json()
    k = client.post("/api/kanban/karten", json={"board_id": board["id"], "spalte": bd["spalten"][0]["id"], "titel": "SCA-Karte", "zustaendig": "SCA"}, headers=s["kopf"]).json()
    assert client.post(f"/api/kanban/karten/{k['id']}/timer/start", headers=s["kopf"]).status_code == 403


def test_termin_bestaetigung_nur_eigene(client, szenario):
    s = szenario
    # Termin-Serie fuer SCA anlegen und materialisieren (als Admin, Login ist aktiv).
    from datetime import date, timedelta
    kopf_admin = _login(client, "SCA", "sca-geheim-1")
    gestern = (date.today() - timedelta(days=1)).isoformat()
    r = client.post("/api/termine/serien", json={"titel": "SCA-Runde", "kuerzel": "SCA", "typ": "taeglich", "dauer_min": 30, "start": gestern}, headers=kopf_admin)
    assert r.status_code == 201, r.text
    client.post("/api/termine/materialisieren", headers=kopf_admin)
    offene = client.get("/api/termine/instanzen?status=schwebend", headers=kopf_admin).json()
    fremde = [i for i in offene if i["kuerzel"] == "SCA"]
    if fremde:
        iid = fremde[0]["id"]
        assert client.post(f"/api/termine/instanzen/{iid}/bestaetigen", json={}, headers=s["kopf"]).status_code == 403
        # Sammel-Bestaetigung filtert fremde Instanzen heraus.
        r = client.post("/api/termine/instanzen/bestaetigen-alle", json={"ids": [iid]}, headers=s["kopf"])
        assert r.status_code == 200 and r.json()["bestaetigt"] == 0
