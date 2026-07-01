"""Tests fuer Self-Service-Planung + Zeiteintrag-Ownership.

Unit: die reine Berechtigungs-Politik (rechte.py) ohne HTTP.
Integration: bei aktivem Login darf ein Mitarbeiter nur EIGENE Planungs-/Zeitdaten
aendern, ein Admin alle; ohne Login bleibt alles offen (Regressionsschutz).
"""
from __future__ import annotations

import pytest

from module.auth import persistence as adb
from module.auth import rechte
from module.auth.akteur import Akteur


@pytest.fixture(autouse=True)
def _login_danach_aus(client):
    # client anfordern, damit die App (und das DB-Schema) sicher aufgebaut ist -
    # auch fuer die reinen Unit-Tests, bevor der Teardown die Einstellung schreibt.
    yield
    adb.setze_einstellung("login_erforderlich", "0")


# -- Unit: Politik --------------------------------------------------------

def test_rechte_person_self_or_admin():
    admin = Akteur(person_id="p1", kuerzel="AD", rolle="admin")
    ich = Akteur(person_id="p2", kuerzel="IC", rolle="mitarbeiter")
    assert rechte.darf_person_bearbeiten(admin, "p9")     # Admin: alle
    assert rechte.darf_person_bearbeiten(ich, "p2")        # self
    assert not rechte.darf_person_bearbeiten(ich, "p9")    # fremd
    assert not rechte.darf_person_bearbeiten(ich, None)    # globale Regel = nur Admin
    assert rechte.darf_person_bearbeiten(admin, None)


def test_rechte_zeiteintrag_eigentum_ueber_kuerzel():
    admin = Akteur(person_id="p1", kuerzel="AD", rolle="admin")
    ich = Akteur(person_id="p2", kuerzel="IC", rolle="mitarbeiter")
    ohne_kuerzel = Akteur(person_id="p3", kuerzel=None, rolle="mitarbeiter")
    assert rechte.darf_zeiteintrag_bearbeiten(admin, "XY")
    assert rechte.darf_zeiteintrag_bearbeiten(ich, "IC")
    assert not rechte.darf_zeiteintrag_bearbeiten(ich, "XY")
    assert not rechte.darf_zeiteintrag_bearbeiten(ohne_kuerzel, None)  # fail-closed


def test_offener_akteur_hat_vollzugriff():
    assert Akteur.offen().ist_admin


# -- Integration ----------------------------------------------------------

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


def test_mitarbeiter_nur_eigene_daten(client):
    admin = _person(client, "SS Chefin", "SSC", "admin")
    ich = _person(client, "SS Ich", "SSI", "mitarbeiter")
    andere = _person(client, "SS Andere", "SSA", "mitarbeiter")
    assert client.post(f"/api/planung/personen/{admin['id']}/passwort", json={"passwort": "chef-geheim-1"}).status_code == 200
    assert client.post(f"/api/planung/personen/{ich['id']}/passwort", json={"passwort": "ich-geheim-1"}).status_code == 200

    # Karten fuer die Ownership-Pruefung (Eigentum ueber zustaendig = Kuerzel)
    m = client.post("/api/kanban/mappen", json={"titel": "SS-Mappe"}).json()
    b = client.post(f"/api/kanban/mappen/{m['id']}/boards", json={"titel": "SS-Board"}).json()
    spalte = b["spalten"][0]["id"]

    def _karte(zust):
        return client.post(
            "/api/kanban/karten",
            json={"board_id": b["id"], "spalte": spalte, "titel": "K " + zust, "zustaendig": zust},
        ).json()["id"]

    meine_karte = _karte("SSI")
    fremde_karte = _karte("SSA")

    assert client.put("/api/auth/login-modus", json={"erforderlich": True}).status_code == 200
    kopf = _login(client, "SSI", "ich-geheim-1")

    # Urlaub: eigener ok, fremder verboten
    assert client.post("/api/planung/urlaub", json={"person_id": ich["id"], "von": "2026-08-04", "typ": "urlaub"}, headers=kopf).status_code == 200
    assert client.post("/api/planung/urlaub", json={"person_id": andere["id"], "von": "2026-08-04", "typ": "urlaub"}, headers=kopf).status_code == 403

    # Arbeitszeiten (Wochen-Override): eigener ok, fremder verboten
    assert client.post(f"/api/planung/personen/{ich['id']}/wochen-override", json={"jahr": 2026, "kw": 32, "wochenstunden": [8, 8, 8, 8, 8, 0, 0]}, headers=kopf).status_code == 200
    assert client.post(f"/api/planung/personen/{andere['id']}/wochen-override", json={"jahr": 2026, "kw": 32, "wochenstunden": [8, 8, 8, 8, 8, 0, 0]}, headers=kopf).status_code == 403

    # Person: eigenes Bundesland ok, aber Rolle (Rechtefeld) verboten
    assert client.patch(f"/api/planung/personen/{ich['id']}", json={"bundesland": "ST"}, headers=kopf).status_code == 200
    assert client.patch(f"/api/planung/personen/{ich['id']}", json={"rolle": "admin"}, headers=kopf).status_code == 403

    # Globale Konfig (Feiertage) bleibt admin-only (Middleware) -> 403 fuer Mitarbeiter
    assert client.delete("/api/planung/feiertage?jahr=2026", headers=kopf).status_code == 403

    # Zeiteintrag: eigene Karte ok, fremde Karte verboten
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": meine_karte, "datum": "2026-08-05", "sekunden": 600}, headers=kopf).status_code == 201
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": fremde_karte, "datum": "2026-08-05", "sekunden": 600}, headers=kopf).status_code == 403

    # Admin darf fremde Karte bebuchen
    kopf_admin = _login(client, "SSC", "chef-geheim-1")
    assert client.post("/api/kanban/zeiteintraege", json={"karte_id": fremde_karte, "datum": "2026-08-05", "sekunden": 600}, headers=kopf_admin).status_code == 201


def test_ohne_login_bleibt_offen(client):
    # Ohne aktiven Login (Standardzustand der Test-DB) darf ohne Sitzung geschrieben werden.
    ich = _person(client, "Off Ich", "OFI", "mitarbeiter")
    andere = _person(client, "Off Andere", "OFA", "mitarbeiter")
    # Fremder Urlaub ohne Sitzung -> offen (passwortloser Modus)
    assert client.post("/api/planung/urlaub", json={"person_id": andere["id"], "von": "2026-09-01", "typ": "urlaub"}).status_code == 200
