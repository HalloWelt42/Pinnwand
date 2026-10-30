"""App-Zugang als eigene Person (HELF-43): wer sich mit dem App-Schlüssel eines Zugangs anmeldet (etwa der Helfer),
ist eine eigene Person mit Namen, Kürzel und Farbe; was er tut, läuft unter ihr. Beim ersten Anmelden übernimmt sie nur
das sicher Erkennbare: Zeiten mit der Notiz "Helfer: ...", die Mitgliedschaft im Board, das wie der Zugang heißt. Als
Besitzer der App zählt sie wie ihre Person."""

from __future__ import annotations

from conftest import Pinnwand
from test_verwaltung import ok

HELFER = {"Authorization": "Bearer kw_app_helfer_anna"}


async def test_helfer_ist_eine_eigene_person(pw: Pinnwand):
    helf = await pw.board("anna", "Helfer", "HELF")
    haus = await pw.board("anna")
    k = await pw.karte("anna", helf, "Ticket")
    # was der Helfer bisher unter anna buchte, und was anna selbst buchte
    await ok(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 600, "notiz": "Helfer: Arbeit"})
    await ok(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 300, "notiz": "selbst"})
    pw.kopf["helfer"] = HELFER
    s = await pw.stand("helfer")
    ich = next(x for x in s["konten"] if x["id"] == s["ich"])
    assert (ich["name"], ich["kuerzel"], ich["app"], ich["inhaber"], ich["kellerwolke"]) == ("Helfer", "HE", "Helfer", "1", "anna/Helfer")
    assert s["ich"] != (await pw.stand("anna"))["ich"]
    # Mitglied nur im Board Helfer; seine Zeit ist seine, annas bleibt annas
    assert [b["kuerzel"] for b in s["boards"]] == ["HELF"] and haus["id"] not in [b["id"] for b in s["boards"]]
    zeiten = {z["notiz"]: z["konto"] for z in (await pw.stand("anna"))["zeiteintraege"]}
    assert zeiten == {"Helfer: Arbeit": s["ich"], "selbst": "1"}
    # Kommentar und Timer laufen unter ihm
    await ok(pw, "helfer", f"/karten/{k['id']}/kommentieren", {"text": "Erledigt."})
    karte = next(x for x in (await pw.stand("anna"))["karten"] if x["id"] == k["id"])
    assert karte["kommentare"][-1]["von"] == s["ich"]
    await ok(pw, "helfer", "/timer/starten", {"karte": k["id"]})
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})            # annas eigener Timer läuft daneben
    assert sorted(t["konto"] for t in (await pw.stand("anna"))["timer"]) == sorted(["1", s["ich"]])
    # zählt als Besitzer der App wie anna (Commits einspielen)
    assert s["appBesitzer"] is True
    # noch einmal angemeldet: dieselbe Person, kein zweiter Nachtrag
    assert (await pw.stand("helfer"))["ich"] == s["ich"]


async def test_einladen_als_konto_und_zugang(pw: Pinnwand):
    haus = await pw.board("anna")
    await ok(pw, "anna", f"/boards/{haus['id']}/mitglieder", {"kellerwolke": "anna/Helfer"})
    pw.kopf["helfer"] = HELFER
    s = await pw.stand("helfer")
    assert [b["kuerzel"] for b in s["boards"]] == ["HAUS"]
    m = next(m for m in s["boards"][0]["mitglieder"] if m["kellerwolke"] == "anna/Helfer")
    assert m["konto"] == s["ich"]


async def test_altbestand_eindeutiges_geht_ueber(pw: Pinnwand):
    """Was der Helfer vor seiner eigenen Person unter anna tat, geht über, wenn es eindeutig ist (Merkmale seiner Berichte
    und Werkzeuge); Verschieben und eigene Kommentare annas bleiben bei anna. Nur einmal."""
    from app.anwendung import altbestand
    helf = await pw.board("anna", "Helfer", "HELF")
    k = await pw.karte("anna", helf, "Ticket")
    await ok(pw, "anna", f"/karten/{k['id']}/kommentieren", {"text": "Ursache gefunden, ausgerollt in 0.2.0."})
    await ok(pw, "anna", f"/karten/{k['id']}/kommentieren", {"text": "Danke, sieht gut aus."})
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"prioritaet": "hoch"}, "text": "HELF-1: Priorität hoch (Einschätzung des Helfers)"})
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": next(s["id"] for s in helf["spalten"] if s["name"] == "Dran")})
    pw.kopf["helfer"] = HELFER
    helfer = (await pw.stand("helfer"))["ich"]
    v = pw.app.state.dienste.anwendung.v
    assert await v.db.transaktion(lambda c: altbestand.uebertragen(c, "2026-10-27T00:00:00")) == 3
    assert await v.db.transaktion(lambda c: altbestand.uebertragen(c, "2026-10-27T00:00:00")) == 0
    karte = next(x for x in (await pw.stand("anna"))["karten"] if x["id"] == k["id"])
    assert [(c["text"][:7], c["von"]) for c in karte["kommentare"]] == [("Ursache", helfer), ("Danke, ", "1")]
    verlauf = [(e["text"], e["von"] == helfer) for e in karte["verlauf"]]
    assert verlauf == [("hat die Karte angelegt", False), ("hat kommentiert", True), ("hat kommentiert", False),
                       ("hat die Priorität auf Hoch gesetzt", True), ("hat sie von Offen nach Dran verschoben", False)]
