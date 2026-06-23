"""Isolations- und Aggregationstests fuer das geteilte Datenmodell.

Pinnwand hat bewusst KEINE getrennten Datenbanken je Nutzer. Stattdessen gilt das
Modell "geteilte Boards + eigene Daten":
- Boards und Karten sind GETEILT - jede Person sieht dieselben.
- Die ZEIT-Kennzahlen (Ist/Soll) sind PRO PERSON getrennt; die Zuordnung laeuft
  ueber das Kuerzel der Karte (karte.zustaendig). Die Personen-Sicht filtert nur
  Kennzahlen, nicht die Board-Daten.

Diese Tests stellen sicher, dass genau das stimmt: getrennt wo noetig, geteilt wo
gewollt - und dass die zentralen Zeit-Invarianten halten.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest


# --- kleine API-Helfer ---------------------------------------------------

def _person(client, name, kuerzel, wochenstunden):
    r = client.post("/api/planung/personen", json={"name": name, "kuerzel": kuerzel, "wochenstunden": wochenstunden})
    assert r.status_code == 201, r.text
    return r.json()


def _board(client, titel="Test-Board"):
    m = client.post("/api/kanban/mappen", json={"titel": "Test-Mappe"})
    assert m.status_code == 201, m.text
    b = client.post(f"/api/kanban/mappen/{m.json()['id']}/boards", json={"titel": titel})
    assert b.status_code == 201, b.text
    return b.json()


def _karte(client, board_id, spalte, titel, zustaendig=None):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel, "zustaendig": zustaendig})
    assert r.status_code == 201, r.text
    return r.json()


def _buche(client, karte_id, datum, sekunden):
    r = client.post("/api/kanban/zeiteintraege", json={"karte_id": karte_id, "datum": datum, "sekunden": sekunden})
    assert r.status_code == 201, r.text
    return r.json()


def _stunden(client, person_id=None):
    url = "/api/planung/stunden-uebersicht" + (f"?person={person_id}" if person_id else "")
    r = client.get(url)
    assert r.status_code == 200, r.text
    return r.json()


def _board_detail(client, board_id):
    r = client.get(f"/api/kanban/boards/{board_id}")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def szenario(client):
    """Baut die Vergleichslage auf: zwei Personen (T1 Vollzeit, T2 Halbtags), ein
    geteiltes Board mit je einer Karte pro Person und am HEUTIGEN Tag gebuchte Zeit
    (T1: 2h, T2: 1h). Eindeutige Kuerzel (T1/T2) sorgen dafuer, dass die Pruefungen
    unabhaengig von etwaigen Seed-Daten sind.
    """
    heute = date.today().isoformat()
    t1 = _person(client, "Tester Eins", "T1", [8, 8, 8, 8, 8, 0, 0])
    t2 = _person(client, "Tester Zwei", "T2", [4, 4, 4, 4, 4, 0, 0])
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k1 = _karte(client, board["id"], spalte, "Aufgabe T1", "T1")
    k2 = _karte(client, board["id"], spalte, "Aufgabe T2", "T2")
    _buche(client, k1["id"], heute, 7200)  # 2h fuer T1
    _buche(client, k2["id"], heute, 3600)  # 1h fuer T2
    return {"t1": t1, "t2": t2, "board": board, "spalte": spalte, "k1": k1, "k2": k2, "heute": heute}


# --- Trennung der Ist-Zeit ----------------------------------------------

def test_ist_zeit_pro_person_getrennt(client, szenario):
    """Die erfasste Ist-Zeit wird strikt der Person zugeordnet, der die Karte gehoert.
    T1 sieht heute genau die eigenen 2h, T2 genau die eigene 1h - keine Vermischung,
    obwohl beide am selben Tag auf demselben Board gebucht haben."""
    s1 = _stunden(client, szenario["t1"]["id"])
    s2 = _stunden(client, szenario["t2"]["id"])
    assert s1["heute"]["ist_sek"] == 7200
    assert s2["heute"]["ist_sek"] == 3600


def test_team_ist_ist_summe_ueber_alle_personen(client, szenario):
    """Die Team-Sicht (ohne Person) summiert die Ist-Zeit ueber alle Personen. Sie
    enthaelt T1 und T2 zusammen und entspricht der Summe aller heutigen Zeiteintraege -
    die Einzelsichten sind also echte Teilmengen der Team-Summe."""
    heute = szenario["heute"]
    alle = client.get(f"/api/kanban/zeiteintraege?von={heute}&bis={heute}").json()
    summe_eintraege = sum(e["sekunden"] for e in alle)
    team = _stunden(client)
    assert team["heute"]["ist_sek"] == summe_eintraege
    assert team["heute"]["ist_sek"] >= 7200 + 3600


# --- Geteilte Board-Daten -----------------------------------------------

def test_boards_und_karten_sind_geteilt(client, szenario):
    """Boards und Karten sind nicht personengebunden: dasselbe Board liefert beide
    Karten (von T1 und T2). Die Trennung passiert erst auf der Kennzahlen-Ebene, nicht
    auf der Board-Ebene."""
    bd = _board_detail(client, szenario["board"]["id"])
    titel = {k["titel"] for k in bd["karten"]}
    assert "Aufgabe T1" in titel
    assert "Aufgabe T2" in titel


def test_eigentum_ueber_zustaendig(client, szenario):
    """Der Eigentuemer eines Zeiteintrags ergibt sich aus dem Kuerzel der Karte
    (karte_zustaendig). Genau darauf beruht die read-only-Sperre fremder Eintraege in
    der Zeiten-Ansicht."""
    e1 = client.get(f"/api/kanban/zeiteintraege?karte_id={szenario['k1']['id']}").json()
    e2 = client.get(f"/api/kanban/zeiteintraege?karte_id={szenario['k2']['id']}").json()
    assert e1 and all(e["karte_zustaendig"] == "T1" for e in e1)
    assert e2 and all(e["karte_zustaendig"] == "T2" for e in e2)


# --- Trennung des Solls --------------------------------------------------

def test_soll_pro_person_getrennt(client, szenario):
    """Das Soll richtet sich nach den Wochenstunden der jeweiligen Person. T1 (Vollzeit)
    hat ein hoeheres Jahres-Soll als T2 (Halbtags); das Team-Soll ist die Summe der
    aktiven Personen und damit mindestens so gross wie das von T1."""
    s1 = _stunden(client, szenario["t1"]["id"])
    s2 = _stunden(client, szenario["t2"]["id"])
    team = _stunden(client)
    assert s1["jahr"]["soll_sek"] > s2["jahr"]["soll_sek"] > 0
    assert team["jahr"]["soll_sek"] >= s1["jahr"]["soll_sek"]


# --- Zeit-Invarianten ----------------------------------------------------

def test_ticketzeit_ist_summe_der_datierten_eintraege(client, szenario):
    """Ticketzeit (erfasst_sek einer Karte) ist immer die Summe ihrer datierten
    Eintraege. Ein zweiter Eintrag an einem anderen Tag erhoeht die Summe, Loeschen
    senkt sie wieder - es gibt keine freie, undatierte Gesamtzeit."""
    heute = date.today()
    gestern = (heute - timedelta(days=1)).isoformat()
    k = _karte(client, szenario["board"]["id"], szenario["spalte"], "Summen-Karte", "T1")
    _buche(client, k["id"], heute.isoformat(), 1800)
    e_gestern = _buche(client, k["id"], gestern, 600)

    def erfasst():
        bd = _board_detail(client, szenario["board"]["id"])
        return next(x["erfasst_sek"] for x in bd["karten"] if x["id"] == k["id"])

    assert erfasst() == 2400
    assert client.delete(f"/api/kanban/zeiteintraege/{e_gestern['id']}").status_code == 204
    assert erfasst() == 1800


def test_fertig_abschlussdatum_nicht_serie_ist_verschiebe_tag(client, szenario):
    """Fuer Nicht-Serien-Karten ist das Abschlussdatum (abschluss_am, Grundlage des
    Fertig-Zeitfilters) der Erledigt-Zeitpunkt: der Tag, an dem die Karte in die als
    erledigt markierte Spalte verschoben wurde (bewegt_am) - unabhaengig davon, an
    welchem Tag Zeit gebucht wurde."""
    bd = _board_detail(client, szenario["board"]["id"])
    fertig = bd["spalten"][-1]["id"]
    assert client.post(f"/api/kanban/spalten/{fertig}/erledigt").status_code == 200
    k = _karte(client, szenario["board"]["id"], szenario["spalte"], "Erledigt-Karte", "T1")
    # Zeit auf gestern buchen, aber HEUTE verschieben -> Abschlussdatum = heute.
    gestern = (date.today() - timedelta(days=1)).isoformat()
    _buche(client, k["id"], gestern, 600)
    assert client.post(f"/api/kanban/karten/{k['id']}/move", json={"spalte": fertig, "reihenfolge": 0}).status_code == 200
    bd2 = _board_detail(client, szenario["board"]["id"])
    karte = next(x for x in bd2["karten"] if x["id"] == k["id"])
    assert karte["abschluss_am"] == date.today().isoformat()
