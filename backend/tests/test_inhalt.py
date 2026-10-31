"""Inhalte von Karten über die Schnittstelle: Felder bearbeiten mit Prüfung gegen das Board, Verlauf vom Server,
Konflikt je Feld, Art, Kommentare (auch als Leser), Duplizieren, Sammelaktionen."""

from __future__ import annotations

from conftest import Pinnwand


async def karte(pw: Pinnwand, wer: str, schluessel: str) -> dict:
    r = await pw.get(wer, f"/karten/{schluessel}")
    assert r.status_code == 200, r.text
    return r.json()


async def bearbeiten(pw: Pinnwand, wer: str, k: dict, felder: dict, **mehr):
    return await pw.post(wer, f"/karten/{k['id']}/bearbeiten", {"felder": felder, **mehr})


async def test_eigenen_kommentar_bearbeiten_und_loeschen(pw: Pinnwand):
    """HELF-94: wer kommentiert hat, ändert oder löscht seinen Kommentar über dessen Kennung; die alte Fassung und der
    gelöschte Text stehen im Verlauf, Bilder bleiben als Anhang, Rückgängig holt Gelöschtes zurück. Fremde Kommentare
    lehnt der Server ab, auch für Besitzer."""
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": "leser"}, {"kellerwolke": "cora"}])
    for wer in ("bert", "cora"):
        await pw.anmelden(wer)
        await pw.stand(wer)
    k = await pw.karte("anna", b, "Fenster")
    await pw.post("bert", f"/karten/{k['id']}/kommentieren", {"text": "| A | B |\n| 1 | 2 |"})
    await pw.post("anna", f"/karten/{k['id']}/kommentieren", {"text": "Danke"})
    erster, zweiter = [c["id"] for c in (await karte(pw, "anna", "HAUS-1"))["kommentare"]]
    assert erster.startswith("m-") and erster != zweiter
    pfad = f"/karten/{k['id']}/kommentare/{erster}"

    r = await pw.post("bert", pfad + "/bearbeiten", {"text": "Tabelle:\n\n| A | B |\n|---|---|\n| 1 | 2 |"})
    assert (r.status_code, r.json()["meldung"]) == (200, "Kommentar an HAUS-1 bearbeitet")
    c = await karte(pw, "anna", "HAUS-1")
    eins = c["kommentare"][0]
    assert eins["text"] == "Tabelle:\n\n| A | B |\n|---|---|\n| 1 | 2 |" and eins["bearbeitet"] == "2026-10-27T10:00:00"
    assert eins["id"] == erster and c["kommentare"][1].get("bearbeitet") is None
    e = c["verlauf"][-1]
    assert (e["von"], e["text"], e["vorher"]) == ("2", "hat einen Kommentar bearbeitet", "| A | B |\n| 1 | 2 |")

    # fremd, unbekannt, leer: abgelehnt
    for wer, kid, was, daten, status, meldung in [
            ("anna", erster, "bearbeiten", {"text": "Anders"}, 403, "Nur eigene Kommentare lassen sich bearbeiten oder löschen"),
            ("cora", zweiter, "bearbeiten", {"text": "Anders"}, 403, "Nur eigene Kommentare lassen sich bearbeiten oder löschen"),
            ("anna", erster, "loeschen", None, 403, "Nur eigene Kommentare lassen sich bearbeiten oder löschen"),
            ("bert", "m-gibtesnicht", "bearbeiten", {"text": "Anders"}, 404, "Diesen Kommentar gibt es an HAUS-1 nicht (mehr)"),
            ("bert", erster, "bearbeiten", {"text": "  "}, 400, "Ein Kommentar braucht Text")]:
        r = await pw.post(wer, f"/karten/{k['id']}/kommentare/{kid}/{was}", daten)
        assert (r.status_code, r.json().get("detail")) == (status, meldung)

    # löschen: der Text steht im Verlauf, der andere Kommentar bleibt mit seiner Kennung; Rückgängig holt ihn zurück
    r = await pw.post("bert", pfad + "/loeschen")
    assert (r.status_code, r.json()["meldung"]) == (200, "Kommentar an HAUS-1 gelöscht")
    c = await karte(pw, "anna", "HAUS-1")
    assert [x["id"] for x in c["kommentare"]] == [zweiter]
    e = c["verlauf"][-1]
    assert (e["von"], e["text"], e["vorher"]) == ("2", "hat einen Kommentar gelöscht", "Tabelle:\n\n| A | B |\n|---|---|\n| 1 | 2 |")
    assert (await pw.post("bert", pfad + "/loeschen")).status_code == 404
    r = await pw.post("bert", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert r.status_code == 200, r.text
    assert [x["id"] for x in (await karte(pw, "anna", "HAUS-1"))["kommentare"]] == [erster, zweiter]


async def test_felder_und_verlauf(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    k = await pw.karte("anna", b, "Fenster")
    r = await bearbeiten(pw, "anna", k, {"titel": " Fenster putzen ", "faellig": "2026-10-30", "zustaendig": ["1", "2"],
                                         "prioritaet": "hoch"}, text="fällig Fr 30.10.")
    assert r.json()["meldung"] == "HAUS-1: fällig Fr 30.10."
    k = await karte(pw, "anna", "HAUS-1")
    assert (k["titel"], k["faellig"], k["zustaendig"], k["prioritaet"]) == ("Fenster putzen", "2026-10-30", ["1", "2"], "hoch")
    assert [e["text"] for e in k["verlauf"][1:]] == [
        "hat bert zugewiesen", "hat fällig auf Fr 30.10.2026 gesetzt", "hat die Priorität auf Hoch gesetzt"]
    # entfernen über null; nichts geändert: keine Meldung, kein Rückweg
    await bearbeiten(pw, "anna", k, {"faellig": None})
    assert "faellig" not in await karte(pw, "anna", "HAUS-1")
    r = await bearbeiten(pw, "anna", k, {"titel": "Fenster putzen"})
    assert r.json() == {"meldung": None, "rueckgaengig": None, "geaendert": []}


async def test_felder_abgelehnt(pw: Pinnwand):
    b = await pw.board("anna")
    k = await pw.karte("anna", b, "Fenster")
    for felder, meldung in [
        ({"titel": ""}, "Eine Karte braucht einen Titel"),
        ({"zustaendig": ["9"]}, "Zuständig kann nur sein, wer im Board Mitglied ist"),
        ({"labels": ["l-fremd"]}, "Dieses Label gibt es in diesem Board nicht"),
        ({"felder": {"f-fremd": "x"}}, "Dieses Feld gibt es in diesem Board nicht"),
        ({"start": "2026-11-02", "faellig": "2026-11-01"}, "Der Start liegt nach dem Fälligkeitstag"),
        ({"checkliste": [{"text": "  "}]}, "Ein Punkt der Checkliste braucht Text (höchstens 500 Zeichen)"),
        ({"faellig": "morgen"}, "morgen ist kein Tag (JJJJ-MM-TT)"),
    ]:
        r = await bearbeiten(pw, "anna", k, felder)
        assert (r.status_code, r.json()["detail"]) == (400, meldung)


async def test_ueberfaellig_gestartet_bleibt_bearbeitbar(pw: Pinnwand):
    b = await pw.board("anna")
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"faellig": "2026-10-26"})
    # der Timer setzt den Start auf heute, nach den Fälligkeitstag: so war es wirklich
    assert (await pw.post("anna", "/timer/starten", {"karte": k["id"]})).status_code == 200
    assert (await karte(pw, "anna", "HAUS-1"))["start"] == "2026-10-27"
    assert (await bearbeiten(pw, "anna", k, {"notizen": "erst heute angefangen"})).status_code == 200
    # wer Start oder Fällig selbst setzt, setzt sie stimmig
    r = await bearbeiten(pw, "anna", k, {"start": "2026-10-28"})
    assert (r.status_code, r.json()["detail"]) == (400, "Der Start liegt nach dem Fälligkeitstag")


