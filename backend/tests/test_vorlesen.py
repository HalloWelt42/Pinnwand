"""Stufe 4, Vorlesen über die Vertonung (Baustein appkern.vorlesen, HELF-73): Modul und Mitgliedschaft geprüft, der
Text geht im Auftrag der Person an die Vertonung (lange Texte in Teilen, Sätze durchgezählt), die Zeilen kommen an den
Vorleser; Fehler vor dem ersten Satz als Ablehnung, danach als Zeile. Die Vorlesestimme wählt die Pinnwand aus dem, was
die Vertonung ihr anbietet."""

from __future__ import annotations

import json

import pytest

from conftest import Pinnwand
from nachgestellt import VORLESEN, VORLESEN_EINRICHTUNG
from test_verwaltung import abgelehnt, mit_bert, ok


@pytest.fixture(autouse=True)
def leere_vorleseapp():
    VORLESEN.leeren()
    yield
    VORLESEN.leeren()


async def einstellen(pw: Pinnwand, **werte) -> None:
    r = await pw.c.patch("/api/v1/einstellungen", headers=pw.kopf["anna"], json={"werte": werte})
    assert r.status_code == 200, r.text


async def mit_vorlesen(pw: Pinnwand) -> dict:
    b = await mit_bert(pw)                                       # Vorlesen bringt die Vorlage Aufgaben mit
    await einstellen(pw, **VORLESEN_EINRICHTUNG)
    return b


async def lesen(pw: Pinnwand, wer: str, daten: dict) -> list[dict]:
    r = await pw.post(wer, "/vorlesen", daten)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/x-ndjson")
    return [json.loads(z) for z in r.text.splitlines() if z]


async def test_ohne_modul_und_adresse(pw: Pinnwand):
    b = await mit_bert(pw)
    assert b["module"]["vorlesen"]                                  # die Vorlage Aufgaben bringt es mit
    await ok(pw, "anna", f"/boards/{b['id']}/module/vorlesen", {"an": False})
    assert (await pw.stand("anna"))["vorlesenAdresse"] == ""
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo.", "board": b["id"]}, 403, "Vorlesen ist im Board Haushalt aus")
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo."}, 403, "Vorlesen ist in keinem deiner Boards an")
    await ok(pw, "anna", f"/boards/{b['id']}/module/vorlesen", {"an": True})
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo.", "board": b["id"]}, 503,
                    "Vorlesen ist nicht eingerichtet (Einstellungen, Verbindungen)")
    await einstellen(pw, **VORLESEN_EINRICHTUNG)
    assert (await pw.stand("anna"))["vorlesenAdresse"] == "https://vt.test"
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "   ", "board": b["id"]}, 400, "Es gibt nichts vorzulesen")
    assert VORLESEN.anfragen == []


async def test_saetze_im_auftrag_der_person(pw: Pinnwand):
    b = await mit_vorlesen(pw)
    zeilen = await lesen(pw, "bert", {"text": "Fenster putzen. Leiter holen!", "board": b["id"]})
    assert [(z["art"], z.get("nr"), z.get("text")) for z in zeilen] == [
        ("satz", 0, "Fenster putzen."), ("satz", 1, "Leiter holen!"), ("ende", None, None)]
    assert zeilen[-1] == {"art": "ende", "saetze": 2, "dauer_ms": 2000} and zeilen[0]["ton"]
    assert VORLESEN.koerper() == {"text": "Fenster putzen. Leiter holen!", "ausschreiben": True}   # ohne Wahl: ab Werk
    ruf = VORLESEN.anfragen[-1]
    assert ruf.url.path == "/api/v1/sprechen/strom" and ruf.headers["x-kellerwolke-sitzung"] == "t-bert"
    assert ruf.headers["authorization"].startswith("Bearer kw_app_")
    await lesen(pw, "anna", {"text": "Kurz."})                      # ohne Board: Heute und Berichte
    # Adresse und Vorlesestimme aus dem Baustein, unter Verbindungen; zur Wahl steht, was die Vertonung der Pinnwand gibt
    felder = {f["name"]: f for f in (await pw.get("anna", "/einstellungen")).json()}
    assert "vorlesen_tempo" not in felder and "vorlesen_adresse" not in felder
    assert felder["vertonung_adresse"]["gruppe"] == "Verbindungen" and felder["vertonung_adresse"]["angebot"]
    angebot = (await pw.get("anna", "/einstellungen/angebot/vorlesen_stimme")).json()
    assert [o["wert"] for o in angebot["optionen"]] == ["", "katalog:stimme_a"]      # private gibt sie nicht frei
    await einstellen(pw, vorlesen_stimme="katalog:stimme_a")
    await lesen(pw, "anna", {"text": "Mit Stimme."})
    assert VORLESEN.koerper()["stimme"] == {"art": "katalog", "name": "stimme_a"}
    verbindungen = {v["name"]: v for v in (await pw.get("anna", "/verbindungen")).json()}
    assert verbindungen["Vertonung"]["ok"]


async def test_langer_text_in_teilen(pw: Pinnwand):
    b = await mit_vorlesen(pw)
    satz = "Das ist ein Satz mit genau so vielen Wörtern, dass er lang genug ist. "
    zeilen = await lesen(pw, "anna", {"text": satz * 130, "board": b["id"]})
    gesprochen = [a for a in VORLESEN.anfragen if a.url.path == "/api/v1/sprechen/strom"]
    assert len(gesprochen) == 2 and all(len(json.loads(a.content)["text"]) <= 7500 for a in gesprochen)
    assert [z["nr"] for z in zeilen if z["art"] == "satz"] == list(range(130))
    assert zeilen[-1] == {"art": "ende", "saetze": 130, "dauer_ms": 130_000}
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "x" * 40_001, "board": b["id"]}, 400, "Der Text ist länger als 40000 Zeichen")


async def test_fehler_vor_und_nach_dem_ersten_satz(pw: Pinnwand):
    b = await mit_vorlesen(pw)
    # cora ist Mitglied, darf die Vertonung aber nicht nutzen: noch vor dem ersten Satz, also eine Ablehnung
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "cora", "rolle": "mitglied"})
    assert (await pw.anmelden("cora")).status_code == 200
    await abgelehnt(pw, "cora", "/vorlesen", {"text": "Hallo.", "board": b["id"]}, 403,
                    "Die Vertonung lässt das nicht zu: Dieses Konto darf die Vertonung nicht nutzen")
    # bricht sie mittendrin ab, steht das als letzte Zeile da
    VORLESEN.fehler_nach = 1
    zeilen = await lesen(pw, "anna", {"text": "Eins. Zwei. Drei.", "board": b["id"]})
    assert [z["art"] for z in zeilen] == ["satz", "fehler"] and zeilen[-1]["meldung"] == "Der Sprechdienst ist weg"
