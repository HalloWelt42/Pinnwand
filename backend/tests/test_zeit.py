"""Stufe 2: der Timer je Person (Buchen, Mitternacht, Deckel, automatische Stopps), Zeiteinträge setzen und ändern, wer
welche Zeit sieht, Arbeitszeit und Urlaub, die Tagessummen des Teams."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.regeln.zeit import sitzung_teile
from conftest import Pinnwand
from test_verwaltung import abgelehnt, mit_bert, ok, spalte


def stellen(pw: Pinnwand, tag: int, stunde: int, minute: int = 0) -> None:
    pw.zeiger.zeit = datetime(2026, 10, tag, stunde, minute)


def vor(pw: Pinnwand, minuten: int) -> None:
    pw.zeiger.zeit += timedelta(minutes=minuten)


async def eintraege(pw: Pinnwand, wer: str, karte: dict | None = None) -> list[dict]:
    alle = (await pw.stand(wer))["zeiteintraege"]
    return sorted((e for e in alle if karte is None or e["karte"] == karte["id"]), key=lambda e: (e["datum"], e.get("von", "")))


async def zeitboard(pw: Pinnwand, rolle: str = "mitglied") -> tuple[dict, dict]:
    """Board Haushalt (Zeiterfassung an) mit bert in der Rolle und einer Karte."""
    b = await mit_bert(pw, rolle)
    return b, await pw.karte("anna", b, "Fenster putzen")


# ═══ Regeln ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

def test_sitzung_ueber_die_zeitumstellung():
    # in der Nacht auf den 25.10.2026 wird 3 Uhr wieder 2 Uhr: von Mitternacht bis 3 Uhr vergehen vier Stunden
    teile, gesamt = sitzung_teile("2026-10-24T23:00:00", "2026-10-25T03:00:00", ZoneInfo("Europe/Berlin"))
    assert [(t.tag, t.von, t.bis, t.sekunden) for t in teile] == [
        ("2026-10-24", "23:00", "24:00", 3600), ("2026-10-25", "00:00", "03:00", 4 * 3600)]
    assert gesamt == 5 * 3600


def test_sitzung_gedeckelt():
    teile, gesamt = sitzung_teile("2026-10-26T20:00:00", "2026-10-27T08:30:00", ZoneInfo("Europe/Berlin"))
    assert [(t.tag, t.von, t.bis) for t in teile] == [("2026-10-26", "20:00", "24:00"), ("2026-10-27", "00:00", "08:00")]
    assert sum(t.sekunden for t in teile) == 12 * 3600 and gesamt == 12.5 * 3600


# ═══ Timer ════════════════════════════════════════════════════════════════════════════════════════════════════════════

async def test_timer_bucht_und_fasst_sitzungen_zusammen(pw: Pinnwand):
    b, k = await zeitboard(pw)
    a = await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    assert a["meldung"] == "Timer läuft auf HAUS-1" and a["rueckgaengig"]
    s = await pw.stand("anna")
    assert s["timer"] == [{"id": "1", "konto": "1", "karte": k["id"], "board": b["id"], "seit": "2026-10-27T10:00:00", "fassung": 1}]
    karte = next(c for c in s["karten"] if c["id"] == k["id"])
    assert karte["start"] == "2026-10-27" and karte["verlauf"][-1]["text"] == "hat den Timer gestartet"

    vor(pw, 90)
    assert (await ok(pw, "anna", "/timer/anhalten"))["meldung"] == "HAUS-1 angehalten, 1:30 gebucht"
    assert (await pw.stand("anna"))["timer"][0].get("seit") is None
    vor(pw, 30)
    assert (await ok(pw, "anna", "/timer/fortsetzen"))["meldung"] == "Timer auf HAUS-1 fortgesetzt"
    vor(pw, 15)
    assert (await ok(pw, "anna", "/timer/stoppen"))["meldung"] == "HAUS-1 gestoppt, 0:15 gebucht"
    [e] = await eintraege(pw, "anna", k)
    assert (e["von"], e["bis"], e["sekunden"], e["herkunft"]) == ("10:00", "12:15", 6300, "timer")
    assert e["sitzungen"] == [{"von": "10:00", "bis": "11:30"}, {"von": "12:00", "bis": "12:15"}]
    assert (await pw.stand("anna"))["timer"] == []


async def test_start_auf_anderer_karte_beendet_nur_den_eigenen(pw: Pinnwand):
    b, k = await zeitboard(pw)
    zweite = await pw.karte("anna", b, "Keller aufräumen")
    await ok(pw, "bert", "/timer/starten", {"karte": k["id"]})
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    vor(pw, 20)
    a = await ok(pw, "anna", "/timer/starten", {"karte": zweite["id"]})
    assert a["meldung"] == "Timer läuft auf HAUS-2; HAUS-1 beendet, 0:20 gebucht"
    timer = {t["konto"]: t["karte"] for t in (await pw.stand("anna"))["timer"]}
    assert timer == {"1": zweite["id"], "2": k["id"]}                    # berts Timer läuft weiter (M-80)


async def test_mitternacht_und_deckel(pw: Pinnwand):
    _, k = await zeitboard(pw)
    stellen(pw, 26, 23)
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    stellen(pw, 27, 1, 30)
    await ok(pw, "anna", "/timer/stoppen")
    teile = await eintraege(pw, "anna", k)
    assert [(e["datum"], e["von"], e["bis"], e["zerlegt"]) for e in teile] == [
        ("2026-10-26", "23:00", "24:00", "2026-10-27"), ("2026-10-27", "00:00", "01:30", "2026-10-26")]

    # vergessen: 12:30 Stunden, gebucht sind 12 mit Rückfrage
    stellen(pw, 27, 20)
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    stellen(pw, 28, 8, 30)
    assert (await ok(pw, "anna", "/timer/stoppen"))["meldung"] == "HAUS-1 gestoppt, 12:00 gebucht"
    gedeckelt = [e for e in await eintraege(pw, "anna", k) if e.get("gedeckelt")]
    assert [(e["datum"], e["von"], e["bis"]) for e in gedeckelt] == [("2026-10-27", "20:00", "24:00"), ("2026-10-28", "00:00", "08:00")]
    assert gedeckelt[0]["gedeckelt"] == {"seit": "2026-10-27T20:00:00", "bis": "2026-10-28T08:30:00", "sekunden": 45000}

    await abgelehnt(pw, "anna", "/zeiten/deckel", {"ids": [gedeckelt[0]["id"]], "ende": "2026-10-28T09:00"}, 400,
                    "Das Ende muss zwischen Beginn und Stopp der Sitzung liegen")
    a = await ok(pw, "anna", "/zeiten/deckel", {"ids": [gedeckelt[1]["id"]], "ende": "2026-10-28T02:00"})
    assert a["meldung"] == "Ende auf 02:00 gesetzt, 6:00 gebucht; Rückfrage erledigt"
    neu = [e for e in await eintraege(pw, "anna", k) if e["datum"] >= "2026-10-27" and e["von"] >= "20:00" or e["datum"] == "2026-10-28"]
    assert [(e["datum"], e["von"], e["bis"], e.get("gedeckelt")) for e in neu] == [
        ("2026-10-27", "20:00", "24:00", None), ("2026-10-28", "00:00", "02:00", None)]

    # Rückgängig bringt die gedeckelte Sitzung genau zurück
    await ok(pw, "anna", f"/rueckgaengig/{a['rueckgaengig']}")
    assert {e["id"] for e in await eintraege(pw, "anna", k) if e.get("gedeckelt")} == {e["id"] for e in gedeckelt}
    a = await ok(pw, "anna", "/zeiten/deckel/bestaetigen", {"ids": [gedeckelt[0]["id"]]})
    assert a["meldung"] == "12 Stunden bleiben gebucht, Rückfrage erledigt"
    assert not any(e.get("gedeckelt") for e in await eintraege(pw, "anna", k))


async def test_timer_enden_von_selbst(pw: Pinnwand):
    b, k = await zeitboard(pw)
    await ok(pw, "bert", "/timer/starten", {"karte": k["id"]})
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    vor(pw, 45)
    a = await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Erledigt")})
    assert a["meldung"] == "HAUS-1 erledigt; dein Timer ist gestoppt, 0:45 gebucht"
    s = await pw.stand("anna")
    assert s["timer"] == [] and sorted(e["konto"] for e in s["zeiteintraege"]) == ["1", "2"]
    verlauf = [v["text"] for v in next(c for c in s["karten"] if c["id"] == k["id"])["verlauf"]]
    assert "Timer von bert: 0:45 gebucht" in verlauf and "Timer: 0:45 gebucht" in verlauf
    await abgelehnt(pw, "anna", "/timer/starten", {"karte": k["id"]}, 400, "Auf einer erledigten Karte läuft kein Timer")

    zweite = await pw.karte("anna", b, "Keller")
    await ok(pw, "anna", "/timer/starten", {"karte": zweite["id"]})
    vor(pw, 10)
    a = await ok(pw, "anna", f"/karten/{zweite['id']}/art", {"art": "idee"})
    assert a["meldung"] == "HAUS-2 ist jetzt eine Idee; dein Timer ist gestoppt, 0:10 gebucht"
    await abgelehnt(pw, "anna", "/timer/starten", {"karte": zweite["id"]}, 400, "Eine Idee hat keine Zeiterfassung")

    dritte = await pw.karte("anna", b, "Dachrinne")
    await ok(pw, "anna", "/timer/starten", {"karte": dritte["id"]})
    vor(pw, 5)
    a = await ok(pw, "anna", "/karten/in-papierkorb", {"ids": [dritte["id"]]})
    assert a["meldung"].endswith("; dein Timer ist gestoppt, 0:05 gebucht")
    papierkorb = (await pw.stand("anna"))["papierkorb"][0]["karten"][0]
    assert papierkorb["verlauf"][-2]["text"] == "Timer: 0:05 gebucht"         # der Verlauf liegt mit im Papierkorb

    vierte = await pw.karte("anna", b, "Heizung")
    await ok(pw, "bert", "/timer/starten", {"karte": vierte["id"]})
    vor(pw, 5)
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"})
    assert (await pw.stand("bert"))["timer"] == []
    berts = [e for e in await eintraege(pw, "bert") if e["karte"] == vierte["id"]]
    assert [e["sekunden"] for e in berts] == [300]

    await ok(pw, "anna", "/timer/starten", {"karte": vierte["id"]})
    vor(pw, 5)
    a = await ok(pw, "anna", f"/boards/{b['id']}/module/zeiterfassung", {"an": False})
    assert a["meldung"] == "Zeiterfassung in Haushalt ausgeblendet; die Daten bleiben; dein Timer ist gestoppt, 0:05 gebucht"


async def test_timer_ohne_recht(pw: Pinnwand):
    b, k = await zeitboard(pw, rolle="leser")
    await abgelehnt(pw, "bert", "/timer/starten", {"karte": k["id"]}, 403, "Dir fehlt im Board Haushalt das Recht Eigene Zeit buchen")
    await ok(pw, "anna", f"/boards/{b['id']}/module/zeiterfassung", {"an": False})
    await abgelehnt(pw, "anna", "/timer/starten", {"karte": k["id"]}, 400, "Im Board Haushalt ist die Zeiterfassung aus")
    assert (await pw.post("anna", "/timer/stoppen")).json()["meldung"] is None     # kein Timer: nichts geschieht


# ═══ Zeiten buchen und ändern ═════════════════════════════════════════════════════════════════════════════════════════

async def test_tageszeit_und_ticketzeit(pw: Pinnwand):
    _, k = await zeitboard(pw)
    await ok(pw, "bert", "/zeiten", {"karte": k["id"], "datum": "2026-10-26", "sekunden": 3600})
    a = await ok(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 1800, "notiz": " Rahmen "})
    assert a["meldung"] == "0:30 auf HAUS-1 gebucht (Di 27.10.)"
    a = await ok(pw, "anna", "/zeiten/tag", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 3600})
    assert a["meldung"] == "HAUS-1 Di 27.10.: 0:30 auf 1:00 gesetzt"
    assert sorted((e["herkunft"], e["sekunden"]) for e in await eintraege(pw, "anna", k) if e["konto"] == "1") == [
        ("hand", 1800), ("korrektur", 1800)]
    # weniger: die Korrektur geht zuerst, dann wird der nachgetragene gekürzt
    await ok(pw, "anna", "/zeiten/tag", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 1200})
    assert [(e["herkunft"], e["sekunden"]) for e in await eintraege(pw, "anna", k) if e["konto"] == "1"] == [("hand", 1200)]

    # Ticketzeit: die Summe aller Einträge (anna sieht berts Stunde) auf 2:00 setzen bucht die Differenz heute bei anna
    a = await ok(pw, "anna", "/zeiten/ticketzeit", {"karte": k["id"], "sekunden": 7200})
    assert a["meldung"] == "HAUS-1 Di 27.10.: 0:20 auf 1:00 gesetzt"
    assert sum(e["sekunden"] for e in await eintraege(pw, "anna", k)) == 7200
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    await abgelehnt(pw, "anna", "/zeiten/ticketzeit", {"karte": k["id"], "sekunden": 0}, 400,
                    "Solange dein Timer auf dieser Karte läuft, lässt sich ihre Zeit nicht setzen")
    await abgelehnt(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 0}, 400,
                    "Die Dauer muss größer als null sein")
    await abgelehnt(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "27.10.", "sekunden": 60}, 400, "Das ist kein gültiger Tag")


async def test_eintrag_aendern_und_loeschen(pw: Pinnwand):
    _, k = await zeitboard(pw)
    await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
    vor(pw, 60)
    await ok(pw, "anna", "/timer/stoppen")
    [e] = await eintraege(pw, "anna", k)
    a = await ok(pw, "anna", f"/zeiten/{e['id']}/dauer", {"sekunden": 2700})
    assert a["meldung"] == "HAUS-1 Di 27.10.: 1:00 auf 0:45 geändert"
    [e] = await eintraege(pw, "anna", k)
    assert (e["von"], e["bis"], e["sekunden"]) == ("10:00", "10:45", 2700)          # das Ende rückt mit
    assert (await ok(pw, "anna", f"/zeiten/{e['id']}/datum", {"datum": "2026-10-23"}))["meldung"] == (
        "HAUS-1: Zeiteintrag (0:45) von Di 27.10. auf Fr 23.10. gelegt")
    a = await ok(pw, "anna", f"/zeiten/{e['id']}/notiz", {"notiz": "Rahmen innen"})
    assert a["meldung"] is None and a["rueckgaengig"] is None

    # bert ist Mitglied: fremde Einträge ändern darf er ohne "Zeiten anderer bearbeiten" nicht
    await abgelehnt(pw, "bert", f"/zeiten/{e['id']}/dauer", {"sekunden": 60}, 403,
                    "Dir fehlt im Board Haushalt das Recht Zeiten anderer bearbeiten")
    vorher = (await eintraege(pw, "anna", k))[0]
    r = await pw.delete("anna", f"/zeiten/{e['id']}")
    assert r.json()["meldung"] == "Zeiteintrag (0:45, Fr 23.10.) gelöscht"
    assert await eintraege(pw, "anna", k) == []
    await ok(pw, "anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    [zurueck] = await eintraege(pw, "anna", k)
    assert {**zurueck, "fassung": 0} == {**vorher, "fassung": 0}


# ═══ Wer was sieht ════════════════════════════════════════════════════════════════════════════════════════════════════

async def test_zeit_anderer_nur_mit_recht(pw: Pinnwand):
    b, k = await zeitboard(pw)
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "cora", "rolle": "leser"})
    await pw.anmelden("cora")
    await pw.stand("cora")
    hub = pw.app.state.dienste.ereignisse
    with hub.abo("2") as bert, hub.abo("3") as cora:
        await ok(pw, "anna", "/timer/starten", {"karte": k["id"]})
        teil = await asyncio.wait_for(anext(bert), 1)
        assert {g.tabelle for g in teil.geaendert} == {"timer", "karten"}     # bert sieht Zeiten anderer
        teil = await asyncio.wait_for(anext(cora), 1)
        assert {g.tabelle for g in teil.geaendert} == {"karten"}             # cora als Leser nur die Karte
    vor(pw, 30)
    await ok(pw, "anna", "/timer/stoppen")
    assert [e["konto"] for e in (await pw.stand("bert"))["zeiteintraege"]] == ["1"]
    assert (await pw.stand("cora"))["zeiteintraege"] == [] and (await pw.stand("cora"))["timer"] == []

    # die Rolle Mitglied verliert das Recht: bert sieht nur noch seine eigene Zeit
    await ok(pw, "anna", f"/boards/{b['id']}/rollen/mitglied/recht", {"recht": "zeit.andere.sehen", "an": False})
    await ok(pw, "bert", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 600})
    assert [e["konto"] for e in (await pw.stand("bert"))["zeiteintraege"]] == ["2"]
    # Ticketzeit ohne das Recht: nur die eigene Zeit zählt
    await ok(pw, "bert", "/zeiten/ticketzeit", {"karte": k["id"], "sekunden": 900})
    berts = (await pw.stand("bert"))["zeiteintraege"]
    assert sum(e["sekunden"] for e in berts) == 900 and {e["konto"] for e in berts} == {"2"}


async def test_kartennamen_ausserhalb_des_stands(pw: Pinnwand):
    b, k = await zeitboard(pw)
    await ok(pw, "bert", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 600})
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"})
    s = await pw.stand("bert")
    assert s["boards"] == [] and [e["karte"] for e in s["zeiteintraege"]] == [k["id"]]
    assert s["kartennamen"] == [{"karte": k["id"], "board": b["id"], "schluessel": "HAUS-1", "titel": "Fenster putzen"}]


# ═══ Arbeitszeit ══════════════════════════════════════════════════════════════════════════════════════════════════════

KONTO = {"ab": "2026-01-01", "wochenstunden": 40, "tage": [5, 1, 2, 3, 4], "bundesland": "Nordrhein-Westfalen",
         "urlaubsanspruch": 30, "resturlaubVorjahr": 2, "halbtage": [{"monat": 12, "tag": 24, "name": "Heiligabend"}]}


async def test_zeitkonto_und_abwesenheiten(pw: Pinnwand):
    b, _ = await zeitboard(pw)
    await abgelehnt(pw, "anna", "/zeitkonten", KONTO, 403, "Arbeitszeit und Urlaub sind in keinem deiner Boards eingeschaltet")
    await ok(pw, "anna", f"/boards/{b['id']}/module/arbeitszeit", {"an": True})
    a = await ok(pw, "anna", "/zeitkonten", KONTO)
    assert a["meldung"] == "Zeitkonto gespeichert, gilt ab Do 01.01.2026; frühere Tage behalten ihr Soll"
    [z] = (await pw.stand("anna"))["zeitkonten"]
    assert z["tage"] == [1, 2, 3, 4, 5] and z["resturlaubVorjahr"] == 2
    await ok(pw, "anna", "/zeitkonten", {**KONTO, "wochenstunden": 32})
    [z2] = (await pw.stand("anna"))["zeitkonten"]                         # gleicher Tag: dieselbe Fassung, ersetzt
    assert z2["id"] == z["id"] and z2["wochenstunden"] == 32
    await abgelehnt(pw, "anna", "/zeitkonten", {**KONTO, "bundesland": "Atlantis"}, 400, "Unbekanntes Bundesland")

    a = await ok(pw, "anna", "/abwesenheiten", {"von": "2026-11-16", "bis": "2026-11-20", "art": "urlaub"})
    assert a["meldung"] == "Urlaub eingetragen: Mo 16.11. bis Fr 20.11.2026"
    a = await ok(pw, "anna", "/abwesenheiten", {"von": "2026-11-18", "bis": "2026-11-18", "art": "krank", "anteil": 0.5})
    assert a["meldung"] == "Halber Tag Krank eingetragen: Mi 18.11.2026; 1 Abwesenheit angepasst, ihre übrigen Tage bleiben"
    # der Urlaub drumherum bleibt vor und nach dem Krankentag stehen
    assert sorted((x["von"], x["bis"], x["art"]) for x in (await pw.stand("anna"))["abwesenheiten"]) == [
        ("2026-11-16", "2026-11-17", "urlaub"), ("2026-11-18", "2026-11-18", "krank"), ("2026-11-19", "2026-11-20", "urlaub")]
    a = await ok(pw, "anna", "/abwesenheiten", {"von": "2026-11-16", "bis": "2026-11-17", "art": "krank"})
    assert a["meldung"] == "Krank eingetragen: Mo 16.11. bis Di 17.11.2026; ersetzt 1 Abwesenheit"
    await ok(pw, "anna", f"/abwesenheiten/entfernen", {"ids": [x["id"] for x in (await pw.stand("anna"))["abwesenheiten"]
                                                         if x["von"] != "2026-11-18"]})
    await abgelehnt(pw, "anna", "/abwesenheiten", {"von": "2026-11-18", "bis": "2026-11-19", "art": "urlaub", "anteil": 0.3},
                    400, "Ein Tag zählt ganz oder halb")
    await abgelehnt(pw, "anna", "/abwesenheiten", {"von": "2026-11-19", "bis": "2026-11-18", "art": "urlaub"}, 400,
                    "Bis liegt vor von")
    [abw] = (await pw.stand("anna"))["abwesenheiten"]
    # bert sieht annas Abwesenheit (Mitglied hat "Abwesenheiten sehen"), entfernen darf er sie nicht
    assert [x["id"] for x in (await pw.stand("bert"))["abwesenheiten"]] == [abw["id"]]
    assert [x["konto"] for x in (await pw.stand("bert"))["zeitkonten"]] == ["1"]
    await abgelehnt(pw, "bert", "/abwesenheiten/entfernen", {"ids": [abw["id"]]}, 403,
                    "Du kannst nur deine eigenen Abwesenheiten entfernen")
    a = await ok(pw, "anna", "/abwesenheiten/entfernen", {"ids": [abw["id"]]})
    assert a["meldung"] == "Halber Tag Krank Mi 18.11.2026 entfernt"


async def test_team(pw: Pinnwand):
    b, k = await zeitboard(pw)
    await ok(pw, "anna", f"/boards/{b['id']}/module/arbeitszeit", {"an": True})
    anderes = await pw.board("bert", name="Werkstatt", kuerzel="WERK")
    w = await pw.karte("bert", anderes, "Hobeln")
    await ok(pw, "bert", "/zeiten", {"karte": w["id"], "datum": "2026-10-26", "sekunden": 3600})   # aus einem anderen Board
    await ok(pw, "bert", "/zeiten", {"karte": k["id"], "datum": "2026-10-26", "sekunden": 1800})
    await ok(pw, "anna", "/zeiten", {"karte": k["id"], "datum": "2026-10-27", "sekunden": 600})
    r = await pw.get("anna", f"/team/{b['id']}", params={"von": "2026-10-26", "bis": "2026-10-27"})
    assert r.json() == {"personen": ["1", "2"], "ist": {"1": {"2026-10-27": 600}, "2": {"2026-10-26": 5400}}}
    await ok(pw, "anna", f"/boards/{b['id']}/rollen/mitglied/recht", {"recht": "abwesenheit.sehen", "an": False})
    r = await pw.get("bert", f"/team/{b['id']}", params={"von": "2026-10-26", "bis": "2026-10-27"})
    assert r.json() == {"personen": ["2"], "ist": {"2": {"2026-10-26": 5400}}}
    r = await pw.get("anna", f"/team/{b['id']}", params={"von": "2026-10-27", "bis": "2026-10-26"})
    assert r.status_code == 400
