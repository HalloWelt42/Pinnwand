"""Konten zurücksetzen und löschen: selbst oder als Besitzer der App (anna besitzt den App-Schlüssel), bestätigt mit
dem Namen des Kontos, ohne Rückweg. Was dem Konto allein gehört, geht ganz (auch gebuchte Zeiten); Boards, in denen es
allein angemeldet ist, gehen mit Karten, Serien und Terminen; in geteilten Boards wird es ausgetragen, als einziger
Besitzer wandert der Besitz. Zurücksetzen legt das Konto mit neuer `anlage` gleich neu an, Löschen nimmt es heraus."""

from __future__ import annotations

from conftest import Pinnwand
from test_papierkorb import direkt, zeilen
from test_verwaltung import abgelehnt, mit_bert, ok


def zeit(id: str, konto: str, board: str) -> dict:
    return {"id": id, "konto": konto, "karte": "x", "board": board, "datum": "2026-10-26", "sekunden": 60, "herkunft": "nachgetragen"}


async def konto(pw: Pinnwand, wer: str, id: str) -> dict | None:
    return next((k for k in (await pw.stand(wer))["konten"] if k["id"] == id), None)


async def test_selbst_zuruecksetzen(pw: Pinnwand):
    haus = await mit_bert(pw)                                         # anna Besitzer, bert Mitglied
    werk = await pw.board("bert", "Werkstatt", "WERK")                # bert allein
    await pw.karte("bert", werk, "Hobeln")
    c = await pw.karte("anna", haus, "Fenster")
    await ok(pw, "anna", f"/karten/{c['id']}/bearbeiten", {"felder": {"zustaendig": ["1", "2"]}})
    await ok(pw, "bert", "/ordner", {"name": "Meins"})
    await direkt(pw, "zeiteintraege", zeit("z-b", "2", haus["id"]))
    await direkt(pw, "zeiteintraege", zeit("z-a", "1", haus["id"]))
    vorher = await konto(pw, "bert", "2")
    assert vorher and vorher["anlage"]
    assert not (await pw.stand("bert"))["appBesitzer"] and (await pw.stand("anna"))["appBesitzer"]

    await abgelehnt(pw, "bert", "/konten/2/zuruecksetzen", {"bestaetigung": "anna"}, 400, "Zur Sicherheit den Namen bert eintippen")
    await abgelehnt(pw, "bert", "/konten/1/zuruecksetzen", {"bestaetigung": "anna"}, 403,
                    "Andere Konten setzt nur der Besitzer der App zurück oder löscht sie")
    a = await ok(pw, "bert", "/konten/2/zuruecksetzen", {"bestaetigung": " Bert "})
    assert (a["meldung"], a["rueckgaengig"]) == ("Konto bert zurückgesetzt: 1 Board gelöscht, aus 1 Board ausgetragen", None)

    s = await pw.stand("bert")
    assert s["boards"] == [] and s["ordner"] == [] and s["zeiteintraege"] == []
    nachher = await konto(pw, "bert", "2")
    assert nachher and nachher["anlage"] != vorher["anlage"]
    # was anna gehört, bleibt; bert ist aus ihrem Board und ihrer Karte heraus, seine Werkstatt ist ganz weg
    assert [z["id"] for z in await zeilen(pw, "zeiteintraege")] == ["z-a"]
    assert [b["kuerzel"] for b in await zeilen(pw, "boards")] == ["HAUS"]
    sa = await pw.stand("anna")
    assert [m["kellerwolke"] for m in sa["boards"][0]["mitglieder"]] == ["anna"]
    assert next(k for k in sa["karten"] if k["id"] == c["id"])["zustaendig"] == ["1"]
    assert await zeilen(pw, "ordner") == [] and not [z for z in await zeilen(pw, "laufnummern") if z["id"] == werk["id"]]


async def test_besitzer_loescht_ein_konto(pw: Pinnwand):
    haus = await mit_bert(pw, "besitzer")                             # anna und bert besitzen Haushalt
    await abgelehnt(pw, "bert", "/konten/1/entfernen", {"bestaetigung": "anna"}, 403,
                    "Andere Konten setzt nur der Besitzer der App zurück oder löscht sie")
    a = await ok(pw, "anna", "/konten/2/entfernen", {"bestaetigung": "bert"})
    assert a["meldung"] == "Konto bert gelöscht: aus 1 Board ausgetragen"
    assert await konto(pw, "anna", "2") is None
    assert [m["kellerwolke"] for m in (await pw.stand("anna"))["boards"][0]["mitglieder"]] == ["anna"]
    await abgelehnt(pw, "anna", "/konten/2/entfernen", {"bestaetigung": "bert"}, 404, "Dieses Konto gibt es nicht (mehr)")
    # meldet bert sich wieder an, ist er neu und ohne Boards
    s = await pw.stand("bert")
    assert s["boards"] == [] and (await konto(pw, "bert", "2"))["fassung"] == 1
    assert haus["id"] in {b["id"] for b in await zeilen(pw, "boards")}


async def test_einziger_besitzer_gibt_den_besitz_weiter(pw: Pinnwand):
    """anna allein Besitzerin, bert Mitglied: setzt anna sich zurück, wird bert Besitzer; das Board bleibt."""
    haus = await mit_bert(pw)
    a = await ok(pw, "anna", "/konten/1/zuruecksetzen", {"bestaetigung": "anna"})
    assert a["meldung"] == "Konto anna zurückgesetzt: aus 1 Board ausgetragen"
    [b] = (await pw.stand("bert"))["boards"]
    assert b["id"] == haus["id"] and [(m["kellerwolke"], m["rolle"]) for m in b["mitglieder"]] == [("bert", "besitzer")]
    assert (await pw.stand("anna"))["boards"] == []
