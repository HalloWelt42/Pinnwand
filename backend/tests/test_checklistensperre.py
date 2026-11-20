"""Ohne abgehakte Checkliste nie fertig (HELF-255): eine Spalte mit dem Schalter "nur mit abgehakter Checkliste" nimmt
keine Karte mit offenem Punkt, auf keinem Weg; kommt dort ein Punkt dazu oder geht ein Haken weg, geht die Karte zurück
in die erste Spalte ohne Sperre. Die Vorlage Projekt sperrt Prüfung und Erledigt; der Start trägt den Schalter in
bestehenden Boards nach."""

from __future__ import annotations

import json

from conftest import Pinnwand
from test_verwaltung import ok, spalte

PUNKTE = [{"text": "Erster Schritt", "erledigt": True}, {"text": "Zweiter Schritt", "erledigt": False}]


async def _projekt(pw: Pinnwand, kuerzel: str = "PROJ") -> dict:
    """Board der Vorlage Projekt: Eingang, Geplant, In Arbeit, Prüfung, Erledigt."""
    return await pw.board("anna", "Projekt", kuerzel, vorlage="v-projekt")


async def _mit_punkten(pw: Pinnwand, b: dict, titel: str = "Ticket", punkte: list[dict] | None = None, wo: str = "In Arbeit") -> dict:
    k = await pw.karte("anna", b, titel, spalte=spalte(b, wo))
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": punkte or PUNKTE}})
    return k


async def _karte(pw: Pinnwand, kid: str) -> dict:
    return next(c for c in (await pw.stand("anna"))["karten"] if c["id"] == kid)


async def _abgelehnt(pw: Pinnwand, pfad: str, daten: dict) -> str:
    r = await pw.post("anna", pfad, daten)
    assert r.status_code == 400, r.text
    return r.json()["detail"]


async def test_vorlage_sperrt_pruefung_und_erledigt(pw: Pinnwand):
    b = await _projekt(pw)
    gesperrt = {s["name"] for s in b["spalten"] if s.get("nurAbgehakt")}
    assert gesperrt == {"Prüfung", "Erledigt"}


