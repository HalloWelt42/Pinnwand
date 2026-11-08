"""Dran heißt, man arbeitet dran (HELF-193): in einer Spalte, die misst, läuft für jeden zuständigen App-Zugang (etwa den
Helfer) auf jeder Karte ein eigener Timer; er bucht, wenn die Karte die Spalte verlässt oder der Zugang nicht mehr
zuständig ist. Der Helfer arbeitet in mehreren Sitzungen parallel, darum je Karte ein Timer; Menschen startet die Spalte
nie einen, ihr eigener Timer bleibt einer."""

from __future__ import annotations

from conftest import Pinnwand
from test_app_person import HELFER
from test_verwaltung import ok, spalte
from test_zeit import eintraege, stellen, vor


async def _helferboard(pw: Pinnwand) -> tuple[dict, str]:
    """Board Helfer (Vorlage Aufgaben: Offen, Dran misst, Erledigt) mit dem Helfer als Mitglied; Ergebnis: Board, seine Kennung."""
    stellen(pw, 27, 9)
    b = await pw.board("anna", "Helfer", "HELF")
    pw.kopf["helfer"] = HELFER
    helfer = (await pw.stand("helfer"))["ich"]
    return next(x for x in (await pw.stand("anna"))["boards"] if x["id"] == b["id"]), helfer


async def _zustaendig(pw: Pinnwand, k: dict, wer: list[str]) -> None:
    await ok(pw, "anna", f"/karten/{k['id']}/bearbeiten", {"felder": {"zustaendig": wer}})


async def _timer(pw: Pinnwand) -> dict[str, str]:
    """Laufende Timer als Karte -> Konto (anna sieht die Zeiten anderer)."""
    return {t["karte"]: t["konto"] for t in (await pw.stand("anna"))["timer"] if t.get("seit")}


async def test_dran_misst_je_karte_fuer_den_helfer(pw: Pinnwand):
    b, helfer = await _helferboard(pw)
    assert next(s for s in b["spalten"] if s["name"] == "In Arbeit").get("misst") is True
    a = await pw.karte("anna", b, "Erstes Ticket")
    c = await pw.karte("anna", b, "Zweites Ticket")
    for k in (a, c):
        await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "In Arbeit")})
        await _zustaendig(pw, k, [helfer])
    assert await _timer(pw) == {a["id"]: helfer, c["id"]: helfer}, "zwei Dran-Karten, zwei laufende Timer des Helfers"
    await ok(pw, "anna", "/timer/starten", {"karte": a["id"]})                # annas eigener Timer läuft daneben
    vor(pw, 30)
    await ok(pw, "anna", f"/karten/{a['id']}/verschieben", {"nach": spalte(b, "Erledigt")})
    vor(pw, 15)
    await ok(pw, "anna", f"/karten/{c['id']}/verschieben", {"nach": spalte(b, "Offen")})
    assert await _timer(pw) == {}
    helfers = {e["karte"]: e["sekunden"] for e in await eintraege(pw, "anna") if e["konto"] == helfer}
    assert helfers == {a["id"]: 30 * 60, c["id"]: 45 * 60}


async def test_zustaendigkeit_startet_und_bucht(pw: Pinnwand):
    """Wie das Werkzeug des Helfers arbeitet: erst nach Dran, dann zuständig; zurück an den Nutzer bucht."""
    b, helfer = await _helferboard(pw)
    k = await pw.karte("anna", b, "Ticket")
    await ok(pw, "anna", f"/karten/{k['id']}/verschieben", {"nach": spalte(b, "In Arbeit")})
    assert await _timer(pw) == {}, "anna ist zuständig: einem Menschen startet die Spalte nie einen Timer"
    await _zustaendig(pw, k, [helfer])
    assert await _timer(pw) == {k["id"]: helfer}
    vor(pw, 20)
    await _zustaendig(pw, k, ["1"])
    assert await _timer(pw) == {}
    assert [e["sekunden"] for e in await eintraege(pw, "anna", k) if e["konto"] == helfer] == [20 * 60]


