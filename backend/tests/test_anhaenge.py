"""Anhänge über die Schnittstelle gegen die nachgestellte Kellerwolke: hochladen in den Ordner des Boards (mehrere auf
einmal, Namensdoppel, Grenze, leere und unvollständige Dateien), Recht, Aufräumen, wenn Ablegen oder Festhalten
scheitert, verknüpfen aus der eigenen Kellerwolke mit der Dateiwahl, entfernen mit Rückgängig, Verlauf und Öffnen."""

from __future__ import annotations

import json

import pytest

from app.anwendung import anhaenge
from conftest import Pinnwand
from nachgestellt import ABLAGE

MB = 1024 * 1024


@pytest.fixture(autouse=True)
def leere_ablage():
    ABLAGE.leeren()
    yield
    ABLAGE.leeren()


def koerper(*dateien: tuple[str, bytes, str]) -> bytes:
    """Wie die Oberfläche hochlädt: Kopfzeile mit den Angaben, dahinter die Inhalte."""
    kopf = json.dumps({"dateien": [{"name": n, "groesse": len(b), "typ": t} for n, b, t in dateien]}).encode()
    return kopf + b"\n" + b"".join(b for _, b, _ in dateien)


async def hochladen(pw: Pinnwand, wer: str, k: dict, *dateien: tuple[str, bytes, str], roh: bytes | None = None):
    return await pw.c.post(f"/api/v1/karten/{k['id']}/anhaenge/hochladen", headers=pw.kopf[wer],
                           content=koerper(*dateien) if roh is None else roh)


async def karte(pw: Pinnwand, wer: str, schluessel: str = "HAUS-1") -> dict:
    r = await pw.get(wer, f"/karten/{schluessel}")
    assert r.status_code == 200, r.text
    return r.json()


async def mit_bert(pw: Pinnwand, rolle: str = "mitglied") -> tuple[dict, dict]:
    """Board Haushalt mit bert in der Rolle, dazu die Karte HAUS-1."""
    b = await pw.board("anna", einladungen=[{"kellerwolke": "bert", "rolle": rolle}])
    await pw.anmelden("bert")
    await pw.stand("bert")
    return b, await pw.karte("anna", b, "Fenster")


def verlauf(k: dict) -> list[str]:
    return [e["text"] for e in k["verlauf"][1:]]


# --- Hochladen --------------------------------------------------------------------------------------------------

async def test_hochladen_in_den_ordner_des_boards(pw: Pinnwand):
    _, k = await mit_bert(pw)
    r = await hochladen(pw, "anna", k, ("Skizze.png", b"\x89PNG bild", "image/png"))
    assert r.status_code == 200, r.text
    assert r.json()["meldung"] == "Skizze.png an HAUS-1 angehängt, abgelegt in der Kellerwolke unter Pinnwand/Haushalt"
    assert r.json()["rueckgaengig"]
    datei = ABLAGE.im_zweig()[0]
    assert (ABLAGE.pfad(datei), datei.inhalt, datei.inhaltstyp) == ("Apps/Pinnwand/Haushalt/Skizze.png", b"\x89PNG bild", "image/png")
    k = await karte(pw, "bert")
    assert k["anhaenge"] == [{"name": "Skizze.png", "groesse": "9 B", "art": "bild", "datei": datei.id,
                              "pfad": "Apps/Pinnwand/Haushalt/Skizze.png", "von": "1"}]
    assert verlauf(k) == ["hat den Anhang Skizze.png hochgeladen"]


async def test_mehrere_auf_einmal_und_namensdoppel(pw: Pinnwand):
    b, k = await mit_bert(pw)
    await hochladen(pw, "anna", k, ("Skizze.png", b"eins", "image/png"))
    r = await hochladen(pw, "bert", k, ("Skizze.png", b"zwei", "image/png"), ("Maße.pdf", b"x" * 3000, "application/pdf"))
    assert r.json()["meldung"] == "2 Dateien an HAUS-1 angehängt, abgelegt in der Kellerwolke unter Pinnwand/Haushalt"
    k = await karte(pw, "anna")
    assert [(a["name"], a["groesse"], a["art"]) for a in k["anhaenge"]] == [
        ("Skizze.png", "4 B", "bild"), ("Skizze (2).png", "4 B", "bild"), ("Maße.pdf", "3 KB", "pdf")]
    # an einer anderen Karte desselben Boards ist der Name frei; im Ordner des Boards zählt die Kellerwolke weiter
    andere = await pw.karte("anna", b, "Keller")
    await hochladen(pw, "anna", andere, ("Skizze.png", b"drei", "image/png"))
    a = (await karte(pw, "anna", "HAUS-2"))["anhaenge"][0]
    assert (a["name"], a["pfad"]) == ("Skizze.png", "Apps/Pinnwand/Haushalt/Skizze (3).png")
    assert sorted(e.name for e in ABLAGE.im_zweig()) == ["Maße.pdf", "Skizze (2).png", "Skizze (3).png", "Skizze.png"]


