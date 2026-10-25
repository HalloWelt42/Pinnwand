"""Stufe 4, Berichte: Inhalt je Art (Stundennachweis, Zeiten je Karte, Erledigtes) mit denselben Rechten wie Stand und
Team, die Datei als PDF, Tabelle oder Markdown in der Ablage der Pinnwand, Herunterladen nur für die eigene Person."""

from __future__ import annotations

import pytest

from conftest import Pinnwand
from nachgestellt import ABLAGE
from test_verwaltung import abgelehnt, mit_bert, ok, spalte

KONTO = {"ab": "2026-01-01", "wochenstunden": 40, "tage": [1, 2, 3, 4, 5], "bundesland": "Nordrhein-Westfalen",
         "urlaubsanspruch": 30}


@pytest.fixture(autouse=True)
def leere_ablage():
    ABLAGE.leeren()
    yield
    ABLAGE.leeren()


async def mit_zeiten(pw: Pinnwand) -> tuple[dict, dict]:
    """Haushalt mit Berichten und Arbeitszeit, anna und bert mit Zeitkonto und Zeit auf einer Karte; anna hat Urlaub."""
    b = await mit_bert(pw)
    for m in ("berichte", "arbeitszeit"):
        await ok(pw, "anna", f"/boards/{b['id']}/module/{m}", {"an": True})
    for wer in ("anna", "bert"):
        await ok(pw, wer, "/zeitkonten", KONTO)
    k = await pw.karte("anna", b, "Fenster putzen")
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"schaetzungMin": 120}})
    await ok(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-26", "sekunden": 6 * 3600})
    await ok(pw, "bert", "/zeiten", {"karte": k["id"], "datum": "2026-10-26", "sekunden": 1800})
    await ok(pw, "anna", "/abwesenheiten", {"von": "2026-10-27", "bis": "2026-10-27", "art": "urlaub", "anteil": 0.5})
    return b, k


async def vorschau(pw: Pinnwand, wer: str, **auswahl) -> dict:
    r = await pw.post(wer, "/berichte/vorschau", auswahl)
    assert r.status_code == 200, r.text
    return r.json()


async def test_stundennachweis(pw: Pinnwand):
    await mit_zeiten(pw)
    v = await vorschau(pw, "anna", art="stundennachweis", von="2026-10-26", bis="2026-10-27", personen=["1", "2"])
    assert (v["titel"], v["zeitraum"]) == ("Stundennachweis je Person", "Mo 26.10. bis Di 27.10.2026")
    anna, bert = v["abschnitte"]
    assert anna["zeilen"] == [["Mo 26.10.", "8:00", "6:00", "-2:00", "HAUS-1", ""],
                              ["Di 27.10.", "4:00", "0:00", "-4:00", "", "Halber Tag Urlaub"]]
    assert anna["summe"] == ["Summe", "12:00", "6:00", "-6:00", "", ""]
    assert bert["titel"] == "bert" and bert["zeilen"][0][:5] == ["Mo 26.10.", "8:00", "0:30", "-7:30", "HAUS-1"]

    # ohne "Abwesenheiten sehen" geht der Nachweis nur für dich
    b = (await pw.stand("anna"))["boards"][0]
    await ok(pw, "anna", f"/boards/{b['id']}/rollen/mitglied/recht", {"recht": "abwesenheit.sehen", "an": False})
    await abgelehnt(pw, "bert", "/berichte/vorschau", {"art": "stundennachweis", "von": "2026-10-26", "bis": "2026-10-27",
                                                       "personen": ["1"]}, 403,
                    "Ein Stundennachweis geht für dich und, wessen Abwesenheiten du siehst, mit Zeitkonto")


async def test_zeiten_je_karte_und_erledigt(pw: Pinnwand):
    b, k = await mit_zeiten(pw)
    v = await vorschau(pw, "anna", art="board", von="2026-10-26", bis="2026-10-30", boards=[b["id"]])
    [abschnitt] = v["abschnitte"]
    assert abschnitt["zeilen"] == [["HAUS-1", "Fenster putzen", "AN, BE", "6:30", "2:00"]]
    # bert ohne "Zeiten anderer sehen" sieht nur seine eigene halbe Stunde
    await ok(pw, "anna", f"/boards/{b['id']}/rollen/mitglied/recht", {"recht": "zeit.andere.sehen", "an": False})
    v = await vorschau(pw, "bert", art="board", von="2026-10-26", bis="2026-10-30", boards=[b["id"]])
    assert v["abschnitte"][0]["zeilen"] == [["HAUS-1", "Fenster putzen", "BE", "0:30", "2:00"]]

    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Erledigt")})
    v = await vorschau(pw, "anna", art="erledigt", von="2026-10-27", bis="2026-10-27", boards=[b["id"]])
    assert v["abschnitte"][0]["zeilen"] == [["HAUS-1", "Fenster putzen", "Di 27.10.", "AN", "6:30"]]
    assert v["abschnitte"][0]["summe"] == ["", "1 Karte", "", "", "6:30"]


async def test_ohne_modul_und_falsche_auswahl(pw: Pinnwand):
    b = await mit_bert(pw)
    await abgelehnt(pw, "anna", "/berichte/vorschau", {"art": "board", "von": "2026-10-26", "bis": "2026-10-30", "boards": [b["id"]]},
                    403, "Berichte sind in keinem deiner Boards eingeschaltet, oder dir fehlt das Recht dazu")
    await ok(pw, "anna", f"/boards/{b['id']}/module/berichte", {"an": True})
    await abgelehnt(pw, "anna", "/berichte/vorschau", {"art": "board", "von": "2026-10-30", "bis": "2026-10-26", "boards": [b["id"]]},
                    400, "Von und bis sind Tage, bis nicht vor von")


@pytest.mark.parametrize("format, endung, anfang", [("pdf", "pdf", b"%PDF"), ("tabelle", "csv", b"\xef\xbb\xbfZeiten je Board"),
                                                    ("markdown", "md", b"# Zeiten je Board")])
async def test_datei_in_der_ablage(pw: Pinnwand, format: str, endung: str, anfang: bytes):
    b, _ = await mit_zeiten(pw)
    a = await ok(pw, "anna", "/berichte", {"art": "board", "von": "2026-10-26", "bis": "2026-10-30", "boards": [b["id"]],
                                          "format": format})
    name = f"Zeiten_HAUS_2026-10-26_2026-10-30.{endung}"
    assert a["meldung"] == f"Abgelegt in der Kellerwolke unter Apps/Pinnwand/Berichte/{name}" and a["rueckgaengig"] is None
    [bericht] = (await pw.stand("anna"))["berichte"]
    assert (bericht["datei"], bericht["titel"], bericht["format"]) == (name, "Zeiten je Karte: Haushalt", format)
    assert (await pw.stand("bert"))["berichte"] == []
    r = await pw.c.get(f"/api/v1/inhalt/berichte/{bericht['id']}", headers=pw.kopf["anna"])
    assert r.status_code == 200 and r.content.startswith(anfang)
    assert (await pw.c.get(f"/api/v1/inhalt/berichte/{bericht['id']}", headers=pw.kopf["bert"])).status_code == 404
