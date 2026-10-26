"""Stufe 4, Vorlesen: Modul und Mitgliedschaft geprüft, Stimme und Tempo aus den Einstellungen, lange Texte in Teilen
mit durchgezählten Sätzen, Fehler vor dem ersten Satz als Ablehnung, danach als Zeile; Stimmen nur aus Katalog und
freigegebenen privaten."""

from __future__ import annotations

import json

import pytest

from conftest import Pinnwand
from nachgestellt import VERTONUNG, VERTONUNG_EINRICHTUNG
from test_verwaltung import abgelehnt, mit_bert, ok


@pytest.fixture(autouse=True)
def leere_vertonung():
    VERTONUNG.leeren()
    yield
    VERTONUNG.leeren()


async def einstellen(pw: Pinnwand, **werte) -> None:
    r = await pw.c.patch("/api/v1/einstellungen", headers=pw.kopf["anna"], json={"werte": werte})
    assert r.status_code == 200, r.text


async def mit_vorlesen(pw: Pinnwand) -> dict:
    b = await mit_bert(pw)                                       # Vorlesen bringt die Vorlage Aufgaben mit
    await einstellen(pw, **VERTONUNG_EINRICHTUNG)
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
    assert (await pw.stand("anna"))["vertonungAdresse"] == ""
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo.", "board": b["id"]}, 403, "Vorlesen ist im Board Haushalt aus")
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo."}, 403, "Vorlesen ist in keinem deiner Boards an")
    await ok(pw, "anna", f"/boards/{b['id']}/module/vorlesen", {"an": True})
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "Hallo.", "board": b["id"]}, 503,
                    "Die Vertonung ist nicht eingerichtet (Einstellungen, Verbindungen)")
    await einstellen(pw, **VERTONUNG_EINRICHTUNG)
    assert (await pw.stand("anna"))["vertonungAdresse"] == "https://vt.test"
    await abgelehnt(pw, "anna", "/vorlesen", {"text": "   ", "board": b["id"]}, 400, "Es gibt nichts vorzulesen")
    assert VERTONUNG.anfragen == []


async def test_saetze_mit_stimme_und_tempo(pw: Pinnwand):
    b = await mit_vorlesen(pw)
    zeilen = await lesen(pw, "bert", {"text": "Fenster putzen. Leiter holen!", "board": b["id"]})
    assert [(z["art"], z.get("nr"), z.get("text")) for z in zeilen] == [
        ("satz", 0, "Fenster putzen."), ("satz", 1, "Leiter holen!"), ("ende", None, None)]
    assert zeilen[-1] == {"art": "ende", "saetze": 2, "dauer_ms": 2000} and zeilen[0]["ton"]
    koerper = VERTONUNG.koerper()
    assert koerper == {"text": "Fenster putzen. Leiter holen!", "tempo": 1.0, "sprache": "de", "ausschreiben": True}
    assert VERTONUNG.anfragen[-1].headers["x-kellerwolke-sitzung"] == "t-bert"

    await einstellen(pw, vorlesen_stimme="katalog:serena", vorlesen_tempo=1.2)
    await lesen(pw, "anna", {"text": "Kurz."})                      # ohne Board: Heute und Berichte
    assert VERTONUNG.koerper()["stimme"] == {"art": "katalog", "name": "serena"} and VERTONUNG.koerper()["tempo"] == 1.2

    # zur Wahl stehen Katalog und freigegebene private Stimmen; private gibt diese Vertonung nicht frei
    r = await pw.get("anna", "/einstellungen/angebot/vorlesen_stimme")
    assert [o["wert"] for o in r.json()["optionen"]] == ["", "katalog:serena"]


async def test_langer_text_in_teilen(pw: Pinnwand):
    b = await mit_vorlesen(pw)
    satz = "Das ist ein Satz mit genau so vielen Wörtern, dass er lang genug ist. "
    text = satz * 130                                           # gut 9000 Zeichen: zwei Teile für die Vertonung
    zeilen = await lesen(pw, "anna", {"text": text, "board": b["id"]})
    gesprochen = [z for z in VERTONUNG.anfragen if z.url.path == "/api/v1/sprechen/strom"]
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
    VERTONUNG.fehler_nach = 1
    zeilen = await lesen(pw, "anna", {"text": "Eins. Zwei. Drei.", "board": b["id"]})
    assert [z["art"] for z in zeilen] == ["satz", "fehler"] and zeilen[-1]["meldung"] == "Der Sprechdienst ist weg"
