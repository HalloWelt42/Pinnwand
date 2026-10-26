"""Verwaltung über die Schnittstelle: Board einstellen (Name, Farbe, Kartenart, Einstellungen, Module, Vorlage), Spalten,
Labels, eigene Felder, Rollen und Rechte, Mitglieder (auch wartende Einladungen), Ordner, eigenes Kürzel und die Prüfung
eines Kürzels beim Anlegen; je Fall Recht, Regel, Rückgängig und was an den Karten hängt."""

from __future__ import annotations

import asyncio

import pytest

from app.modell import MODULE_DA
from conftest import Pinnwand


def spalte(b: dict, name: str) -> str:
    return next(s["id"] for s in b["spalten"] if s["name"] == name)


async def board(pw: Pinnwand, wer: str = "anna", kuerzel: str = "HAUS") -> dict:
    return next(b for b in (await pw.stand(wer))["boards"] if b["kuerzel"] == kuerzel)


async def karte(pw: Pinnwand, wer: str, schluessel: str) -> dict:
    r = await pw.get(wer, f"/karten/{schluessel}")
    assert r.status_code == 200, r.text
    return r.json()


async def ok(pw: Pinnwand, wer: str, pfad: str, daten: dict | None = None) -> dict:
    r = await pw.post(wer, pfad, daten)
    assert r.status_code == 200, r.text
    return r.json()


async def abgelehnt(pw: Pinnwand, wer: str, pfad: str, daten: dict | None, status: int, meldung: str) -> None:
    r = await pw.post(wer, pfad, daten)
    assert (r.status_code, r.json().get("detail")) == (status, meldung)


async def mit_bert(pw: Pinnwand, rolle: str = "mitglied") -> dict:
    """Board Haushalt mit bert als angemeldetem Mitglied der Rolle."""
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": rolle}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    return b


# --- Allgemein ---------------------------------------------------------------------------------------------------

async def test_umbenennen_farbe_kartenart(pw: Pinnwand):
    b = await mit_bert(pw)
    a = await ok(pw, "anna", f"/boards/{b['id']}/umbenennen", {"name": " Zuhause "})
    assert a["meldung"] == "Haushalt heißt jetzt Zuhause; das Kürzel HAUS bleibt" and a["rueckgaengig"]
    assert (await ok(pw, "anna", f"/boards/{b['id']}/umbenennen", {"name": "Zuhause"}))["geaendert"] == []
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/umbenennen", {"name": " "}, 400, "Ein Board braucht einen Namen")
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/umbenennen", {"name": "x" * 101}, 400, "Ein Name hat höchstens 100 Zeichen")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/umbenennen", {"name": "Meins"}, 403,
                    "Dir fehlt im Board Zuhause das Recht Board verwalten")

    assert (await ok(pw, "anna", f"/boards/{b['id']}/farbe", {"farbe": "rose"}))["meldung"] == "Farbe von Zuhause geändert"
    a = await ok(pw, "anna", f"/boards/{b['id']}/kartenart", {"kartenart": "idee"})
    assert a["meldung"] == "Neue Karten in Zuhause sind ab jetzt Ideen"
    assert (await pw.karte("anna", b, "Gartenhaus"))["art"] == "idee"
    neu = await board(pw)
    assert (neu["name"], neu["kuerzel"], neu["farbe"], neu["kartenart"]) == ("Zuhause", "HAUS", "rose", "idee")
    # Rückgängig stellt den alten Namen wieder her
    r = await pw.post("anna", f"/rueckgaengig/{a['rueckgaengig']}")
    assert r.status_code == 200 and (await board(pw))["kartenart"] == "arbeit"


async def test_einstellungen_in_grenzen(pw: Pinnwand):
    b = await pw.board("anna")
    a = await ok(pw, "anna", f"/boards/{b['id']}/einstellungen", {"alterungWarnung": 0, "archivTage": 30})
    assert a["meldung"] == "Einstellungen von Haushalt gespeichert"
    assert (await board(pw))["einstellungen"] == {"alterungWarnung": 0, "alterungGefahr": 8, "ladeschritt": 50, "archivTage": 30}
    assert (await ok(pw, "anna", f"/boards/{b['id']}/einstellungen", {"archivTage": 30}))["geaendert"] == []
    for daten, meldung in [({"alterungGefahr": 366}, "Gefahr ab: ganze Zahl von 0 bis 365"),
                           ({"ladeschritt": 0}, "Karten je Ladeschritt: ganze Zahl von 1 bis 500"),
                           ({"archivTage": 100_001}, "Archiv ab: ganze Zahl von 1 bis 100.000")]:
        await abgelehnt(pw, "anna", f"/boards/{b['id']}/einstellungen", daten, 400, meldung)


