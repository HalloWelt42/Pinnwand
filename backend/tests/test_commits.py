"""Commits an Karten (HELF-35): Einspielen nur durch den Besitzer der App, Verknüpfen über den Schlüssel in der Nachricht
(auch frühere Schlüssel), wiederholtes Einspielen ohne Doppel, ein neuer Verweis zieht nach, von Hand verknüpfen und
lösen mit Rückgängig, ein gelöster Bezug kommt nicht wieder, Suche, Sicht nur für Mitglieder, Umzug nimmt Bezüge mit."""

from __future__ import annotations

from conftest import Pinnwand
from test_verwaltung import abgelehnt, mit_bert, ok

from app.anwendung.commits import schluessel_in

REPO = {"kennung": "HalloWelt42/Pinnwand", "name": "Pinnwand", "quelle": "GitHub",
        "verweis": "https://github.com/HalloWelt42/Pinnwand/commit/{hash}"}


def commit(h: str, nachricht: str, zeit: str = "2026-10-30T10:00:00") -> dict:
    return {"hash": h * 40 if len(h) == 1 else h, "autor": "HalloWelt42", "zeit": zeit, "nachricht": nachricht,
            "dateien": ["backend/app/main.py"]}


async def einspielen(pw: Pinnwand, *commits: dict, wer: str = "anna", repo: dict = REPO) -> dict:
    return await ok(pw, wer, "/commits/einspielen", {"repo": repo, "commits": list(commits)})


async def bezuege(pw: Pinnwand, wer: str = "anna") -> list[dict]:
    return (await pw.stand(wer))["commitbezuege"]


def test_schluessel_in_nachrichten():
    assert schluessel_in("HELF-12: Fehler, auch HAUS-3 und HELF-12 wieder") == ["HELF-12", "HAUS-3"]
    assert schluessel_in("UTF-8 und x-HAUS-3, HAUS-03, haus-4, HAUS-5x") == ["UTF-8", "HAUS-3"]      # nur Schlüsselform
    assert schluessel_in("(HAUS-7), [HAUS-8]") == ["HAUS-7", "HAUS-8"]


async def test_einspielen_verknuepft_ueber_den_schluessel(pw: Pinnwand):
    b = await mit_bert(pw)
    await pw.karte("anna", b, "Fenster")
    await pw.karte("anna", b, "Keller")
    journal = await pw.app.state.dienste.anwendung.v.db.zeile("SELECT count(*) AS n FROM journal")
    r = await einspielen(pw, commit("a", "HAUS-1: Fenster gedichtet"), commit("b", "HAUS-1, HAUS-2 und UTF-9"),
                         commit("c", "ohne Bezug"))
    assert r == {"neu": 3, "verknuepft": 3}
    # Eingespieltes kommt nicht ins Journal
    assert (await pw.app.state.dienste.anwendung.v.db.zeile("SELECT count(*) AS n FROM journal"))["n"] == journal["n"]
    bz = await bezuege(pw, "bert")                                  # Mitglieder sehen sie
    assert sorted((x["hash"][:1], x["karte"] == b["id"]) for x in bz) == [("a", False), ("b", False), ("b", False)]
    erster = next(x for x in bz if x["hash"].startswith("a"))
    assert erster["verweis"] == "https://github.com/HalloWelt42/Pinnwand/commit/" + "a" * 40
    assert (erster["art"], erster["reponame"], erster["nachricht"], erster["dateien"]) == (
        "kennung", "Pinnwand", "HAUS-1: Fenster gedichtet", ["backend/app/main.py"])
    # noch einmal dasselbe: nichts Neues, kein Doppel
    assert await einspielen(pw, commit("a", "HAUS-1: Fenster gedichtet")) == {"neu": 0, "verknuepft": 0}
    assert len(await bezuege(pw)) == 3
    # ein anderer Verweis (Ziel des Repos geändert) zieht in die Bezüge nach; lokal: ohne Verweis
    await einspielen(pw, commit("a", "HAUS-1: Fenster gedichtet"), repo={**REPO, "quelle": "lokal", "verweis": None})
    erster = next(x for x in await bezuege(pw) if x["hash"].startswith("a"))
    assert erster["quelle"] == "lokal" and "verweis" not in erster


async def test_nur_der_besitzer_der_app_spielt_ein(pw: Pinnwand):
    await mit_bert(pw)
    await abgelehnt(pw, "bert", "/commits/einspielen", {"repo": REPO, "commits": [commit("a", "HAUS-1")]}, 403,
                    "Commits spielt nur der Besitzer der App ein")
    r = await pw.post("anna", "/commits/einspielen", {"repo": REPO, "commits": [{**commit("a", "x"), "hash": "kein hash"}]})
    assert r.status_code == 422


async def test_sicht_nur_fuer_mitglieder(pw: Pinnwand):
    b = await pw.board("anna")
    await pw.karte("anna", b, "Fenster")
    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "bert", "rolle": "mitglied"}])
    await pw.anmelden("bert")
    await einspielen(pw, commit("a", "HAUS-1"))
    assert len(await bezuege(pw)) == 1 and await bezuege(pw, "bert") == []


