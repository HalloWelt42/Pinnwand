"""Papierkorb und Archiv über die Schnittstelle: Karten, Spalten und Boards hineinlegen und an die alte Stelle
wiederherstellen, Gruppen, Rechte, Rückgängig, Ereignisse an frühere Mitglieder, das Kürzel eines gelöschten Boards,
endgültig entfernen ohne Rückweg mit dem Namen jeder Karte in `entfernt`, das Archiv seitenweise."""

from __future__ import annotations

import asyncio
from datetime import datetime

from conftest import Pinnwand


def spalte(b: dict, name: str) -> str:
    return next(s["id"] for s in b["spalten"] if s["name"] == name)


async def karte(pw: Pinnwand, wer: str, schluessel: str) -> dict:
    r = await pw.get(wer, f"/karten/{schluessel}")
    assert r.status_code == 200, r.text
    return r.json()


async def reihe(pw: Pinnwand, wer: str, b: dict, name: str) -> list[str]:
    """Schlüssel der Karten einer Spalte in ihrer Reihenfolge."""
    karten = [k for k in (await pw.stand(wer))["karten"] if k["spalte"] == spalte(b, name)]
    return [k["schluessel"] for k in sorted(karten, key=lambda k: k["reihe"])]


async def wegwerfen(pw: Pinnwand, wer: str, *karten: dict):
    return await pw.post(wer, "/karten/in-papierkorb", {"ids": [k["id"] for k in karten]})


async def eintrag(pw: Pinnwand, wer: str, schluessel: str) -> dict:
    """Der Eintrag im Papierkorb, der die Karte mit diesem Schlüssel hält."""
    return next(e for e in (await pw.stand(wer))["papierkorb"] if any(k["schluessel"] == schluessel for k in e["karten"]))


async def direkt(pw: Pinnwand, tabelle: str, daten: dict) -> None:
    """Schreibt eine Zeile an den Anwendungsfällen vorbei: für Zustände, die andere Bereiche herstellen (Ordner, Spalten)."""
    await pw.app.state.dienste.anwendung.v.transaktion(lambda s: s.schreib(tabelle, daten))


async def zeilen(pw: Pinnwand, tabelle: str) -> list[dict]:
    return await pw.app.state.dienste.anwendung.v.alle(tabelle)


# --- Karten ------------------------------------------------------------------------------------------------------