async def test_module_bietet_diese_fassung_nicht_an(pw: Pinnwand, monkeypatch: pytest.MonkeyPatch):
    # diese Fassung bietet alle Module an; ein Modul, das sie (noch) nicht anbietet, stellt der Test nach
    ohne_vorlesen = tuple(m for m in MODULE_DA if m != "vorlesen")
    monkeypatch.setattr("app.anwendung.boards.MODULE_DA", ohne_vorlesen)
    b = await pw.board("anna", vorlage="v-leer")
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/module/vorlesen", {"an": True}, 400,
                    "Dieses Modul bietet diese Pinnwand nicht an")
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/module/gibt-es-nicht", {"an": False}, 400,
                    "Dieses Modul bietet diese Pinnwand nicht an")
    assert not (await board(pw))["module"]["vorlesen"]
    # bietet eine spätere Fassung ein Modul an, schaltet derselbe Weg es
    monkeypatch.setattr("app.anwendung.boards.MODULE_DA", MODULE_DA)
    a = await ok(pw, "anna", f"/boards/{b['id']}/module/vorlesen", {"an": True})
    assert a["meldung"] == "Vorlesen in Haushalt eingeschaltet" and (await board(pw))["module"]["vorlesen"]


async def test_als_vorlage_speichern(pw: Pinnwand):
    b = await mit_bert(pw)
    await ok(pw, "anna", f"/boards/{b['id']}/labels", {"name": "Dringend", "farbe": "koralle"})
    await ok(pw, "anna", f"/boards/{b['id']}/felder", {"name": "Raum", "art": "auswahl"})
    a = await ok(pw, "anna", f"/boards/{b['id']}/vorlage", {"name": "Wohnung"})
    assert a["meldung"] == ("Vorlage Wohnung gespeichert: 3 Spalten, 1 Feld, 1 Label; sie steht beim Anlegen unter den "
                            "eigenen Vorlagen")
    v = next(x for x in (await pw.stand("anna"))["vorlagen"] if x["name"] == "Wohnung")
    assert (v["eigen"], v["konto"], [s["name"] for s in v["spalten"]]) == (True, "1", ["Offen", "Dran", "Erledigt"])
    assert v["felder"] == [{"name": "Raum", "art": "auswahl", "optionen": [], "aufKarte": False}]
    assert "Wohnung" not in {x["name"] for x in (await pw.stand("bert"))["vorlagen"]}          # nur für anna
    neu = await pw.board("anna", "Zweitwohnung", "ZWEI", vorlage=v["id"])
    assert [l["name"] for l in neu["labels"]] == ["Dringend"] and neu["felder"][0]["name"] == "Raum"
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/vorlage", {"name": ""}, 400, "Eine Vorlage braucht einen Namen")
    r = await pw.post("bert", "/boards", {"vorlage": v["id"], "name": "Meins", "kuerzel": "MEIN"})
    assert r.status_code == 404


async def test_kuerzel_pruefen(pw: Pinnwand):
    await pw.board("anna")
    await pw.board("anna", "Werkstatt", "WERK")
    assert (await pw.get("anna", "/kuerzel/NEU")).json() == {
        "kuerzel": "NEU", "stand": "frei", "text": "Frei. Karten heißen NEU-1, NEU-2 und so weiter.", "frei": []}
    r = (await pw.get("anna", "/kuerzel/HAUS")).json()
    assert (r["stand"], r["text"], r["frei"]) == ("vergeben", "HAUS ist schon vergeben, an das Board Haushalt.",
                                                  ["HAUS2", "HAUS3", "HAUS4"])
    assert (await pw.get("anna", "/kuerzel/1X")).json()["stand"] == "form"
    # bert sieht Werkstatt nicht: vergeben, ohne den Namen
    await ok(pw, "anna", f"/boards/{(await board(pw))['id']}/mitglieder", {"kellerwolke": "bert"})
    await pw.anmelden("bert")
    r = (await pw.get("bert", "/kuerzel/WERK")).json()
    assert (r["stand"], r["text"]) == ("vergeben", "WERK ist schon vergeben, an ein Board, das du nicht siehst.")


