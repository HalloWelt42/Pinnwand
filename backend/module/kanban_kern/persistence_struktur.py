"""Persistenz der Struktur: Projektmappen, Boards und Spalten.

Enthält auch die Mitgliedschafts-/Sichtbarkeitsregeln je Person und den
Projekt-Aufwand (Mappe = Projekt).
"""
from __future__ import annotations

import re
import sqlite3
from uuid import uuid4

from .models import (
    Board,
    BoardDetail,
    MappeUpdate,
    ProjektAufwand,
    ProjektBoardAufwand,
    ProjektDetail,
    ProjektPersonAufwand,
    Projektmappe,
    Spalte,
    SpalteUpdate,
)
from .persistence_basis import _verb
from .persistence_karten import (
    _karte_aus_row,
    _loesche_serien_fuer_boards,
    _raeume_karten_restdaten,
    _reichere_gruppen_an,
)


def _spalten(conn: sqlite3.Connection, board_id: str) -> list[Spalte]:
    rows = conn.execute(
        "SELECT * FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)
    ).fetchall()
    return [Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"], erledigt=bool(r["erledigt"])) for r in rows]


def liste_mappen(person_id: str | None = None, alle: bool = True) -> list[Projektmappe]:
    """Projektmappen. alle=True (Admin/offener Modus): alle. Sonst nur Mappen, die
    entweder KEINE Mitglieder haben (geteilt) ODER in denen die Person Mitglied ist."""
    with _verb() as conn:
        if alle or not person_id:
            rows = conn.execute("SELECT * FROM mappe ORDER BY titel").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mappe m WHERE"
                " NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
                " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)"
                " ORDER BY titel",
                (person_id,),
            ).fetchall()
    return [Projektmappe(**dict(r)) for r in rows]


# -- Projekt-Mitgliedschaft (Sichtbarkeit von Mappen/Projekten je Person) --------
# Regel: eine Mappe OHNE Mitglieder ist fuer alle sichtbar (geteilt, rueckwaerts-
# kompatibel). Sobald Mitglieder hinterlegt sind, sehen nur diese (plus Admin) sie.