async def test_karte_in_papierkorb_und_zurueck(pw: Pinnwand):
    b = await pw.board("anna")
    k = [await pw.karte("anna", b, t) for t in ("Fenster", "Keller", "Dach")]
    r = await wegwerfen(pw, "anna", k[1])
    assert r.json()["meldung"] == "1 Karte im Papierkorb, mit Kommentaren und Anhängen wiederherstellbar"
    assert r.json()["rueckgaengig"]
    s = await pw.stand("anna")
    assert [x["schluessel"] for x in s["karten"]] == ["HAUS-3", "HAUS-1"]             # neueste oben
    [e] = s["papierkorb"]
    assert (e["art"], e["board"], e["von"], e["am"]) == ("karte", b["id"], "1", "2026-10-27T10:00:00")
    assert e["stelle"] == {"spalte": spalte(b, "Offen"), "platz": 1}
    assert e["karten"][0]["schluessel"] == "HAUS-2"
    assert e["karten"][0]["verlauf"][-1]["text"] == "hat sie in den Papierkorb gelegt"
    assert (await pw.get("anna", "/karten/HAUS-2")).status_code == 404

    r = await pw.post("anna", f"/papierkorb/{e['id']}/wiederherstellen")
    assert r.json()["meldung"] == "HAUS-2 wiederhergestellt, an der alten Stelle in Offen in Haushalt"
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-3", "HAUS-2", "HAUS-1"]
    assert (await pw.stand("anna"))["papierkorb"] == []
    assert (await karte(pw, "anna", "HAUS-2"))["verlauf"][-1]["text"] == "hat sie wiederhergestellt"
    # Rückgängig legt sie wieder hinein, der Eintrag ist derselbe
    assert (await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")).status_code == 200
    assert [x["id"] for x in (await pw.stand("anna"))["papierkorb"]] == [e["id"]]
    r = await pw.post("anna", "/papierkorb/p-gibt-es-nicht/wiederherstellen")
    assert (r.status_code, r.json()["detail"]) == (404, "Das liegt nicht (mehr) im Papierkorb")


async def test_rueckgaengig_bringt_die_karte_genau_zurueck(pw: Pinnwand):
    b = await pw.board("anna")
    k = await pw.karte("anna", b, "Fenster")
    r = await wegwerfen(pw, "anna", k)
    r = await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert r.json()["meldung"].startswith("Rückgängig: 1 Karte im Papierkorb")
    s = await pw.stand("anna")
    assert s["papierkorb"] == [] and [{**x, "fassung": 0} for x in s["karten"]] == [{**k, "fassung": 0}]


async def test_mehrere_karten_je_ein_eintrag(pw: Pinnwand):
    b = await pw.board("anna")
    k = [await pw.karte("anna", b, t) for t in ("A", "B", "C", "D")]
    r = await wegwerfen(pw, "anna", k[3], k[2])                                      # die obersten zwei
    assert r.json()["meldung"] == "2 Karten im Papierkorb, mit Kommentaren und Anhängen wiederherstellbar"
    erste, zweite = await eintrag(pw, "anna", "HAUS-4"), await eintrag(pw, "anna", "HAUS-3")
    assert (erste["stelle"]["platz"], zweite["stelle"]["platz"]) == (0, 0)          # nacheinander herausgenommen
    for e in (zweite, erste):
        await pw.post("anna", f"/papierkorb/{e['id']}/wiederherstellen")
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-4", "HAUS-3", "HAUS-2", "HAUS-1"]

    andere = await pw.board("anna", "Werkstatt", "WERK")
    fremd = await pw.karte("anna", andere, "Bohrer")
    r = await wegwerfen(pw, "anna", k[2], fremd)
    assert (r.status_code, r.json()["detail"]) == (400, "Sammelaktionen gehen nur mit Karten eines Boards")
    assert (await pw.post("anna", "/karten/in-papierkorb", {"ids": []})).status_code == 400


async def test_gruppen(pw: Pinnwand):
    b = await pw.board("anna")
    a, c, d = [await pw.karte("anna", b, t) for t in ("A", "B", "C")]
    # zu zweit endet die Gruppe (wie beim Lösen); zurück kommt die Karte ohne Verknüpfung
    await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    await wegwerfen(pw, "anna", a)
    s = await pw.stand("anna")
    assert s["gruppen"] == [] and all("gruppe" not in x for x in s["karten"])
    await pw.post("anna", f"/papierkorb/{s['papierkorb'][0]['id']}/wiederherstellen")
    assert "gruppe" not in await karte(pw, "anna", "HAUS-1")
    # zu dritt bleibt sie, und die Karte kommt in sie zurück
    await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    await pw.post("anna", f"/karten/{c['id']}/verknuepfen", {"mit": d["id"]})
    await wegwerfen(pw, "anna", a)
    [g] = (await pw.stand("anna"))["gruppen"]
    await pw.post("anna", f"/papierkorb/{(await eintrag(pw, 'anna', 'HAUS-1'))['id']}/wiederherstellen")
    verknuepft = {x["schluessel"] for x in (await pw.stand("anna"))["karten"] if x.get("gruppe") == g["id"]}
    assert verknuepft == {"HAUS-1", "HAUS-2", "HAUS-3"}


async def test_karte_ohne_ihre_spalte_kommt_in_die_erste(pw: Pinnwand):
    b = await pw.board("anna")
    k = await pw.karte("anna", b, "Fenster", spalte=spalte(b, "Dran"))
    await wegwerfen(pw, "anna", k)
    await pw.post("anna", f"/boards/{b['id']}/spalten/{spalte(b, 'Dran')}/loeschen")
    r = await pw.post("anna", f"/papierkorb/{(await eintrag(pw, 'anna', 'HAUS-1'))['id']}/wiederherstellen")
    assert r.json()["meldung"] == "HAUS-1 wiederhergestellt, in Offen in Haushalt; ihre Spalte gibt es nicht mehr"
    assert (await karte(pw, "anna", "HAUS-1"))["spalte"] == spalte(b, "Offen")


# --- Rechte ------------------------------------------------------------------------------------------------------

async def test_rechte(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}, {"kellerwolke": "cora", "rolle": "leser"}])
    for name in ("bert", "cora"):
        await pw.anmelden(name)
        await pw.stand(name)
    k = await pw.karte("anna", b, "Fenster")
    r = await wegwerfen(pw, "cora", k)
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Karten löschen")
    assert (await wegwerfen(pw, "bert", k)).status_code == 200                       # ein Mitglied darf löschen
    e = (await pw.stand("bert"))["papierkorb"][0]
    assert (await pw.post("cora", f"/papierkorb/{e['id']}/wiederherstellen")).status_code == 403
    r = await pw.post("bert", "/papierkorb/entfernen", {"ids": [e["id"]]})
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Papierkorb leeren")
    assert (await pw.post("bert", f"/boards/{b['id']}/papierkorb/leeren")).status_code == 403
    r = await pw.post("bert", f"/boards/{b['id']}/spalten/{spalte(b, 'Dran')}/loeschen")
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Board verwalten")
    assert (await pw.post("bert", f"/boards/{b['id']}/in-papierkorb")).status_code == 403
    assert (await pw.post("bert", f"/papierkorb/{e['id']}/wiederherstellen")).status_code == 200
    # wer nicht Mitglied ist, kommt an nichts heran
    werk = await pw.board("anna", "Werkstatt", "WERK")
    geheim = await pw.karte("anna", werk, "Geheim")
    assert (await wegwerfen(pw, "bert", geheim)).status_code == 403
    await wegwerfen(pw, "anna", geheim)
    e = await eintrag(pw, "anna", "WERK-1")
    assert (await pw.post("bert", f"/papierkorb/{e['id']}/wiederherstellen")).status_code == 403
    assert (await pw.post("bert", "/papierkorb/entfernen", {"ids": [e["id"]]})).status_code == 403
    assert all(x["board"] != werk["id"] for x in (await pw.stand("bert"))["papierkorb"])