async def test_rueckgaengig_nimmt_alle_von_der_karte(pw: Pinnwand):
    _, k = await mit_bert(pw)
    r = await hochladen(pw, "anna", k, ("a.txt", b"a", "text/plain"), ("b.txt", b"b", "text/plain"))
    r = await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert r.json()["meldung"].startswith("Rückgängig: 2 Dateien an HAUS-1 angehängt")
    assert (await karte(pw, "anna"))["anhaenge"] == []
    # die Dateien bleiben im Ordner des Boards (Rückgängig stellt nur die Karte her)
    assert sorted(e.name for e in ABLAGE.im_zweig()) == ["a.txt", "b.txt"]


async def test_grenze_leer_und_unvollstaendig(pw: Pinnwand):
    _, k = await mit_bert(pw)
    gross = json.dumps({"dateien": [{"name": "Film.mov", "groesse": 25 * MB + 1, "typ": "video/quicktime"}]}).encode() + b"\n"
    faelle = [
        (gross, "Nicht angehängt: Film.mov ist größer als 25 MB"),
        (koerper(("leer.txt", b"", "text/plain")), "Nicht angehängt: leer.txt ist leer"),
        (koerper(("a.txt", b"abc", "")).replace(b'"groesse": 3', b'"groesse": 9'), "Die Dateien kamen nicht vollständig an"),
        (koerper(("a.txt", b"abc", "")) + b"mehr", "Es kam mehr an als angegeben"),
        (b"kein json\n", "Die Angaben zu den Dateien sind nicht lesbar"),
        (koerper(*[(f"{i}.txt", b"x", "") for i in range(21)]), "Höchstens 20 Dateien auf einmal"),
        (koerper(("   ", b"x", "")), "Eine Datei braucht einen Namen"),
        (koerper(("a" * 256, b"x", "")), "Ein Dateiname hat höchstens 255 Zeichen"),
    ]
    for roh, meldung in faelle:
        r = await hochladen(pw, "anna", k, roh=roh)
        assert (r.status_code, r.json()["detail"]) == (400, meldung), r.text
    # genau an der Grenze geht es
    r = await hochladen(pw, "anna", k, ("Grenze.bin", b"0" * 25 * MB, ""))
    assert r.status_code == 200 and (await karte(pw, "anna"))["anhaenge"][0]["groesse"] == "25,0 MB"
    assert [e.name for e in ABLAGE.im_zweig()] == ["Grenze.bin"]


