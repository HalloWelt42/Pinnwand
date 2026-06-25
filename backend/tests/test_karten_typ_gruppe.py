"""Tests fuer Karten-Typ (Idee) und verknuepfte Aufgaben mit geteilter Zeit.

Geprueft wird:
- Ideentickets erfassen keine Zeit: der Timer-Start wird abgewiesen.
- Verknuepfte Karten bilden eine Zeitgruppe; die kombinierte Zeit (gruppe_sek) ist
  die Summe ueber alle Mitglieder, wird aber NUR ANGEZEIGT - die echten Zeiteintraege
  bleiben je Karte, also zaehlt jede Sekunde genau einmal.
- Der Spezialfall "Zeit getrennt zaehlen" (zeit_geteilt=false) zeigt je Karte die
  eigene Zeit statt der Gruppensumme.
- Loesen einer Verknuepfung loest eine Gruppe mit nur noch einem Mitglied auf.
- Verknuepfte Tickets ziehen bei Spaltenwechsel als Gruppe mit; reines Umsortieren
  innerhalb einer Spalte laesst die Gruppe unberuehrt.
"""
from __future__ import annotations


def _board(client):
    m = client.post("/api/kanban/mappen", json={"titel": "TG-Mappe"})
    assert m.status_code == 201, m.text
    b = client.post(f"/api/kanban/mappen/{m.json()['id']}/boards", json={"titel": "TG-Board"})
    assert b.status_code == 201, b.text
    return b.json()


def _karte(client, board_id, spalte, titel, typ="arbeit"):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel, "typ": typ})
    assert r.status_code == 201, r.text
    return r.json()


def _buche(client, karte_id, datum, sekunden):
    r = client.post("/api/kanban/zeiteintraege", json={"karte_id": karte_id, "datum": datum, "sekunden": sekunden})
    assert r.status_code in (200, 201), r.text


def _karte_aus_board(client, board_id, karte_id):
    d = client.get(f"/api/kanban/boards/{board_id}").json()
    return next(k for k in d["karten"] if k["id"] == karte_id)


def _move(client, karte_id, spalte, reihenfolge=0):
    r = client.post(f"/api/kanban/karten/{karte_id}/move", json={"spalte": spalte, "reihenfolge": reihenfolge})
    assert r.status_code == 200, r.text
    return r.json()


def test_ideenticket_blockt_timer(client):
    """Ein Ideenticket (typ=idee) darf nicht per Play gestartet werden -> 409."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    idee = _karte(client, board["id"], spalte, "Nur eine Idee", typ="idee")
    assert idee["typ"] == "idee"
    r = client.post(f"/api/kanban/karten/{idee['id']}/timer/start")
    assert r.status_code == 409, r.text


def test_gruppe_zeit_geteilt_zaehlt_einmal(client):
    """Verknuepfte Karten zeigen die kombinierte Zeit (Summe), aber die echte Zeit
    bleibt je Karte erhalten - es wird nichts dupliziert."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    a = _karte(client, board["id"], spalte, "Gruppe A")
    b = _karte(client, board["id"], spalte, "Gruppe B")
    _buche(client, a["id"], "2026-06-20", 3600)
    _buche(client, b["id"], "2026-06-20", 1800)

    r = client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": b["id"]})
    assert r.status_code == 200, r.text

    ka = _karte_aus_board(client, board["id"], a["id"])
    kb = _karte_aus_board(client, board["id"], b["id"])
    # Eigene Ticketzeit bleibt je Karte (nicht dupliziert).
    assert ka["erfasst_sek"] == 3600
    assert kb["erfasst_sek"] == 1800
    # Kombinierte Anzeige = Summe ueber die Gruppe, auf beiden Karten gleich.
    assert ka["gruppe_sek"] == 5400
    assert kb["gruppe_sek"] == 5400
    assert ka["gruppe_zeit_geteilt"] is True
    assert {m["id"] for m in ka["gruppe_mitglieder"]} == {b["id"]}
    assert ka["gruppe_id"] == kb["gruppe_id"]


