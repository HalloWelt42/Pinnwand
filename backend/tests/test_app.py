"""Pinnwand auf dem Gerüst: einrichten, anmelden nur mit Erlaubnis, ohne Sitzung kein Stand, Protokoll."""

import httpx

from conftest import Pinnwand


async def test_einrichten_und_anmelden(pw: Pinnwand):
    app = (await pw.c.get("/api/v1/app")).json()
    assert not app["einrichtung_noetig"]
    assert (await pw.c.get("/api/v1/stand")).status_code == 401
    assert (await pw.anmelden("cora")).status_code != 200                     # nicht erlaubt
    r = await pw.c.post("/api/v1/anmeldung", json={"kennung": "anna", "passwort": "falsch"})
    assert r.status_code != 200
    ereignisse = [e["ereignis"] for e in (await pw.get("anna", "/protokoll")).json()["eintraege"]]
    assert "app.eingerichtet" in ereignisse


async def test_oberflaeche_ohne_sitzung(pw: Pinnwand):
    r = await pw.c.get("/api/v1/ereignisse")
    assert isinstance(r, httpx.Response) and r.status_code == 401