# --- Spalten -----------------------------------------------------------------------------------------------------

async def test_spalten_anlegen_aendern_ordnen(pw: Pinnwand):
    b = await mit_bert(pw)
    a = await ok(pw, "anna", f"/boards/{b['id']}/spalten", {"name": "Warten", "farbe": "sand"})
    assert a["meldung"] == "Spalte Warten angelegt, am Ende"
    neu = await board(pw)
    warten = spalte(neu, "Warten")
    assert [s["name"] for s in neu["spalten"]] == ["Offen", "Dran", "Erledigt", "Warten"]
    a = await ok(pw, "anna", f"/boards/{b['id']}/spalten/{warten}/aendern",
                 {"name": "Wartet", "grenze": 3, "eingeklappt": True, "farbe": "honig"})
    assert a["meldung"] == "Spalte Wartet: heißt jetzt Wartet, neue Farbe, Grenze 3, anfangs eingeklappt"
    a = await ok(pw, "anna", f"/boards/{b['id']}/spalten/{warten}/aendern", {"grenze": None})
    assert a["meldung"] == "Spalte Wartet: ohne Grenze"
    s = next(x for x in (await board(pw))["spalten"] if x["id"] == warten)
    assert (s["farbe"], s.get("grenze"), s["eingeklappt"]) == ("honig", None, True)

    erledigt = spalte(neu, "Erledigt")
    pfad = f"/boards/{b['id']}/spalten"
    for sp, daten, meldung in [
        (warten, {"grenze": 0}, "Grenze: ganze Zahl von 1 bis 999, leer heißt keine"),
        (warten, {"name": " "}, "Eine Spalte braucht einen Namen"),
        (warten, {"zeitfenster": "woche"}, "Ein Zeitfenster hat nur die Erledigt-Spalte"),
        (erledigt, {"grenze": 5}, "Die Erledigt-Spalte hat keine Grenze"),
    ]:
        await abgelehnt(pw, "anna", f"{pfad}/{sp}/aendern", daten, 400, meldung)
    assert (await ok(pw, "anna", f"{pfad}/{erledigt}/aendern", {"zeitfenster": "woche"}))["meldung"] == "Spalte Erledigt: neues Zeitfenster"
    await abgelehnt(pw, "anna", f"{pfad}/s-fremd/aendern", {"name": "x"}, 404, "Diese Spalte gibt es in diesem Board nicht (mehr)")

    ids = [s["id"] for s in neu["spalten"]]
    a = await ok(pw, "anna", f"{pfad}/ordnen", {"ids": [ids[3], *ids[:3]]})
    assert a["meldung"] == "Spalten von Haushalt neu geordnet"
    assert [s["name"] for s in (await board(pw))["spalten"]] == ["Wartet", "Offen", "Dran", "Erledigt"]
    await abgelehnt(pw, "anna", f"{pfad}/ordnen", {"ids": ids[:3]}, 400,
                    "Die Reihenfolge muss jede Spalte des Boards genau einmal nennen")
    await abgelehnt(pw, "bert", f"{pfad}/ordnen", {"ids": ids}, 403, "Dir fehlt im Board Haushalt das Recht Board verwalten")
    await abgelehnt(pw, "bert", pfad, {"name": "Meins", "farbe": "rose"}, 403, "Dir fehlt im Board Haushalt das Recht Board verwalten")


