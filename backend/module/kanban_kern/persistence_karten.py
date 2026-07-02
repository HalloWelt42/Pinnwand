"""Persistenz rund um Karten.

Karten lesen/schreiben/verschieben, Gruppen/Verknüpfungen, Fertig-Fenster
und Archiv, Timer und Zeiteinträge, Serien-Marker sowie die Lösch-Kaskaden
für Massen-Löschungen.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from uuid import uuid4

from .models import (
    GruppenMitglied,
    Karte,
    KarteUpdate,
    Zeiteintrag,
    ZeiteintragUpdate,
)
from .persistence_basis import (
    _als_int,
    _jetzt,
    _jetzt_genau,
    _protokolliere,
    _protokolliere_feldaenderungen,
    _tagessegmente,
    _verb,
)
from .persistence_inhalte import _loesche_anhang_dateien, hole_kanban_einstellungen


# -- Lesen ----------------------------------------------------------------

def _karte_aus_row(row: sqlite3.Row) -> Karte:
    return Karte(
        id=row["id"],
        board_id=row["board_id"],
        spalte=row["spalte"],
        titel=row["titel"],
        schluessel=row["schluessel"],
        beschreibung=row["beschreibung"],
        notizen=row["notizen"],
        blockiert_grund=row["blockiert_grund"],
        labels=json.loads(row["labels"]),
        prioritaet=row["prioritaet"],
        checkliste=json.loads(row["checkliste"]),
        kommentare=json.loads(row["kommentare"]),
        cover=row["cover"],
        reihenfolge=row["reihenfolge"],
        start=row["start"],
        faellig=row["faellig"],
        zustaendig=row["zustaendig"],
        erstellt_am=row["erstellt_am"],
        bewegt_am=row["bewegt_am"],
        schaetzung_min=row["schaetzung_min"],
        erfasst_sek=row["erfasst_sek"],
        laeuft_seit=row["laeuft_seit"],
        transkript_id=row["transkript_id"],
        transkript_name=row["transkript_name"],
        typ=row["typ"] if "typ" in row.keys() else "arbeit",
        gruppe_id=row["gruppe_id"] if "gruppe_id" in row.keys() else None,
    )


def _reichere_gruppen_an(conn: sqlite3.Connection, karten: list[Karte]) -> None:
    """Setzt je verknuepfter Karte gruppe_mitglieder, gruppe_sek und gruppe_zeit_geteilt.

    Zeit zaehlt nur einmal: die echten Zeiteintraege bleiben je Karte; gruppe_sek ist
    eine reine ANZEIGE (kombinierte erfasst_sek der Gruppe, wenn die Gruppe die Zeit
    teilt). Mitglieder werden ueber alle Boards hinweg gesucht (eine Gruppe darf
    boarduebergreifend sein), nicht nur im aktuellen Board.
    """
    gids = {k.gruppe_id for k in karten if k.gruppe_id}
    if not gids:
        return
    platz = ",".join("?" for _ in gids)
    gliste = list(gids)
    mit_rows = conn.execute(
        f"SELECT id, schluessel, titel, erfasst_sek, gruppe_id FROM karte WHERE gruppe_id IN ({platz})",
        gliste,
    ).fetchall()
    geteilt_rows = conn.execute(
        f"SELECT id, zeit_geteilt FROM kartengruppe WHERE id IN ({platz})", gliste
    ).fetchall()
    geteilt = {r["id"]: bool(r["zeit_geteilt"]) for r in geteilt_rows}
    je_gruppe: dict[str, list[sqlite3.Row]] = {}
    for r in mit_rows:
        je_gruppe.setdefault(r["gruppe_id"], []).append(r)
    for k in karten:
        if not k.gruppe_id:
            continue
        mitglieder = je_gruppe.get(k.gruppe_id, [])
        ist_geteilt = geteilt.get(k.gruppe_id, True)
        k.gruppe_zeit_geteilt = ist_geteilt
        k.gruppe_mitglieder = [
            GruppenMitglied(id=m["id"], schluessel=m["schluessel"], titel=m["titel"])
            for m in mitglieder if m["id"] != k.id
        ]
        if ist_geteilt:
            k.gruppe_sek = sum(int(m["erfasst_sek"] or 0) for m in mitglieder)
        else:
            k.gruppe_sek = k.erfasst_sek


def hole_karte(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT * FROM karte WHERE id = ?", (karte_id,)).fetchone()
        karte = _karte_aus_row(row) if row else None
        if karte and karte.gruppe_id:
            _reichere_gruppen_an(conn, [karte])
    return karte


def finde_karte_per_text(text: str, board_id: str | None = None) -> Karte | None:
    """Löst eine Karte über ihren Schlüssel (z.B. R3-130) oder per Titel auf.

    Reihenfolge: exakter Schlüssel, dann Titel-Gleichheit, dann Titel enthält.
    Ohne board_id wird über alle Boards gesucht.
    """
    suchtext = (text or "").strip()
    if not suchtext:
        return None
    bedingung = " AND board_id = ?" if board_id else ""
    args_basis: tuple = (board_id,) if board_id else ()
    with _verb() as conn:
        row = conn.execute(
            f"SELECT * FROM karte WHERE LOWER(schluessel) = LOWER(?){bedingung} LIMIT 1",
            (suchtext, *args_basis),
        ).fetchone()
        if row is None:
            row = conn.execute(
                f"SELECT * FROM karte WHERE LOWER(titel) = LOWER(?){bedingung} ORDER BY bewegt_am DESC LIMIT 1",
                (suchtext, *args_basis),
            ).fetchone()
        if row is None:
            row = conn.execute(
                f"SELECT * FROM karte WHERE titel LIKE ?{bedingung} ORDER BY bewegt_am DESC LIMIT 1",
                (f"%{suchtext}%", *args_basis),
            ).fetchone()
    return _karte_aus_row(row) if row else None


# -- Fertig-Karten: Fenster, Deckel, Nachladen + Archiv --------------------
# Erledigt-Spalten werden nicht komplett geladen, sondern serverseitig gefiltert
# (Zeitfenster), gedeckelt (Seitengroesse) und beim Scrollen nachgeladen. Karten,
# deren Abschluss aelter als die Archiv-Schwelle ist, erscheinen nur im Archiv.

# Abschlussdatum (YYYY-MM-DD) als SQL-Ausdruck, konsistent zu Karte.abschluss_am:
# Serien-/REKO-Karten haben ein FESTES Datum (faellig), alle anderen zaehlen ab dem
# Erledigt-Zeitpunkt (bewegt_am). Ohne beides bleibt der Abschluss NULL.
_ABSCHLUSS_SQL = (
    "CASE WHEN serie_id IS NOT NULL AND faellig IS NOT NULL THEN faellig "
    "WHEN bewegt_am IS NOT NULL THEN substr(bewegt_am, 1, 10) ELSE NULL END"
)

# Volltext ueber alle durchsuchbaren Felder (labels/checkliste/kommentare sind JSON-Text
# und enthalten die Begriffe im Klartext) - spiegelt die Tiefensuche des Frontends.
_VOLLTEXT_SQL = (
    "LOWER(COALESCE(titel,'') || ' ' || COALESCE(schluessel,'') || ' ' || "
    "COALESCE(beschreibung,'') || ' ' || COALESCE(notizen,'') || ' ' || "
    "COALESCE(zustaendig,'') || ' ' || COALESCE(prioritaet,'') || ' ' || "
    "COALESCE(labels,'') || ' ' || COALESCE(checkliste,'') || ' ' || COALESCE(kommentare,''))"
)


def _karte_mit_abschluss(row: sqlite3.Row) -> Karte:
    k = _karte_aus_row(row)
    if row["serie_id"] and row["faellig"]:
        k.abschluss_am = row["faellig"]
    elif row["bewegt_am"]:
        k.abschluss_am = row["bewegt_am"][:10]
    return k


def _zeitfenster(zeitraum: str) -> tuple[str | None, str | None]:
    """(von, bis) als ISO-Datum fuer den Fertig-Zeitfilter; (None, None) = alle."""
    heute = datetime.now().date()
    if zeitraum == "heute":
        return heute.isoformat(), heute.isoformat()
    if zeitraum == "gestern":
        g = heute - timedelta(days=1)
        return g.isoformat(), g.isoformat()
    if zeitraum == "woche":
        mo = heute - timedelta(days=heute.weekday())
        return mo.isoformat(), (mo + timedelta(days=6)).isoformat()
    if zeitraum == "monat":
        von = heute.replace(day=1)
        naechster = (von + timedelta(days=32)).replace(day=1)
        return von.isoformat(), (naechster - timedelta(days=1)).isoformat()
    if zeitraum == "jahr":
        return heute.replace(month=1, day=1).isoformat(), heute.replace(month=12, day=31).isoformat()
    return None, None


def _archiv_grenze(archiv_tage: int) -> str:
    return (datetime.now().date() - timedelta(days=archiv_tage)).isoformat()


def _suchbedingung(
    q: str | None, labels: list[str] | None, prioritaet: str | None
) -> tuple[list[str], list]:
    """WHERE-Teilbedingungen + Argumente fuer Suche/Label/Prio (alle als UND verknuepft;
    innerhalb der Suche muss jedes Wort vorkommen, Labels sind ODER-verknuepft)."""
    bed: list[str] = []
    args: list = []
    if q and q.strip():
        for wort in q.strip().lower().split():
            bed.append(f"{_VOLLTEXT_SQL} LIKE ?")
            args.append(f"%{wort}%")
    if labels:
        teil = ["labels LIKE ?" for _ in labels]
        args += [f'%"{name}"%' for name in labels]
        bed.append("(" + " OR ".join(teil) + ")")
    if prioritaet:
        bed.append("prioritaet = ?")
        args.append(prioritaet)
    return bed, args


def fertige_seite(
    spalte_id: str,
    zeitraum: str = "heute",
    offset: int = 0,
    limit: int | None = None,
    q: str | None = None,
    labels: list[str] | None = None,
    prioritaet: str | None = None,
    zustaendig: list[str] | None = None,
) -> tuple[list[Karte], int]:
    """Eine Seite fertiger Karten EINER Erledigt-Spalte: nach Abschlussdatum (neueste
    zuerst), ohne archivierte (aelter als die Schwelle), gedeckelt + per Offset nachladbar.
    Sind Suche/Label/Prio aktiv, wird das Zeitfenster ausgesetzt (wie im Frontend)."""
    conf = hole_kanban_einstellungen()
    seite = _als_int(limit, conf["fertig_seitengroesse"], 1, 500)
    offset = max(0, int(offset))
    grenze = _archiv_grenze(conf["archiv_tage"])
    such_bed, such_args = _suchbedingung(q, labels, prioritaet)
    where = ["spalte = ?", f"({_ABSCHLUSS_SQL} IS NULL OR {_ABSCHLUSS_SQL} >= ?)"]
    args: list = [spalte_id, grenze]
    if not such_bed and zeitraum != "alle":
        von, bis = _zeitfenster(zeitraum)
        if von and bis:
            where.append(f"{_ABSCHLUSS_SQL} BETWEEN ? AND ?")
            args += [von, bis]
    where += such_bed
    args += such_args
    if zustaendig:
        platz = ",".join("?" for _ in zustaendig)
        where.append(f"zustaendig IN ({platz})")
        args += zustaendig
    wsql = " AND ".join(where)
    with _verb() as conn:
        gesamt = conn.execute(f"SELECT COUNT(*) AS n FROM karte WHERE {wsql}", args).fetchone()["n"]
        rows = conn.execute(
            f"SELECT * FROM karte WHERE {wsql} ORDER BY {_ABSCHLUSS_SQL} DESC, reihenfolge, id LIMIT ? OFFSET ?",
            args + [seite, offset],
        ).fetchall()
        karten = [_karte_mit_abschluss(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return karten, int(gesamt)


def archiv_seite(
    board_id: str,
    offset: int = 0,
    limit: int | None = None,
    q: str | None = None,
) -> tuple[list[Karte], int]:
    """Archivierte fertige Karten eines Boards (Abschluss aelter als die Schwelle), ueber
    alle Erledigt-Spalten, neueste zuerst, gedeckelt + nachladbar, optional durchsucht."""
    conf = hole_kanban_einstellungen()
    seite = _als_int(limit, conf["fertig_seitengroesse"], 1, 500)
    offset = max(0, int(offset))
    grenze = _archiv_grenze(conf["archiv_tage"])
    such_bed, such_args = _suchbedingung(q, None, None)
    with _verb() as conn:
        erledigt = [
            r["id"]
            for r in conn.execute(
                "SELECT id FROM spalte WHERE board_id = ? AND erledigt = 1", (board_id,)
            ).fetchall()
        ]
        if not erledigt:
            return [], 0
        platz = ",".join("?" for _ in erledigt)
        where = [
            "board_id = ?",
            f"spalte IN ({platz})",
            f"{_ABSCHLUSS_SQL} IS NOT NULL",
            f"{_ABSCHLUSS_SQL} < ?",
        ]
        args: list = [board_id, *erledigt, grenze]
        where += such_bed
        args += such_args
        wsql = " AND ".join(where)
        gesamt = conn.execute(f"SELECT COUNT(*) AS n FROM karte WHERE {wsql}", args).fetchone()["n"]
        rows = conn.execute(
            f"SELECT * FROM karte WHERE {wsql} ORDER BY {_ABSCHLUSS_SQL} DESC, id LIMIT ? OFFSET ?",
            args + [seite, offset],
        ).fetchall()
        karten = [_karte_mit_abschluss(r) for r in rows]
        _reichere_gruppen_an(conn, karten)
    return karten, int(gesamt)


# -- Verknuepfung / Zeitgruppe -------------------------------------------

def verknuepfe_karten(karte_id: str, ziel_id: str) -> Karte | None:
    """Legt beide Karten in EINE Gruppe. Bestehende Gruppe(n) werden verwendet bzw.
    zusammengefuehrt; sonst entsteht eine neue Gruppe (Zeit teilen = Standard an)."""
    if karte_id == ziel_id:
        return hole_karte(karte_id)
    with _verb() as conn:
        a = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        b = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (ziel_id,)).fetchone()
        if a is None or b is None:
            return None
        ga, gb = a["gruppe_id"], b["gruppe_id"]
        if ga and gb and ga != gb:
            # Beide haben Gruppen -> b-Gruppe in a-Gruppe ueberfuehren.
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE gruppe_id = ?", (ga, gb))
            conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gb,))
            ziel_gruppe = ga
        elif ga:
            ziel_gruppe = ga
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id = ?", (ga, ziel_id))
        elif gb:
            ziel_gruppe = gb
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id = ?", (gb, karte_id))
        else:
            ziel_gruppe = "g_" + uuid4().hex[:8]
            conn.execute(
                "INSERT INTO kartengruppe (id, zeit_geteilt, erstellt_am) VALUES (?, 1, ?)",
                (ziel_gruppe, _jetzt()),
            )
            conn.execute("UPDATE karte SET gruppe_id = ? WHERE id IN (?, ?)", (ziel_gruppe, karte_id, ziel_id))
    return hole_karte(karte_id)


def loese_verknuepfung(karte_id: str) -> Karte | None:
    """Loest die Karte aus ihrer Gruppe. Bleibt danach < 2 Mitglieder, wird die Gruppe
    (und der Rest-Verweis) aufgeloest."""
    with _verb() as conn:
        row = conn.execute("SELECT gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        gid = row["gruppe_id"]
        conn.execute("UPDATE karte SET gruppe_id = NULL WHERE id = ?", (karte_id,))
        if gid:
            rest = conn.execute("SELECT id FROM karte WHERE gruppe_id = ?", (gid,)).fetchall()
            if len(rest) < 2:
                conn.execute("UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ?", (gid,))
                conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))
    return hole_karte(karte_id)


def setze_gruppe_zeit_geteilt(gruppe_id: str, geteilt: bool) -> bool:
    with _verb() as conn:
        cur = conn.execute(
            "UPDATE kartengruppe SET zeit_geteilt = ? WHERE id = ?", (1 if geteilt else 0, gruppe_id)
        )
        return cur.rowcount > 0


# -- Karten schreiben -----------------------------------------------------

def _naechste_reihenfolge(conn: sqlite3.Connection, board_id: str, spalte: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(reihenfolge), -1) AS m FROM karte WHERE board_id = ? AND spalte = ?",
        (board_id, spalte),
    ).fetchone()
    return int(row["m"]) + 1


def _kompaktiere(conn: sqlite3.Connection, board_id: str, spalte: str) -> None:
    rows = conn.execute(
        "SELECT id FROM karte WHERE board_id = ? AND spalte = ? ORDER BY reihenfolge, id", (board_id, spalte)
    ).fetchall()
    for index, r in enumerate(rows):
        conn.execute("UPDATE karte SET reihenfolge = ? WHERE id = ?", (index, r["id"]))


def erstelle_karte(
    karte_id: str, board_id: str, spalte: str, titel: str,
    beschreibung: str | None, labels: list[str], prioritaet: str | None,
    cover: str | None, start: str | None, faellig: str | None, zustaendig: str | None,
    typ: str = "arbeit", akteur: str | None = None,
) -> Karte:
    with _verb() as conn:
        b = conn.execute("SELECT kuerzel, laufnummer FROM board WHERE id = ?", (board_id,)).fetchone()
        kuerzel = (b["kuerzel"] if b and b["kuerzel"] else "K")
        nummer = (b["laufnummer"] if b and b["laufnummer"] is not None else 0) + 1
        conn.execute("UPDATE board SET laufnummer = ? WHERE id = ?", (nummer, board_id))
        reihenfolge = _naechste_reihenfolge(conn, board_id, spalte)
        jetzt = _jetzt()
        conn.execute(
            "INSERT INTO karte (id, board_id, spalte, titel, schluessel, beschreibung, labels, prioritaet,"
            " checkliste, kommentare, cover, reihenfolge, start, faellig, zustaendig, erstellt_am, bewegt_am, typ)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', ?, ?, ?, ?, ?, ?, ?, ?)",
            (karte_id, board_id, spalte, titel, f"{kuerzel}-{nummer}", beschreibung, json.dumps(labels),
             prioritaet, cover, reihenfolge, start, faellig, zustaendig, jetzt, jetzt,
             "idee" if typ == "idee" else "arbeit"),
        )
        _protokolliere(conn, karte_id, "angelegt", "Karte angelegt", akteur)
    karte = hole_karte(karte_id)
    assert karte is not None
    return karte


def verschiebe_karte(karte_id: str, ziel_spalte: str, ziel_reihenfolge: int, akteur: str | None = None) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT board_id, spalte, gruppe_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        board_id, quelle, gruppe_id = row["board_id"], row["spalte"], row["gruppe_id"]
        conn.execute(
            "UPDATE karte SET reihenfolge = reihenfolge + 1"
            " WHERE board_id = ? AND spalte = ? AND reihenfolge >= ? AND id != ?",
            (board_id, ziel_spalte, ziel_reihenfolge, karte_id),
        )
        conn.execute("UPDATE karte SET spalte = ?, reihenfolge = ? WHERE id = ?", (ziel_spalte, ziel_reihenfolge, karte_id))
        jetzt = _jetzt()
        # Wechsel der Spalte setzt die Verweildauer (Card-Aging) zurück.
        ziel_titel = ziel_spalte
        if quelle != ziel_spalte:
            conn.execute("UPDATE karte SET bewegt_am = ? WHERE id = ?", (jetzt, karte_id))
            sp = conn.execute("SELECT titel FROM spalte WHERE id = ?", (ziel_spalte,)).fetchone()
            if sp is not None:
                ziel_titel = sp["titel"]
            _protokolliere(conn, karte_id, "verschoben", f'Verschoben nach "{ziel_titel}"', akteur)
        betroffene = {quelle, ziel_spalte}
        # Verknuepfte Tickets ziehen bei Spaltenwechsel als Gruppe mit (ans Ende der
        # Zielspalte, dort frei sortierbar). Nur im selben Board und nur Mitglieder,
        # die nicht ohnehin schon in der Zielspalte stehen. Innerhalb derselben Spalte
        # (reines Umsortieren) bleibt die Gruppe unberuehrt.
        if gruppe_id and quelle != ziel_spalte:
            mitglieder = conn.execute(
                "SELECT id, spalte FROM karte"
                " WHERE board_id = ? AND gruppe_id = ? AND id != ? AND spalte != ?",
                (board_id, gruppe_id, karte_id, ziel_spalte),
            ).fetchall()
            for m in mitglieder:
                ziel_pos = _naechste_reihenfolge(conn, board_id, ziel_spalte)
                conn.execute(
                    "UPDATE karte SET spalte = ?, reihenfolge = ?, bewegt_am = ? WHERE id = ?",
                    (ziel_spalte, ziel_pos, jetzt, m["id"]),
                )
                _protokolliere(conn, m["id"], "verschoben",
                               f'Mit verknüpfter Karte verschoben nach "{ziel_titel}"', akteur)
                betroffene.add(m["spalte"])
        # Erledigen stoppt laufende Timer sauber (bucht die Sitzung) - fuer die Karte
        # selbst und fuer mitgezogene Gruppenmitglieder.
        if quelle != ziel_spalte:
            ziel = conn.execute("SELECT erledigt FROM spalte WHERE id = ?", (ziel_spalte,)).fetchone()
            if ziel is not None and ziel["erledigt"]:
                laufende = conn.execute(
                    "SELECT id FROM karte WHERE board_id = ? AND spalte = ? AND laeuft_seit IS NOT NULL",
                    (board_id, ziel_spalte),
                ).fetchall()
                for r in laufende:
                    _pause_intern(conn, r["id"])
        for spalte in betroffene:
            _kompaktiere(conn, board_id, spalte)
    return hole_karte(karte_id)


def aktualisiere_karte(karte_id: str, aenderungen: dict, akteur: str | None = None) -> Karte | None:
    # KarteUpdate ist die einzige Feldquelle - keine doppelte Whitelist, die driften koennte.
    felder = {k: v for k, v in aenderungen.items() if k in KarteUpdate.model_fields}
    if not felder:
        return hole_karte(karte_id)
    # Ein Spaltenwechsel ist ein echtes Verschieben und laeuft ueber verschiebe_karte,
    # damit bewegt_am, Gruppen-Mitzug und Kompaktierung auf JEDEM Weg greifen
    # (Drawer-Status, Agenten-API) - nicht nur beim Drag ueber den Move-Endpunkt.
    neue_spalte = felder.pop("spalte", None)
    if neue_spalte is not None:
        with _verb() as conn:
            row = conn.execute("SELECT board_id, spalte FROM karte WHERE id = ?", (karte_id,)).fetchone()
            if row is None:
                return None
            ziel_pos = _naechste_reihenfolge(conn, row["board_id"], neue_spalte)
        if row["spalte"] != neue_spalte:
            verschiebe_karte(karte_id, neue_spalte, ziel_pos, akteur=akteur)
    # Wechsel auf 'idee' stoppt einen laufenden Timer sauber (bucht die Sitzung),
    # sonst tickt die Zeit unsichtbar auf einem Ticket weiter, das keine erfasst.
    if felder.get("typ") == "idee":
        with _verb() as conn:
            r = conn.execute("SELECT laeuft_seit FROM karte WHERE id = ?", (karte_id,)).fetchone()
            if r is not None and r["laeuft_seit"]:
                _pause_intern(conn, karte_id)
    if not felder:
        return hole_karte(karte_id)
    for json_feld in ("labels", "checkliste"):
        if json_feld in felder:
            felder[json_feld] = json.dumps(felder[json_feld])
    zuweisung = ", ".join(f"{k} = ?" for k in felder)
    with _verb() as conn:
        vorher = conn.execute(
            "SELECT zustaendig, faellig, prioritaet, blockiert_grund, typ FROM karte WHERE id = ?",
            (karte_id,),
        ).fetchone()
        conn.execute(f"UPDATE karte SET {zuweisung} WHERE id = ?", (*felder.values(), karte_id))
        if vorher is not None:
            _protokolliere_feldaenderungen(conn, karte_id, vorher, felder, akteur)
    return hole_karte(karte_id)


def kommentar_anhaengen(karte_id: str, autor: str, text: str, zeit: str) -> Karte | None:
    with _verb() as conn:
        # Atomar in SQL anhaengen (json_insert) - ein Read-Modify-Write kann bei
        # zwei gleichzeitigen Kommentaren einen davon verlieren.
        cur = conn.execute(
            "UPDATE karte SET kommentare = json_insert(kommentare, '$[#]', json(?)) WHERE id = ?",
            (json.dumps({"autor": autor, "text": text, "zeit": zeit}, ensure_ascii=False), karte_id),
        )
        if cur.rowcount == 0:
            return None
        _protokolliere(conn, karte_id, "kommentar", "Kommentar hinterlassen", autor)
    return hole_karte(karte_id)


def _loesche_marken(conn: sqlite3.Connection, wo: str, params: tuple) -> None:
    """Transkript-Marken der betroffenen Karten mitloeschen (Tabelle aus dem
    transkripte-Modul; defensiv, falls dieses Modul nicht geladen ist)."""
    try:
        conn.execute(f"DELETE FROM transkript_marke {wo}", params)
    except sqlite3.OperationalError:
        pass


def loesche_karte(karte_id: str, auslass_merken: bool = True) -> None:
    with _verb() as conn:
        row = conn.execute(
            "SELECT board_id, spalte, gruppe_id, serie_id, serie_datum FROM karte WHERE id = ?", (karte_id,)
        ).fetchone()
        # Bewusst geloeschte Serien-Instanz merken, sonst legt der naechste
        # Vorbuchungslauf sie kommentarlos wieder an (Tabelle des serien-Moduls).
        if auslass_merken and row is not None and row["serie_id"] and row["serie_datum"]:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO serie_auslass (serie_id, datum) VALUES (?, ?)",
                    (row["serie_id"], row["serie_datum"]),
                )
            except sqlite3.OperationalError:
                pass
        conn.execute("DELETE FROM karte WHERE id = ?", (karte_id,))
        conn.execute("DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id = ?", (karte_id,))
        # Zeiteintraege der Karte mitloeschen, sonst verfaelschen Waisen die Ist-Summen.
        conn.execute("DELETE FROM zeiteintrag WHERE karte_id = ?", (karte_id,))
        conn.execute("DELETE FROM aktivitaet WHERE karte_id = ?", (karte_id,))
        conn.execute("DELETE FROM anhang WHERE karte_id = ?", (karte_id,))
        _loesche_marken(conn, "WHERE karte_id = ?", (karte_id,))
        # Verwaiste Zeitgruppe aufloesen, wenn nach dem Loeschen < 2 Mitglieder bleiben.
        if row is not None and row["gruppe_id"]:
            gid = row["gruppe_id"]
            rest = conn.execute("SELECT id FROM karte WHERE gruppe_id = ?", (gid,)).fetchall()
            if len(rest) < 2:
                conn.execute("UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ?", (gid,))
                conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))
        if row is not None:
            _kompaktiere(conn, row["board_id"], row["spalte"])
    _loesche_anhang_dateien([karte_id])


# -- Zeiterfassung --------------------------------------------------------

def _mappe_fuer_board(conn: sqlite3.Connection, board_id: str | None) -> str | None:
    if not board_id:
        return None
    r = conn.execute("SELECT mappe_id FROM board WHERE id = ?", (board_id,)).fetchone()
    return r["mappe_id"] if r else None


def _recompute_erfasst(conn: sqlite3.Connection, karte_id: str) -> None:
    """erfasst_sek einer Karte = Summe ihrer Zeiteinträge (Single Source of Truth)."""
    r = conn.execute("SELECT COALESCE(SUM(sekunden), 0) AS s FROM zeiteintrag WHERE karte_id = ?", (karte_id,)).fetchone()
    conn.execute("UPDATE karte SET erfasst_sek = ? WHERE id = ?", (int(r["s"]), karte_id))


# Hinweis: Es gibt bewusst keine undatierte Gesamt-Eingabe der erfassten Zeit mehr.
# Ticketzeit (erfasst_sek) = Summe der datierten Zeiteintraege je Karte; jede Korrektur
# laeuft ueber einen datierten Zeiteintrag, damit die Arbeitszeit dem richtigen Tag
# zugeordnet wird. Siehe docs/ZEITMODELL.md.


def _pause_intern(conn: sqlite3.Connection, karte_id: str) -> None:
    """Stoppt eine laufende Karte, schreibt einen Zeiteintrag und berechnet erfasst_sek neu.

    Start/Stopp-Sitzungen derselben Karte am selben Tag werden zu EINEM automatischen
    Eintrag zusammengefasst (Summe der Sekunden, frueheste Start- und spaeteste End-Zeit),
    damit die Uebersichten nicht mit vielen Fragmenten volllaufen. Die erfasste Zeit
    bleibt exakt gleich - es ist eine Zusammenfassung, kein Verlust. Siehe ZEITMODELL.md.
    """
    row = conn.execute("SELECT laeuft_seit, board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
    if row is None or not row["laeuft_seit"]:
        return
    start = row["laeuft_seit"]
    ende = _jetzt_genau()
    conn.execute("UPDATE karte SET laeuft_seit = NULL WHERE id = ?", (karte_id,))
    try:
        segmente = _tagessegmente(start, ende)
    except ValueError:
        segmente = []
    # Plausibilitaets-Deckel: ein vergessener Timer (Standby, Absturz, Wochenende)
    # bucht sonst kommentarlos zig Stunden. Sitzungen ueber 12 h werden auf die
    # ersten 12 h gedeckelt - der Rest ist mit hoher Sicherheit keine Arbeitszeit.
    MAX_SITZUNG_SEK = 12 * 3600
    if sum(s[3] for s in segmente) > MAX_SITZUNG_SEK:
        gedeckelt: list[tuple[str, str, str, int]] = []
        rest = MAX_SITZUNG_SEK
        for datum, s_start, s_ende, sek in segmente:
            if rest <= 0:
                break
            gedeckelt.append((datum, s_start, s_ende, min(sek, rest)))
            rest -= min(sek, rest)
        segmente = gedeckelt
    mappe_id = _mappe_fuer_board(conn, row["board_id"])
    gesamt = sum(s[3] for s in segmente)
    if gesamt > 0:
        _protokolliere(conn, karte_id, "zeit",
                       f"Timer gestoppt: {max(1, gesamt // 60)} min erfasst", row["zustaendig"])
    for datum, seg_start, seg_ende, sek in segmente:
        vorhanden = conn.execute(
            "SELECT id, start, ende FROM zeiteintrag WHERE manuell = 0 AND karte_id = ? AND datum = ? LIMIT 1",
            (karte_id, datum),
        ).fetchone()
        if vorhanden:
            neu_start = min(vorhanden["start"], seg_start) if vorhanden["start"] else seg_start
            neu_ende = max(vorhanden["ende"], seg_ende) if vorhanden["ende"] else seg_ende
            conn.execute(
                "UPDATE zeiteintrag SET sekunden = sekunden + ?, start = ?, ende = ? WHERE id = ?",
                (sek, neu_start, neu_ende, vorhanden["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?)",
                (f"z_{uuid4().hex[:8]}", karte_id, row["board_id"], mappe_id, datum, seg_start, seg_ende, sek, row["zustaendig"]),
            )
    _recompute_erfasst(conn, karte_id)


def timer_start(karte_id: str) -> Karte | None:
    with _verb() as conn:
        row = conn.execute("SELECT start FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        # Timer je PERSON: der Start pausiert nur laufende Karten derselben Person
        # (gleiches Zustaendigkeits-Kuerzel; IS vergleicht auch NULL korrekt) -
        # fremde Timer laufen weiter, statt still gestoppt zu werden.
        eigene = conn.execute("SELECT zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        for r in conn.execute(
            "SELECT id FROM karte WHERE laeuft_seit IS NOT NULL AND id != ? AND zustaendig IS ?",
            (karte_id, eigene["zustaendig"] if eigene else None),
        ).fetchall():
            _pause_intern(conn, r["id"])
        jetzt = _jetzt_genau()
        # Ohne gesetztes Start-Datum gilt der erste Timer-Start als Arbeitsbeginn;
        # einmal gesetzt wird der Wert beim Fortsetzen nie wieder ueberschrieben.
        if not row["start"]:
            conn.execute("UPDATE karte SET laeuft_seit = ?, start = ? WHERE id = ?", (jetzt, jetzt[:10], karte_id))
        else:
            conn.execute("UPDATE karte SET laeuft_seit = ? WHERE id = ?", (jetzt, karte_id))
    return hole_karte(karte_id)


def timer_pause(karte_id: str) -> Karte | None:
    with _verb() as conn:
        if conn.execute("SELECT 1 FROM karte WHERE id = ?", (karte_id,)).fetchone() is None:
            return None
        _pause_intern(conn, karte_id)
    return hole_karte(karte_id)


def laufende_karte(kuerzel: str | None = None, nur_eigene: bool = False) -> Karte | None:
    """Die laufende Karte - mit kuerzel bevorzugt die der Person (Timer je Person);
    nur_eigene unterdrueckt den Fallback auf fremde Timer (Nicht-Admins)."""
    with _verb() as conn:
        row = None
        if kuerzel:
            row = conn.execute(
                "SELECT * FROM karte WHERE laeuft_seit IS NOT NULL AND zustaendig = ? LIMIT 1", (kuerzel,)
            ).fetchone()
        if row is None and not nur_eigene:
            row = conn.execute("SELECT * FROM karte WHERE laeuft_seit IS NOT NULL LIMIT 1").fetchone()
    return _karte_aus_row(row) if row else None


# -- Zeiteinträge (Auswertung / Korrektur) -------------------------------

_ZE_SELECT = (
    "SELECT z.*, k.titel AS karte_titel, k.schluessel AS karte_schluessel, k.zustaendig AS karte_zustaendig "
    "FROM zeiteintrag z LEFT JOIN karte k ON k.id = z.karte_id "
)


def _zeiteintrag_aus_row(row: sqlite3.Row) -> Zeiteintrag:
    return Zeiteintrag(
        id=row["id"], karte_id=row["karte_id"], board_id=row["board_id"], mappe_id=row["mappe_id"],
        datum=row["datum"], start=row["start"], ende=row["ende"], sekunden=row["sekunden"],
        kommentar=row["kommentar"], manuell=bool(row["manuell"]), kuerzel=row["kuerzel"],
        karte_titel=row["karte_titel"], karte_schluessel=row["karte_schluessel"],
        karte_zustaendig=row["karte_zustaendig"],
    )


def zeiteintraege_range(von: str | None = None, bis: str | None = None, karte_id: str | None = None,
                        nur_mappen: set[str] | None = None) -> list[Zeiteintrag]:
    """Zeiteintraege gefiltert. Mit karte_id (ohne von/bis) liefert es ALLE Eintraege
    einer Karte ueber alle Tage - Grundlage der Tages-Aufschluesselung im Ticket."""
    bed: list[str] = []
    params: list[str] = []
    if von:
        bed.append("z.datum >= ?")
        params.append(von)
    if bis:
        bed.append("z.datum <= ?")
        params.append(bis)
    if karte_id:
        bed.append("z.karte_id = ?")
        params.append(karte_id)
    if nur_mappen is not None:
        # Projekt-Scoping fuer Nicht-Admins: nur Eintraege sichtbarer Mappen.
        if not nur_mappen:
            return []
        platz = ",".join("?" for _ in nur_mappen)
        bed.append(f"z.mappe_id IN ({platz})")
        params.extend(sorted(nur_mappen))
    where = ("WHERE " + " AND ".join(bed) + " ") if bed else ""
    with _verb() as conn:
        rows = conn.execute(
            _ZE_SELECT + where + "ORDER BY z.datum, z.start, z.id",
            tuple(params),
        ).fetchall()
    return [_zeiteintrag_aus_row(r) for r in rows]


def hole_zeiteintrag(eintrag_id: str) -> Zeiteintrag | None:
    with _verb() as conn:
        r = conn.execute(_ZE_SELECT + "WHERE z.id = ?", (eintrag_id,)).fetchone()
    return _zeiteintrag_aus_row(r) if r else None


def erstelle_zeiteintrag(eintrag_id: str, karte_id: str, datum: str, sekunden: int, kommentar: str | None,
                         kuerzel: str | None = None) -> Zeiteintrag | None:
    """kuerzel = Person, der die Zeit gehoert (Akteur beim Buchen); ohne Angabe
    faellt es auf die Karten-Zustaendigkeit zurueck (offener Modus, Timer)."""
    with _verb() as conn:
        b = conn.execute("SELECT board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if b is None:
            return None
        board_id = b["board_id"]
        conn.execute(
            "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
            " VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, 1, ?)",
            (eintrag_id, karte_id, board_id, _mappe_fuer_board(conn, board_id), datum, max(0, sekunden), kommentar,
             kuerzel or b["zustaendig"]),
        )
        _protokolliere(conn, karte_id, "zeit",
                       f"Zeit gebucht: {max(0, sekunden) // 60} min ({datum})", kuerzel or b["zustaendig"])
        _recompute_erfasst(conn, karte_id)
    return hole_zeiteintrag(eintrag_id)


def setze_ticketzeit(karte_id: str, ziel_sek: int, kuerzel: str | None = None) -> bool:
    """Setzt die Gesamt-Ticketzeit in EINER Transaktion (gegen die aktuelle Summe
    gerechnet): Mehrzeit wird als manueller Eintrag heute gebucht, Minderzeit von
    den juengsten Eintraegen abgezogen. Keine halben Korrekturen bei Abbruechen."""
    ziel = max(0, int(ziel_sek))
    with _verb() as conn:
        b = conn.execute("SELECT board_id, zustaendig FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if b is None:
            return False
        summe = int(conn.execute(
            "SELECT COALESCE(SUM(sekunden), 0) FROM zeiteintrag WHERE karte_id = ?", (karte_id,)
        ).fetchone()[0])
        if ziel > summe:
            heute = _jetzt()[:10]
            conn.execute(
                "INSERT INTO zeiteintrag (id, karte_id, board_id, mappe_id, datum, start, ende, sekunden, kommentar, manuell, kuerzel)"
                " VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, 'Korrektur', 1, ?)",
                (f"z_{uuid4().hex[:8]}", karte_id, b["board_id"], _mappe_fuer_board(conn, b["board_id"]),
                 heute, ziel - summe, kuerzel or b["zustaendig"]),
            )
        elif ziel < summe:
            rest = summe - ziel
            for r in conn.execute(
                "SELECT id, sekunden FROM zeiteintrag WHERE karte_id = ? ORDER BY datum DESC, id DESC", (karte_id,)
            ).fetchall():
                if rest <= 0:
                    break
                if r["sekunden"] <= rest:
                    conn.execute("DELETE FROM zeiteintrag WHERE id = ?", (r["id"],))
                    rest -= r["sekunden"]
                else:
                    conn.execute("UPDATE zeiteintrag SET sekunden = sekunden - ? WHERE id = ?", (rest, r["id"]))
                    rest = 0
        if ziel != summe:
            _protokolliere(conn, karte_id, "zeit",
                           f"Ticketzeit gesetzt: {ziel // 60} min", kuerzel or b["zustaendig"])
        _recompute_erfasst(conn, karte_id)
    return True


def aktualisiere_zeiteintrag(eintrag_id: str, aenderungen: dict) -> Zeiteintrag | None:
    with _verb() as conn:
        row = conn.execute("SELECT karte_id FROM zeiteintrag WHERE id = ?", (eintrag_id,)).fetchone()
        if row is None:
            return None
        felder = {k: v for k, v in aenderungen.items() if k in ZeiteintragUpdate.model_fields}
        if "sekunden" in felder and felder["sekunden"] is not None:
            felder["sekunden"] = max(0, int(felder["sekunden"]))
        if felder:
            zuweisung = ", ".join(f"{k} = ?" for k in felder)
            conn.execute(f"UPDATE zeiteintrag SET {zuweisung} WHERE id = ?", (*felder.values(), eintrag_id))
        _recompute_erfasst(conn, row["karte_id"])
    return hole_zeiteintrag(eintrag_id)


def loesche_zeiteintrag(eintrag_id: str) -> bool:
    with _verb() as conn:
        row = conn.execute("SELECT karte_id FROM zeiteintrag WHERE id = ?", (eintrag_id,)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM zeiteintrag WHERE id = ?", (eintrag_id,))
        _recompute_erfasst(conn, row["karte_id"])
    return True


def markiere_serie(karte_id: str, serie_id: str, datum: str) -> None:
    """Verknüpft eine Karte mit einer Serie und ihrem Termin-Datum (für Vorbuchung/Dedup)."""
    with _verb() as conn:
        conn.execute("UPDATE karte SET serie_id = ?, serie_datum = ? WHERE id = ?", (serie_id, datum, karte_id))


def serien_instanz_existiert(serie_id: str, datum: str) -> bool:
    with _verb() as conn:
        r = conn.execute(
            "SELECT 1 FROM karte WHERE serie_id = ? AND serie_datum = ? LIMIT 1", (serie_id, datum)
        ).fetchone()
    return r is not None


def letztes_serie_datum(serie_id: str) -> str | None:
    """Spätestes bereits materialisiertes Datum einer Serie (für Backfill verpasster Tage)."""
    with _verb() as conn:
        r = conn.execute(
            "SELECT MAX(serie_datum) AS m FROM karte WHERE serie_id = ?", (serie_id,)
        ).fetchone()
    return r["m"] if r and r["m"] else None


def _raeume_karten_restdaten(conn: sqlite3.Connection, karten_ids: list[str]) -> None:
    """Alles, was an Karten haengt, konsistent mitloeschen - EIN Pfad fuer alle
    Massen-Loeschungen (Spalte/Board/Mappe): Dokumente, Zeiteintraege,
    Transkript-Marken und verwaiste Zeitgruppen."""
    if not karten_ids:
        return
    platz = ",".join("?" for _ in karten_ids)
    try:
        conn.execute(
            f"INSERT OR IGNORE INTO serie_auslass (serie_id, datum)"
            f" SELECT serie_id, serie_datum FROM karte"
            f" WHERE id IN ({platz}) AND serie_id IS NOT NULL AND serie_datum IS NOT NULL",
            karten_ids,
        )
    except sqlite3.OperationalError:
        pass
    conn.execute(f"DELETE FROM dokument WHERE kontext = 'karte' AND kontext_id IN ({platz})", karten_ids)
    conn.execute(f"DELETE FROM zeiteintrag WHERE karte_id IN ({platz})", karten_ids)
    conn.execute(f"DELETE FROM aktivitaet WHERE karte_id IN ({platz})", karten_ids)
    conn.execute(f"DELETE FROM anhang WHERE karte_id IN ({platz})", karten_ids)
    _loesche_anhang_dateien(karten_ids)
    _loesche_marken(conn, f"WHERE karte_id IN ({platz})", tuple(karten_ids))
    gruppen = [r[0] for r in conn.execute(
        f"SELECT DISTINCT gruppe_id FROM karte WHERE id IN ({platz}) AND gruppe_id IS NOT NULL", karten_ids
    ).fetchall()]
    for gid in gruppen:
        rest = conn.execute(
            f"SELECT COUNT(*) FROM karte WHERE gruppe_id = ? AND id NOT IN ({platz})", (gid, *karten_ids)
        ).fetchone()[0]
        if rest < 2:
            conn.execute(
                f"UPDATE karte SET gruppe_id = NULL WHERE gruppe_id = ? AND id NOT IN ({platz})", (gid, *karten_ids)
            )
            conn.execute("DELETE FROM kartengruppe WHERE id = ?", (gid,))


def _loesche_serien_fuer_boards(conn: sqlite3.Connection, board_ids: list[str]) -> None:
    """Serien geloeschter Boards mitloeschen - sonst materialisieren sie weiter
    Geisterkarten in ein Board, das es nicht mehr gibt (Tabelle des serien-Moduls,
    defensiv falls nicht geladen)."""
    if not board_ids:
        return
    platz = ",".join("?" for _ in board_ids)
    try:
        conn.execute(
            f"DELETE FROM serie_auslass WHERE serie_id IN (SELECT id FROM serie WHERE board_id IN ({platz}))",
            board_ids,
        )
        conn.execute(f"DELETE FROM serie WHERE board_id IN ({platz})", board_ids)
    except sqlite3.OperationalError:
        pass
