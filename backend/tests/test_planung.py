"""Stufe 3: Serien mit Vorbuchung durch den Server (anlegen, Tageswechsel, ändern, Pause, Auslass, Urlaub, löschen), der
Nachtrag am Folgetag und Termine mit Zusage und bestätigter Zeit."""

from __future__ import annotations

from datetime import datetime

from conftest import Pinnwand
from test_verwaltung import abgelehnt, mit_bert, ok, spalte


def stellen(pw: Pinnwand, tag: int, stunde: int = 10) -> None:
    pw.zeiger.zeit = datetime(2026, 10, tag, stunde) if tag > 3 else datetime(2026, 11, tag, stunde)


async def serienkarten(pw: Pinnwand, wer: str = "anna") -> dict[str, dict]:
    """Karten der Serien nach Tag."""
    return {c["faellig"]: c for c in (await pw.stand(wer))["karten"] if c.get("serie")}


async def runde(pw: Pinnwand, b: dict, **mehr) -> dict:
    """Serie "Runde" werktags um 09:00, eine halbe Stunde, anna und bert, drei Tage Vorlauf."""
    daten = {"board": b["id"], "titel": "Runde", "rhythmus": "werktags", "uhrzeit": "09:00", "dauerMin": 30,
             "zielspalte": spalte(b, "Offen"), "teilnehmer": ["1", "2"], "ab": "2026-10-26", "vorlaufTage": 3, **mehr}
    a = await ok(pw, "anna", "/serien", daten)
    return {**a, "serie": next(s for s in (await pw.stand("anna"))["serien"] if s["titel"] == daten["titel"])}