def mappe_mitglieder(mappe_id: str) -> list[str]:
    with _verb() as conn:
        rows = conn.execute("SELECT person_id FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,)).fetchall()
    return [r[0] for r in rows]


def mappe_sichtbar_fuer(mappe_id: str, person_id: str | None) -> bool:
    with _verb() as conn:
        anzahl = conn.execute("SELECT COUNT(*) FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,)).fetchone()[0]
        if anzahl == 0:
            return True
        if not person_id:
            return False
        treffer = conn.execute(
            "SELECT 1 FROM mappe_mitglied WHERE mappe_id = ? AND person_id = ?", (mappe_id, person_id)
        ).fetchone()
    return treffer is not None


def setze_mappe_mitglied(mappe_id: str, person_id: str) -> None:
    with _verb() as conn:
        conn.execute("INSERT OR IGNORE INTO mappe_mitglied (mappe_id, person_id) VALUES (?, ?)", (mappe_id, person_id))


def entferne_mappe_mitglied(mappe_id: str, person_id: str) -> bool:
    with _verb() as conn:
        cur = conn.execute("DELETE FROM mappe_mitglied WHERE mappe_id = ? AND person_id = ?", (mappe_id, person_id))
    return cur.rowcount > 0


def gruppe_mappe_id(gruppe_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM karte k JOIN board b ON b.id = k.board_id WHERE k.gruppe_id = ? LIMIT 1",
            (gruppe_id,),
        ).fetchone()
    return r[0] if r else None


def karte_mappe_id(karte_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM karte k JOIN board b ON b.id = k.board_id WHERE k.id = ?", (karte_id,)
        ).fetchone()
    return r[0] if r else None


def spalte_mappe_id(spalte_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute(
            "SELECT b.mappe_id FROM spalte s JOIN board b ON b.id = s.board_id WHERE s.id = ?", (spalte_id,)
        ).fetchone()
    return r[0] if r else None


def sichtbare_mappen_ids(person_id: str | None) -> set[str]:
    """Alle Mappen, die diese Person sehen darf (memberlos = geteilt)."""
    with _verb() as conn:
        rows = conn.execute(
            "SELECT m.id FROM mappe m WHERE"
            " NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
            " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)",
            (person_id,),
        ).fetchall()
    return {r[0] for r in rows}


def board_mappe_id(board_id: str) -> str | None:
    with _verb() as conn:
        r = conn.execute("SELECT mappe_id FROM board WHERE id = ?", (board_id,)).fetchone()
    return r[0] if r else None


def zaehle_mappen() -> int:
    with _verb() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM mappe").fetchone()[0])


def erstelle_mappe(mappe_id: str, titel: str, beschreibung: str | None = None) -> Projektmappe:
    """Legt eine Projektmappe an und gibt ihr direkt ein erstes nutzbares Board mit."""
    with _verb() as conn:
        conn.execute("INSERT INTO mappe (id, titel, beschreibung) VALUES (?, ?, ?)",
                     (mappe_id, titel, beschreibung))
    erstelle_board(f"b_{uuid4().hex[:8]}", mappe_id, "Aufgaben")
    return Projektmappe(id=mappe_id, titel=titel, beschreibung=beschreibung)


def aktualisiere_mappe(mappe_id: str, felder: dict) -> Projektmappe | None:
    erlaubt = {k: v for k, v in felder.items() if k in MappeUpdate.model_fields}
    with _verb() as conn:
        if erlaubt:
            sql = ", ".join(f"{k} = ?" for k in erlaubt)
            conn.execute(f"UPDATE mappe SET {sql} WHERE id = ?", (*erlaubt.values(), mappe_id))
        r = conn.execute("SELECT * FROM mappe WHERE id = ?", (mappe_id,)).fetchone()
    return Projektmappe(**dict(r)) if r else None


# -- Projekt-Aufwand (Mappe = Projekt) --------------------------------------------
# Ist = tatsaechlich erfasste Zeit (zeiteintrag.sekunden als SSOT), Soll = Summe der
# Karten-Schaetzungen (karte.schaetzung_min). Bewusst getrennt gehalten. Die
# Sichtbarkeit folgt derselben Mitgliedschaftsregel wie liste_mappen.

def _sichtbarkeits_klausel(alle: bool, person_id: str | None) -> tuple[str, tuple]:
    if alle or not person_id:
        return "", ()
    return (
        " WHERE NOT EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id)"
        " OR EXISTS (SELECT 1 FROM mappe_mitglied x WHERE x.mappe_id = m.id AND x.person_id = ?)",
        (person_id,),
    )


def projekt_aufwand_liste(person_id: str | None = None, alle: bool = True) -> list[ProjektAufwand]:
    klausel, params = _sichtbarkeits_klausel(alle, person_id)
    sql = (
        "SELECT m.id AS mappe_id, m.titel, COALESCE(m.status, 'aktiv') AS status,"
        " m.owner, m.budget_min,"
        " (SELECT COALESCE(SUM(z.sekunden), 0) FROM zeiteintrag z WHERE z.mappe_id = m.id) AS ist_sekunden,"
        " (SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k JOIN board b ON k.board_id = b.id"
        "  WHERE b.mappe_id = m.id) AS soll_minuten,"
        " (SELECT COUNT(*) FROM karte k JOIN board b ON k.board_id = b.id WHERE b.mappe_id = m.id) AS karten,"
        " (SELECT COUNT(*) FROM board b WHERE b.mappe_id = m.id) AS boards"
        " FROM mappe m" + klausel + " ORDER BY m.titel"
    )
    with _verb() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [ProjektAufwand(**dict(r)) for r in rows]


def projekt_detail(mappe_id: str) -> ProjektDetail | None:
    with _verb() as conn:
        m = conn.execute(
            "SELECT id, titel, COALESCE(status, 'aktiv') AS status, owner, budget_min"
            " FROM mappe WHERE id = ?", (mappe_id,)
        ).fetchone()
        if not m:
            return None
        ist = conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) FROM zeiteintrag WHERE mappe_id = ?", (mappe_id,)
        ).fetchone()[0]
        soll = conn.execute(
            "SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k JOIN board b ON k.board_id = b.id"
            " WHERE b.mappe_id = ?", (mappe_id,)
        ).fetchone()[0]
        boards = conn.execute(
            "SELECT b.id AS board_id, b.titel,"
            " (SELECT COALESCE(SUM(z.sekunden), 0) FROM zeiteintrag z WHERE z.board_id = b.id) AS ist_sekunden,"
            " (SELECT COALESCE(SUM(k.schaetzung_min), 0) FROM karte k WHERE k.board_id = b.id) AS soll_minuten,"
            " (SELECT COUNT(*) FROM karte k WHERE k.board_id = b.id) AS karten"
            " FROM board b WHERE b.mappe_id = ? ORDER BY b.laufnummer, b.titel", (mappe_id,)
        ).fetchall()
        personen = conn.execute(
            "SELECT COALESCE(z.kuerzel, k.zustaendig) AS kuerzel, COALESCE(SUM(z.sekunden), 0) AS ist_sekunden"
            " FROM zeiteintrag z LEFT JOIN karte k ON z.karte_id = k.id"
            " WHERE z.mappe_id = ? GROUP BY COALESCE(z.kuerzel, k.zustaendig) ORDER BY ist_sekunden DESC", (mappe_id,)
        ).fetchall()
    d = dict(m)
    return ProjektDetail(
        mappe_id=d["id"],
        titel=d["titel"],
        status=d["status"],
        owner=d["owner"],
        budget_min=d["budget_min"],
        ist_sekunden=ist,
        soll_minuten=soll,
        boards=[ProjektBoardAufwand(**dict(b)) for b in boards],
        personen=[ProjektPersonAufwand(**dict(p)) for p in personen],
    )


def loesche_mappe(mappe_id: str) -> tuple[bool, list[str]]:
    """Loescht die Mappe samt aller Boards, Spalten, Karten und Zeiteintraege.

    Die letzte verbliebene Mappe bleibt erhalten, damit die Anwendung immer eine
    nutzbare Mappe hat.
    """
    with _verb() as conn:
        if conn.execute("SELECT COUNT(*) FROM mappe").fetchone()[0] <= 1:
            return False, []
        board_ids = [r[0] for r in conn.execute("SELECT id FROM board WHERE mappe_id = ?", (mappe_id,)).fetchall()]
        alle_karten: list[str] = []
        for bid in board_ids:
            karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (bid,)).fetchall()]
            alle_karten.extend(karten)
            _raeume_karten_restdaten(conn, karten)
            conn.execute("DELETE FROM karte WHERE board_id = ?", (bid,))
            conn.execute("DELETE FROM spalte WHERE board_id = ?", (bid,))
        _loesche_serien_fuer_boards(conn, board_ids)
        conn.execute("DELETE FROM dokument WHERE kontext = 'mappe' AND kontext_id = ?", (mappe_id,))
        conn.execute("DELETE FROM zeiteintrag WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM board WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM mappe_mitglied WHERE mappe_id = ?", (mappe_id,))
        conn.execute("DELETE FROM mappe WHERE id = ?", (mappe_id,))
    return True, alle_karten


