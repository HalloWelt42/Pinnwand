"""Kern der Pinnwand über die Schnittstelle, wie die Oberfläche sie nutzt: Board aus Vorlage, Karten mit Nummern,
Verschieben (Platz, Grenze, Erledigt, verknüpfte ziehen mit), Rechte je Rolle, Einladen, Rückgängig, Ereignisse."""

from __future__ import annotations

import asyncio

from conftest import Pinnwand


def spalte(b: dict, name: str) -> str:
    return next(s["id"] for s in b["spalten"] if s["name"] == name)


async def reihe(pw: Pinnwand, wer: str, b: dict, name: str) -> list[str]:
    """Schlüssel der Karten einer Spalte in ihrer Reihenfolge."""
    karten = [k for k in (await pw.stand(wer))["karten"] if k["spalte"] == spalte(b, name)]
    return [k["schluessel"] for k in sorted(karten, key=lambda k: k["reihe"])]


async def karte(pw: Pinnwand, wer: str, schluessel: str) -> dict:
    r = await pw.get(wer, f"/karten/{schluessel}")
    assert r.status_code == 200, r.text
    return r.json()


# --- Start und Boards --------------------------------------------------------------------------------------------

async def test_erster_stand(pw: Pinnwand):
    s = await pw.stand("anna")
    assert s["ich"] == "1" and s["jetzt"] == "2026-10-27T10:00:00"
    assert [(k["kellerwolke"], k["kuerzel"]) for k in s["konten"]] == [("anna", "AN")]
    assert {v["id"] for v in s["vorlagen"]} == {"v-aufgaben", "v-projekt", "v-ideen"}
    assert s["boards"] == [] and s["karten"] == []


async def test_board_aus_vorlage(pw: Pinnwand):
    r = await pw.post("anna", "/boards", {"vorlage": "v-aufgaben", "name": "Haushalt", "kuerzel": "HAUS"})
    assert r.json()["meldung"] == "Board Haushalt angelegt, Karten heißen HAUS-1 und so weiter"
    b = (await pw.stand("anna"))["boards"][0]
    assert [s["name"] for s in b["spalten"]] == ["Offen", "Dran", "Erledigt"]
    assert [s.get("zeitfenster") for s in b["spalten"]] == [None, None, "heute"]
    assert b["mitglieder"] == [{"konto": "1", "kellerwolke": "anna", "rolle": "besitzer", "seit": "2026-10-27"}]
    assert [r["id"] for r in b["rollen"]] == ["besitzer", "mitglied", "leser"]
    assert b["module"]["zeiterfassung"] and b["module"]["serien"] and not b["module"]["arbeitszeit"]


async def test_board_abgelehnt(pw: Pinnwand):
    await pw.board("anna")
    faelle = [
        ({"name": "Zweites", "kuerzel": "HAUS"}, 409, "HAUS ist schon vergeben, an das Board Haushalt."),
        ({"name": "Zweites", "kuerzel": "1X"}, 400, "2 bis 6 Zeichen, vorne ein Buchstabe."),
        ({"name": "  ", "kuerzel": "ZWEI"}, 400, "Ein Board braucht einen Namen"),
        ({"name": "Zweites", "kuerzel": "ZWEI", "vorlage": "v-gibt-es-nicht"}, 404, "Diese Vorlage gibt es nicht"),
        ({"name": "Zweites", "kuerzel": "ZWEI", "ordner": "o-fremd"}, 404, "Diesen Ordner gibt es nicht"),
    ]
    for daten, status, meldung in faelle:
        r = await pw.post("anna", "/boards", {"vorlage": "v-aufgaben", **daten})
        assert (r.status_code, r.json()["detail"]) == (status, meldung)
    assert len((await pw.stand("anna"))["boards"]) == 1


# --- Karten ------------------------------------------------------------------------------------------------------