# --- Spalten -----------------------------------------------------------------------------------------------------

async def test_spalte_mit_karten_in_den_papierkorb(pw: Pinnwand):
    b = await pw.board("anna")
    dran = spalte(b, "Dran")
    x, y = await pw.karte("anna", b, "Fenster", spalte=dran), await pw.karte("anna", b, "Rahmen", spalte=dran)
    await pw.post("anna", f"/karten/{x['id']}/verknuepfen", {"mit": y["id"]})
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{dran}/loeschen")
    assert r.json()["meldung"] == "Spalte Dran im Papierkorb mit 2 Karten"
    s = await pw.stand("anna")
    assert [x["name"] for x in s["boards"][0]["spalten"]] == ["Offen", "Erledigt"]
    assert s["karten"] == [] and s["gruppen"] == []
    [e] = s["papierkorb"]
    assert (e["art"], e["spalte"]["name"], e["stelle"]) == ("spalte", "Dran", {"platz": 1})
    assert [k["schluessel"] for k in e["karten"]] == ["HAUS-2", "HAUS-1"]

    r = await pw.post("anna", f"/papierkorb/{e['id']}/wiederherstellen")
    assert r.json()["meldung"] == "Spalte Dran wiederhergestellt, an der alten Stelle in Haushalt"
    s = await pw.stand("anna")
    assert [x["name"] for x in s["boards"][0]["spalten"]] == ["Offen", "Dran", "Erledigt"]
    assert await reihe(pw, "anna", b, "Dran") == ["HAUS-2", "HAUS-1"]
    [g] = s["gruppen"]                                                  # beide lagen in der Spalte: wieder verknüpft
    assert {k.get("gruppe") for k in s["karten"]} == {g["id"]}