async def test_von_hand_verknuepfen_und_loesen(pw: Pinnwand):
    b = await mit_bert(pw)
    k1 = await pw.karte("anna", b, "Fenster")
    k2 = await pw.karte("anna", b, "Keller")
    await einspielen(pw, commit("a", "HAUS-1: Fenster"), commit("b", "Aufräumen im Keller", "2026-10-30T11:00:00"))
    # suchen: Anfang des Hashs oder Wörter der Nachricht
    r = await pw.get("bert", f"/karten/{k2['id']}/commits/suche?text=keller")
    assert [c["hash"][:1] for c in r.json()] == ["b"]
    r = await pw.get("bert", f"/karten/{k2['id']}/commits/suche?text=" + "a" * 6)
    assert [c["id"] for c in r.json()] == ["HalloWelt42/Pinnwand@" + "a" * 40]
    a = await ok(pw, "bert", f"/karten/{k2['id']}/commits", {"commit": "HalloWelt42/Pinnwand@" + "b" * 40})
    assert a["meldung"] == "HAUS-2: Commit bbbbbbb verknüpft" and a["rueckgaengig"]
    await abgelehnt(pw, "bert", f"/karten/{k2['id']}/commits", {"commit": "HalloWelt42/Pinnwand@" + "b" * 40}, 409,
                    "Commit bbbbbbb hängt schon an HAUS-2")
    await abgelehnt(pw, "bert", f"/karten/{k2['id']}/commits", {"commit": "x@1234567"}, 404, "Diesen Commit kennt die Pinnwand nicht")
    hand = next(x for x in await bezuege(pw) if x["karte"] == k2["id"])
    assert hand["art"] == "hand" and hand["von"] == (await pw.stand("bert"))["ich"]
    # von Hand gelöst: weg; Rückgängig bringt ihn zurück
    r = await pw.c.delete(f"/api/v1/karten/{k2['id']}/commits/{hand['id']}", headers=pw.kopf["bert"])
    assert r.json()["meldung"] == "HAUS-2: Commit bbbbbbb gelöst"
    assert [x for x in await bezuege(pw) if x["karte"] == k2["id"]] == []
    await ok(pw, "bert", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert [x["art"] for x in await bezuege(pw) if x["karte"] == k2["id"]] == ["hand"]
    # aus der Nachricht gelöst: bleibt als gelöst stehen und kommt beim nächsten Einspielen nicht wieder
    auto = next(x for x in await bezuege(pw) if x["karte"] == k1["id"])
    r = await pw.c.delete(f"/api/v1/karten/{k1['id']}/commits/{auto['id']}", headers=pw.kopf["anna"])
    assert r.status_code == 200
    await einspielen(pw, commit("a", "HAUS-1: Fenster"))
    assert [x.get("geloest") for x in await bezuege(pw) if x["karte"] == k1["id"]] == [True]
    # von Hand wieder verknüpft: gilt wieder
    await ok(pw, "anna", f"/karten/{k1['id']}/commits", {"commit": "HalloWelt42/Pinnwand@" + "a" * 40})
    assert [(x["art"], x.get("geloest", False)) for x in await bezuege(pw) if x["karte"] == k1["id"]] == [("hand", False)]
    assert (await pw.get("anna", "/karten/HAUS-1")).json()["verlauf"][-1]["text"] == "hat Commit aaaaaaa aus Pinnwand verknüpft"


async def test_rechte_beim_verknuepfen(pw: Pinnwand):
    b = await mit_bert(pw, "leser")
    k = await pw.karte("anna", b, "Fenster")
    await einspielen(pw, commit("a", "irgendwas"))
    await abgelehnt(pw, "bert", f"/karten/{k['id']}/commits", {"commit": "HalloWelt42/Pinnwand@" + "a" * 40}, 403,
                    "Dir fehlt im Board Haushalt das Recht Karten bearbeiten")
    r = await pw.get("bert", f"/karten/{k['id']}/commits/suche?text=irgendwas")
    assert r.status_code == 404


async def test_umzug_und_fruehere_schluessel(pw: Pinnwand):
    b = await pw.board("anna")
    ziel = await pw.board("anna", "Werkstatt", "WERK")
    k = await pw.karte("anna", b, "Fenster")
    await einspielen(pw, commit("a", "HAUS-1: vor dem Umzug"))
    await ok(pw, "anna", f"/karten/{k['id']}/umziehen", {"board": ziel["id"]})
    assert [x["board"] for x in await bezuege(pw)] == [ziel["id"]]
    # der alte Schlüssel führt weiter zur Karte
    assert await einspielen(pw, commit("b", "HAUS-1: nach dem Umzug")) == {"neu": 1, "verknuepft": 1}
    assert {x["karte"] for x in await bezuege(pw)} == {k["id"]}