async def test_karten_nummern_laufen_nur_vorwaerts(pw: Pinnwand):
    b = await pw.board("anna")
    k1 = await pw.karte("anna", b, "Fenster putzen")
    assert (k1["schluessel"], k1["spalte"], k1["zustaendig"], k1["art"]) == ("HAUS-1", spalte(b, "Offen"), ["1"], "arbeit")
    assert k1["verlauf"] == [{"zeit": "2026-10-27T10:00:00", "von": "1", "text": "hat die Karte angelegt"}]
    r = await pw.post("anna", f"/boards/{b['id']}/karten", {"titel": "Keller"})
    assert r.json()["meldung"] == "HAUS-2 in Offen angelegt"
    assert (await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")).status_code == 200
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-1"]
    assert (await pw.karte("anna", b, "Dach"))["schluessel"] == "HAUS-3"          # HAUS-2 wird nie wieder vergeben
    assert (await pw.stand("anna"))["laufnummern"] == [{"id": b["id"], "board": b["id"], "zahl": 3, "fassung": 3}]


async def test_karte_abgelehnt(pw: Pinnwand):
    b = await pw.board("anna")
    for daten, meldung in [({"titel": " "}, "Eine Karte braucht einen Titel"),
                           ({"titel": "x" * 301}, "Der Titel ist länger als 300 Zeichen"),
                           ({"titel": "Steuer", "faellig": "2026-02-30"}, "2026-02-30 ist kein Tag (JJJJ-MM-TT)"),
                           ({"titel": "Steuer", "spalte": "s-fremd"}, "Diese Spalte gibt es in diesem Board nicht")]:
        r = await pw.post("anna", f"/boards/{b['id']}/karten", daten)
        assert (r.status_code, r.json()["detail"]) == (400, meldung)
    assert (await pw.post("anna", "/boards/b-fremd/karten", {"titel": "Steuer"})).status_code == 404


async def test_ideen_board_legt_ideen_an(pw: Pinnwand):
    b = await pw.board("anna", "Einfälle", "IDEE", vorlage="v-ideen")
    assert (await pw.karte("anna", b, "Gartenhaus"))["art"] == "idee"


# --- Verschieben -------------------------------------------------------------------------------------------------

async def test_verschieben_platz_und_erledigt(pw: Pinnwand):
    b = await pw.board("anna")
    for t in ("Fenster", "Keller", "Dach"):
        await pw.karte("anna", b, t)
    pw.zeiger.zeit = pw.zeiger.zeit.replace(hour=11)
    r = await pw.post("anna", f"/karten/{(await karte(pw, 'anna', 'HAUS-1'))['id']}/verschieben", {"nach": spalte(b, "Dran")})
    assert r.json()["meldung"] == "HAUS-1 nach Dran"
    k1 = await karte(pw, "anna", "HAUS-1")
    assert k1["bewegtAm"] == "2026-10-27T11:00:00" and k1["verlauf"][-1]["text"] == "hat sie von Offen nach Dran verschoben"

    k3 = await karte(pw, "anna", "HAUS-3")
    r = await pw.post("anna", f"/karten/{k3['id']}/verschieben", {"nach": spalte(b, "Offen"), "platz": 0})
    assert r.json()["meldung"] == "Offen neu geordnet"
    assert await reihe(pw, "anna", b, "Offen") == ["HAUS-3", "HAUS-2"]

    r = await pw.post("anna", f"/karten/{(await karte(pw, 'anna', 'HAUS-2'))['id']}/erledigen")
    assert r.json()["meldung"] == "HAUS-2 erledigt"
    assert (await karte(pw, "anna", "HAUS-2"))["abgeschlossen"] == "2026-10-27"
    # in Erledigt steht die Ordnung fest: nichts geschieht
    r = await pw.post("anna", f"/karten/{(await karte(pw, 'anna', 'HAUS-2'))['id']}/verschieben", {"nach": spalte(b, "Erledigt"), "platz": 0})
    assert r.json() == {"meldung": None, "rueckgaengig": None, "geaendert": []}
    # zurück in eine offene Spalte: kein Abschluss mehr
    await pw.post("anna", f"/karten/{(await karte(pw, 'anna', 'HAUS-2'))['id']}/verschieben", {"nach": spalte(b, "Offen")})
    assert "abgeschlossen" not in await karte(pw, "anna", "HAUS-2")


async def test_grenze_ist_nur_eine_warnung(pw: Pinnwand):
    b = await pw.board("anna", "Projekt", "PRO", vorlage="v-projekt")
    pruefung = spalte(b, "Prüfung")                                   # Grenze 3
    for i in range(4):
        r = await pw.post("anna", f"/boards/{b['id']}/karten", {"titel": f"Teil {i}", "spalte": pruefung})
    assert r.json()["meldung"] == "PRO-4 in Prüfung angelegt; Prüfung über der Grenze (4/3)"


async def test_sammel_verschieben(pw: Pinnwand):
    b = await pw.board("anna")
    ids = [(await pw.karte("anna", b, t))["id"] for t in ("Fenster", "Keller", "Dach")]
    r = await pw.post("anna", "/karten/sammel/verschieben", {"ids": ids, "nach": spalte(b, "Dran")})
    assert (r.status_code, r.json()["meldung"]) == (200, "3 Karten nach Dran")
    assert await reihe(pw, "anna", b, "Dran") == ["HAUS-1", "HAUS-2", "HAUS-3"]


async def test_enge_reihe_wird_neu_nummeriert(pw: Pinnwand):
    """Immer wieder an Platz 1: der Raum halbiert sich, bis die Spalte neu nummeriert; die Reihenfolge bleibt richtig."""
    b = await pw.board("anna")
    offen = spalte(b, "Offen")
    erste = await pw.karte("anna", b, "Anfang")
    zweite = await pw.karte("anna", b, "Zweite")
    neue = [await pw.karte("anna", b, f"Neu {i}") for i in range(36)]
    for k in neue:
        assert (await pw.post("anna", f"/karten/{k['id']}/verschieben", {"nach": offen, "platz": 1})).status_code == 200
    erwartet = [erste["schluessel"], *[k["schluessel"] for k in reversed(neue)], zweite["schluessel"]]
    assert await reihe(pw, "anna", b, "Offen") == erwartet
    reihen = [k["reihe"] for k in (await pw.stand("anna"))["karten"]]
    assert len(set(reihen)) == len(reihen)


async def test_verknuepfte_ziehen_mit(pw: Pinnwand):
    b = await pw.board("anna")
    a, c = await pw.karte("anna", b, "Fenster"), await pw.karte("anna", b, "Rahmen")
    r = await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    assert r.json()["meldung"] == "HAUS-1 und HAUS-2 verknüpft: ziehen zusammen, Zeit wird geteilt"
    gruppen = (await pw.stand("anna"))["gruppen"]
    assert len(gruppen) == 1 and gruppen[0]["board"] == b["id"]

    r = await pw.post("anna", f"/karten/{a['id']}/verschieben", {"nach": spalte(b, "Dran")})
    assert r.json()["meldung"] == "HAUS-1 nach Dran; 1 verknüpfte zieht mit"
    assert (await karte(pw, "anna", "HAUS-2"))["verlauf"][-1]["text"] == "mit verknüpfter Karte verschoben nach Dran"

    await pw.post("anna", f"/karten/{a['id']}/loesen")
    s = await pw.stand("anna")
    assert s["gruppen"] == [] and all("gruppe" not in k for k in s["karten"])

    idee = await pw.karte("anna", b, "Vielleicht", art="idee")
    r = await pw.post("anna", f"/karten/{a['id']}/verknuepfen", {"mit": idee["id"]})
    assert r.status_code == 400


async def test_gruppen_verschmelzen(pw: Pinnwand):
    b = await pw.board("anna")
    k = [await pw.karte("anna", b, t) for t in ("A", "B", "C", "D")]
    await pw.post("anna", f"/karten/{k[0]['id']}/verknuepfen", {"mit": k[1]["id"]})
    await pw.post("anna", f"/karten/{k[2]['id']}/verknuepfen", {"mit": k[3]["id"]})
    await pw.post("anna", f"/karten/{k[0]['id']}/verknuepfen", {"mit": k[2]["id"]})
    s = await pw.stand("anna")
    assert len(s["gruppen"]) == 1 and {c["gruppe"] for c in s["karten"]} == {s["gruppen"][0]["id"]}


# --- Rechte und Einladungen --------------------------------------------------------------------------------------

async def test_einladen_schaltet_frei_und_rechte_gelten(pw: Pinnwand):
    b = await pw.board("anna")
    k = await pw.karte("anna", b, "Fenster")
    assert (await pw.anmelden("bert")).status_code != 200                    # noch nicht eingeladen
    r = await pw.post("anna", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "bert", "rolle": "leser"})
    assert r.json()["meldung"] == "bert ist eingeladen und sieht Haushalt ab sofort in der Seitenleiste"
    assert pw.app.state.geruest.einstellungen.stand.weitere_konten == ["bert"]

    assert (await pw.anmelden("bert")).status_code == 200
    s = await pw.stand("bert")
    assert [x["id"] for x in s["boards"]] == [b["id"]] and [x["id"] for x in s["karten"]] == [k["id"]]
    mitglied = next(m for m in s["boards"][0]["mitglieder"] if m["kellerwolke"] == "bert")
    assert (mitglied["konto"], mitglied["rolle"]) == ("2", "leser")             # die wartende Einladung gilt jetzt

    r = await pw.post("bert", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Dran")})
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Karten verschieben")
    assert (await pw.post("bert", f"/boards/{b['id']}/karten", {"titel": "Hallo"})).status_code == 403
    assert (await pw.post("bert", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "cora"})).status_code == 403