async def test_spalte_loeschen_karten_wandern_vorher(pw: Pinnwand):
    b = await pw.board("anna")
    dran, offen = spalte(b, "Dran"), spalte(b, "Offen")
    await pw.karte("anna", b, "Fenster")
    k2 = await pw.karte("anna", b, "Keller", spalte=dran)
    await pw.karte("anna", b, "Dach", spalte=dran)
    fertig = await pw.karte("anna", b, "Rahmen", spalte=spalte(b, "Erledigt"))
    await pw.post("anna", f"/karten/{k2['id']}/verknuepfen", {"mit": fertig["id"]})
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{dran}/loeschen", {"nach": offen})
    assert r.json()["meldung"] == "Spalte Dran im Papierkorb; 2 Karten nach Offen; 1 verknüpfte zieht mit"
    assert set(await reihe(pw, "anna", b, "Offen")) == {"HAUS-1", "HAUS-2", "HAUS-3", "HAUS-4"}
    assert (await karte(pw, "anna", "HAUS-2"))["verlauf"][-1]["text"] == "hat sie von Dran nach Offen verschoben"
    [e] = (await pw.stand("anna"))["papierkorb"]
    assert e["karten"] == []
    # Rückgängig: die Spalte steht wieder, die Karten sind zurück
    await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    s = await pw.stand("anna")
    assert [x["name"] for x in s["boards"][0]["spalten"]] == ["Offen", "Dran", "Erledigt"] and s["papierkorb"] == []
    assert await reihe(pw, "anna", b, "Dran") == ["HAUS-3", "HAUS-2"]


async def test_spalte_regeln(pw: Pinnwand):
    b = await pw.board("anna")
    dran = spalte(b, "Dran")

    async def loeschen(s: str, daten: dict | None = None):
        return await pw.post("anna", f"/boards/{b['id']}/spalten/{s}/loeschen", daten)

    for s, daten, status, meldung in [
        (spalte(b, "Erledigt"), None, 400, "Die Erledigt-Spalte bleibt; mach erst eine andere Spalte zur Erledigt-Spalte"),
        ("s-fremd", None, 404, "Diese Spalte gibt es in diesem Board nicht"),
        (dran, {"nach": dran}, 400, "Die Karten können nur in eine andere Spalte dieses Boards"),
        (dran, {"nach": "s-fremd"}, 400, "Die Karten können nur in eine andere Spalte dieses Boards"),
    ]:
        r = await loeschen(s, daten)
        assert (r.status_code, r.json()["detail"]) == (status, meldung)
    # ein Board mit nur noch einer Spalte
    await direkt(pw, "boards", {**b, "spalten": [x for x in b["spalten"] if x["name"] == "Offen"]})
    r = await loeschen(spalte(b, "Offen"))
    assert (r.status_code, r.json()["detail"]) == (400, "Die letzte Spalte bleibt: ein Board braucht mindestens eine")


# --- Boards ------------------------------------------------------------------------------------------------------

