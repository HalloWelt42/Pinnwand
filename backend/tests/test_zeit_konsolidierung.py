"""Tests fuer die Zusammenfassung automatischer Start/Stopp-Zeiten.

Viele Start/Stopp-Sitzungen derselben Karte am selben Tag sollen nicht als viele
Fragmente in den Uebersichten landen, sondern zu EINEM automatischen Eintrag je
Karte+Tag verschmolzen werden. Die erfasste Zeit (Summe) bleibt dabei exakt gleich -
es ist eine Zusammenfassung, kein Verlust. Manuelle Buchungen bleiben eigenstaendig.
"""
from __future__ import annotations

from datetime import date

from module.kanban_kern import persistence


def _board(client):
    m = client.post("/api/kanban/mappen", json={"titel": "KZ-Mappe"})
    assert m.status_code == 201, m.text
    b = client.post(f"/api/kanban/mappen/{m.json()['id']}/boards", json={"titel": "KZ-Board"})
    assert b.status_code == 201, b.text
    return b.json()


def _karte(client, board_id, spalte, titel):
    r = client.post("/api/kanban/karten", json={"board_id": board_id, "spalte": spalte, "titel": titel})
    assert r.status_code == 201, r.text
    return r.json()


def _karte_aus_board(client, board_id, karte_id):
    d = client.get(f"/api/kanban/boards/{board_id}").json()
    return next(k for k in d["karten"] if k["id"] == karte_id)


def _auto_fragment(conn, eintrag_id, karte_id, board_id, datum, stunde, sekunden):
    conn.execute(
        "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell)"
        " VALUES (?, ?, ?, NULL, ?, ?, ?, ?, NULL, 0)",
        (eintrag_id, karte_id, board_id, datum, f"{datum}T{stunde:02d}:00:00", f"{datum}T{stunde:02d}:10:00", sekunden),
    )


def test_fragmente_werden_je_karte_und_tag_zusammengefasst(client):
    """Drei automatische Fragmente am selben Tag -> ein Eintrag, Summe exakt erhalten;
    eine manuelle Buchung bleibt separat; ein zweiter Tag bleibt eine eigene Zeile."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Viel Start/Stopp")

    with persistence._verb() as conn:
        _auto_fragment(conn, "zf_a1", k["id"], board["id"], "2026-06-22", 8, 120)
        _auto_fragment(conn, "zf_a2", k["id"], board["id"], "2026-06-22", 9, 300)
        _auto_fragment(conn, "zf_a3", k["id"], board["id"], "2026-06-22", 10, 75)
        _auto_fragment(conn, "zf_b1", k["id"], board["id"], "2026-06-23", 8, 600)
        _auto_fragment(conn, "zf_b2", k["id"], board["id"], "2026-06-23", 11, 200)

    # Manuelle Buchung am selben Tag wie die Fragmente (mit Kommentar) -> bleibt eigenstaendig.
    r = client.post("/api/kanban/zeiteintraege", json={"karte_id": k["id"], "datum": "2026-06-22", "sekunden": 600, "kommentar": "Meeting"})
    assert r.status_code in (200, 201), r.text

    with persistence._verb() as conn:
        betroffen = persistence._konsolidiere_auto_zeiten(conn)
    assert betroffen >= 1

    eintraege = persistence.zeiteintraege_range(karte_id=k["id"])
    auto = [e for e in eintraege if not e.manuell]
    manuell = [e for e in eintraege if e.manuell]

    # Pro Tag genau ein automatischer Eintrag (statt fuenf Fragmenten).
    auto_pro_tag = {e.datum: e.sekunden for e in auto}
    assert auto_pro_tag == {"2026-06-22": 495, "2026-06-23": 800}
    # Frueheste Start- und spaeteste End-Zeit des Tages bleiben erhalten.
    tag22 = next(e for e in auto if e.datum == "2026-06-22")
    assert tag22.start == "2026-06-22T08:00:00"
    assert tag22.ende == "2026-06-22T10:10:00"

    # Manuelle Buchung bleibt separat (Kommentar geht nicht verloren).
    assert len(manuell) == 1
    assert manuell[0].sekunden == 600
    assert manuell[0].kommentar == "Meeting"

    # Ticketzeit = Summe ueber alles, exakt unveraendert (495 + 800 + 600).
    ka = _karte_aus_board(client, board["id"], k["id"])
    assert ka["erfasst_sek"] == 495 + 800 + 600

    # Eine Roh-Sicherung der Fragmente wurde angelegt.
    with persistence._verb() as conn:
        assert conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'zeiteintrag_roh_backup'"
        ).fetchone() is not None


def test_pause_fasst_sitzungen_desselben_tages_zusammen(client):
    """Zwei Start/Stopp-Sitzungen am selben Tag erzeugen nur EINEN automatischen
    Eintrag (zweite Sitzung wird in den ersten Tageseintrag eingerechnet)."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Zwei Sitzungen")
    heute = date.today().isoformat()

    # Erste Sitzung: lief seit heute frueh -> Pause schreibt einen Tageseintrag.
    with persistence._verb() as conn:
        conn.execute("UPDATE karte SET laeuft_seit = ? WHERE id = ?", (f"{heute}T00:00:01", k["id"]))
    persistence.timer_pause(k["id"])
    # Zweite Sitzung am selben Tag -> wird in denselben Tageseintrag eingerechnet.
    with persistence._verb() as conn:
        conn.execute("UPDATE karte SET laeuft_seit = ? WHERE id = ?", (f"{heute}T00:00:03", k["id"]))
    persistence.timer_pause(k["id"])

    auto_heute = [e for e in persistence.zeiteintraege_range(karte_id=k["id"]) if not e.manuell and e.datum == heute]
    assert len(auto_heute) == 1
    assert auto_heute[0].sekunden > 0


def test_konsolidierung_ist_idempotent(client):
    """Ein zweiter Lauf ohne neue Fragmente aendert nichts mehr (betroffen = 0)."""
    board = _board(client)
    spalte = board["spalten"][0]["id"]
    k = _karte(client, board["id"], spalte, "Idempotenz")
    with persistence._verb() as conn:
        _auto_fragment(conn, "zi_1", k["id"], board["id"], "2026-07-01", 8, 100)
        _auto_fragment(conn, "zi_2", k["id"], board["id"], "2026-07-01", 9, 200)
    with persistence._verb() as conn:
        assert persistence._konsolidiere_auto_zeiten(conn) >= 1
    with persistence._verb() as conn:
        assert persistence._konsolidiere_auto_zeiten(conn) == 0
    auto = [e for e in persistence.zeiteintraege_range(karte_id=k["id"]) if not e.manuell]
    assert len(auto) == 1 and auto[0].sekunden == 300