async def test_zur_erledigt_spalte(pw: Pinnwand):
    b = await pw.board("anna")
    alt, dran = spalte(b, "Erledigt"), spalte(b, "Dran")
    fertig = await pw.karte("anna", b, "Fenster", spalte=alt)
    laeuft = await pw.karte("anna", b, "Keller", spalte=dran)
    assert fertig["abgeschlossen"] == "2026-10-27"
    pw.zeiger.zeit = pw.zeiger.zeit.replace(day=28, hour=9)
    a = await ok(pw, "anna", f"/boards/{b['id']}/spalten/{dran}/erledigt")
    assert a["meldung"] == "Dran ist jetzt die Erledigt-Spalte; Karten in Erledigt sind wieder offen"
    neu = await board(pw)
    assert [(s["name"], s["erledigt"], s.get("zeitfenster")) for s in neu["spalten"]] == [
        ("Offen", False, None), ("Dran", True, "heute"), ("Erledigt", False, "heute")]
    wieder = await karte(pw, "anna", fertig["schluessel"])
    assert "abgeschlossen" not in wieder and wieder["bewegtAm"] == "2026-10-28T09:00:00"
    assert (await karte(pw, "anna", laeuft["schluessel"]))["abgeschlossen"] == "2026-10-28"
    # schon die Erledigt-Spalte: nichts geschieht; Rückgängig stellt alles her
    assert (await ok(pw, "anna", f"/boards/{b['id']}/spalten/{dran}/erledigt"))["geaendert"] == []
    await ok(pw, "anna", f"/rueckgaengig/{a['rueckgaengig']}")
    assert (await karte(pw, "anna", fertig["schluessel"]))["abgeschlossen"] == "2026-10-27"
    assert "abgeschlossen" not in await karte(pw, "anna", laeuft["schluessel"])


# --- Labels ------------------------------------------------------------------------------------------------------

async def test_labels(pw: Pinnwand):
    b = await pw.board("anna")
    pfad = f"/boards/{b['id']}/labels"
    assert (await ok(pw, "anna", pfad, {"name": "Garten", "farbe": "minze"}))["meldung"] == "Label Garten angelegt"
    await abgelehnt(pw, "anna", pfad, {"name": " garten ", "farbe": "rose"}, 409, "Das Label Garten gibt es schon")
    await abgelehnt(pw, "anna", pfad, {"name": "", "farbe": "rose"}, 400, "Ein Label braucht einen Namen")
    await ok(pw, "anna", pfad, {"name": "Keller", "farbe": "stahl"})
    garten, keller = (l["id"] for l in (await board(pw))["labels"])

    a = await ok(pw, "anna", f"{pfad}/{garten}/aendern", {"name": "Draußen"})
    assert a["meldung"] == "Label Garten heißt jetzt Draußen, auf allen Karten"
    assert (await ok(pw, "anna", f"{pfad}/{garten}/aendern", {"farbe": "honig"}))["meldung"] == "Farbe des Labels Draußen geändert"
    assert (await ok(pw, "anna", f"{pfad}/{garten}/aendern", {"farbe": "honig"}))["geaendert"] == []
    await abgelehnt(pw, "anna", f"{pfad}/{garten}/aendern", {"name": "KELLER"}, 409, "Das Label Keller gibt es schon")

    k1 = await pw.karte("anna", b, "Hecke")
    k2 = await pw.karte("anna", b, "Beet", spalte=spalte(b, "Erledigt"))
    for k in (k1, k2):
        await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"labels": [garten, keller]}})
    a = await ok(pw, "anna", f"{pfad}/{garten}/loeschen")
    assert a["meldung"] == "Label Draußen gelöscht, an 2 Karten entfernt"
    assert [l["name"] for l in (await board(pw))["labels"]] == ["Keller"]
    assert (await karte(pw, "anna", k1["schluessel"]))["labels"] == [keller]
    assert (await karte(pw, "anna", k2["schluessel"]))["labels"] == [keller]
    await ok(pw, "anna", f"/rueckgaengig/{a['rueckgaengig']}")
    assert (await karte(pw, "anna", k1["schluessel"]))["labels"] == [garten, keller]
    await abgelehnt(pw, "anna", f"{pfad}/l-fremd/loeschen", None, 404, "Dieses Label gibt es in diesem Board nicht (mehr)")


# --- Eigene Felder -----------------------------------------------------------------------------------------------