async def test_vorbuchung_und_tageswechsel(pw: Pinnwand):
    b = await mit_bert(pw)                                         # Di 27.10.2026, 10 Uhr
    a = await runde(pw, b)
    assert a["meldung"] == "Serie Runde angelegt; 4 Tage vorgebucht"
    k = await serienkarten(pw)
    assert sorted(k) == ["2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]
    c = k["2026-10-28"]
    assert (c["titel"], c["zustaendig"], c["schaetzungMin"], c["spalte"]) == ("09:00 Runde", ["1", "2"], 30, spalte(b, "Offen"))
    assert c["verlauf"][0]["text"] == "aus der Serie Runde angelegt"

    # der Begleiter am Freitag: der Vorlauf reicht bis Montag, nur der kommt dazu; doppelt legt nichts doppelt an
    stellen(pw, 30)
    serien = pw.app.state.dienste.serien
    assert (await serien.alle_vorbuchen()).meldung is None             # still
    assert (await serien.alle_vorbuchen()).geaendert == []
    k = await serienkarten(pw)
    assert sorted(k)[-1] == "2026-11-02" and len(k) == 5
    assert k["2026-11-02"]["verlauf"][0]["von"] == "pinnwand"


async def test_aendern_pause_und_auslass(pw: Pinnwand):
    b = await mit_bert(pw)
    s = (await runde(pw, b))["serie"]
    k = await serienkarten(pw)
    await ok(pw, "anna", f"/karten/{k['2026-10-29']['id']}/verschieben", {"nach": spalte(b, "Dran")})   # angefasst

    r = await pw.c.patch(f"/api/v1/serien/{s['id']}", headers=pw.kopf["anna"], json={"uhrzeit": "08:30", "teilnehmer": ["1"]})
    assert r.json()["meldung"] == ("Serie Runde gespeichert; 2 Tage angepasst; angefasste und vergangene Tage bleiben")
    k = await serienkarten(pw)
    assert (k["2026-10-28"]["titel"], k["2026-10-28"]["zustaendig"]) == ("08:30 Runde", ["1"])
    assert (k["2026-10-29"]["titel"], k["2026-10-29"]["zustaendig"]) == ("09:00 Runde", ["1", "2"])   # angefasst bleibt
    assert k["2026-10-27"]["titel"] == "09:00 Runde"                                                # heute bleibt

    a = await ok(pw, "anna", f"/serien/{s['id']}/pausieren")
    assert a["meldung"] == "Serie Runde pausiert; 2 Tage zurückgenommen, angefasste Karten bleiben"
    assert sorted(await serienkarten(pw)) == ["2026-10-27", "2026-10-29"]
    a = await ok(pw, "anna", f"/serien/{s['id']}/fortsetzen")
    assert a["meldung"] == "Serie Runde fortgesetzt; 2 Tage ab heute vorgebucht"

    a = await ok(pw, "anna", f"/serien/{s['id']}/auslassen", {"tag": "2026-10-30"})
    assert a["meldung"].startswith("Runde am Fr 30.10. ausgelassen; der Tag kommt nicht wieder, HAUS-")
    assert "2026-10-30" not in await serienkarten(pw)
    await pw.app.state.dienste.serien.alle_vorbuchen()
    assert "2026-10-30" not in await serienkarten(pw)
    # Wiederherstellen aus dem Papierkorb nimmt den Auslass zurück
    eintrag = (await pw.stand("anna"))["papierkorb"][0]
    await ok(pw, "anna", f"/papierkorb/{eintrag['id']}/wiederherstellen")
    assert next(x for x in (await pw.stand("anna"))["serien"])["auslass"] == []
    # eine Serienkarte in den Papierkorb legen lässt ihren Tag aus
    await ok(pw, "anna", "/karten/in-papierkorb", {"ids": [(await serienkarten(pw))["2026-10-28"]["id"]]})
    assert [x["tag"] for x in (await pw.stand("anna"))["serien"][0]["auslass"]] == ["2026-10-28"]


async def test_urlaub_nimmt_aus_vorbuchungen(pw: Pinnwand):
    b = await mit_bert(pw)
    await ok(pw, "anna", f"/boards/{b['id']}/module/arbeitszeit", {"an": True})
    await runde(pw, b, teilnehmer=["2"], titel="Werkstatt")
    await runde(pw, b)
    a = await ok(pw, "bert", "/abwesenheiten", {"von": "2026-10-29", "bis": "2026-10-29", "art": "urlaub"})
    assert a["meldung"].endswith("; 2 Vorbuchungen einer Serie zurückgenommen")
    tag29 = [c for c in (await pw.stand("anna"))["karten"] if c.get("faellig") == "2026-10-29" and c.get("serie")]
    assert [(c["titel"], c["zustaendig"]) for c in tag29] == [("09:00 Runde", ["1"])]   # Werkstatt entfällt ganz


async def test_nachtrag_und_loeschen(pw: Pinnwand):
    b = await mit_bert(pw)
    s = (await runde(pw, b))["serie"]
    stellen(pw, 28)
    a = await ok(pw, "anna", f"/serien/{s['id']}/bestaetigen", {"tag": "2026-10-27", "sekunden": 2700})
    assert a["meldung"] == "0:45 auf HAUS-1 gebucht (Di 27.10.), Karte erledigt"
    c = (await serienkarten(pw))["2026-10-27"]
    assert c["spalte"] == spalte(b, "Erledigt") and c["abgeschlossen"] == "2026-10-27"
    [e] = [x for x in (await pw.stand("anna"))["zeiteintraege"] if x["karte"] == c["id"]]
    assert (e["herkunft"], e["von"], e["bis"], e["sekunden"]) == ("serie", "09:00", "09:45", 2700)
    a = await ok(pw, "bert", f"/serien/{s['id']}/verwerfen", {"tag": "2026-10-27"})
    assert a["meldung"] == "HAUS-1: für dich verworfen, die Karte bleibt für die anderen"
    await abgelehnt(pw, "anna", f"/serien/{s['id']}/bestaetigen", {"tag": "2026-10-28", "sekunden": 60}, 400,
                    "Nachtragen geht für die vergangenen 31 Tage")

    # Leser dürfen Serien nicht verwalten
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/rolle", {"kellerwolke": "bert", "rolle": "leser"})
    await abgelehnt(pw, "bert", f"/serien/{s['id']}/pausieren", None, 403, "Dir fehlt im Board Haushalt das Recht Serien verwalten")

    r = await pw.c.delete(f"/api/v1/serien/{s['id']}", headers=pw.kopf["anna"])
    assert r.json()["meldung"] == "Serie Runde gelöscht; 2 Tage im Papierkorb, 2 Karten bleiben als Verlauf"
    s = await pw.stand("anna")
    assert s["serien"] == [] and not any(c.get("serie") for c in s["karten"])
    assert len(s["papierkorb"]) == 2


async def test_termine(pw: Pinnwand):
    b = await mit_bert(pw)
    a = await ok(pw, "anna", "/termine", {"board": b["id"], "titel": "Abstimmung", "datum": "2026-10-28", "von": "14:00",
                                          "bis": "15:30", "teilnehmer": ["1", "2"], "ort": "Küche"})
    assert a["meldung"] == "Termin Abstimmung, Mi 28.10. 14:00 angelegt"
    [t] = (await pw.stand("anna"))["termine"]
    assert (t["zugesagt"], t["bestaetigt"]) == (["1"], [])
    [h] = [x for x in (await pw.stand("bert"))["hinweise"] if x["art"] == "termin"]
    assert h["text"] == "Termin Abstimmung, Mi 28.10. 14:00 (Küche)" and "karte" not in h
    assert (await ok(pw, "bert", f"/termine/{t['id']}/zusagen", {"ja": True}))["meldung"] == "Zugesagt: Abstimmung, Mi 28.10. 14:00"
    await abgelehnt(pw, "anna", f"/termine/{t['id']}/bestaetigen", None, 400, "Die Zeit eines Termins bestätigst du nach dem Termin")

    stellen(pw, 29)
    a = await ok(pw, "anna", "/nachtrag", {"posten": [{"art": "termin", "bezug": t["id"], "tag": "2026-10-28"}]})
    assert a["meldung"] == "1 Zeit bestätigt"
    [e] = [x for x in (await pw.stand("anna"))["zeiteintraege"] if x.get("termin") == t["id"]]
    assert (e["herkunft"], e["sekunden"], e["von"], e["bis"], e.get("karte")) == ("termin", 5400, "14:00", "15:30", None)
    # den Eintrag löschen nimmt die Bestätigung zurück
    r = await pw.delete("anna", f"/zeiten/{e['id']}")
    assert r.json()["meldung"] == "Zeiteintrag (1:30, Mi 28.10.) gelöscht"
    assert (await pw.stand("anna"))["termine"][0]["bestaetigt"] == []
    a = await ok(pw, "bert", f"/termine/{t['id']}/verwerfen")
    assert a["meldung"] == "Abstimmung am Mi 28.10.: fand für dich nicht statt, es zählt keine Zeit"
    assert (await pw.stand("anna"))["termine"][0]["teilnehmer"] == ["1"]