def liste_boards(mappe_id: str) -> list[Board]:
    with _verb() as conn:
        rows = conn.execute("SELECT * FROM board WHERE mappe_id = ? ORDER BY titel", (mappe_id,)).fetchall()
        return [
            Board(id=r["id"], mappe_id=r["mappe_id"], titel=r["titel"], kuerzel=r["kuerzel"], spalten=_spalten(conn, r["id"]))
            for r in rows
        ]


def board_detail(board_id: str) -> BoardDetail | None:
    with _verb() as conn:
        b = conn.execute("SELECT * FROM board WHERE id = ?", (board_id,)).fetchone()
        if b is None:
            return None
        spalten = _spalten(conn, board_id)
        # Karten in Erledigt-Spalten werden hier NICHT geladen - sie kommen gefenstert
        # ueber fertige_seite() (Zeitfilter + Anzahl-Deckel + Nachladen), damit das Board
        # bei vielen fertigen Karten nicht geflutet wird. Sehr alte fertige Karten liegen
        # ausserdem im Archiv (archiv_seite). Offene Spalten werden voll geladen.
        rows = conn.execute(
            "SELECT k.* FROM karte k JOIN spalte s ON k.spalte = s.id "
            "WHERE k.board_id = ? AND s.erledigt = 0 ORDER BY k.reihenfolge, k.id",
            (board_id,),
        ).fetchall()
        karten = [_karte_aus_row(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return BoardDetail(
        id=b["id"], mappe_id=b["mappe_id"], titel=b["titel"], kuerzel=b["kuerzel"],
        spalten=spalten, karten=karten,
    )


def hole_spalte(spalte_id: str) -> Spalte | None:
    with _verb() as conn:
        r = conn.execute("SELECT * FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
    return Spalte(id=r["id"], titel=r["titel"], wip_limit=r["wip_limit"], reihenfolge=r["reihenfolge"], erledigt=bool(r["erledigt"])) if r else None


# -- Spalten schreiben ----------------------------------------------------

def _kompaktiere_spalten(conn: sqlite3.Connection, board_id: str) -> None:
    rows = conn.execute("SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (board_id,)).fetchall()
    for index, r in enumerate(rows):
        conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, r["id"]))


def erstelle_spalte(spalte_id: str, board_id: str, titel: str, wip_limit: int | None) -> Spalte:
    with _verb() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(reihenfolge), -1) AS m FROM spalte WHERE board_id = ?", (board_id,)
        ).fetchone()
        conn.execute(
            "INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge) VALUES (?, ?, ?, ?, ?)",
            (spalte_id, board_id, titel, wip_limit, int(row["m"]) + 1),
        )
    spalte = hole_spalte(spalte_id)
    assert spalte is not None
    return spalte