async def test_einladen_abgelehnt(pw: Pinnwand):
    b = await pw.board("anna")
    await pw.post("anna", f"/boards/{b['id']}/mitglieder", {"kellerwolke": "bert"})
    for daten, status, meldung in [
        ({"kellerwolke": "bert"}, 409, "bert ist schon im Board Haushalt"),
        ({"kellerwolke": "anna"}, 409, "anna ist schon im Board Haushalt"),
        ({"kellerwolke": "zwei worte"}, 400, "zwei worte ist kein Kontoname der Kellerwolke"),
        ({"kellerwolke": "cora", "rolle": "chef"}, 400, "Die Rolle chef gibt es im Board Haushalt nicht"),
    ]:
        r = await pw.post("anna", f"/boards/{b['id']}/mitglieder", daten)
        assert (r.status_code, r.json()["detail"]) == (status, meldung)
    assert pw.app.state.geruest.einstellungen.stand.weitere_konten == ["bert"]


async def test_board_mit_einladungen_und_fremde_boards(pw: Pinnwand):
    """Einladungen gleich beim Anlegen; wer nicht Mitglied ist, sieht weder Board noch Karte noch Kürzel-Inhaber."""
    haus = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": "mitglied"}])
    werk = await pw.board("anna", "Werkstatt", "WERK")
    geheim = await pw.karte("anna", werk, "Geheim")
    assert (await pw.anmelden("bert")).status_code == 200
    s = await pw.stand("bert")
    assert [x["id"] for x in s["boards"]] == [haus["id"]]
    r = await pw.get("bert", f"/karten/{geheim['schluessel']}")
    assert r.status_code == 403
    r = await pw.post("bert", "/boards", {"vorlage": "v-aufgaben", "name": "Meins", "kuerzel": "WERK"})
    assert r.json()["detail"] == "WERK ist schon vergeben, an ein Board, das du nicht siehst."
    r = await pw.post("bert", f"/karten/{geheim['id']}/verschieben", {"nach": spalte(werk, "Dran")})
    assert r.status_code == 403
    # als Mitglied darf bert in Haushalt verschieben
    k = await pw.karte("anna", haus, "Fenster")
    assert (await pw.post("bert", f"/karten/{k['id']}/verschieben", {"nach": spalte(haus, "Dran")})).status_code == 200