async def test_felder(pw: Pinnwand):
    b = await pw.board("anna")
    pfad = f"/boards/{b['id']}/felder"
    assert (await ok(pw, "anna", pfad, {"name": "Raum", "art": "auswahl"}))["meldung"] == "Feld Raum angelegt"
    await ok(pw, "anna", pfad, {"name": "Kosten", "art": "zahl"})
    raum, kosten = (f["id"] for f in (await board(pw))["felder"])
    assert (await board(pw))["felder"][0]["optionen"] == []

    assert (await ok(pw, "anna", f"{pfad}/{raum}/option", {"option": "Küche"}))["meldung"] == "Option Küche in Raum hinzugefügt"
    await ok(pw, "anna", f"{pfad}/{raum}/option", {"option": "Bad"})
    await abgelehnt(pw, "anna", f"{pfad}/{raum}/option", {"option": "küche"}, 409, "Die Option Küche gibt es schon")
    await abgelehnt(pw, "anna", f"{pfad}/{kosten}/option", {"option": "x"}, 400, "Optionen hat nur ein Feld der Art Auswahl")

    a = await ok(pw, "anna", f"{pfad}/{kosten}/aendern", {"name": "Preis", "aufKarte": True, "art": "text"})
    assert a["meldung"] == "Feld Preis: heißt jetzt Preis, neue Art, auf der Karte"
    k1 = await pw.karte("anna", b, "Fliesen")
    k2 = await pw.karte("anna", b, "Spiegel")
    await ok(pw, "anna", f"/karten/{k1['id']}/bearbeiten", {"felder": {"felder": {raum: "Küche", kosten: "40 Euro"}}})
    await ok(pw, "anna", f"/karten/{k2['id']}/bearbeiten", {"felder": {"felder": {raum: "Bad"}}})
    await abgelehnt(pw, "anna", f"{pfad}/{raum}/aendern", {"art": "text"}, 400, "Die Art von Raum bleibt fest, solange Karten Werte tragen")

    # eine entfernte Option fällt an den Karten weg, die sie tragen
    a = await ok(pw, "anna", f"{pfad}/{raum}/option", {"option": "Küche", "dazu": False})
    assert a["meldung"] == "Option Küche aus Raum entfernt, an 1 Karte geleert"
    assert (await karte(pw, "anna", k1["schluessel"]))["felder"] == {kosten: "40 Euro"}
    assert (await board(pw))["felder"][0]["optionen"] == ["Bad"]

    assert (await ok(pw, "anna", f"{pfad}/ordnen", {"ids": [kosten, raum]}))["meldung"] == "Felder neu geordnet"
    assert [f["name"] for f in (await board(pw))["felder"]] == ["Preis", "Raum"]
    a = await ok(pw, "anna", f"{pfad}/{raum}/loeschen")
    assert a["meldung"] == "Feld Raum gelöscht, Werte an 1 Karte entfernt"
    assert (await karte(pw, "anna", k2["schluessel"]))["felder"] == {}
    await abgelehnt(pw, "anna", pfad, {"name": " ", "art": "text"}, 400, "Ein Feld braucht einen Namen")
    assert (await pw.post("anna", pfad, {"name": "Etwas", "art": "farbe"})).status_code == 422


# --- Rollen und Rechte -------------------------------------------------------------------------------------------

