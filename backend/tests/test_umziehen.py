"""Eine Karte zieht in ein anderes Board (vom Ideenboard aufs Arbeitsboard): neue Nummer und Kartenart, Labels und Felder
mit gleichem Namen, Zuständige nur als Mitglieder, Zeit zieht mit, der alte Schlüssel führt weiter, Rückgängig."""

from __future__ import annotations

import asyncio

from conftest import Pinnwand
from test_verwaltung import abgelehnt, ok


async def zwei_boards(pw: Pinnwand) -> tuple[dict, dict]:
    """Ideen (bert ist Mitglied) und Haushalt (nur anna), beide mit dem Label Garten und dem Feld Kosten."""
    ideen = await pw.board("anna", name="Ideen", kuerzel="IDEE", vorlage="v-ideen", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    haus = await pw.board("anna")
    for b in (ideen, haus):
        await ok(pw, "anna", f"/boards/{b['id']}/labels", {"name": "Garten", "farbe": "minze"})
        await ok(pw, "anna", f"/boards/{b['id']}/felder", {"name": "Kosten", "art": "zahl"})
    await ok(pw, "anna", f"/boards/{ideen['id']}/labels", {"name": "Irgendwann", "farbe": "sand"})
    s = await pw.stand("anna")
    return tuple(next(b for b in s["boards"] if b["kuerzel"] == k) for k in ("IDEE", "HAUS"))  # type: ignore[return-value]


async def test_idee_wird_arbeit(pw: Pinnwand):
    ideen, haus = await zwei_boards(pw)
    k = await pw.karte("anna", ideen, "Hochbeet bauen")
    andere = await pw.karte("anna", ideen, "Teich")
    label = {l["name"]: l["id"] for l in ideen["labels"]}
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {
        "labels": [label["Garten"], label["Irgendwann"]], "felder": {ideen["felder"][0]["id"]: "120"}, "zustaendig": ["1", "2"],
        "checkliste": [{"text": "Holz"}]}})
    await ok(pw, "anna", f"/karten/{k['id']}/kommentieren", {"text": "Lärche nehmen"})
    assert k["art"] == "idee"

    hub = pw.app.state.dienste.ereignisse
    with hub.abo("2") as bert:
        a = await ok(pw, "anna", f"/karten/{k['id']}/umziehen", {"board": haus["id"]})
        teil = await asyncio.wait_for(anext(bert), 1)
    assert a["meldung"] == "IDEE-1 ist jetzt HAUS-1 in Haushalt, Offen; 1 Label oder Feld ohne Gegenstück entfällt"
    assert [(g.tabelle, g.daten is None) for g in teil.geaendert if g.tabelle == "karten"] == [("karten", True)]   # weg für bert

    c = next(x for x in (await pw.stand("anna"))["karten"] if x["id"] == k["id"])
    assert (c["board"], c["schluessel"], c["art"], c["frueher"]) == (haus["id"], "HAUS-1", "arbeit", ["IDEE-1"])
    assert c["spalte"] == haus["spalten"][0]["id"] and c["zustaendig"] == ["1"]
    assert c["labels"] == [next(l["id"] for l in haus["labels"] if l["name"] == "Garten")]
    assert c["felder"] == {haus["felder"][0]["id"]: "120"}
    assert c["checkliste"][0]["text"] == "Holz" and c["kommentare"][0]["text"] == "Lärche nehmen"
    assert c["verlauf"][-1]["text"] == "hat sie aus Ideen (IDEE-1) nach Haushalt verschoben"

    # der alte Schlüssel führt weiter zur Karte; die nächste Idee bekommt trotzdem eine neue Nummer
    assert (await pw.get("anna", "/karten/IDEE-1")).json()["schluessel"] == "HAUS-1"
    assert (await pw.get("bert", "/karten/IDEE-1")).status_code == 403
    assert (await pw.karte("anna", ideen, "Kräuterspirale"))["schluessel"] == "IDEE-3"
    assert andere["schluessel"] == "IDEE-2"

    await ok(pw, "anna", f"/rueckgaengig/{a['rueckgaengig']}")
    c = next(x for x in (await pw.stand("anna"))["karten"] if x["id"] == k["id"])
    assert (c["board"], c["schluessel"], c["art"], c.get("frueher", [])) == (ideen["id"], "IDEE-1", "idee", [])
    assert len(c["labels"]) == 2 and c["zustaendig"] == ["1", "2"]


async def test_zeit_und_gruppe_ziehen_mit(pw: Pinnwand):
    _, haus = await zwei_boards(pw)
    werk = await pw.board("anna", name="Werkstatt", kuerzel="WERK")
    a, b = await pw.karte("anna", haus, "Regal"), await pw.karte("anna", haus, "Brett")
    await ok(pw, "anna", f"/karten/{a['id']}/verknuepfen", {"mit": b["id"]})
    await ok(pw, "anna", "/zeiten", {"karte": a["id"], "datum": "2026-10-26", "sekunden": 1800})
    await ok(pw, "anna", "/timer/starten", {"karte": a["id"]})
    pw.zeiger.zeit = pw.zeiger.zeit.replace(minute=15)
    zweite = next(s["id"] for s in werk["spalten"] if s["name"] == "Dran")
    m = (await ok(pw, "anna", f"/karten/{a['id']}/umziehen", {"board": werk["id"], "spalte": zweite}))["meldung"]
    assert m == "HAUS-1 ist jetzt WERK-1 in Werkstatt, Dran; dein Timer ist gestoppt, 0:15 gebucht"
    s = await pw.stand("anna")
    assert {e["board"] for e in s["zeiteintraege"]} == {werk["id"]} and len(s["zeiteintraege"]) == 2
    assert all(not x.get("gruppe") for x in s["karten"] if x["id"] in (a["id"], b["id"])) and s["gruppen"] == []


async def test_umziehen_abgelehnt(pw: Pinnwand):
    ideen, haus = await zwei_boards(pw)
    k = await pw.karte("anna", ideen, "Hochbeet")
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/umziehen", {"board": ideen["id"]}, 400, "Die Karte liegt schon in diesem Board")
    await abgelehnt(pw, "anna", f"/karten/{k['id']}/umziehen", {"board": haus["id"], "spalte": "s-fremd"}, 400,
                    "Diese Spalte gibt es im Board Haushalt nicht")
    # bert ist im Haushalt kein Mitglied: dort darf er nichts anlegen
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/umziehen", {"board": haus["id"]}, 403,
                    "Dir fehlt im Board Haushalt das Recht Karten anlegen")