async def test_board_in_papierkorb_und_zurueck(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    a, c = await pw.karte("anna", b, "Fenster"), await pw.karte("anna", b, "Rahmen")
    await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    await wegwerfen(pw, "anna", await pw.karte("anna", b, "Alt"))
    for wer, konto in (("anna", "1"), ("bert", "2")):
        await direkt(pw, "ordner", {"id": f"o-{wer}", "konto": konto, "name": "Zuhause", "boards": [b["id"]], "reihe": 1})

    hub = pw.app.state.dienste.ereignisse
    with hub.abo("2") as bert:                                          # bert ist danach kein Mitglied mehr
        r = await pw.post("anna", f"/boards/{b['id']}/in-papierkorb")
        teil = await asyncio.wait_for(anext(bert), 1)
    assert r.json()["meldung"] == "Haushalt mit 2 Karten im Papierkorb; wiederherstellen unter Einstellungen, Papierkorb"
    assert {(g.tabelle, g.daten is None) for g in teil.geaendert} >= {("boards", True), ("karten", True), ("papierkorb", False)}

    s = await pw.stand("anna")
    assert (s["boards"], s["karten"], s["gruppen"]) == ([], [], [])
    assert s["ordner"][0]["boards"] == []
    [e] = s["papierkorb"]                                               # der Eintrag der Karte wartet mit dem Board
    assert (e["art"], e["inhalt"]["board"]["name"], len(e["karten"])) == ("board", "Haushalt", 2)
    assert len(e["inhalt"]["gruppen"]) == 1 and set(e["inhalt"]["ordner"]) == {"o-anna", "o-bert"}
    s = await pw.stand("bert")
    assert s["boards"] == [] and s["papierkorb"] == [] and s["ordner"][0]["boards"] == []

    # das Kürzel bleibt vergeben
    r = await pw.post("anna", "/boards", {"vorlage": "v-aufgaben", "name": "Neu", "kuerzel": "HAUS"})
    assert (r.status_code, r.json()["detail"]) == (409, "HAUS ist schon vergeben, an das Board Haushalt im Papierkorb.")
    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "cora"}])
    await pw.anmelden("cora")
    r = await pw.post("cora", "/boards", {"vorlage": "v-aufgaben", "name": "Meins", "kuerzel": "HAUS"})
    assert r.json()["detail"] == "HAUS ist schon vergeben, an ein Board, das du nicht siehst."

    r = await pw.post("bert", f"/papierkorb/{e['id']}/wiederherstellen")
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Board verwalten")
    r = await pw.post("anna", f"/papierkorb/{e['id']}/wiederherstellen")
    assert r.json()["meldung"] == "Board Haushalt wiederhergestellt, mit 2 Karten"
    s = await pw.stand("anna")
    assert b["id"] in {x["id"] for x in s["boards"]} and len(s["karten"]) == 2 and len(s["gruppen"]) == 1
    assert [x["art"] for x in s["papierkorb"]] == ["karte"] and s["ordner"][0]["boards"] == [b["id"]]
    assert (await pw.stand("bert"))["ordner"][0]["boards"] == [b["id"]]
    assert (await pw.karte("anna", b, "Dach"))["schluessel"] == "HAUS-4"   # die Nummern laufen weiter


