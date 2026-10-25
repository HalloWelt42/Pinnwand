"""Stufe 4, KI an der Karte: Vorschläge über die Leitstelle mit fester Antwortform, gesäubert und gegen die Karte
geprüft, mit denselben Rechten wie das Übernehmen; nichts wird geschrieben, bis die Person übernimmt. Mehrere Karten
entstehen in einer Änderung mit einem Rückgängig."""

from __future__ import annotations

import json
from urllib.parse import unquote

import pytest

from conftest import Pinnwand
from nachgestellt import LEITSTELLE, LEITSTELLE_EINRICHTUNG
from test_verwaltung import abgelehnt, mit_bert, ok, spalte

HALB, UNTEN, OBEN = chr(0x2013), chr(0x201E), chr(0x201C)


@pytest.fixture(autouse=True)
def leere_leitstelle():
    LEITSTELLE.leeren()
    yield
    LEITSTELLE.leeren()


async def einstellen(pw: Pinnwand, **werte) -> None:
    r = await pw.c.patch("/api/v1/einstellungen", headers=pw.kopf["anna"], json={"werte": werte})
    assert r.status_code == 200, r.text


async def mit_ki(pw: Pinnwand, rolle: str = "mitglied") -> dict:
    """Haushalt mit KI an der Karte und bert in der Rolle; die Leitstelle ist eingerichtet."""
    b = await mit_bert(pw, rolle)
    await ok(pw, "anna", f"/boards/{b['id']}/module/ki", {"an": True})
    await einstellen(pw, **LEITSTELLE_EINRICHTUNG)
    return b


def antwort(**daten) -> str:
    return json.dumps(daten, ensure_ascii=False)


async def test_ohne_leitstelle_keine_vorschlaege(pw: Pinnwand):
    b = await mit_bert(pw)
    k = await pw.karte("anna", b, "Fenster putzen")
    assert (await pw.stand("anna"))["kiBereit"] is False
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/ki/zusammenfassung", None, 403, "KI an der Karte ist im Board Haushalt aus")
    await ok(pw, "anna", f"/boards/{b['id']}/module/ki", {"an": True})
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/ki/zusammenfassung", None, 503,
                    "Die Leitstelle ist nicht eingerichtet (Einstellungen, Verbindungen)")
    await einstellen(pw, **LEITSTELLE_EINRICHTUNG)
    assert (await pw.stand("anna"))["kiBereit"] is True
    # das Modell wählt man aus den Textmodellen der Leitstelle, leer gilt die Kette der App
    r = await pw.get("anna", "/einstellungen/angebot/ki_modell")
    assert r.status_code == 200, r.text
    assert [o["wert"] for o in r.json()["optionen"]] == ["", "gross"]
    assert LEITSTELLE.anfragen == [] or all(a.url.path == "/v1/models" for a in LEITSTELLE.anfragen)


async def test_zusammenfassung(pw: Pinnwand):
    b = await mit_ki(pw, "leser")
    k = await pw.karte("anna", b, "Fenster putzen", beschreibung="Alle Fenster im Erdgeschoss")
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"notizen": "Leiter fehlt noch", "faellig": "2026-10-30",
                                                                     "checkliste": [{"text": "Leiter holen", "erledigt": True}]}})
    await ok(pw, "bert", f"/karten/{k['id']}/kommentieren", {"text": "Ich bringe die Leiter am Donnerstag"})

    LEITSTELLE.antworten.append(antwort(text=f"Die Fenster im Erdgeschoss {HALB} bis {UNTEN}Fr 30.10.{OBEN} putzen."))
    r = await pw.post("bert", f"/karten/{k['id']}/ki/zusammenfassung")       # lesen genügt
    assert r.status_code == 200, r.text
    assert r.json() == {"text": 'Die Fenster im Erdgeschoss - bis "Fr 30.10." putzen.'}

    anfrage = LEITSTELLE.anfragen[-1]
    koerper = LEITSTELLE.koerper()
    assert [m["role"] for m in koerper["messages"]] == ["system", "user"] and "model" not in koerper
    karte = koerper["messages"][1]["content"]
    for teil in ("Karte HAUS-1: Fenster putzen", "Status: Offen", "Fällig: Fr 30.10.2026", "Beschreibung:\nAlle Fenster",
                 "Notizen:\nLeiter fehlt noch", "- [x] Leiter holen", "- bert am Di 27.10.2026: Ich bringe die Leiter"):
        assert teil in karte, teil
    assert koerper["response_format"]["json_schema"]["name"] == "zusammenfassung" and koerper["response_format"]["json_schema"]["strict"]
    assert anfrage.headers["x-leitstelle-prioritaet"] == "hoch"
    assert unquote(anfrage.headers["x-leitstelle-titel"]) == "Pinnwand: Zusammenfassung HAUS-1"
    # nichts geschrieben: die Karte ist wie vorher
    assert (await pw.get("anna", "/karten/HAUS-1")).json()["fassung"] == k["fassung"] + 2

    # ein gewähltes Modell geht mit
    await einstellen(pw, ki_modell="gross")
    LEITSTELLE.antworten.append(antwort(text="Kurz."))
    await ok(pw, "anna", f"/karten/{k['id']}/ki/zusammenfassung")
    assert LEITSTELLE.koerper()["model"] == "gross"

    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "cora"}])
    assert (await pw.anmelden("cora")).status_code == 200
    await abgelehnt(pw, "cora", f"/karten/{k['id']}/ki/zusammenfassung", None, 403, "Im Board Haushalt bist du nicht Mitglied")


