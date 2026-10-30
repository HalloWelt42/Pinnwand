"""Gesamtnummer der Karten (HELF-49): fortlaufend über alle Boards, lückenlos, nur vom Server vergeben, eindeutig auch
bei gleichzeitigem Anlegen, unverändert bei Umzug, Papierkorb und Löschen, nie wiederverwendet; der Nachtrag nummeriert
vorhandene Karten einmal nach ihrer Anlage."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta

from app.anwendung import gesamtnummer
from conftest import Pinnwand


async def nummern(pw: Pinnwand, wer: str = "anna") -> dict[str, int]:
    return {k["schluessel"]: k["nummer"] for k in (await pw.stand(wer))["karten"]}


async def test_fortlaufend_ueber_alle_boards_und_jeden_weg(pw: Pinnwand):
    haus = await pw.board("anna")
    garten = await pw.board("anna", name="Garten", kuerzel="GART")
    a = await pw.karte("anna", haus, "Eins")
    b = await pw.karte("anna", garten, "Zwei")
    assert (a["nummer"], b["nummer"]) == (1, 2)
    # Duplizieren bekommt die nächste Nummer, nie die des Originals
    r = await pw.post("anna", f"/karten/{a['id']}/duplizieren")
    assert r.status_code == 200, r.text
    # mehrere auf einmal: der Reihe nach
    r = await pw.post("anna", f"/boards/{haus['id']}/karten/mehrere",
                      {"karten": [{"titel": "Drei"}, {"titel": "Vier"}], "spalte": haus["spalten"][0]["id"], "art": "arbeit"})
    assert r.status_code == 200, r.text
    n = await nummern(pw)
    assert n == {"HAUS-1": 1, "GART-1": 2, "HAUS-2": 3, "HAUS-3": 4, "HAUS-4": 5}
    # Umzug ändert den Schlüssel, nicht die Gesamtnummer
    r = await pw.post("anna", f"/karten/{a['id']}/umziehen", {"board": garten["id"]})
    assert r.status_code == 200, r.text
    assert (await nummern(pw))["GART-2"] == 1


async def test_papierkorb_und_loeschen_aendern_nichts(pw: Pinnwand):
    haus = await pw.board("anna")
    karten = [await pw.karte("anna", haus, f"Karte {i}") for i in range(3)]
    r = await pw.post("anna", "/karten/in-papierkorb", {"ids": [karten[1]["id"]]})
    assert r.status_code == 200, r.text
    eintrag = next(e for e in (await pw.stand("anna"))["papierkorb"])
    assert eintrag["karten"][0]["nummer"] == 2
    r = await pw.post("anna", f"/papierkorb/{eintrag['id']}/wiederherstellen")
    assert r.status_code == 200, r.text
    assert (await nummern(pw))["HAUS-2"] == 2
    # endgültig gelöscht: die übrigen behalten ihre Nummer, die gelöschte wird nie wieder vergeben
    r = await pw.post("anna", f"/karten/{karten[2]['id']}/endgueltig", {"bestaetigung": "HAUS-3"})
    assert r.status_code == 200, r.text
    neu = await pw.karte("anna", haus, "Danach")
    assert neu["nummer"] == 4
    assert await nummern(pw) == {"HAUS-1": 1, "HAUS-2": 2, "HAUS-4": 4}


async def test_abgelehntes_anlegen_verbraucht_keine_nummer(pw: Pinnwand):
    haus = await pw.board("anna")
    await pw.karte("anna", haus, "Eins")
    r = await pw.post("anna", f"/boards/{haus['id']}/karten", {"titel": "Falsche Spalte", "spalte": "s-gibt-es-nicht"})
    assert r.status_code == 400
    assert (await pw.karte("anna", haus, "Zwei"))["nummer"] == 2


async def test_gleichzeitig_angelegt_eindeutig_und_lueckenlos(pw: Pinnwand):
    haus = await pw.board("anna")
    garten = await pw.board("anna", name="Garten", kuerzel="GART")
    antworten = await asyncio.gather(*(pw.karte("anna", haus if i % 2 else garten, f"Karte {i}") for i in range(30)))
    assert sorted(k["nummer"] for k in antworten) == list(range(1, 31))


async def test_nachtrag_nummeriert_nach_anlage_einmal(pw: Pinnwand):
    haus = await pw.board("anna")
    titel = ["Alt", "Mittel", "Neu", "Weggelegt"]
    karten = []
    for t in titel:
        karten.append(await pw.karte("anna", haus, t))
        pw.zeiger.zeit += timedelta(minutes=1)
    r = await pw.post("anna", "/karten/in-papierkorb", {"ids": [karten[1]["id"]]})
    assert r.status_code == 200, r.text
    db = pw.app.state.geruest.db

    def vergessen(v):
        """Stand wie vor der Gesamtnummer: kein Zähler, keine Nummern (auch nicht im Papierkorb)."""
        v.execute("DELETE FROM zaehler")
        for z in v.execute("SELECT id, daten FROM karten").fetchall():
            d = json.loads(z["daten"])
            d.pop("nummer")
            v.execute("UPDATE karten SET daten=?, nummer=NULL WHERE id=?", (json.dumps(d), z["id"]))
        for z in v.execute("SELECT id, daten FROM papierkorb").fetchall():
            d = json.loads(z["daten"])
            for c in d["karten"]:
                c.pop("nummer")
            v.execute("UPDATE papierkorb SET daten=? WHERE id=?", (json.dumps(d), z["id"]))

    await db.transaktion(vergessen)
    assert await db.transaktion(gesamtnummer.nachtragen) == 4
    assert await db.transaktion(gesamtnummer.nachtragen) == 0
    s = await pw.stand("anna")
    assert {k["titel"]: k["nummer"] for k in s["karten"]} == {"Alt": 1, "Neu": 3, "Weggelegt": 4}
    assert s["papierkorb"][0]["karten"][0]["nummer"] == 2
    assert (await pw.karte("anna", haus, "Danach"))["nummer"] == 5


async def test_nachtrag_in_derselben_sekunde_nach_nummer_im_board(pw: Pinnwand):
    haus = await pw.board("anna")
    for i in range(12):
        await pw.karte("anna", haus, f"Karte {i}")
    db = pw.app.state.geruest.db

    def vergessen(v):
        v.execute("DELETE FROM zaehler")
        for z in v.execute("SELECT id, daten FROM karten").fetchall():
            d = json.loads(z["daten"])
            d.pop("nummer")
            v.execute("UPDATE karten SET daten=?, nummer=NULL WHERE id=?", (json.dumps(d), z["id"]))

    await db.transaktion(vergessen)
    await db.transaktion(gesamtnummer.nachtragen)
    assert await nummern(pw) == {f"HAUS-{i}": i for i in range(1, 13)}