async def test_rollen_und_rechte(pw: Pinnwand, monkeypatch: pytest.MonkeyPatch):
    b = await mit_bert(pw, "leser")
    pfad = f"/boards/{b['id']}/rollen"
    a = await ok(pw, "anna", pfad, {"name": "Helfer", "kopieVon": "mitglied"})
    assert a["meldung"] == "Rolle Helfer angelegt, mit den Rechten von Mitglied"
    helfer = next(r for r in (await board(pw))["rollen"] if r["name"] == "Helfer")
    assert "karten.verschieben" in helfer["rechte"] and not helfer.get("vorgabe")
    await abgelehnt(pw, "anna", pfad, {"name": "leser", "kopieVon": "mitglied"}, 409, "Die Rolle Leser gibt es schon")
    await abgelehnt(pw, "anna", pfad, {"name": "Gast", "kopieVon": "r-fremd"}, 404, "Diese Rolle gibt es in diesem Board nicht (mehr)")

    assert (await ok(pw, "anna", f"{pfad}/leser/umbenennen", {"name": "Zuschauer"}))["meldung"] == "Rolle Leser heißt jetzt Zuschauer"
    a = await ok(pw, "anna", f"{pfad}/leser/recht", {"recht": "karten.verschieben", "an": True})
    assert a["meldung"] == "Zuschauer: Recht erteilt, gilt sofort für 1 Person"
    k = await pw.karte("anna", b, "Fenster")
    assert (await pw.post("bert", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Dran")})).status_code == 200

    # ein Recht eines Moduls, das diese Fassung nicht anbietet (hier: Berichte weggenommen)
    monkeypatch.setattr("app.anwendung.mitglieder.MODULE_DA", ("zeiterfassung", "arbeitszeit", "serien"))
    for rolle, daten, meldung in [
        ("besitzer", {"recht": "board.verwalten", "an": False}, "Besitzer behalten Board verwalten und Mitglieder verwalten"),
        ("leser", {"recht": "gibt.es.nicht", "an": True}, "Dieses Recht gibt es nicht"),
        ("leser", {"recht": "berichte.erstellen", "an": True}, "Dieses Recht gehört zu einem Modul, das diese Pinnwand nicht anbietet"),
    ]:
        await abgelehnt(pw, "anna", f"{pfad}/{rolle}/recht", daten, 400, meldung)
    await abgelehnt(pw, "bert", f"{pfad}/leser/recht", {"recht": "karten.anlegen", "an": True}, 403,
                    "Dir fehlt im Board Haushalt das Recht Mitglieder und Rollen verwalten")

    # löschen: Start-Rollen bleiben, wer die Rolle hat, braucht einen Ersatz (nicht Besitzer)
    await abgelehnt(pw, "anna", f"{pfad}/leser/loeschen", {}, 400, "Besitzer, Mitglied und Leser bleiben; umbenennen geht")
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/rolle", {"kellerwolke": "bert", "rolle": helfer["id"]})
    await abgelehnt(pw, "anna", f"{pfad}/{helfer['id']}/loeschen", {}, 400, "Wähle die Rolle für die Personen, die sie haben")
    await abgelehnt(pw, "anna", f"{pfad}/{helfer['id']}/loeschen", {"ersatz": "besitzer"}, 400, "Als Ersatz geht jede Rolle außer Besitzer")
    a = await ok(pw, "anna", f"{pfad}/{helfer['id']}/loeschen", {"ersatz": "leser"})
    assert a["meldung"] == "Rolle Helfer gelöscht; 1 Person hat jetzt Zuschauer"
    neu = await board(pw)
    assert [r["id"] for r in neu["rollen"]] == ["besitzer", "mitglied", "leser"]
    assert next(m for m in neu["mitglieder"] if m["kellerwolke"] == "bert")["rolle"] == "leser"


# --- Mitglieder --------------------------------------------------------------------------------------------------

async def test_rolle_setzen_und_einziger_besitzer(pw: Pinnwand):
    b = await mit_bert(pw)
    pfad = f"/boards/{b['id']}/mitglieder/rolle"
    await abgelehnt(pw, "anna", pfad, {"kellerwolke": "anna", "rolle": "mitglied"}, 400,
                    "Ein Board hat immer einen Besitzer: erst den Besitz übertragen")
    assert (await ok(pw, "anna", pfad, {"kellerwolke": "bert", "rolle": "besitzer"}))["meldung"] == "bert ist jetzt Besitzer"
    # zwei Besitzer: jetzt darf anna ihre Rolle abgeben
    assert (await ok(pw, "anna", pfad, {"kellerwolke": "anna", "rolle": "leser"}))["meldung"] == "anna ist jetzt Leser"
    await abgelehnt(pw, "bert", pfad, {"kellerwolke": "cora", "rolle": "leser"}, 404, "cora ist nicht im Board Haushalt")
    await abgelehnt(pw, "anna", pfad, {"kellerwolke": "bert", "rolle": "leser"}, 403,
                    "Dir fehlt im Board Haushalt das Recht Mitglieder und Rollen verwalten")


async def test_wartende_einladung_und_entfernen(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}, {"kellerwolke": "cora"}])
    wartend = [m for m in (await board(pw))["mitglieder"] if not m["konto"]]
    assert [m["kellerwolke"] for m in wartend] == ["bert", "cora"]                 # warten auf die erste Anmeldung
    a = await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "cora"})
    assert a["meldung"] == "Die Einladung an cora ist zurückgenommen"

    await pw.anmelden("bert")
    await pw.stand("bert")
    await ok(pw, "bert", "/ordner", {"name": "Privat"})
    ordner = (await pw.stand("bert"))["ordner"][0]
    await ok(pw, "bert", f"/boards/{b['id']}/ordner", {"ordner": ordner["id"]})
    offen = await pw.karte("anna", b, "Fenster")
    fertig = await pw.karte("anna", b, "Keller", spalte=spalte(b, "Erledigt"))
    for k in (offen, fertig):
        await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"zustaendig": ["1", "2"]}})

    await abgelehnt(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "anna"}, 400,
                    "Der einzige Besitzer bleibt, bis er den Besitz überträgt")
    hub = pw.app.state.dienste.ereignisse
    with hub.abo("2") as bert:
        a = await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"})
        teil = await asyncio.wait_for(anext(bert), 1)
    assert a["meldung"] == "bert aus Haushalt entfernt; Zuständigkeit an 1 Karte frei"
    assert {g.tabelle for g in teil.geaendert} == {"boards", "karten", "ordner"}   # bert erfährt es und sein Ordner wird leer
    k = await karte(pw, "anna", offen["schluessel"])
    assert k["zustaendig"] == ["1"] and k["verlauf"][-1]["text"] == "hat bert als zuständig entfernt"
    assert (await karte(pw, "anna", fertig["schluessel"]))["zustaendig"] == ["1", "2"]    # erledigte bleiben, wie sie waren
    s = await pw.stand("bert")
    assert s["boards"] == [] and s["ordner"][0]["boards"] == []