async def test_checkliste_ohne_vorhandenes(pw: Pinnwand):
    b = await mit_ki(pw)
    k = await pw.karte("anna", b, "Fenster putzen")
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"checkliste": [{"text": "Leiter holen"}]}})
    LEITSTELLE.antworten.append(antwort(begruendung="Erst die Leiter, dann putzen.",
                                        punkte=["1. leiter holen", "- Fenster putzen", "fenster putzen", "", "[ ] Rahmen  wischen",
                                                f"Glas {HALB} innen"]))
    r = await ok(pw, "bert", f"/karten/{k['id']}/ki/checkliste")
    assert r == {"punkte": ["Fenster putzen", "Rahmen wischen", "Glas - innen"]}
    schema = LEITSTELLE.koerper()["response_format"]["json_schema"]["schema"]
    assert list(schema["properties"]) == ["begruendung", "punkte"] and schema["required"] == ["begruendung", "punkte"]


async def test_checkliste_braucht_das_recht(pw: Pinnwand):
    b = await mit_ki(pw, "leser")
    k = await pw.karte("anna", b, "Fenster putzen")
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/ki/checkliste", None, 403, "Dir fehlt im Board Haushalt das Recht Karten bearbeiten")
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/ki/labels", None, 403, "Dir fehlt im Board Haushalt das Recht Karten bearbeiten")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/ki/karten", {"text": "Fenster"}, 403, "Dir fehlt im Board Haushalt das Recht Karten anlegen")
    assert LEITSTELLE.anfragen == []                                        # gefragt wird erst nach der Prüfung


async def test_labels_ueber_kennungen(pw: Pinnwand):
    b = await mit_ki(pw)
    for name, farbe in (("Garten", "minze"), ("Dringend", "rose"), ("Einkauf", "honig")):
        await ok(pw, "anna", f"/boards/{b['id']}/labels", {"name": name, "farbe": farbe})
    labels = {lab["name"]: lab["id"] for lab in next(x for x in (await pw.stand("anna"))["boards"] if x["id"] == b["id"])["labels"]}
    k = await pw.karte("anna", b, "Rasen mähen")
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"labels": [labels["Garten"]]}})

    LEITSTELLE.antworten.append(antwort(begruendung="Eilt.", labels=["L1", "l1", "Einkauf", "L9"]))
    r = await ok(pw, "anna", f"/karten/{k['id']}/ki/labels")
    assert r == {"labels": [labels["Dringend"], labels["Einkauf"]]}
    koerper = LEITSTELLE.koerper()
    assert "Labels zur Wahl:\nL1: Dringend\nL2: Einkauf" in koerper["messages"][1]["content"]
    assert koerper["response_format"]["json_schema"]["schema"]["properties"]["labels"]["items"]["enum"] == ["L1", "L2"]

    # hat die Karte alle Labels, fragt niemand
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"labels": list(labels.values())}})
    gefragt = len(LEITSTELLE.anfragen)
    assert await ok(pw, "anna", f"/karten/{k['id']}/ki/labels") == {"labels": []}
    assert len(LEITSTELLE.anfragen) == gefragt


