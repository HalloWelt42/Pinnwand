"""Nachbesserungen nach den Stufen 1 bis 3: Rückgängig trotz gelesenem Hinweis, Schlüssel im Hinweis, das Konto nach
Rückgängig neu gelesen, Namen von Terminen außerhalb des Stands."""

from __future__ import annotations

from datetime import datetime

from conftest import Pinnwand
from test_hinweise import bearbeiten, hinweise, zu_dritt
from test_verwaltung import ok


async def test_rueckgaengig_trotz_gelesenem_hinweis(pw: Pinnwand):
    b = await zu_dritt(pw)
    k = await pw.karte("anna", b, "Fenster")
    r = await bearbeiten(pw, "anna", k, {"zustaendig": ["1", "2"]})
    [h] = await hinweise(pw, "bert")
    assert h["schluessel"] == "HAUS-1"                       # führt auch zu einer archivierten Karte
    await ok(pw, "bert", f"/hinweise/{h['id']}/gelesen", {"gelesen": True})
    assert (await pw.post("anna", f"/rueckgaengig/{r.json()['rueckgaengig']}")).status_code == 200
    assert await hinweise(pw, "bert") == []


async def test_konto_nach_rueckgaengig_neu_gelesen(pw: Pinnwand):
    konten = pw.app.state.dienste.konten
    a = await ok(pw, "anna", "/ich/kuerzel", {"kuerzel": "AX"})
    await pw.stand("anna")
    assert konten._bekannt["1"].kuerzel == "AX"
    await ok(pw, "anna", f"/rueckgaengig/{a['rueckgaengig']}")
    await pw.stand("anna")
    assert konten._bekannt["1"].kuerzel != "AX"


async def test_terminname_ausserhalb_des_stands(pw: Pinnwand):
    b = await zu_dritt(pw)
    await ok(pw, "anna", "/termine", {"board": b["id"], "titel": "Abstimmung", "datum": "2026-10-27", "von": "09:00",
                                      "bis": "10:00", "teilnehmer": ["1", "2"]})
    [t] = (await pw.stand("bert"))["termine"]
    pw.zeiger.zeit = datetime(2026, 10, 28, 10)
    await ok(pw, "bert", f"/termine/{t['id']}/bestaetigen")
    await ok(pw, "anna", f"/boards/{b['id']}/mitglieder/entfernen", {"kellerwolke": "bert"})
    s = await pw.stand("bert")
    assert s["termine"] == [] and [e["termin"] for e in s["zeiteintraege"]] == [t["id"]]
    assert s["terminnamen"] == [{"termin": t["id"], "board": b["id"], "titel": "Abstimmung", "datum": "2026-10-27"}]


async def test_zusammenfuehren_nennt_die_geltende_zeit(pw: Pinnwand):
    b = await pw.board("anna")
    a, c, d, e = [await pw.karte("anna", b, t) for t in ("Fenster", "Rahmen", "Dach", "Rinne")]
    await ok(pw, "anna", f"/karten/{a['id']}/verknuepfen", {"mit": c["id"]})
    await ok(pw, "anna", f"/karten/{d['id']}/verknuepfen", {"mit": e["id"]})
    s = await pw.stand("anna")
    erste = next(x for x in s["karten"] if x["id"] == a["id"])["gruppe"]
    await ok(pw, "anna", f"/gruppen/{erste}/zeit-teilen", {"an": False})
    m = (await ok(pw, "anna", f"/karten/{a['id']}/verknuepfen", {"mit": d["id"]}))["meldung"]
    assert m == ("HAUS-1 und HAUS-3 verknüpft: ziehen zusammen, Zeit wird nicht geteilt; "
                 "es gilt die Einstellung der Verknüpfung von HAUS-1")