async def test_besitz_uebertragen(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}, {"kellerwolke": "cora"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    pfad = f"/boards/{b['id']}/besitz"
    await abgelehnt(pw, "anna", pfad, {"an": "cora", "ichWerde": "mitglied"}, 400,
                    "cora hat sich noch nie angemeldet; den Besitz übernimmt erst, wer schon da war")
    await abgelehnt(pw, "anna", pfad, {"an": "anna", "ichWerde": "mitglied"}, 400, "Wähle ein anderes Mitglied als dich")
    await abgelehnt(pw, "anna", pfad, {"an": "bert", "ichWerde": "besitzer"}, 400, "Wähle für dich eine Rolle außer Besitzer")
    a = await ok(pw, "anna", pfad, {"an": "bert", "ichWerde": "mitglied"})
    assert a["meldung"] == "bert besitzt jetzt Haushalt; du bist Mitglied"
    rollen = {m["kellerwolke"]: m["rolle"] for m in (await board(pw))["mitglieder"]}
    assert rollen == {"anna": "mitglied", "bert": "besitzer", "cora": "mitglied"}
    await abgelehnt(pw, "anna", f"/boards/{b['id']}/umbenennen", {"name": "Meins"}, 403,
                    "Dir fehlt im Board Haushalt das Recht Board verwalten")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"}, 400,
                    "Der einzige Besitzer bleibt, bis er den Besitz überträgt")


# --- Ordner ------------------------------------------------------------------------------------------------------