def test_spezialfall_getrennt_zaehlen(client):
    """Mit zeit_geteilt=false zeigt jede Karte wieder ihre eigene Zeit."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    a = _karte(client, board["id"], spalte, "S A")
    b = _karte(client, board["id"], spalte, "S B")
    _buche(client, a["id"], "2026-06-21", 1200)
    _buche(client, b["id"], "2026-06-21", 600)
    client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": b["id"]})

    gid = _karte_aus_board(client, board["id"], a["id"])["gruppe_id"]
    r = client.patch(f"/api/kanban/gruppen/{gid}", json={"zeit_geteilt": False})
    assert r.status_code == 204, r.text

    ka = _karte_aus_board(client, board["id"], a["id"])
    kb = _karte_aus_board(client, board["id"], b["id"])
    assert ka["gruppe_zeit_geteilt"] is False
    assert ka["gruppe_sek"] == 1200   # eigene Zeit, nicht die Summe
    assert kb["gruppe_sek"] == 600


def test_verknuepfung_loesen_loest_kleine_gruppe_auf(client):
    """Bleibt nach dem Loesen nur eine Karte uebrig, wird die Gruppe ganz aufgeloest."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    a = _karte(client, board["id"], spalte, "L A")
    b = _karte(client, board["id"], spalte, "L B")
    client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": b["id"]})
    assert _karte_aus_board(client, board["id"], a["id"])["gruppe_id"]

    r = client.post(f"/api/kanban/karten/{a['id']}/verknuepfung-loesen")
    assert r.status_code == 200, r.text
    # Beide Karten sind danach ohne Gruppe.
    assert _karte_aus_board(client, board["id"], a["id"])["gruppe_id"] is None
    assert _karte_aus_board(client, board["id"], b["id"])["gruppe_id"] is None


def test_gruppe_zieht_bei_spaltenwechsel_mit(client):
    """Wird eine verknuepfte Karte in eine andere Spalte gezogen, folgen alle
    Gruppen-Mitglieder (auch aus dritten Spalten) in die Zielspalte."""
    board = _board(client)
    s_offen, s_arbeit, s_fertig = (board["spalten"][i]["id"] for i in range(3))
    a = _karte(client, board["id"], s_offen, "MZ A")
    b = _karte(client, board["id"], s_offen, "MZ B")
    c = _karte(client, board["id"], s_fertig, "MZ C")
    # Alle drei in eine Gruppe (a-b und a-c).
    client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": b["id"]})
    client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": c["id"]})

    _move(client, a["id"], s_arbeit, 0)

    # a, b und c stehen jetzt alle in der Zielspalte (In Arbeit).
    assert _karte_aus_board(client, board["id"], a["id"])["spalte"] == s_arbeit
    assert _karte_aus_board(client, board["id"], b["id"])["spalte"] == s_arbeit
    assert _karte_aus_board(client, board["id"], c["id"])["spalte"] == s_arbeit


def test_umsortieren_in_spalte_zieht_gruppe_nicht(client):
    """Reines Umsortieren innerhalb derselben Spalte (kein Spaltenwechsel) laesst
    Gruppen-Mitglieder in anderen Spalten unberuehrt."""
    board = _board(client)
    s_offen, s_arbeit, _ = (board["spalten"][i]["id"] for i in range(3))
    a = _karte(client, board["id"], s_offen, "US A")
    b = _karte(client, board["id"], s_arbeit, "US B")  # Mitglied in anderer Spalte
    client.post(f"/api/kanban/karten/{a['id']}/verknuepfen", json={"ziel_karte_id": b["id"]})

    # a innerhalb von s_offen umsortieren (Quelle == Ziel).
    _move(client, a["id"], s_offen, 0)

    # b bleibt in seiner Spalte, wird NICHT mitgezogen.
    assert _karte_aus_board(client, board["id"], a["id"])["spalte"] == s_offen
    assert _karte_aus_board(client, board["id"], b["id"])["spalte"] == s_arbeit