async def test_spalte_umschalten_gleicht_ab(pw: Pinnwand):
    b, helfer = await _helferboard(pw)
    k = await pw.karte("anna", b, "Ticket", spalte=spalte(b, "In Arbeit"))
    await _zustaendig(pw, k, [helfer])
    dran = spalte(b, "In Arbeit")
    assert await _timer(pw) == {k["id"]: helfer}
    await ok(pw, "anna", f"/boards/{b['id']}/spalten/{dran}/aendern", {"misst": False})
    assert await _timer(pw) == {}
    await ok(pw, "anna", f"/boards/{b['id']}/spalten/{dran}/aendern", {"misst": True})
    assert await _timer(pw) == {k["id"]: helfer}
    r = await pw.post("anna", f"/boards/{b['id']}/spalten/{spalte(b, "Erledigt")}/aendern", {"misst": True})
    assert r.status_code == 400 and "Erledigt" in r.text


async def test_helfer_startet_und_stoppt_je_karte(pw: Pinnwand):
    """Von Hand: der Helfer startet auf zwei Karten, keine pausiert die andere; Stoppen mit Karte trifft nur sie."""
    b, helfer = await _helferboard(pw)
    a = await pw.karte("anna", b, "Eins")
    c = await pw.karte("anna", b, "Zwei")
    await ok(pw, "helfer", "/timer/starten", {"karte": a["id"]})
    await ok(pw, "helfer", "/timer/starten", {"karte": c["id"]})
    assert await _timer(pw) == {a["id"]: helfer, c["id"]: helfer}
    vor(pw, 10)
    await ok(pw, "helfer", "/timer/stoppen", {"karte": a["id"]})
    assert await _timer(pw) == {c["id"]: helfer}
    await ok(pw, "helfer", "/timer/stoppen", {})
    assert await _timer(pw) == {}


async def test_vorlage_projekt_misst_in_arbeit_nicht_in_pruefung(pw: Pinnwand):
    b = await pw.board("anna", "Projekt", "PROJ", vorlage="v-projekt")
    misst = {s["name"]: bool(s.get("misst")) for s in b["spalten"]}
    assert misst["In Arbeit"] and not misst["Prüfung"] and not misst["Erledigt"] and not misst["Eingang"]


async def test_der_helfer_legt_gleich_in_dran_an(pw: Pinnwand):
    """Legt der Helfer eine Karte gleich in einer messenden Spalte an, ist er zuständig und seine Zeit läuft sofort."""
    b, helfer = await _helferboard(pw)
    k = await pw.karte("helfer", b, "Selbst angelegt", spalte=spalte(b, "In Arbeit"))
    assert await _timer(pw) == {k["id"]: helfer}


async def test_nachtrag_beim_start_macht_dran_messend(pw: Pinnwand):
    """Bestehende Boards (vor HELF-193 ohne das Feld): Spalten namens Dran messen nach dem Start; eine ausdrücklich
    ausgeschaltete bleibt aus, auch beim nächsten Start."""
    import json
    from app.anwendung import spaltenmessung
    b, _ = await _helferboard(pw)

    def ohne_feld(v):
        z = v.execute("SELECT daten FROM boards WHERE id=?", (b["id"],)).fetchone()
        d = json.loads(z["daten"])
        for s in d["spalten"]:
            s.pop("misst", None)
            if s["name"] == "In Arbeit":
                s["name"] = "Dran"          # ein Board von vor HELF-198
        v.execute("UPDATE boards SET daten=? WHERE id=?", (json.dumps(d), b["id"]))
    db = pw.app.state.dienste.anwendung.v.db
    await db.transaktion(ohne_feld)
    assert await db.transaktion(spaltenmessung.nachtragen) == 1
    assert await db.transaktion(spaltenmessung.nachtragen) == 0, "ein zweiter Lauf ändert nichts"
    await ok(pw, "anna", f"/boards/{b['id']}/spalten/{spalte(b, 'In Arbeit')}/aendern", {"misst": False})
    assert await db.transaktion(spaltenmessung.nachtragen) == 0, "aus bleibt aus"