async def test_ordner(pw: Pinnwand):
    haus = await pw.board("anna")
    werk = await pw.board("anna", "Werkstatt", "WERK")
    assert (await ok(pw, "anna", "/ordner", {"name": " Privat "}))["meldung"] == "Ordner Privat angelegt"
    await ok(pw, "anna", "/ordner", {"name": "Firma"})
    privat, firma = (await pw.stand("anna"))["ordner"]
    assert (privat["name"], privat["reihe"], firma["reihe"]) == ("Privat", 1, 2)
    await abgelehnt(pw, "anna", "/ordner", {"name": ""}, 400, "Ein Ordner braucht einen Namen")

    assert (await ok(pw, "anna", f"/boards/{haus['id']}/ordner", {"ordner": privat["id"]}))["meldung"] == "Haushalt liegt jetzt im Ordner Privat"
    await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": privat["id"]})
    a = await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": firma["id"]})
    assert a["meldung"] == "Werkstatt liegt jetzt im Ordner Firma"
    assert [(o["name"], o["boards"]) for o in (await pw.stand("anna"))["ordner"]] == [("Privat", [haus["id"]]), ("Firma", [werk["id"]])]
    assert (await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": firma["id"]}))["geaendert"] == []
    # an eine Stelle (Ziehen in der Seitenleiste): hinein vor ein anderes Board, im selben Ordner umsortieren, zurück
    await ok(pw, "anna", f"/boards/{haus['id']}/ordner", {"ordner": firma["id"], "stelle": 0})
    assert [o["boards"] for o in (await pw.stand("anna"))["ordner"]] == [[], [haus["id"], werk["id"]]]
    assert (await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": firma["id"], "stelle": 0}))["meldung"] == "Werkstatt umsortiert"
    assert [o["boards"] for o in (await pw.stand("anna"))["ordner"]] == [[], [werk["id"], haus["id"]]]
    assert (await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": firma["id"], "stelle": 0}))["geaendert"] == []
    await ok(pw, "anna", f"/boards/{haus['id']}/ordner", {"ordner": privat["id"]})

    assert (await ok(pw, "anna", "/ordner/ordnen", {"ids": [firma["id"], privat["id"]]}))["meldung"] == "Ordner neu geordnet"
    assert [o["name"] for o in (await pw.stand("anna"))["ordner"]] == ["Firma", "Privat"]
    await abgelehnt(pw, "anna", "/ordner/ordnen", {"ids": [firma["id"]]}, 400,
                    "Die Reihenfolge muss jeden deiner Ordner genau einmal nennen")
    assert (await ok(pw, "anna", f"/ordner/{firma['id']}/umbenennen", {"name": "Arbeit"}))["meldung"] == "Ordner Firma heißt jetzt Arbeit"

    a = await ok(pw, "anna", f"/ordner/{privat['id']}/loeschen")
    assert a["meldung"] == "Ordner Privat gelöscht; 1 Board steht jetzt ohne Ordner"
    assert [o["name"] for o in (await pw.stand("anna"))["ordner"]] == ["Arbeit"]
    assert (await ok(pw, "anna", f"/boards/{werk['id']}/ordner", {"ordner": None}))["meldung"] == "Werkstatt liegt jetzt ohne Ordner"

    # Ordner sind persönlich: fremde gibt es nicht, fremde Boards lassen sich nicht einsortieren
    await pw.post("anna", f"/boards/{haus['id']}/mitglieder", {"kellerwolke": "bert"})
    await pw.anmelden("bert")
    assert (await pw.stand("bert"))["ordner"] == []
    await abgelehnt(pw, "bert", f"/ordner/{firma['id']}/umbenennen", {"name": "Meins"}, 404, "Diesen Ordner gibt es nicht")
    await ok(pw, "bert", "/ordner", {"name": "Bert"})
    eigen = (await pw.stand("bert"))["ordner"][0]
    await abgelehnt(pw, "bert", f"/boards/{werk['id']}/ordner", {"ordner": eigen["id"]}, 403, "Dieses Board siehst du nicht")
    await ok(pw, "bert", f"/boards/{haus['id']}/ordner", {"ordner": eigen["id"]})       # Rechte im Board braucht es nicht


# --- Eigenes Kürzel ----------------------------------------------------------------------------------------------

async def test_eigenes_kuerzel(pw: Pinnwand):
    a = await ok(pw, "anna", "/ich/kuerzel", {"kuerzel": " ab "})
    assert a["meldung"] == "Dein Kürzel ist jetzt AB" and a["rueckgaengig"]
    assert "1" not in pw.app.state.dienste.konten._bekannt                           # die Anmeldung liest neu
    assert (await pw.stand("anna"))["konten"][0]["kuerzel"] == "AB"
    assert pw.app.state.dienste.konten._bekannt["1"].kuerzel == "AB"
    assert (await ok(pw, "anna", "/ich/kuerzel", {"kuerzel": "AB"}))["geaendert"] == []
    assert (await ok(pw, "anna", "/ich/kuerzel", {"kuerzel": "Öz"}))["meldung"] == "Dein Kürzel ist jetzt ÖZ"
    for falsch in ("", "ABCD", "A1"):
        await abgelehnt(pw, "anna", "/ich/kuerzel", {"kuerzel": falsch}, 400, "Ein Kürzel hat ein bis drei Buchstaben")