async def test_karten_aus_text_und_anlegen(pw: Pinnwand):
    b = await mit_ki(pw)
    LEITSTELLE.antworten.append(antwort(karten=[
        {"titel": "1. Fenster putzen", "beschreibung": f"Erdgeschoss {HALB} alle", "checkliste": ["Leiter holen", "leiter holen"]},
        {"titel": "fenster putzen", "beschreibung": "", "checkliste": []},
        {"titel": " ", "beschreibung": "ohne Titel", "checkliste": []},
        {"titel": "Gartenmöbel einlagern", "beschreibung": "", "checkliste": []}]))
    text = "Morgen: Fenster putzen (Erdgeschoss, alle), vorher Leiter holen. Gartenmöbel in den Keller."
    r = await ok(pw, "bert", f"/boards/{b['id']}/ki/karten", {"text": text})
    assert r == {"karten": [{"titel": "Fenster putzen", "beschreibung": "Erdgeschoss - alle", "checkliste": ["Leiter holen"]},
                            {"titel": "Gartenmöbel einlagern", "beschreibung": None, "checkliste": []}]}
    assert LEITSTELLE.koerper()["messages"][1]["content"].endswith(text)
    assert (await pw.stand("anna"))["karten"] == []                          # nur ein Vorschlag

    a = await ok(pw, "bert", f"/boards/{b['id']}/karten/mehrere", {"karten": r["karten"], "spalte": spalte(b, "Dran")})
    assert a["meldung"] == "2 Karten in Dran angelegt (HAUS-1 bis HAUS-2)"
    karten = sorted((await pw.stand("anna"))["karten"], key=lambda c: c["reihe"])
    assert [(c["schluessel"], c["titel"], c["zustaendig"], [p["text"] for p in c["checkliste"]]) for c in karten] == [
        ("HAUS-1", "Fenster putzen", ["2"], ["Leiter holen"]), ("HAUS-2", "Gartenmöbel einlagern", ["2"], [])]
    await ok(pw, "bert", f"/rueckgaengig/{a['rueckgaengig']}")
    assert (await pw.stand("anna"))["karten"] == []

    await abgelehnt(pw, "bert", f"/boards/{b['id']}/ki/karten", {"text": "  "}, 400, "Aus einem leeren Text werden keine Karten")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/ki/karten", {"text": "x" * 20_001}, 400, "Der Text ist länger als 20000 Zeichen")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/karten/mehrere", {"karten": []}, 400, "Keine Karte zum Anlegen")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/karten/mehrere", {"karten": [{"titel": "ok"}, {"titel": " "}]}, 400,
                    "Eine Karte braucht einen Titel")
    await abgelehnt(pw, "bert", f"/boards/{b['id']}/karten/mehrere", {"karten": [{"titel": "x"}] * 51}, 400,
                    "Höchstens 50 Karten auf einmal")
    assert (await pw.stand("anna"))["karten"] == []


@pytest.mark.parametrize("wie, status, meldung", [
    ("halt", 503, "Die Leitstelle kann gerade nicht: Die Leitstelle hält gerade an"),
    ("unlesbar", 502, "Die Antwort des Modells war nicht lesbar; noch einmal versuchen"),
    ("abgeschnitten", 502, "Die Antwort des Modells brach ab, bevor sie fertig war; noch einmal versuchen oder den Text kürzen"),
    ("leer", 502, "Das Modell hat keine Zusammenfassung geliefert; noch einmal versuchen"),
])
async def test_fehler_der_leitstelle(pw: Pinnwand, wie: str, status: int, meldung: str):
    b = await mit_ki(pw)
    k = await pw.karte("anna", b, "Fenster putzen")
    if wie == "halt":
        LEITSTELLE.fehler = (503, "halt")
    elif wie == "unlesbar":
        LEITSTELLE.antworten.append("Gern, hier ist sie: die Fenster.")
    elif wie == "abgeschnitten":
        LEITSTELLE.ende = "length"
        LEITSTELLE.antworten.append('{"text": "Die Fens')
    else:
        LEITSTELLE.antworten.append(antwort(text="  "))
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/ki/zusammenfassung", None, status, meldung)