async def test_verschieben_nach_pruefung_nur_abgehakt(pw: Pinnwand):
    b = await _projekt(pw)
    k = await _mit_punkten(pw, b)
    grund = await _abgelehnt(pw, f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Prüfung")})
    assert grund == ("PROJ-1 hat noch 1 offenen Punkt der Checkliste (erster: Zweiter Schritt); "
                     "Prüfung nimmt nur Karten mit vollständig abgehakter Checkliste")
    assert (await _karte(pw, k["id"]))["spalte"] == spalte(b, "In Arbeit"), "nichts bewegt"
    # Ziehen an einen Platz, Abhaken und Sammelaktion: derselbe Riegel
    await _abgelehnt(pw, f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Prüfung"), "platz": 0})
    await _abgelehnt(pw, f"/karten/{k['id']}/erledigen", {})
    zweite = await _mit_punkten(pw, b, "Zweites")
    grund = await _abgelehnt(pw, "/karten/sammel/verschieben", {"ids": [k["id"], zweite["id"]], "nach": spalte(b, "Erledigt")})
    assert grund.startswith("2 Karten haben noch offene Punkte der Checkliste (PROJ-1, PROJ-2)")
    # alles abgehakt: geht
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten",
             {"felder": {"checkliste": [{**p, "erledigt": True} for p in PUNKTE]}})
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Prüfung")})
    assert (await _karte(pw, k["id"]))["spalte"] == spalte(b, "Prüfung")


async def test_ohne_checkliste_frei(pw: Pinnwand):
    """Eine Karte ohne Checkliste hat nichts offen."""
    b = await _projekt(pw)
    k = await pw.karte("anna", b, "Ohne Liste")
    await ok(pw, "anna", f"/karten/{k['id']}/erledigen")


async def test_verknuepfte_ziehen_nicht_offen_mit(pw: Pinnwand):
    b = await _projekt(pw)
    fertig = await _mit_punkten(pw, b, "Fertig", [{"text": "a", "erledigt": True}])
    offen = await _mit_punkten(pw, b, "Offen")
    await ok(pw, "anna", f"/karten/{fertig['id']}/verknuepfen", {"mit": offen["id"]})
    grund = await _abgelehnt(pw, f"/karten/{fertig['id']}/verschieben", {"nach": spalte(b, "Prüfung")})
    assert grund.startswith(f"{offen['schluessel']} hat noch 1 offenen Punkt")


async def test_anlegen_und_umzug_in_gesperrte_spalte(pw: Pinnwand):
    b = await _projekt(pw)
    grund = await _abgelehnt(pw, f"/boards/{b['id']}/karten/mehrere",
                             {"karten": [{"titel": "Neu", "checkliste": ["offen"]}], "spalte": spalte(b, "Prüfung")})
    assert "Prüfung nimmt nur Karten" in grund
    await ok(pw, "anna", f"/boards/{b['id']}/karten/mehrere", {"karten": [{"titel": "Ohne"}], "spalte": spalte(b, "Prüfung")})
    anderes = await _projekt(pw, "ZWEI")
    k = await _mit_punkten(pw, b)
    grund = await _abgelehnt(pw, f"/karten/{k['id']}/umziehen", {"board": anderes["id"], "spalte": spalte(anderes, "Erledigt")})
    assert "Erledigt nimmt nur Karten" in grund
    await ok(pw, "anna", f"/karten/{k['id']}/umziehen", {"board": anderes["id"]})


async def test_kopie_aus_pruefung_landet_vorn(pw: Pinnwand):
    """Die Kopie hat ihre Punkte offen: aus einer gesperrten Spalte kommt sie in die erste Spalte ohne Sperre."""
    b = await _projekt(pw)
    k = await _mit_punkten(pw, b, punkte=[{"text": "a", "erledigt": True}])
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Prüfung")})
    r = await ok(pw, "anna", f"/karten/{k['id']}/duplizieren")
    kopie = next(g["daten"] for g in r["geaendert"] if g["tabelle"] == "karten" and g["daten"]["id"] != k["id"])
    assert kopie["spalte"] == spalte(b, "Eingang")
    assert r["meldung"].endswith("(in Eingang: Checkliste offen)")


async def test_neuer_punkt_in_pruefung_schickt_zurueck(pw: Pinnwand):
    b = await _projekt(pw)
    fertig = [{"text": "a", "erledigt": True}]
    k = await _mit_punkten(pw, b, punkte=fertig)
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Prüfung")})
    r = await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": fertig + [{"text": "Nachtrag"}]}})
    c = await _karte(pw, k["id"])
    assert c["spalte"] == spalte(b, "Eingang")
    assert "Checkliste wieder offen, zurück nach Eingang" in r["meldung"]
    assert any(e["text"] == "Checkliste wieder offen: zurück aus Prüfung" for e in c["verlauf"])


async def test_haken_entfernen_in_erledigt_schickt_zurueck(pw: Pinnwand):
    b = await _projekt(pw)
    k = await _mit_punkten(pw, b, punkte=[{"text": "a", "erledigt": True}])
    await ok(pw, "anna", f"/karten/{k['id']}/erledigen")
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": [{"text": "a", "erledigt": False}]}})
    c = await _karte(pw, k["id"])
    assert c["spalte"] == spalte(b, "Eingang") and not c.get("abgeschlossen")


async def test_abhaken_oder_loeschen_schickt_nicht_zurueck(pw: Pinnwand):
    """Karten, die schon mit offenem Punkt dastehen (vor dem Schalter), bleiben beim Abhaken oder Löschen stehen."""
    b = await _projekt(pw)
    k = await _mit_punkten(pw, b, punkte=[{"text": "a"}, {"text": "b"}])
    pruefung = spalte(b, "Prüfung")
    await ok(pw, "anna", f"/boards/{b['id']}/spalten/{pruefung}/aendern", {"nurAbgehakt": False})
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": pruefung})
    r = await ok(pw, "anna", f"/boards/{b['id']}/spalten/{pruefung}/aendern", {"nurAbgehakt": True})
    assert r["meldung"] == "Spalte Prüfung: nur mit abgehakter Checkliste, 1 Karte steht schon mit offenen Punkten darin"
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": [{"text": "a", "erledigt": True}, {"text": "b"}]}})
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": [{"text": "a", "erledigt": True}]}})
    assert (await _karte(pw, k["id"]))["spalte"] == pruefung


async def test_schalter_aus_laesst_durch(pw: Pinnwand):
    b = await _projekt(pw)
    k = await _mit_punkten(pw, b)
    r = await ok(pw, "anna", f"/boards/{b['id']}/spalten/{spalte(b, 'Erledigt')}/aendern", {"nurAbgehakt": False})
    assert r["meldung"] == "Spalte Erledigt: auch mit offener Checkliste"
    await ok(pw, "anna", f"/karten/{k['id']}/erledigen")


async def test_nachtrag_beim_start(pw: Pinnwand):
    """Bestehende Boards (vor HELF-255 ohne das Feld): Erledigt und Spalten namens Prüfung, Zur Prüfung oder Zu testen
    sperren nach dem Start; eine ausdrücklich ausgeschaltete bleibt aus."""
    from app.anwendung import checklistensperre
    b = await pw.board("anna", "Helfer", "HELF")

    def ohne_feld(v):
        z = v.execute("SELECT daten FROM boards WHERE id=?", (b["id"],)).fetchone()
        d = json.loads(z["daten"])
        for s in d["spalten"]:
            s.pop("nurAbgehakt", None)
        d["spalten"].insert(2, {**d["spalten"][1], "id": "s-pruef", "name": "Zu testen"})
        v.execute("UPDATE boards SET daten=? WHERE id=?", (json.dumps(d), b["id"]))
    db = pw.app.state.dienste.anwendung.v.db
    await db.transaktion(ohne_feld)
    assert await db.transaktion(checklistensperre.nachtragen) == 2, "Zu testen und Erledigt"
    assert await db.transaktion(checklistensperre.nachtragen) == 0, "ein zweiter Lauf ändert nichts"
    neu = next(x for x in (await pw.stand("anna"))["boards"] if x["id"] == b["id"])
    assert {s["name"] for s in neu["spalten"] if s.get("nurAbgehakt")} == {"Zu testen", "Erledigt"}
    await ok(pw, "anna", f"/boards/{b['id']}/spalten/s-pruef/aendern", {"nurAbgehakt": False})
    assert await db.transaktion(checklistensperre.nachtragen) == 0, "aus bleibt aus"
