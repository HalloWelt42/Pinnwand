"""Tests fuer die Anmeldung (Login mit Name/Kuerzel + Passwort, Sitzungen, Rollen-Durchsetzung).

Wichtig: Alle Tests teilen eine Session-Datenbank. Die autouse-Teardown stellt sicher,
dass die Anmeldepflicht nach jedem Test wieder AUS ist - sonst wuerden die uebrigen
Testdateien (ohne Sitzung) lauter 401 bekommen. Reihenfolge in dieser Datei zaehlt:
der Aussperr-Schutz-Test laeuft, bevor irgendein Admin-Passwort gesetzt wird.
"""
from __future__ import annotations

import pytest

from module.auth import persistence as adb


@pytest.fixture(autouse=True)
def _login_danach_aus():
    yield
    adb.setze_einstellung("login_erforderlich", "0")


def _person(client, name, kuerzel, rolle="mitarbeiter"):
    p = client.post(
        "/api/planung/personen",
        json={"name": name, "kuerzel": kuerzel, "wochenstunden": [0, 0, 0, 0, 0, 0, 0]},
    ).json()
    if rolle == "admin":
        client.patch(f"/api/planung/personen/{p['id']}", json={"rolle": "admin"})
    return p


def test_status_ohne_login_ist_offen(client):
    s = client.get("/api/auth/status").json()
    assert s["erforderlich"] is False
    assert s["angemeldet"] is False
    # Ohne aktiven Login ist die API offen (Phase-1-Verhalten).
    assert client.get("/api/kanban/mappen").status_code == 200


def test_aktivieren_ohne_admin_passwort_blockiert(client):
    # Laeuft vor jedem Setzen eines Passworts -> kein Admin hat eines -> 400 (Aussperr-Schutz).
    r = client.put("/api/auth/login-modus", json={"erforderlich": True})
    assert r.status_code == 400, r.text


def test_login_flow_und_serverseitige_durchsetzung(client):
    admin = _person(client, "Auth Chefin", "ACH", "admin")
    mit = _person(client, "Auth Helfer", "AHE", "mitarbeiter")
    assert client.post(f"/api/planung/personen/{admin['id']}/passwort", json={"passwort": "chefin-geheim"}).status_code == 200
    assert client.post(f"/api/planung/personen/{mit['id']}/passwort", json={"passwort": "helfer-geheim"}).status_code == 200

    # Jetzt hat ein Admin ein Passwort -> Aktivieren klappt
    assert client.put("/api/auth/login-modus", json={"erforderlich": True}).status_code == 200

    # Ohne Sitzung ist die geschuetzte API gesperrt
    assert client.get("/api/kanban/mappen").status_code == 401

    # Falsches Passwort
    assert client.post("/api/auth/login", json={"kennung": "ACH", "passwort": "falsch"}).status_code == 401

    # Login per Kuerzel (Admin) und per Name (Mitarbeiter)
    tok_admin = client.post("/api/auth/login", json={"kennung": "ACH", "passwort": "chefin-geheim"}).json()["token"]
    tok_mit = client.post("/api/auth/login", json={"kennung": "Auth Helfer", "passwort": "helfer-geheim"}).json()["token"]
    h_admin = {"X-Pinnwand-Sitzung": tok_admin}
    h_mit = {"X-Pinnwand-Sitzung": tok_mit}

    s = client.get("/api/auth/status", headers=h_admin).json()
    assert s["angemeldet"] is True and s["rolle"] == "admin" and s["kuerzel"] == "ACH"

    # Lesen ist fuer alle Angemeldeten erlaubt
    assert client.get("/api/kanban/mappen", headers=h_mit).status_code == 200
    # Admin-Bereich (Backup) nur fuer Admin
    assert client.get("/api/backup", headers=h_mit).status_code == 403
    assert client.get("/api/backup", headers=h_admin).status_code == 200
    # Schreibender Planungszugriff nur fuer Admin
    assert client.post("/api/planung/personen", json={"name": "X", "kuerzel": "X9"}, headers=h_mit).status_code == 403
    assert client.post("/api/planung/personen", json={"name": "Y", "kuerzel": "Y9"}, headers=h_admin).status_code == 201

    # Logout beendet die Sitzung
    assert client.post("/api/auth/logout", headers=h_admin).status_code == 204
    assert client.get("/api/backup", headers=h_admin).status_code == 401


def test_passwort_aendern_beendet_sitzung(client):
    """Passwortwechsel/-entfernung beendet bestehende Sitzungen der Person (CWE-613)."""
    a1 = _person(client, "Auth Eins", "AE1", "admin")
    a2 = _person(client, "Auth Zwei", "AE2", "admin")
    client.post(f"/api/planung/personen/{a1['id']}/passwort", json={"passwort": "eins-geheim"})
    client.post(f"/api/planung/personen/{a2['id']}/passwort", json={"passwort": "zwei-geheim"})
    client.put("/api/auth/login-modus", json={"erforderlich": True})
    h1 = {"X-Pinnwand-Sitzung": client.post("/api/auth/login", json={"kennung": "AE1", "passwort": "eins-geheim"}).json()["token"]}
    h2 = {"X-Pinnwand-Sitzung": client.post("/api/auth/login", json={"kennung": "AE2", "passwort": "zwei-geheim"}).json()["token"]}
    assert client.get("/api/auth/status", headers=h2).json()["angemeldet"] is True

    # a1 (Admin) entfernt a2s Passwort -> erlaubt (a1 bleibt Admin mit Passwort)
    weg = client.post(f"/api/planung/personen/{a2['id']}/passwort", json={"passwort": ""}, headers=h1)
    assert weg.status_code == 200, weg.text
    assert weg.json()["hat_passwort"] is False
    # a2s bestehende Sitzung ist sofort ungueltig, und Neu-Login schlaegt fehl
    assert client.get("/api/auth/status", headers=h2).json()["angemeldet"] is False
    assert client.post("/api/auth/login", json={"kennung": "AE2", "passwort": "zwei-geheim"}).status_code == 401


def test_letzter_admin_kann_nicht_ausgesperrt_werden(client):
    """Bei aktiver Anmeldung laesst sich der letzte Admin mit Passwort weder
    entpasswortten noch herabstufen noch loeschen (sonst dauerhafte Aussperrung)."""
    # Saubere Ausgangslage herstellen (Login noch aus -> offen): allen bestehenden
    # Admins das Passwort nehmen, damit ASO gleich der einzige Admin mit Passwort ist.
    for p in client.get("/api/planung/personen").json():
        if p["rolle"] == "admin" and p["hat_passwort"]:
            client.post(f"/api/planung/personen/{p['id']}/passwort", json={"passwort": ""})
    a = _person(client, "Auth Solo", "ASO", "admin")
    client.post(f"/api/planung/personen/{a['id']}/passwort", json={"passwort": "solo-geheim"})
    client.put("/api/auth/login-modus", json={"erforderlich": True})
    h = {"X-Pinnwand-Sitzung": client.post("/api/auth/login", json={"kennung": "ASO", "passwort": "solo-geheim"}).json()["token"]}

    assert client.post(f"/api/planung/personen/{a['id']}/passwort", json={"passwort": ""}, headers=h).status_code == 409
    assert client.patch(f"/api/planung/personen/{a['id']}", json={"rolle": "mitarbeiter"}, headers=h).status_code == 409
    assert client.delete(f"/api/planung/personen/{a['id']}", headers=h).status_code == 409
    # Der Admin ist weiterhin funktionsfaehig.
    assert client.get("/api/backup", headers=h).status_code == 200
