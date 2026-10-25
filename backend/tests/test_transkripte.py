"""Stufe 4, Transkripte: Stellen der Transkription an der Karte (im Auftrag der Person gesucht und gelesen, Name,
Sprecher und Text vom Server), Notiz, Lösen mit Rückgängig, Ton mit Bereichen durchgereicht, Notiz vorschlagen mit KI
an der Karte, Spracheingabe beim Erfassen; wer die Transkription nicht nutzen darf, sieht die Marken, hört sie aber
nicht."""

from __future__ import annotations

import json

import pytest

from conftest import Pinnwand
from nachgestellt import LEITSTELLE, LEITSTELLE_EINRICHTUNG, TELEFONAT, TRANSKRIPTION, TRANSKRIPTION_EINRICHTUNG
from test_verwaltung import abgelehnt, mit_bert, ok


@pytest.fixture(autouse=True)
def leere_dienste():
    TRANSKRIPTION.leeren()
    LEITSTELLE.leeren()
    yield
    TRANSKRIPTION.leeren()
    LEITSTELLE.leeren()


async def einstellen(pw: Pinnwand, **werte) -> None:
    r = await pw.c.patch("/api/v1/einstellungen", headers=pw.kopf["anna"], json={"werte": werte})
    assert r.status_code == 200, r.text


async def mit_transkripten(pw: Pinnwand, rolle: str = "mitglied") -> tuple[dict, dict]:
    """Haushalt mit Transkripten, bert in der Rolle, die Transkription eingerichtet; eine Karte."""
    b = await mit_bert(pw, rolle)
    await ok(pw, "anna", f"/boards/{b['id']}/module/transkripte", {"an": True})
    await einstellen(pw, **TRANSKRIPTION_EINRICHTUNG)
    return b, await pw.karte("anna", b, "Angebot Brandt")


def marken(r: dict) -> list[dict]:
    return next(g["daten"] for g in r["geaendert"] if g["tabelle"] == "karten")["transkripte"]


async def test_ohne_adresse_kein_modul(pw: Pinnwand):
    b = await mit_bert(pw)
    k = await pw.karte("anna", b, "Angebot Brandt")
    assert (await pw.stand("anna"))["transkriptionAdresse"] == ""
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT}, 403, "Transkripte sind im Board Haushalt aus")
    await ok(pw, "anna", f"/boards/{b['id']}/module/transkripte", {"an": True})
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT}, 503,
                    "Die Transkription ist nicht eingerichtet (Einstellungen, Verbindungen)")
    await einstellen(pw, **TRANSKRIPTION_EINRICHTUNG)
    assert (await pw.stand("anna"))["transkriptionAdresse"] == "https://tr.test"
    verbindung = next(v for v in (await pw.get("anna", "/verbindungen")).json() if v["name"] == "Transkription")
    assert verbindung["ok"] and verbindung["meldung"] == "Fassung 0.12.0"


async def test_suchen_verknuepfen_notiz_loesen(pw: Pinnwand):
    b, k = await mit_transkripten(pw)
    r = await pw.get("bert", f"/karten/{k['id']}/transkripte/suche", params={"text": "preis"})
    assert r.status_code == 200, r.text
    assert r.json() == {"gesamt": 1, "ab": 0, "treffer": [{"transkript": TELEFONAT, "name": "Telefonat Kunde 26.10.", "dauerS": 300.0,
                        "fundstellen": [{"zeit": 252.0, "ausschnitt": "Den Preis der Beschichtung sage ich am 28.10."}]}]}
    anfrage = TRANSKRIPTION.anfragen[-1]
    assert anfrage.headers["x-kellerwolke-sitzung"] == "t-bert" and anfrage.url.params["suche"] == "preis"

    # die Oberfläche schickt nur Transkript und Sekunde; Name, Sprecher und Text kommen aus dem Transkript
    a = await ok(pw, "bert", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT, "sekunde": 255.4})
    assert a["meldung"] == "HAUS-1: Telefonat Kunde 26.10. bei 4:15 verknüpft"
    [m] = marken(a)
    assert {x: m[x] for x in ("transkript", "name", "sekunde", "sprecher", "text", "von")} == {
        "transkript": TELEFONAT, "name": "Telefonat Kunde 26.10.", "sekunde": 255.4, "sprecher": "Brandt",
        "text": "Den Preis der Beschichtung sage ich am 28.10.", "von": "2"}
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT, "sekunde": 255.4}, 400,
                    "Diese Stelle hängt schon an der Karte")
    ganz = marken(await ok(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT}))[1]
    assert not {"sekunde", "text", "sprecher"} & set(ganz)                        # das ganze Transkript

    n = await ok(pw, "bert", f"/karten/{k['id']}/transkripte/{m['id']}/notiz", {"notiz": "  Preis kommt am 28.10.  "})
    assert n["meldung"] == "HAUS-1: Notiz zu Telefonat Kunde 26.10. bei 4:15 gespeichert" and marken(n)[0]["notiz"] == "Preis kommt am 28.10."
    r = await pw.delete("bert", f"/karten/{k['id']}/transkripte/{m['id']}")
    assert r.status_code == 200 and r.json()["meldung"] == "HAUS-1: Telefonat Kunde 26.10. bei 4:15 gelöst"
    assert [x["id"] for x in marken(r.json())] == [ganz["id"]]
    await ok(pw, "bert", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    karte = (await pw.get("anna", "/karten/HAUS-1")).json()
    assert [x["id"] for x in karte["transkripte"]] == [m["id"], ganz["id"]]
    assert [e["text"] for e in karte["verlauf"]][-3:] == [
        "hat Telefonat Kunde 26.10. bei 4:15 verknüpft", "hat Telefonat Kunde 26.10. verknüpft",
        "hat die Notiz zu Telefonat Kunde 26.10. bei 4:15 geändert"]


async def test_rechte_und_zugang_der_transkription(pw: Pinnwand):
    b, k = await mit_transkripten(pw, "leser")
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT}, 403,
                    "Dir fehlt im Board Haushalt das Recht Karten bearbeiten")
    assert (await pw.get("bert", f"/karten/{k['id']}/transkripte/suche", params={"text": "x"})).status_code == 403
    assert TRANSKRIPTION.anfragen == []                                      # gefragt wird erst nach der Prüfung
    # cora ist Mitglied mit Recht, darf aber die Transkription nicht nutzen: die Transkription sagt es
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "cora", "rolle": "mitglied"})
    assert (await pw.anmelden("cora")).status_code == 200
    await abgelehnt(pw, "cora", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT}, 403,
                    "Die Transkription lässt dich nicht zu: Dieses Konto darf die Transkription nicht nutzen")
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": "7a0f0000-0000-4000-8000-000000000009"}, 404,
                    "Dieses Transkript gibt es in der Transkription nicht (mehr)")