async def test_konflikt_nur_beim_selben_feld(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "bert", k, {"faellig": "2026-10-29"})
    # anna kannte noch keine Fälligkeit: ihre Änderung daran wird abgelehnt, nicht still überschrieben
    r = await bearbeiten(pw, "anna", k, {"faellig": "2026-10-30"}, vorher={"faellig": None})
    assert r.status_code == 409 and "inzwischen geändert" in r.json()["detail"]
    assert (await karte(pw, "anna", "HAUS-1"))["faellig"] == "2026-10-29"
    # ein anderes Feld geht weiter, auch wenn die Karte inzwischen anders ist
    r = await bearbeiten(pw, "anna", k, {"titel": "Fenster innen"}, vorher={"titel": "Fenster"})
    assert r.status_code == 200


async def test_kommentar_art_duplizieren(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": "leser"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    k = await pw.karte("anna", b, "Fenster")
    await bearbeiten(pw, "anna", k, {"checkliste": [{"text": "innen", "erledigt": True}, {"text": "außen"}]})

    r = await pw.post("bert", f"/karten/{k['id']}/kommentieren", {"text": "Mache ich am Freitag"})
    assert r.json()["meldung"] == "Kommentar an HAUS-1 gespeichert"
    assert (await pw.post("bert", f"/karten/{k['id']}/art", {"art": "idee"})).status_code == 403
    assert (await pw.post("anna", f"/karten/{k['id']}/kommentieren", {"text": " "})).status_code == 400

    r = await pw.post("anna", f"/karten/{k['id']}/art", {"art": "idee"})
    assert r.json()["meldung"] == "HAUS-1 ist jetzt eine Idee"

    r = await pw.post("anna", f"/karten/{k['id']}/duplizieren")
    assert r.json()["meldung"] == "HAUS-1 als HAUS-2 dupliziert"
    kopie = await karte(pw, "anna", "HAUS-2")
    assert kopie["titel"] == "Fenster (Kopie)" and kopie["kommentare"] == [] and kopie["art"] == "idee"
    assert [p["erledigt"] for p in kopie["checkliste"]] == [False, False]
    assert kopie["verlauf"] == [{"zeit": "2026-10-27T10:00:00", "von": "1", "text": "hat die Karte aus HAUS-1 dupliziert"}]


async def test_sammelaktionen(pw: Pinnwand):
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert"}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    ids = [(await pw.karte("anna", b, t))["id"] for t in ("Fenster", "Keller")]
    r = await pw.post("anna", "/karten/sammel/zuweisen", {"ids": ids, "konto": "2"})
    assert r.json()["meldung"] == "2 Karten bert zugewiesen"
    r = await pw.post("anna", "/karten/sammel/prioritaet", {"ids": ids, "prioritaet": "dringend"})
    assert r.json()["meldung"] == "Priorität von 2 Karten gesetzt"
    for s in ("HAUS-1", "HAUS-2"):
        k = await karte(pw, "anna", s)
        assert k["zustaendig"] == ["1", "2"] and k["prioritaet"] == "dringend"
    assert (await pw.post("anna", "/karten/sammel/label", {"ids": ids, "label": "l-fremd"})).status_code == 400
    assert (await pw.post("anna", "/karten/sammel/zuweisen", {"ids": ids, "konto": "3"})).status_code == 400
    andere = await pw.board("anna", "Werkstatt", "WERK")
    fremd = await pw.karte("anna", andere, "Bohrer")
    r = await pw.post("anna", "/karten/sammel/prioritaet", {"ids": [ids[0], fremd["id"]], "prioritaet": "hoch"})
    assert (r.status_code, r.json()["detail"]) == (400, "Sammelaktionen gehen nur mit Karten eines Boards")


def test_kennungen_der_kommentare_nachtragen(tmp_path):
    """HELF-94: Kommentare von früher bekommen beim Start eine Kennung (an Karten und im Papierkorb); vorhandene
    bleiben, alte Rückwege gelten danach nicht mehr; ein zweiter Lauf ändert nichts."""
    import json
    import sqlite3

    from app.anwendung import kommentarkennung

    v = sqlite3.connect(tmp_path / "p.db")
    v.row_factory = sqlite3.Row
    v.executescript("CREATE TABLE karten (id TEXT, fassung INTEGER, daten TEXT); CREATE TABLE papierkorb (id TEXT, fassung INTEGER, daten TEXT);"
                    "CREATE TABLE journal (id TEXT, rueckgaengig INTEGER); INSERT INTO journal VALUES ('j', 1);")
    alt = {"von": "1", "zeit": "2026-10-30T10:00:00", "text": "Alt"}
    v.execute("INSERT INTO karten VALUES ('c-1', 1, ?)", (json.dumps({"kommentare": [alt, {**alt, "id": "m-da"}]}),))
    v.execute("INSERT INTO papierkorb VALUES ('p-1', 1, ?)", (json.dumps({"karten": [{"kommentare": [alt]}]}),))
    assert kommentarkennung.nachtragen(v) == 2
    karte = json.loads(v.execute("SELECT daten FROM karten").fetchone()[0])
    ids = [c["id"] for c in karte["kommentare"]]
    assert ids[0].startswith("m-") and ids[1] == "m-da"
    assert json.loads(v.execute("SELECT daten FROM papierkorb").fetchone()[0])["karten"][0]["kommentare"][0]["id"].startswith("m-")
    assert v.execute("SELECT rueckgaengig FROM journal").fetchone()[0] == 0
    assert kommentarkennung.nachtragen(v) == 0
