"""Tests fuer Rollen (Phase 1, ohne Passwort).

Geprueft wird:
- Eine frische DB hat mindestens einen Admin (Seed), damit niemand ausgesperrt ist.
- Neue Personen entstehen als 'mitarbeiter' (Default).
- Die Rolle ist per PATCH setzbar (Hoch-/Herabstufen).
"""
from __future__ import annotations

import sqlite3

from module.planung import persistence as db


def test_migration_macht_bestand_zu_admin():
    """Beim Einfuehren der Rolle in eine bestehende DB (ohne rolle-Spalte) muessen
    vorhandene Personen 'admin' werden - sonst sperrt sich der Bestand aus."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE person (id TEXT PRIMARY KEY, name TEXT NOT NULL, kuerzel TEXT, farbe TEXT,"
        " wochenstunden TEXT NOT NULL DEFAULT '[8,8,8,8,8,0,0]', bundesland TEXT,"
        " urlaubsanspruch REAL NOT NULL DEFAULT 30, resturlaub_vorjahr REAL NOT NULL DEFAULT 0,"
        " aktiv INTEGER NOT NULL DEFAULT 1)"
    )
    conn.execute("INSERT INTO person (id, name) VALUES ('p_alt', 'Bestand')")
    db._migriere(conn)
    assert conn.execute("SELECT rolle FROM person WHERE id='p_alt'").fetchone()["rolle"] == "admin"
    conn.close()


def test_ungueltige_rolle_wird_abgefangen():
    """Ein ungueltiger rolle-Wert in der DB (z.B. aus fremdem Backup) darf nicht die
    ganze Personenliste killen, sondern wird sicher auf 'mitarbeiter' gemappt."""
    from module.planung.models import Person

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE person (id TEXT, name TEXT, kuerzel TEXT, farbe TEXT, wochenstunden TEXT,"
        " bundesland TEXT, urlaubsanspruch REAL, resturlaub_vorjahr REAL, aktiv INTEGER, rolle TEXT)"
    )
    conn.execute(
        "INSERT INTO person VALUES ('p_x','X',NULL,NULL,'[8,8,8,8,8,0,0]',NULL,30,0,1,'chef')"
    )
    r = conn.execute("SELECT * FROM person WHERE id='p_x'").fetchone()
    p = db._person(r)
    assert p["rolle"] == "mitarbeiter"
    Person(**p)  # darf keinen ValidationError werfen
    conn.close()


def test_seed_hat_admin(client):
    ps = client.get("/api/planung/personen").json()
    assert ps, "Seed sollte Personen anlegen"
    assert any(p["rolle"] == "admin" for p in ps), "mindestens ein Admin im Seed"


def test_neue_person_ist_mitarbeiter(client):
    r = client.post("/api/planung/personen", json={"name": "Neu Person", "kuerzel": "NP"})
    assert r.status_code == 201, r.text
    assert r.json()["rolle"] == "mitarbeiter"


def test_rolle_setzbar(client):
    pid = client.post("/api/planung/personen", json={"name": "Hoch Stufung", "kuerzel": "HS"}).json()["id"]
    r = client.patch(f"/api/planung/personen/{pid}", json={"rolle": "admin"})
    assert r.status_code == 200, r.text
    assert r.json()["rolle"] == "admin"
    # und wieder zurueck
    r = client.patch(f"/api/planung/personen/{pid}", json={"rolle": "mitarbeiter"})
    assert r.status_code == 200, r.text
    assert r.json()["rolle"] == "mitarbeiter"
