"""Hinweise über die Schnittstelle: Anlässe (zugewiesen, erwähnt, Kommentar, verschoben, fällig) an die Betroffenen, nie
an die handelnde Person, nur auf eingeschalteten Wegen; gelesen, alle gelesen, Wege je Art; Ereignis nur an das eigene
Konto; Rückgängig nimmt den Hinweis mit; der Begleiter meldet Fälliges einmal am Tag."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from conftest import Pinnwand

from app.anwendung.hinweise import Faelligkeit


def spalte(b: dict, name: str) -> str:
    return next(s["id"] for s in b["spalten"] if s["name"] == name)


async def zu_dritt(pw: Pinnwand, **mehr) -> dict:
    """Board Haushalt von anna, bert und cora als Mitglieder (beide angemeldet)."""
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}, {"kellerwolke": "cora"}], **mehr)
    for name in ("bert", "cora"):
        await pw.anmelden(name)
        await pw.stand(name)
    return next(x for x in (await pw.stand("anna"))["boards"] if x["id"] == b["id"])


async def hinweise(pw: Pinnwand, wer: str) -> list[dict]:
    return (await pw.stand(wer))["hinweise"]


async def texte(pw: Pinnwand, wer: str) -> list[str]:
    return sorted(h["text"] for h in await hinweise(pw, wer))


async def bearbeiten(pw: Pinnwand, wer: str, k: dict, felder: dict):
    r = await pw.post(wer, f"/karten/{k['id']}/bearbeiten", {"felder": felder})
    assert r.status_code == 200, r.text
    return r


# --- Anlässe -----------------------------------------------------------------------------------------------------

async def test_zugewiesen(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    [h] = await hinweise(pw, "bert")
    assert {x: h[x] for x in ("art", "von", "board", "karte", "text", "gelesen", "zeit")} == {
        "art": "zugewiesen", "von": "1", "board": b["id"], "karte": k["id"], "text": "anna hat dir HAUS-1 zugewiesen",
        "gelesen": False, "zeit": "2026-10-27T10:00:00"}
    assert await hinweise(pw, "anna") == [] and await hinweise(pw, "cora") == []
    # wer schon zuständig ist, bekommt beim nächsten Speichern keinen weiteren; wer sich selbst zuweist, keinen
    await bearbeiten(pw, "anna", k, {"zustaendig": ["2", "1"], "titel": "Fenster putzen"})
    await bearbeiten(pw, "cora", k, {"zustaendig": ["1", "2", "3"]})
    assert len(await hinweise(pw, "bert")) == 1 and await hinweise(pw, "cora") == []
    assert await texte(pw, "anna") == []                                         # cora hat nur sich zugewiesen

    # Sammelaktion: ein Hinweis je Karte, die neu dazukommt
    ids = [k["id"], (await pw.karte("anna", b, "Keller"))["id"], (await pw.karte("anna", b, "Dach"))["id"]]
    await pw.post("bert", "/karten/sammel/zuweisen", {"ids": ids, "konto": "3"})
    await pw.post("anna", "/karten/sammel/zuweisen", {"ids": ids, "konto": "3"})
    assert await texte(pw, "cora") == ["bert hat dir HAUS-2 zugewiesen", "bert hat dir HAUS-3 zugewiesen"]


async def test_erwaehnt_nur_neu(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"beschreibung": "Bitte @Bert und @co prüfen, @anna weiß Bescheid, @niemand nicht"})
    assert await texte(pw, "bert") == ["anna hat dich in HAUS-1 erwähnt"]
    assert await texte(pw, "cora") == ["anna hat dich in HAUS-1 erwähnt"]
    assert await hinweise(pw, "anna") == []
    # erneut gespeichert mit denselben Erwähnungen: nichts Neues; in den Notizen ist bert neu erwähnt
    await bearbeiten(pw, "anna", k, {"beschreibung": "@co und @bert: bitte bis Freitag prüfen"})
    await bearbeiten(pw, "anna", k, {"notizen": "Leiter bei @bert"})
    assert len(await hinweise(pw, "bert")) == 2 and len(await hinweise(pw, "cora")) == 1
    # Code, Adressen und E-Mail sind keine Erwähnung (wie in der Darstellung)
    await bearbeiten(pw, "bert", k, {"notizen": "`@cora`\n```\n@cora\n```\nhttps://beispiel.de/@cora und cora@beispiel.de"})
    assert len(await hinweise(pw, "cora")) == 1
    # beim Anlegen mit Beschreibung (schnell erfassen)
    await pw.karte("bert", b, "Keller", beschreibung="@anna schaut mit")
    assert await texte(pw, "anna") == ["bert hat dich in HAUS-2 erwähnt"]


async def test_kommentar(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    await pw.post("cora", f"/karten/{k['id']}/kommentieren", {"text": "Mache ich am Freitag"})
    assert await texte(pw, "anna") == ["cora hat HAUS-1 kommentiert"]
    assert "cora hat HAUS-1 kommentiert" in await texte(pw, "bert")
    # wer im Kommentar erwähnt ist, bekommt nur den Hinweis "erwähnt"; wer kommentiert, nichts
    await pw.post("anna", f"/karten/{k['id']}/kommentieren", {"text": "@bert hast du Zeit?"})
    assert [h["art"] for h in await hinweise(pw, "bert")].count("erwaehnt") == 1
    assert [h["art"] for h in await hinweise(pw, "bert")].count("kommentar") == 1
    assert await texte(pw, "cora") == []


async def test_verschoben_mit_verknuepften(pw: Pinnwand):
    b = await zu_dritt(pw)
    a = await pw.karte("anna", b, "Fenster")
    c = await pw.karte("anna", b, "Rahmen")
    await bearbeiten(pw, "anna", a, {"zustaendig": ["1", "2"]})
    await bearbeiten(pw, "anna", c, {"zustaendig": ["3"]})
    await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    vorher = {n: await texte(pw, n) for n in ("anna", "bert", "cora")}

    await pw.post("anna", f"/karten/{a['id']}/verschieben", {"nach": spalte(b, "Dran")})
    neu = {n: [t for t in await texte(pw, n) if t not in vorher[n]] for n in vorher}
    assert neu == {"anna": [], "bert": ["anna hat HAUS-1 nach Dran verschoben"],
                   "cora": ["anna hat HAUS-2 mit HAUS-1 nach Dran verschoben"]}
    # neu ordnen in derselben Spalte ist kein Verschieben
    await pw.post("anna", f"/karten/{c['id']}/verschieben", {"nach": spalte(b, "Dran"), "platz": 0})
    assert len(await hinweise(pw, "bert")) == len(vorher["bert"]) + 1

    await pw.post("bert", f"/karten/{a['id']}/erledigen")
    assert "bert hat HAUS-1 erledigt" in await texte(pw, "anna")
    assert "bert hat HAUS-2 mit HAUS-1 erledigt" in await texte(pw, "cora")
    assert not any("erledigt" in t for t in await texte(pw, "bert"))


# --- Wege --------------------------------------------------------------------------------------------------------

async def test_wege_je_art(pw: Pinnwand):
    b = await zu_dritt(pw)
    assert (await pw.stand("bert"))["einstellungen"] == {"id": "2", "hinweise": {}}
    r = await pw.post("bert", "/hinweise/weg", {"art": "verschoben", "weg": "pinnwand", "an": False})
    assert (r.json()["meldung"], bool(r.json()["rueckgaengig"])) == ("Hinweise gespeichert", True)
    assert (await pw.stand("bert"))["einstellungen"]["hinweise"] == {"verschoben": {"pinnwand": False}}
    # Rückgängig stellt die Einstellungen zurück, die Zeile bleibt (die Oberfläche bekommt den Stand, keinen Wegfall)
    r = await pw.post("bert", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert [(g["tabelle"], g["daten"]["hinweise"]) for g in r.json()["geaendert"]] == [("person_einstellungen", {})]
    await pw.post("bert", "/hinweise/weg", {"art": "verschoben", "weg": "pinnwand", "an": False})
    # schon so: nichts geschieht
    r = await pw.post("bert", "/hinweise/weg", {"art": "verschoben", "weg": "pinnwand", "an": False})
    assert r.json() == {"meldung": None, "rueckgaengig": None, "geaendert": []}

    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    await pw.post("anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Dran")})
    assert [h["art"] for h in await hinweise(pw, "bert")] == ["zugewiesen"]

    for daten, meldung in [
        ({"art": "faellig", "weg": "assistent", "an": True}, "Den Weg Über den Assistenten bietet diese Pinnwand nicht an"),
    ]:
        r = await pw.post("bert", "/hinweise/weg", daten)
        assert (r.status_code, r.json()["detail"]) == (400, meldung)
    assert (await pw.post("bert", "/hinweise/weg", {"art": "gibt-es-nicht", "weg": "pinnwand", "an": True})).status_code == 422


# --- gelesen -----------------------------------------------------------------------------------------------------

async def test_gelesen_und_alle_gelesen(pw: Pinnwand):
    b = await zu_dritt(pw)
    for t in ("Fenster", "Keller", "Dach"):
        await bearbeiten(pw, "anna", await pw.karte("anna", b, t), {"zustaendig": ["1", "2"]})
    erster, zweiter, dritter = await hinweise(pw, "bert")

    r = await pw.post("bert", f"/hinweise/{erster['id']}/gelesen", {"gelesen": True})
    assert (r.json()["meldung"], r.json()["rueckgaengig"]) == (None, None)
    assert [g["daten"]["gelesen"] for g in r.json()["geaendert"]] == [True]
    r = await pw.post("bert", f"/hinweise/{erster['id']}/gelesen", {"gelesen": True})
    assert r.json()["geaendert"] == []
    await pw.post("bert", f"/hinweise/{erster['id']}/gelesen", {"gelesen": False})
    await pw.post("bert", f"/hinweise/{dritter['id']}/gelesen")
    # fremde Hinweise gibt es für niemanden sonst
    assert (await pw.post("cora", f"/hinweise/{zweiter['id']}/gelesen")).status_code == 404

    r = await pw.post("bert", "/hinweise/alle-gelesen")
    assert r.json()["meldung"] == "2 Hinweise als gelesen markiert"
    assert all(h["gelesen"] for h in await hinweise(pw, "bert"))
    assert (await pw.post("bert", "/hinweise/alle-gelesen")).json()["meldung"] is None
    await pw.post("bert", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert [h["gelesen"] for h in sorted(await hinweise(pw, "bert"), key=lambda h: h["id"] != dritter["id"])] == [True, False, False]


# --- Ereignisse und Rückgängig -----------------------------------------------------------------------------------

async def test_hinweis_nur_an_sein_konto(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    hub = pw.app.state.dienste.ereignisse
    with hub.abo("2") as bert, hub.abo("3") as cora:
        r = await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
        assert [g["tabelle"] for g in r.json()["geaendert"]] == ["karten"]       # annas Antwort ohne berts Hinweis
        an_bert = await asyncio.wait_for(anext(bert), 1)
        an_cora = await asyncio.wait_for(anext(cora), 1)
    assert sorted(g.tabelle for g in an_bert.geaendert) == ["hinweise", "karten"]
    assert [g.tabelle for g in an_cora.geaendert] == ["karten"]


async def test_rueckgaengig_nimmt_hinweis_mit(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    r = await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    assert len(await hinweise(pw, "bert")) == 1
    assert (await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")).status_code == 200
    assert await hinweise(pw, "bert") == []


# --- fällig ------------------------------------------------------------------------------------------------------

async def test_faellig_einmal_am_tag(pw: Pinnwand):
    b = await zu_dritt(pw)
    melden = pw.app.state.dienste.hinweise.faellige_melden
    heute = await pw.karte("anna", b, "Steuer", faellig="2026-10-27")
    gestern = await pw.karte("anna", b, "Keller", faellig="2026-10-26")
    await pw.karte("anna", b, "Später", faellig="2026-10-30")
    await pw.karte("anna", b, "Ohne Tag")
    fertig = await pw.karte("anna", b, "Fertig", faellig="2026-10-20")
    await pw.post("anna", f"/karten/{fertig['id']}/erledigen")
    await bearbeiten(pw, "anna", heute, {"zustaendig": ["1", "2"]})
    for h in await hinweise(pw, "bert"):
        await pw.post("bert", f"/hinweise/{h['id']}/gelesen")

    await melden()
    assert await texte(pw, "anna") == ["HAUS-1 ist heute fällig", "HAUS-2 ist 1 Tag überfällig"]
    faellig_bert = [h for h in await hinweise(pw, "bert") if h["art"] == "faellig"]
    assert [(h["text"], h["gelesen"], h.get("von")) for h in faellig_bert] == [("HAUS-1 ist heute fällig", False, None)]
    # am selben Tag noch einmal: kein Doppel, nichts geschrieben
    assert (await melden()).geaendert == []

    await pw.post("bert", f"/hinweise/{faellig_bert[0]['id']}/gelesen")
    await pw.post("bert", "/hinweise/weg", {"art": "faellig", "weg": "pinnwand", "an": False})
    pw.zeiger.zeit += timedelta(days=1)
    await melden()
    assert await texte(pw, "anna") == ["HAUS-1 ist 1 Tag überfällig", "HAUS-2 ist 2 Tage überfällig"]
    assert all(not h["gelesen"] and h["zeit"] == "2026-10-28T10:00:00" for h in await hinweise(pw, "anna"))
    # derselbe Hinweis je Karte und Person, erneuert; bert hat fällig ausgeschaltet
    assert [h["id"] for h in await hinweise(pw, "bert") if h["art"] == "faellig"] == [faellig_bert[0]["id"]]
    assert [h["gelesen"] for h in await hinweise(pw, "bert") if h["art"] == "faellig"] == [True]
    assert gestern["schluessel"] == "HAUS-2"


async def test_begleiter_meldet_beim_tageswechsel(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("bert", b, "Steuer", faellig="2026-10-28")
    begleiter = Faelligkeit(pw.app.state.dienste.hinweise)
    assert await begleiter.pruefen() and not await begleiter.pruefen()          # beim Start, dann erst am neuen Tag
    assert await hinweise(pw, "bert") == []
    pw.zeiger.zeit += timedelta(days=1)
    assert await begleiter.pruefen()
    assert [(h["art"], h["karte"]) for h in await hinweise(pw, "bert")] == [("faellig", k["id"])]
    await begleiter.starten()
    await begleiter.stoppen()