# --- Rückgängig --------------------------------------------------------------------------------------------------

async def test_rueckgaengig(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    k = await pw.karte("anna", b, "Fenster")
    j1 = (await pw.post("anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Dran")})).json()["rueckgaengig"]

    assert (await pw.post("bert", f"/rueckgaengig/{j1}")).status_code == 403    # nur eigene Änderungen
    r = await pw.post("anna", f"/rueckgaengig/{j1}")
    assert (r.status_code, r.json()["meldung"], r.json()["rueckgaengig"]) == (200, "Rückgängig: HAUS-1 nach Dran", None)
    assert (await karte(pw, "anna", "HAUS-1"))["spalte"] == spalte(b, "Offen")
    r = await pw.post("anna", f"/rueckgaengig/{j1}")
    assert (r.status_code, r.json()["detail"]) == (400, "Das ist schon rückgängig gemacht")

    # nach einer weiteren Änderung an derselben Karte: Rückgängig würde sie überschreiben
    j2 = (await pw.post("anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "Dran")})).json()["rueckgaengig"]
    await pw.post("bert", f"/karten/{k['id']}/erledigen")
    r = await pw.post("anna", f"/rueckgaengig/{j2}")
    assert r.status_code == 409
    assert (await karte(pw, "anna", "HAUS-1"))["spalte"] == spalte(b, "Erledigt")
    assert (await pw.post("anna", "/rueckgaengig/j-gibt-es-nicht")).status_code == 404


# --- Ereignisse --------------------------------------------------------------------------------------------------

async def test_ereignisse_nur_an_mitglieder(pw: Pinnwand):
    haus = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "cora"}])
    for name in ("bert", "cora"):
        await pw.anmelden(name)
        await pw.stand(name)
    hub = pw.app.state.dienste.ereignisse
    stroeme = {name: hub.strom(konto) for name, konto in (("bert", "2"), ("cora", "3"))}
    naechstes = {name: asyncio.ensure_future(anext(s)) for name, s in stroeme.items()}
    await asyncio.sleep(0)                                                       # beide hören jetzt zu
    try:
        await pw.karte("anna", haus, "Fenster")
        teil = await asyncio.wait_for(naechstes["bert"], 1)
        assert sorted(g.tabelle for g in teil) == ["karten", "laufnummern"]
        await asyncio.sleep(0.05)
        assert not naechstes["cora"].done()
    finally:
        for f in naechstes.values():
            f.cancel()
        await asyncio.gather(*naechstes.values(), return_exceptions=True)