def aktualisiere_spalte(spalte_id: str, aenderungen: dict) -> Spalte | None:
    felder = {k: v for k, v in aenderungen.items() if k in SpalteUpdate.model_fields}
    if not felder:
        return hole_spalte(spalte_id)
    zuweisung = ", ".join(f"{k} = ?" for k in felder)
    with _verb() as conn:
        conn.execute(f"UPDATE spalte SET {zuweisung} WHERE id = ?", (*felder.values(), spalte_id))
    return hole_spalte(spalte_id)


def setze_erledigt_spalte(spalte_id: str) -> Spalte | None:
    """Markiert eine Spalte als Erledigt-Spalte des Boards (genau eine pro Board)."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return None
        conn.execute("UPDATE spalte SET erledigt = 0 WHERE board_id = ?", (r["board_id"],))
        conn.execute("UPDATE spalte SET erledigt = 1 WHERE id = ?", (spalte_id,))
    return hole_spalte(spalte_id)


def done_spalte_id(board_id: str) -> str | None:
    """Id der als Erledigt markierten Spalte, sonst die letzte Spalte als Rückfall."""
    with _verb() as conn:
        r = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? AND erledigt = 1 ORDER BY reihenfolge LIMIT 1",
            (board_id,),
        ).fetchone()
        if r:
            return r["id"]
        letzte = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge DESC, id DESC LIMIT 1",
            (board_id,),
        ).fetchone()
    return letzte["id"] if letzte else None


def verschiebe_spalte(spalte_id: str, richtung: int) -> Spalte | None:
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return None
        ids = [x["id"] for x in conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge, id", (r["board_id"],)
        ).fetchall()]
        idx = ids.index(spalte_id)
        ziel = idx + richtung
        if 0 <= ziel < len(ids):
            ids[idx], ids[ziel] = ids[ziel], ids[idx]
            for index, sid in enumerate(ids):
                conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, sid))
    return hole_spalte(spalte_id)


def setze_spalten_reihenfolge(board_id: str, spalten_ids: list[str]) -> bool:
    with _verb() as conn:
        vorhandene = {x["id"] for x in conn.execute("SELECT id FROM spalte WHERE board_id = ?", (board_id,)).fetchall()}
        if vorhandene != set(spalten_ids):
            return False
        for index, sid in enumerate(spalten_ids):
            conn.execute("UPDATE spalte SET reihenfolge = ? WHERE id = ?", (index, sid))
    return True


def loesche_spalte(spalte_id: str) -> tuple[str, list[str]]:
    """Löscht eine Spalte samt ihrer Karten. Liefert ('ok'|'letzte'|'fehlt', karten_ids)."""
    with _verb() as conn:
        r = conn.execute("SELECT board_id FROM spalte WHERE id = ?", (spalte_id,)).fetchone()
        if r is None:
            return "fehlt", []
        board_id = r["board_id"]
        anzahl = conn.execute("SELECT COUNT(*) AS n FROM spalte WHERE board_id = ?", (board_id,)).fetchone()["n"]
        if anzahl <= 1:
            return "letzte", []
        karten = [x[0] for x in conn.execute(
            "SELECT id FROM karte WHERE board_id = ? AND spalte = ?", (board_id, spalte_id)
        ).fetchall()]
        _raeume_karten_restdaten(conn, karten)
        conn.execute("DELETE FROM karte WHERE board_id = ? AND spalte = ?", (board_id, spalte_id))
        conn.execute("DELETE FROM spalte WHERE id = ?", (spalte_id,))
        _kompaktiere_spalten(conn, board_id)
    return "ok", karten


# -- Boards schreiben -----------------------------------------------------

def _kuerzel(titel: str) -> str:
    woerter = re.findall(r"[A-Za-z0-9]+", titel)
    if not woerter:
        return "B"
    if len(woerter) == 1:
        return woerter[0][:3].upper()
    return "".join(w[0] for w in woerter[:3]).upper()


def erstelle_board(board_id: str, mappe_id: str, titel: str) -> BoardDetail | None:
    with _verb() as conn:
        conn.execute(
            "INSERT INTO board (id, mappe_id, titel, kuerzel, laufnummer) VALUES (?, ?, ?, ?, 0)",
            (board_id, mappe_id, titel, _kuerzel(titel)),
        )
        for ordnung, titel_s in enumerate(["Offen", "In Arbeit", "Erledigt"]):
            conn.execute(
                "INSERT INTO spalte (id, board_id, titel, wip_limit, reihenfolge, erledigt) VALUES (?, ?, ?, ?, ?, ?)",
                (f"s_{uuid4().hex[:8]}", board_id, titel_s, None, ordnung, 1 if titel_s == "Erledigt" else 0),
            )
    return board_detail(board_id)


def aktualisiere_board(board_id: str, titel: str) -> Board | None:
    with _verb() as conn:
        conn.execute("UPDATE board SET titel = ? WHERE id = ?", (titel, board_id))
        r = conn.execute("SELECT * FROM board WHERE id = ?", (board_id,)).fetchone()
        if r is None:
            return None
        spalten = _spalten(conn, board_id)
    return Board(id=r["id"], mappe_id=r["mappe_id"], titel=r["titel"], kuerzel=r["kuerzel"], spalten=spalten)


def loesche_board(board_id: str) -> list[str]:
    """Loescht das Board samt Spalten/Karten/Restdaten; liefert die Karten-IDs."""
    with _verb() as conn:
        karten = [r[0] for r in conn.execute("SELECT id FROM karte WHERE board_id = ?", (board_id,)).fetchall()]
        _raeume_karten_restdaten(conn, karten)
        conn.execute("DELETE FROM zeiteintrag WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM karte WHERE board_id = ?", (board_id,))
        conn.execute("DELETE FROM spalte WHERE board_id = ?", (board_id,))
        _loesche_serien_fuer_boards(conn, [board_id])
        conn.execute("DELETE FROM board WHERE id = ?", (board_id,))
    return karten