async def test_recht(pw: Pinnwand):
    _, k = await mit_bert(pw, "leser")
    await pw.board("anna", "Werkstatt", "WERK", einladungen=[{"kellerwolke": "cora"}])
    assert (await pw.anmelden("cora")).status_code == 200
    datei = ("Skizze.png", b"bild", "image/png")
    r = await hochladen(pw, "bert", k, datei)
    assert (r.status_code, r.json()["detail"]) == (403, "Dir fehlt im Board Haushalt das Recht Karten bearbeiten")
    assert (await hochladen(pw, "cora", k, datei)).status_code == 403
    await hochladen(pw, "anna", k, datei)
    assert (await pw.post("bert", f"/karten/{k['id']}/anhaenge/entfernen", {"name": "Skizze.png"})).status_code == 403
    r = await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", {"dateien": [{"datei": "x"}]})
    assert r.status_code == 403
    assert [e.name for e in ABLAGE.im_zweig()] == ["Skizze.png"]
    # öffnen darf jedes Mitglied, auch als Leser; wer nicht im Board ist, nicht
    a = (await karte(pw, "anna"))["anhaenge"][0]
    assert (await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{a['datei']}", headers=pw.kopf["bert"])).status_code == 200
    assert (await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{a['datei']}", headers=pw.kopf["cora"])).status_code == 403


# --- Aufräumen, wenn etwas scheitert ----------------------------------------------------------------------------

async def test_scheitert_das_ablegen_kommen_die_abgelegten_weg(pw: Pinnwand):
    _, k = await mit_bert(pw)
    ABLAGE.schreiben_frei = 1
    r = await hochladen(pw, "anna", k, ("a.txt", b"a", ""), ("b.txt", b"b", ""))
    assert (r.status_code, r.json()["detail"]) == (503, "Nicht angehängt: Die Kellerwolke ist gerade nicht erreichbar")
    assert ABLAGE.im_zweig() == [] and (await karte(pw, "anna"))["anhaenge"] == []
    eintraege = (await pw.get("anna", "/protokoll", params={"ereignis": "anhang.verworfen"})).json()["eintraege"]
    assert [e["text"] for e in eintraege] == [
        "Apps/Pinnwand/Haushalt/a.txt in den Papierkorb der Kellerwolke (Nicht angehängt: Die Kellerwolke ist gerade "
        "nicht erreichbar)"]


async def test_scheitert_das_festhalten_kommt_die_datei_weg(pw: Pinnwand, monkeypatch: pytest.MonkeyPatch):
    _, k = await mit_bert(pw)
    monkeypatch.setattr(anhaenge, "JE_KARTE", 1)
    await hochladen(pw, "anna", k, ("a.txt", b"a", ""))
    r = await hochladen(pw, "anna", k, ("b.txt", b"b", ""))
    assert (r.status_code, r.json()["detail"]) == (400, "Eine Karte hat höchstens 1 Anhänge")
    assert [e.name for e in ABLAGE.im_zweig()] == ["a.txt"]
    # geht auch das Wegräumen nicht, bleibt die Datei nicht stillschweigend liegen: sie steht im Protokoll
    ABLAGE.loeschen_geht = False
    await hochladen(pw, "anna", k, ("c.txt", b"c", ""))
    assert sorted(e.name for e in ABLAGE.im_zweig()) == ["a.txt", "c.txt"]
    eintraege = (await pw.get("anna", "/protokoll", params={"ereignis": "anhang.liegengeblieben"})).json()["eintraege"]
    assert len(eintraege) == 1 and eintraege[0]["stufe"] == "warnung"
    assert eintraege[0]["text"].startswith("Apps/Pinnwand/Haushalt/c.txt ist abgelegt, hängt aber an keiner Karte "
                                           "(Eine Karte hat höchstens 1 Anhänge)")


# --- Aus der eigenen Kellerwolke --------------------------------------------------------------------------------

async def test_verknuepfen_aus_der_eigenen_kellerwolke(pw: Pinnwand):
    _, k = await mit_bert(pw)
    kalkulation = ABLAGE.datei("bert", "Dokumente/Angebote/Kalkulation 2026.ods", b"x" * 90_000)
    ABLAGE.datei("anna", "Dokumente/Geheim.pdf", b"anna")
    wurzel = (await pw.get("bert", "/anhaenge/kellerwolke")).json()
    assert wurzel["kette"] == [{"id": None, "name": "Meine Dateien"}]
    assert [(e["name"], e["typ"]) for e in wurzel["eintraege"]] == [("Dokumente", "ordner")]
    dokumente = (await pw.get("bert", "/anhaenge/kellerwolke", params={"ordner": wurzel["eintraege"][0]["id"]})).json()
    angebote = dokumente["eintraege"][0]["id"]
    seite = (await pw.get("bert", "/anhaenge/kellerwolke", params={"ordner": angebote})).json()
    assert [g["name"] for g in seite["kette"]] == ["Meine Dateien", "Dokumente", "Angebote"]
    assert seite["eintraege"] == [{"id": kalkulation.id, "typ": "datei", "name": "Kalkulation 2026.ods", "ordner": angebote,
                                   "pfad": "Dokumente/Angebote", "groesse": "88 KB", "art": "tabelle"}]

    gewaehlt = {"dateien": [{"ordner": angebote, "datei": kalkulation.id}]}
    r = await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", gewaehlt)
    assert r.json()["meldung"] == "Kalkulation 2026.ods an HAUS-1 verknüpft; die Datei bleibt in deiner Kellerwolke"
    k2 = await karte(pw, "anna")
    assert k2["anhaenge"] == [{"name": "Kalkulation 2026.ods", "groesse": "88 KB", "art": "tabelle", "verknuepft": True,
                               "datei": kalkulation.id, "pfad": "Dokumente/Angebote/Kalkulation 2026.ods", "von": "2"}]
    assert verlauf(k2) == ["hat Kalkulation 2026.ods aus der Kellerwolke verknüpft"]
    assert ABLAGE.im_zweig() == []                      # nichts kopiert: die Datei bleibt, wo sie ist
    # schon verknüpft: nichts geschieht
    r = await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", gewaehlt)
    assert r.json() == {"meldung": None, "rueckgaengig": None, "geaendert": []}
    # verknüpfen lässt sich nur, was die Person in ihrer Kellerwolke sieht
    fremd = next(e for e in ABLAGE.eintraege.values() if e.name == "Geheim.pdf")
    r = await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", {"dateien": [{"datei": fremd.id}]})
    assert (r.status_code, r.json()["detail"]) == (404, "Diese Datei gibt es in deiner Kellerwolke nicht (mehr)")
    r = await pw.get("bert", "/anhaenge/kellerwolke", params={"ordner": "00000000-0000-0000-0000-000000000000"})
    assert (r.status_code, r.json()["detail"]) == (404, "Diesen Ordner gibt es in deiner Kellerwolke nicht (mehr)")


# --- Entfernen --------------------------------------------------------------------------------------------------

async def test_entfernen_mit_rueckgaengig(pw: Pinnwand):
    _, k = await mit_bert(pw)
    await hochladen(pw, "anna", k, ("Skizze.png", b"bild", "image/png"))
    kalkulation = ABLAGE.datei("bert", "Kalkulation.ods", b"zahlen")
    await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", {"dateien": [{"datei": kalkulation.id}]})

    r = await pw.post("anna", f"/karten/{k['id']}/anhaenge/entfernen", {"name": "Kalkulation.ods"})
    assert r.json()["meldung"] == "Verknüpfung zu Kalkulation.ods gelöst; die Datei bleibt in der Kellerwolke von bert"
    r = await pw.post("anna", f"/karten/{k['id']}/anhaenge/entfernen", {"name": "Skizze.png"})
    assert r.json()["meldung"] == "Skizze.png von HAUS-1 entfernt"
    k2 = await karte(pw, "anna")
    assert k2["anhaenge"] == [] and verlauf(k2)[-2:] == ["hat den Anhang Kalkulation.ods entfernt", "hat den Anhang Skizze.png entfernt"]
    assert [e.name for e in ABLAGE.im_zweig()] == ["Skizze.png"]          # die Datei bleibt in der Kellerwolke

    await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")
    assert [a["name"] for a in (await karte(pw, "anna"))["anhaenge"]] == ["Skizze.png"]
    r = await pw.post("anna", f"/karten/{k['id']}/anhaenge/entfernen", {"name": "Gibt es nicht.txt"})
    assert (r.status_code, r.json()["detail"]) == (404, "Den Anhang Gibt es nicht.txt gibt es an HAUS-1 nicht (mehr)")


# --- Öffnen -----------------------------------------------------------------------------------------------------

async def test_oeffnen_ueber_die_inhaltsadresse(pw: Pinnwand):
    _, k = await mit_bert(pw)
    await hochladen(pw, "anna", k, ("Skizze.png", b"\x89PNG bild", "image/png"), ("seite.html", b"<script>", "text/html"))
    bild, seite = (await karte(pw, "anna"))["anhaenge"]
    # ein Link sendet keinen Kopf: das Inhalts-Cookie der Anmeldung gilt unter /api/v1/inhalt
    assert (await pw.c.post("/api/v1/anmeldung/zugang", headers=pw.kopf["bert"])).status_code == 204
    r = await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{bild['datei']}")
    assert (r.status_code, r.content, r.headers["content-type"]) == (200, b"\x89PNG bild", "image/png")
    assert r.headers["content-disposition"] == "inline; filename*=UTF-8''Skizze.png"
    r = await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{bild['datei']}", headers={"Range": "bytes=0-3"})
    assert (r.status_code, r.content) == (206, b"\x89PNG")
    # was im Browser laufen könnte, kommt als Download
    r = await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{seite['datei']}")
    assert r.headers["content-disposition"].startswith("attachment;") and r.headers["x-content-type-options"] == "nosniff"
    r = await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/gibt-es-nicht")
    assert (r.status_code, r.json()["detail"]) == (404, "Diesen Anhang gibt es an HAUS-1 nicht (mehr)")
    # eine verknüpfte Datei aus der Kellerwolke einer Person kann die Pinnwand nicht lesen (sie öffnet sich dort)
    eigene = ABLAGE.datei("bert", "Notiz.txt", b"privat", "text/plain")
    await pw.post("bert", f"/karten/{k['id']}/anhaenge/aus-kellerwolke", {"dateien": [{"datei": eigene.id}]})
    r = await pw.c.get(f"/api/v1/inhalt/anhaenge/{k['id']}/{eigene.id}")
    assert (r.status_code, r.json()["detail"]) == (404, "Diese Datei kann die Pinnwand in der Kellerwolke nicht (mehr) lesen")