async def test_ton_mit_bereichen(pw: Pinnwand):
    b, k = await mit_transkripten(pw, "leser")
    [m] = marken(await ok(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT, "sekunde": 3}))
    pfad = f"/api/v1/inhalt/transkripte/{k['id']}/{m['id']}/ton"
    r = await pw.c.get(pfad, headers={**pw.kopf["bert"], "Range": "bytes=1000-1999"})     # lesen genügt
    assert r.status_code == 206 and r.content == TRANSKRIPTION.ton[1000:2000]
    assert r.headers["content-range"] == f"bytes 1000-1999/{len(TRANSKRIPTION.ton)}" and r.headers["content-type"] == "audio/wav"
    assert TRANSKRIPTION.anfragen[-1].headers["x-kellerwolke-sitzung"] == "t-bert"
    # der Spieler sendet keinen Kopf, nur das Inhalts-Cookie der Anmeldung
    pw.c.cookies.set("app_inhalt", "t-anna")
    assert (await pw.c.get(pfad, headers={"Range": "bytes=0-9"})).content == TRANSKRIPTION.ton[:10]
    pw.c.cookies.clear()
    assert (await pw.c.get(pfad)).status_code == 401


async def test_notiz_vorschlagen_mit_ki(pw: Pinnwand):
    b, k = await mit_transkripten(pw)
    [m] = marken(await ok(pw, "anna", f"/karten/{k['id']}/transkripte", {"transkript": TELEFONAT, "sekunde": 255}))
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/transkripte/{m['id']}/ki/notiz", None, 403, "KI an der Karte ist im Board Haushalt aus")
    await ok(pw, "anna", f"/boards/{b['id']}/module/ki", {"an": True})
    await einstellen(pw, **LEITSTELLE_EINRICHTUNG)
    LEITSTELLE.antworten.append(json.dumps({"text": "Brandt nennt den Preis der Beschichtung am 28.10."}))
    assert await ok(pw, "anna", f"/karten/{k['id']}/transkripte/{m['id']}/ki/notiz") == {
        "text": "Brandt nennt den Preis der Beschichtung am 28.10."}
    gespraech = LEITSTELLE.koerper()["messages"][1]["content"]
    # nur die Abschnitte um die Stelle (30 Sekunden davor, 90 danach)
    assert "[4:12] Brandt: Den Preis der Beschichtung" in gespraech and "Guten Tag" not in gespraech
    assert "Markierte Stelle: 4:15" in gespraech


async def test_spracheingabe(pw: Pinnwand):
    b, _ = await mit_transkripten(pw)
    r = await pw.c.post(f"/api/v1/boards/{b['id']}/sprache", headers={**pw.kopf["bert"], "Content-Type": "audio/webm"},
                        content=b"ton" * 100)
    assert r.status_code == 200 and r.json() == {"text": TRANSKRIPTION.gehoert}
    anfrage = TRANSKRIPTION.anfragen[-1]
    assert anfrage.url.path == "/api/v1/hoeren" and b'filename="sprache.webm"' in anfrage.content
    assert b"Content-Type: audio/webm" in anfrage.content and anfrage.headers["x-kellerwolke-sitzung"] == "t-bert"
    r = await pw.c.post(f"/api/v1/boards/{b['id']}/sprache", headers=pw.kopf["bert"], content=b"")
    assert (r.status_code, r.json()["detail"]) == (400, "Es kam kein Ton an")