async def test_board_rueckgaengig(pw: Pinnwand):
    b = await pw.board("anna")
    await pw.karte("anna", b, "Fenster")
    r = await pw.post("anna", f"/boards/{b['id']}/in-papierkorb")
    assert (await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")).status_code == 200
    s = await pw.stand("anna")
    assert [x["id"] for x in s["boards"]] == [b["id"]] and len(s["karten"]) == 1 and s["papierkorb"] == []
    assert (await pw.karte("anna", b, "Dach"))["schluessel"] == "HAUS-2"


# --- Endgültig entfernen -----------------------------------------------------------------------------------------

async def test_endgueltig_entfernen(pw: Pinnwand):
    b = await pw.board("anna")
    k = [await pw.karte("anna", b, t) for t in ("Fenster", "Keller", "Dach")]
    await wegwerfen(pw, "anna", k[0])
    await wegwerfen(pw, "anna", k[1])
    erste = await eintrag(pw, "anna", "HAUS-1")
    r = await pw.post("anna", "/papierkorb/entfernen", {"ids": [erste["id"]]})
    assert (r.json()["meldung"], r.json()["rueckgaengig"]) == ("HAUS-1 endgültig entfernt", None)
    s = await pw.stand("anna")
    assert s["entfernt"] == [{"id": k[0]["id"], "karte": k[0]["id"], "board": b["id"], "schluessel": "HAUS-1",
                              "titel": "Fenster", "am": "2026-10-27T10:00:00", "fassung": 1}]
    assert [x["karten"][0]["schluessel"] for x in s["papierkorb"]] == ["HAUS-2"]
    assert (await pw.post("anna", "/papierkorb/entfernen", {"ids": [erste["id"]]})).status_code == 404

    await wegwerfen(pw, "anna", k[2])
    r = await pw.post("anna", f"/boards/{b['id']}/papierkorb/leeren")
    assert r.json()["meldung"] == "Papierkorb von Haushalt geleert: 2 Einträge endgültig entfernt"
    assert r.json()["rueckgaengig"] is None
    s = await pw.stand("anna")
    assert s["papierkorb"] == [] and {x["schluessel"] for x in s["entfernt"]} == {"HAUS-1", "HAUS-2", "HAUS-3"}
    assert (await pw.post("anna", f"/boards/{b['id']}/papierkorb/leeren")).json()["meldung"] is None


async def test_board_endgueltig_entfernen(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": "besitzer"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    await pw.karte("anna", b, "Fenster")
    await wegwerfen(pw, "anna", await pw.karte("anna", b, "Alt"))
    await pw.post("anna", f"/boards/{b['id']}/in-papierkorb")
    [e] = (await pw.stand("anna"))["papierkorb"]
    # auch ohne die Zeile des Boards erfahren seine früheren Mitglieder, dass der Eintrag weg ist
    with pw.app.state.dienste.ereignisse.abo("2") as bert:
        r = await pw.post("anna", "/papierkorb/entfernen", {"ids": [e["id"]]})
        teil = await asyncio.wait_for(anext(bert), 1)
    assert any(g.tabelle == "papierkorb" and g.id == e["id"] and g.daten is None for g in teil.geaendert)
    assert r.json()["meldung"] == "Board Haushalt endgültig entfernt"
    # mit dem Board gehen der Eintrag seiner Karte und seine Laufnummer; jede Karte behält ihren Namen
    assert await zeilen(pw, "papierkorb") == [] and await zeilen(pw, "laufnummern") == []
    assert {x["schluessel"] for x in await zeilen(pw, "entfernt")} == {"HAUS-1", "HAUS-2"}
    # das Kürzel ist wieder frei
    neu = await pw.board("anna", "Haus neu", "HAUS")
    assert neu["id"] != b["id"]


async def test_karte_sofort_endgueltig(pw: Pinnwand):
    """Ohne Papierkorb, ohne Rückweg, bestätigt mit dem Schlüssel; braucht dazu das Recht "Papierkorb leeren"."""
    from test_planung import mit_bert
    b = await mit_bert(pw)
    c = await pw.karte("anna", b, "Fenster")
    weg = f"/karten/{c['id']}/endgueltig"
    r = await pw.post("anna", weg, {"bestaetigung": "HAUS-2"})
    assert (r.status_code, r.json()["detail"]) == (400, "Zur Sicherheit den Schlüssel HAUS-1 eintippen")
    r = await pw.post("bert", weg, {"bestaetigung": "HAUS-1"})
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Papierkorb leeren")
    r = await pw.post("anna", weg, {"bestaetigung": " haus-1 "})
    assert (r.json()["meldung"], r.json()["rueckgaengig"]) == ("HAUS-1 endgültig gelöscht", None)
    s = await pw.stand("anna")
    assert not [x for x in s["karten"] if x["id"] == c["id"]] and s["papierkorb"] == []
    assert [x["schluessel"] for x in s["entfernt"]] == ["HAUS-1"]
    assert (await pw.post("anna", weg, {"bestaetigung": "HAUS-1"})).status_code == 404


async def test_board_sofort_endgueltig(pw: Pinnwand):
    """Mit allem, auch Serien und Terminen; bestätigt mit dem Kürzel; gebuchte Zeiten bleiben, das Kürzel ist frei."""
    from test_planung import mit_bert, runde
    b = await mit_bert(pw)
    await pw.karte("anna", b, "Fenster")
    await runde(pw, b)
    await pw.post("anna", "/termine", {"board": b["id"], "titel": "Abstimmung", "datum": "2026-10-28", "von": "14:00",
                                       "bis": "15:30", "teilnehmer": ["1"]})
    await direkt(pw, "zeiteintraege", {"id": "z-1", "konto": "1", "karte": "x", "board": b["id"], "datum": "2026-10-26",
                                       "sekunden": 600, "herkunft": "nachgetragen"})
    weg = f"/boards/{b['id']}/endgueltig"
    r = await pw.post("anna", weg, {"bestaetigung": "Haushalt"})
    assert (r.status_code, r.json()["detail"]) == (400, "Zur Sicherheit das Kürzel HAUS eintippen")
    r = await pw.post("bert", weg, {"bestaetigung": "HAUS"})
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Board verwalten")
    r = await pw.post("anna", weg, {"bestaetigung": "haus"})
    assert r.json()["meldung"].startswith("Haushalt mit ") and r.json()["meldung"].endswith("endgültig gelöscht; das Kürzel HAUS ist frei")
    assert r.json()["rueckgaengig"] is None
    for tabelle in ("boards", "karten", "papierkorb", "laufnummern", "serien", "termine"):
        assert await zeilen(pw, tabelle) == [], tabelle
    assert [z["id"] for z in await zeilen(pw, "zeiteintraege")] == ["z-1"]
    assert "HAUS-1" in {x["schluessel"] for x in await zeilen(pw, "entfernt")}
    assert (await pw.board("anna", "Haus neu", "HAUS"))["id"] != b["id"]


# --- Archiv ------------------------------------------------------------------------------------------------------

async def test_archiv_seitenweise(pw: Pinnwand):
    b = await pw.board("anna")
    for i, titel in enumerate(("Alt", "Mittel", "Neu")):
        pw.zeiger.zeit = datetime(2025, 1, 10 + i, 10, 0)
        k = await pw.karte("anna", b, titel)
        await pw.post("anna", f"/karten/{k['id']}/erledigen")
    pw.zeiger.zeit = datetime(2026, 10, 27, 10, 0)                        # mehr als 365 Tage später: im Archiv
    assert (await pw.stand("anna"))["karten"] == []
    r = await pw.get("anna", f"/boards/{b['id']}/archiv", params={"versatz": 0, "grenze": 2})
    assert r.json()["gesamt"] == 3 and [k["schluessel"] for k in r.json()["karten"]] == ["HAUS-3", "HAUS-2"]
    r = await pw.get("anna", f"/boards/{b['id']}/archiv", params={"versatz": 2, "grenze": 2})
    assert r.json()["gesamt"] == 3 and [k["schluessel"] for k in r.json()["karten"]] == ["HAUS-1"]
    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    assert (await pw.get("bert", f"/boards/{b['id']}/archiv")).status_code == 403


async def test_wiederhergestellt_passt_zum_board_von_heute(pw: Pinnwand):
    """Was es im Board inzwischen nicht mehr gibt (Label, Mitglied), trägt die wiederhergestellte Karte nicht mehr."""
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    await pw.post("anna", f"/boards/{b['id']}/labels", {"name": "Garten", "farbe": "minze"})
    label = next(x for x in (await pw.stand("anna"))["boards"] if x["id"] == b["id"])["labels"][0]["id"]
    k = await pw.karte("anna", b, "Hecke")
    await pw.post("anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"labels": [label], "zustaendig": ["1", "2"]}})
    await wegwerfen(pw, "anna", k)
    await pw.post("anna", f"/boards/{b['id']}/labels/{label}/loeschen")
    await pw.post("anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"})
    r = await pw.post("anna", f"/papierkorb/{(await eintrag(pw, 'anna', 'HAUS-1'))['id']}/wiederherstellen")
    assert r.status_code == 200, r.text
    c = await karte(pw, "anna", "HAUS-1")
    assert c["labels"] == [] and c["zustaendig"] == ["1"]
