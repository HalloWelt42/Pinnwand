"""Ordnung der Spalten (HELF-50): Sortierung je Spalte als Vorgabe für alle, aus der Vorlage und in eine gespeicherte
Vorlage; neue Karten und Karten ohne Platz kommen oben in die Spalte."""

from __future__ import annotations

from conftest import Pinnwand
from test_kern import reihe, spalte


async def test_vorlagen_bringen_die_sortierung_mit(pw: Pinnwand):
    b = await pw.board("anna")
    assert [(s["name"], s["sortierung"]) for s in b["spalten"]] == [
        ("Offen", "prioritaet"), ("Dran", "arbeitsbeginn"), ("Erledigt", "erledigung")]
    p = await pw.board("anna", "Projekt", "PRO", vorlage="v-projekt")
    assert [s["sortierung"] for s in p["spalten"]] == ["prioritaet", "prioritaet", "arbeitsbeginn", "arbeitsbeginn", "erledigung"]


async def test_sortierung_aendern_und_als_vorlage(pw: Pinnwand):
    b = await pw.board("anna")
    offen = spalte(b, "Offen")
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{offen}/aendern", {"sortierung": "hand"})
    assert r.json()["meldung"] == "Spalte Offen: sortiert nach Hand" and r.json()["rueckgaengig"]
    # dieselbe noch einmal ändert nichts
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{offen}/aendern", {"sortierung": "hand"})
    assert r.json()["meldung"] is None
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{offen}/aendern", {"sortierung": "irgendwie"})
    assert r.status_code == 422
    await pw.post("anna", f"/boards/{b['id']}/vorlage", {"name": "Meine Art"})
    v = next(x for x in (await pw.stand("anna"))["vorlagen"] if x["name"] == "Meine Art")
    assert [s.get("sortierung") for s in v["spalten"]] == ["hand", "arbeitsbeginn", "erledigung"]
    neu = await pw.board("anna", "Zweites", "ZWEI", vorlage=v["id"])
    assert [s["sortierung"] for s in neu["spalten"]] == ["hand", "arbeitsbeginn", "erledigung"]


async def test_neue_karten_oben(pw: Pinnwand):
    b = await pw.board("anna")
    for t in ("Alt", "Mittel", "Neu"):
        await pw.karte("anna", b, t)
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-3", "HAUS-2", "HAUS-1"]
    # mehrere auf einmal: oben, in ihrer Reihenfolge
    r = await pw.post("anna", f"/boards/{b['id']}/karten/mehrere", {"spalte": spalte(b, "Offen"), "art": "arbeit",
                                                                     "karten": [{"titel": "Eins"}, {"titel": "Zwei"}]})
    assert r.status_code == 200, r.text
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-4", "HAUS-5", "HAUS-3", "HAUS-2", "HAUS-1"]
    # duplizieren: die Kopie oben
    alt = next(k for k in (await pw.stand("anna"))["karten"] if k["schluessel"] == "HAUS-1")
    await pw.post("anna", f"/karten/{alt['id']}/duplizieren")
    assert (await reihe(pw, "anna", b, "Offen"))[0] == "HAUS-6"
    # verschieben ohne Platz (Status im Detail, Telefon, Liste): oben in der Zielspalte
    await pw.karte("anna", b, "Schon dran", spalte=spalte(b, "Dran"))
    await pw.post("anna", f"/karten/{alt['id']}/verschieben", {"nach": spalte(b, "Dran")})
    assert await reihe(pw, "anna", b, "Dran") == ["HAUS-1", "HAUS-7"]
