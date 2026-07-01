"""Persistenz der Planung: Personen, Urlaub, Feiertage.

Personen tragen ihr Wochen-Soll je Wochentag (Mo..So in Stunden). Urlaub wird
taggenau geführt (Anteil 1.0 oder 0.5). Feiertage werden importiert (mit
Region-Kennung) und in die Kapazität eingerechnet.
"""
from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from app.db import verbindung

from module.auth.passwort import hash_passwort
from module.auth.passwort import pruefe as pruefe_passwort

from .models import AbwesenheitTypUpdate, PersonUpdate

SCHEMA = """
CREATE TABLE IF NOT EXISTS person (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kuerzel TEXT,
    farbe TEXT,
    wochenstunden TEXT NOT NULL DEFAULT '[8,8,8,8,8,0,0]',
    bundesland TEXT,
    urlaubsanspruch REAL NOT NULL DEFAULT 30,
    resturlaub_vorjahr REAL NOT NULL DEFAULT 0,
    aktiv INTEGER NOT NULL DEFAULT 1,
    rolle TEXT NOT NULL DEFAULT 'mitarbeiter',
    passwort_hash TEXT
);
CREATE TABLE IF NOT EXISTS urlaub (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    datum TEXT NOT NULL,
    anteil REAL NOT NULL DEFAULT 1.0,
    typ TEXT NOT NULL DEFAULT 'urlaub',
    notiz TEXT
);
CREATE TABLE IF NOT EXISTS feiertag (
    datum TEXT NOT NULL,
    name TEXT NOT NULL,
    region TEXT,
    PRIMARY KEY (datum, region)
);
CREATE TABLE IF NOT EXISTS abwesenheit_typ (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    farbe TEXT NOT NULL,
    reduziert_soll INTEGER NOT NULL DEFAULT 1,
    anrechnen INTEGER NOT NULL DEFAULT 1,
    anwesend INTEGER NOT NULL DEFAULT 0,
    reihenfolge INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tagesregel (
    id TEXT PRIMARY KEY,
    person_id TEXT,
    art TEXT NOT NULL,
    monat INTEGER,
    tag INTEGER,
    wochentag INTEGER,
    anteil REAL NOT NULL DEFAULT 0.5,
    notiz TEXT,
    aktiv INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS wochen_override (
    person_id TEXT NOT NULL,
    jahr INTEGER NOT NULL,
    kw INTEGER NOT NULL,
    wochenstunden TEXT NOT NULL,
    PRIMARY KEY (person_id, jahr, kw)
);
"""

_STD_WOCHE = [8, 8, 8, 8, 8, 0, 0]

# Abwesenheits-Arten (Seed). Farben aus der Material-Palette. reduziert_soll:
# senkt das Tages-Soll; anrechnen: zählt gegen den Urlaubsanspruch; anwesend:
# gilt trotzdem als anwesend (Homeoffice/Dienstreise).
_ABW_SEED = [
    ("urlaub", "Urlaub", "#4CAF50", 1, 1, 0, 1),
    ("krankheit", "Krankheit", "#EF5350", 1, 1, 0, 2),
    ("sonderurlaub", "Sonderurlaub", "#9575CD", 1, 1, 0, 3),
    ("unbezahlt", "Unbezahlt", "#78909C", 1, 1, 0, 4),
    ("homeoffice", "Homeoffice/Dienstreise", "#2196F3", 0, 0, 1, 5),
]


def _migriere(conn: sqlite3.Connection) -> None:
    """Ergänzt neue Personen-Spalten in einer bestehenden Datenbank."""
    spalten = {r["name"] for r in conn.execute("PRAGMA table_info(person)").fetchall()}
    if "bundesland" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN bundesland TEXT")
    if "urlaubsanspruch" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN urlaubsanspruch REAL NOT NULL DEFAULT 30")
    if "resturlaub_vorjahr" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN resturlaub_vorjahr REAL NOT NULL DEFAULT 0")
    if "rolle" not in spalten:
        # Neue Spalte ohne Default hinzufuegen, dann bestehende Personen auf 'admin'
        # setzen - so wird beim Einfuehren der Rollen niemand aus der Verwaltung ausgesperrt.
        conn.execute("ALTER TABLE person ADD COLUMN rolle TEXT")
        conn.execute("UPDATE person SET rolle = 'admin' WHERE rolle IS NULL")
    # Ungueltige Rollenwerte (z.B. leerer String aus Altdaten) auf 'mitarbeiter'
    # normalisieren. Trifft bewusst NICHT NULL (der Aussperr-Schutz oben setzt NULL frisch
    # migrierter Bestaende zu 'admin') - nur echte Muellwerte.
    conn.execute("UPDATE person SET rolle = 'mitarbeiter' WHERE rolle IS NOT NULL AND rolle NOT IN ('admin', 'mitarbeiter')")
    if "passwort_hash" not in spalten:
        conn.execute("ALTER TABLE person ADD COLUMN passwort_hash TEXT")


def init_db() -> None:
    with verbindung() as conn:
        conn.executescript(SCHEMA)
        _migriere(conn)
        if conn.execute("SELECT COUNT(*) AS n FROM person").fetchone()["n"] == 0:
            # Erste Beispiel-Person ist Admin, damit eine frische DB sofort verwaltbar ist.
            for i, (kuerzel, name) in enumerate([("AK", "Anke Krause"), ("TB", "Tom Berger"), ("ML", "Mara Lang")]):
                conn.execute(
                    "INSERT INTO person (id, name, kuerzel, wochenstunden, aktiv, rolle) VALUES (?, ?, ?, ?, 1, ?)",
                    ("p_" + uuid4().hex[:8], name, kuerzel, json.dumps(_STD_WOCHE), "admin" if i == 0 else "mitarbeiter"),
                )
        if conn.execute("SELECT COUNT(*) AS n FROM abwesenheit_typ").fetchone()["n"] == 0:
            conn.executemany(
                "INSERT INTO abwesenheit_typ (code, name, farbe, reduziert_soll, anrechnen, anwesend, reihenfolge)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                _ABW_SEED,
            )
        if conn.execute("SELECT COUNT(*) AS n FROM tagesregel").fetchone()["n"] == 0:
            # Typische halbe Tage: Heiligabend und Silvester, global.
            for monat, tag, notiz in [(12, 24, "Heiligabend"), (12, 31, "Silvester")]:
                conn.execute(
                    "INSERT INTO tagesregel (id, person_id, art, monat, tag, anteil, notiz, aktiv)"
                    " VALUES (?, NULL, 'jahrestag', ?, ?, 0.5, ?, 1)",
                    ("r_" + uuid4().hex[:8], monat, tag, notiz),
                )
            # Brückentage als globaler Schalter (Standard: aus).
            conn.execute(
                "INSERT INTO tagesregel (id, person_id, art, anteil, notiz, aktiv)"
                " VALUES (?, NULL, 'brueckentag', 0.0, 'Brückentage automatisch', 0)",
                ("r_" + uuid4().hex[:8],),
            )
    # Bundesweite Feiertage für das laufende und nächste Jahr sicherstellen.
    from datetime import date
    jetzt = date.today().year
    for j in (jetzt, jetzt + 1):
        stelle_feiertage_sicher(j)


# -- Wochen-Override (abweichende Wochenstunden einzelner Wochen) ----------

def liste_wochen_override(person_id: str) -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT jahr, kw, wochenstunden FROM wochen_override WHERE person_id = ? ORDER BY jahr, kw",
            (person_id,),
        ).fetchall()
    return [{"jahr": r["jahr"], "kw": r["kw"], "wochenstunden": json.loads(r["wochenstunden"])} for r in rows]


def setze_wochen_override(person_id: str, jahr: int, kw: int, wochenstunden: list) -> dict:
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO wochen_override (person_id, jahr, kw, wochenstunden) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(person_id, jahr, kw) DO UPDATE SET wochenstunden = excluded.wochenstunden",
            (person_id, jahr, kw, json.dumps(wochenstunden)),
        )
    return {"jahr": jahr, "kw": kw, "wochenstunden": wochenstunden}


def loesche_wochen_override(person_id: str, jahr: int, kw: int) -> bool:
    with verbindung() as conn:
        cur = conn.execute(
            "DELETE FROM wochen_override WHERE person_id = ? AND jahr = ? AND kw = ?",
            (person_id, jahr, kw),
        )
    return cur.rowcount > 0


def overrides_je_person() -> dict[str, dict[tuple[int, int], list]]:
    """Alle Wochen-Overrides als person_id -> {(jahr, kw): wochenstunden}."""
    with verbindung() as conn:
        rows = conn.execute("SELECT person_id, jahr, kw, wochenstunden FROM wochen_override").fetchall()
    out: dict[str, dict[tuple[int, int], list]] = {}
    for r in rows:
        out.setdefault(r["person_id"], {})[(r["jahr"], r["kw"])] = json.loads(r["wochenstunden"])
    return out


# -- Personen -------------------------------------------------------------

def _person(r: sqlite3.Row) -> dict:
    schluessel = r.keys()
    return {
        "id": r["id"], "name": r["name"], "kuerzel": r["kuerzel"], "farbe": r["farbe"],
        "wochenstunden": json.loads(r["wochenstunden"]),
        "bundesland": r["bundesland"] if "bundesland" in schluessel else None,
        "urlaubsanspruch": r["urlaubsanspruch"] if "urlaubsanspruch" in schluessel else 30,
        "resturlaub_vorjahr": r["resturlaub_vorjahr"] if "resturlaub_vorjahr" in schluessel else 0,
        "aktiv": bool(r["aktiv"]),
        # Unbekannte/fehlende Werte sicher auf 'mitarbeiter' mappen - sonst wuerde eine
        # einzige kaputte Zeile (z.B. aus fremdem Backup) die ganze Personenliste (500) killen.
        "rolle": (r["rolle"] if "rolle" in schluessel and r["rolle"] in ("admin", "mitarbeiter") else "mitarbeiter"),
        "hat_passwort": bool("passwort_hash" in schluessel and r["passwort_hash"]),
    }


def liste_personen() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute("SELECT * FROM person ORDER BY name").fetchall()
    return [_person(r) for r in rows]


def hole_person(pid: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM person WHERE id = ?", (pid,)).fetchone()
    return _person(r) if r else None


# -- Passwort / Anmeldung (Modul auth nutzt diese Funktionen) ---------------

def setze_passwort(pid: str, klartext: str | None) -> dict | None:
    """Setzt oder entfernt (leerer Wert) das Passwort einer Person."""
    wert = hash_passwort(klartext) if klartext else None
    with verbindung() as conn:
        cur = conn.execute("UPDATE person SET passwort_hash = ? WHERE id = ?", (wert, pid))
        if cur.rowcount == 0:
            return None
    return hole_person(pid)


def pruefe_anmeldung(kennung: str, klartext: str) -> dict | None:
    """Findet eine aktive Person per Name ODER Kuerzel (ohne Gross-/Kleinschreibung)
    und prueft ihr Passwort. Gibt die Person zurueck oder None."""
    kennung = (kennung or "").strip()
    if not kennung or not klartext:
        return None
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT * FROM person WHERE aktiv = 1 AND (name = ? COLLATE NOCASE OR kuerzel = ? COLLATE NOCASE)",
            (kennung, kennung),
        ).fetchall()
    for r in rows:
        if pruefe_passwort(klartext, r["passwort_hash"] if "passwort_hash" in r.keys() else None):
            return _person(r)
    return None


def admin_mit_passwort_existiert(ausser_pid: str | None = None) -> bool:
    """True, wenn (ausser ggf. einer Person) eine aktive Admin-Person mit Passwort
    existiert. Basis fuer den Aussperr-Schutz."""
    sql = (
        "SELECT 1 FROM person WHERE rolle = 'admin' AND aktiv = 1"
        " AND passwort_hash IS NOT NULL AND passwort_hash != ''"
    )
    params: tuple = ()
    if ausser_pid:
        sql += " AND id != ?"
        params = (ausser_pid,)
    with verbindung() as conn:
        return conn.execute(sql + " LIMIT 1", params).fetchone() is not None


def hat_admin_mit_passwort() -> bool:
    """True, wenn mindestens eine aktive Admin-Person ein Passwort hat (Aussperr-Schutz)."""
    return admin_mit_passwort_existiert()


def erstelle_person(name: str, kuerzel: str | None, wochenstunden: list | None, farbe: str | None,
                    bundesland: str | None = None, urlaubsanspruch: float = 30,
                    resturlaub_vorjahr: float = 0) -> dict:
    pid = "p_" + uuid4().hex[:8]
    with verbindung() as conn:
        conn.execute(
            "INSERT INTO person (id, name, kuerzel, farbe, wochenstunden, bundesland, urlaubsanspruch, resturlaub_vorjahr, aktiv)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (pid, name, kuerzel, farbe, json.dumps(wochenstunden or _STD_WOCHE), bundesland, urlaubsanspruch, resturlaub_vorjahr),
        )
    if bundesland:
        _feiertage_nachladen()
    return hole_person(pid)  # type: ignore[return-value]


def aktualisiere_person(pid: str, aenderungen: dict) -> dict | None:
    f = {k: v for k, v in aenderungen.items() if k in PersonUpdate.model_fields}
    if not f:
        return hole_person(pid)
    if "wochenstunden" in f:
        f["wochenstunden"] = json.dumps(f["wochenstunden"])
    if "aktiv" in f:
        f["aktiv"] = 1 if f["aktiv"] else 0
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE person SET {zuweisung} WHERE id = ?", (*f.values(), pid))
    if f.get("bundesland"):
        _feiertage_nachladen()
    return hole_person(pid)


def loesche_person(pid: str) -> bool:
    with verbindung() as conn:
        conn.execute("DELETE FROM urlaub WHERE person_id = ?", (pid,))
        cur = conn.execute("DELETE FROM person WHERE id = ?", (pid,))
    return cur.rowcount > 0


# -- Urlaub ---------------------------------------------------------------

def liste_urlaub(person_id: str | None, von: str, bis: str) -> list[dict]:
    with verbindung() as conn:
        if person_id:
            rows = conn.execute(
                "SELECT * FROM urlaub WHERE person_id = ? AND datum >= ? AND datum <= ? ORDER BY datum",
                (person_id, von, bis),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM urlaub WHERE datum >= ? AND datum <= ? ORDER BY datum", (von, bis)
            ).fetchall()
    return [{"id": r["id"], "person_id": r["person_id"], "datum": r["datum"], "anteil": r["anteil"],
             "typ": r["typ"], "notiz": r["notiz"]} for r in rows]


def setze_urlaub(person_id: str, datum: str, anteil: float, typ: str, notiz: str | None) -> dict:
    """Setzt/aktualisiert einen Urlaubstag (ein Eintrag je Person+Datum)."""
    with verbindung() as conn:
        vorhanden = conn.execute(
            "SELECT id FROM urlaub WHERE person_id = ? AND datum = ?", (person_id, datum)
        ).fetchone()
        if vorhanden:
            conn.execute("UPDATE urlaub SET anteil = ?, typ = ?, notiz = ? WHERE id = ?",
                         (anteil, typ, notiz, vorhanden["id"]))
            uid = vorhanden["id"]
        else:
            uid = "u_" + uuid4().hex[:8]
            conn.execute("INSERT INTO urlaub (id, person_id, datum, anteil, typ, notiz) VALUES (?, ?, ?, ?, ?, ?)",
                         (uid, person_id, datum, anteil, typ, notiz))
    return {"id": uid, "person_id": person_id, "datum": datum, "anteil": anteil, "typ": typ, "notiz": notiz}


def loesche_urlaub(uid: str) -> bool:
    with verbindung() as conn:
        cur = conn.execute("DELETE FROM urlaub WHERE id = ?", (uid,))
    return cur.rowcount > 0


def hole_urlaub(uid: str) -> dict | None:
    """Einzelner Urlaubseintrag (fuer die Eigentumspruefung beim Loeschen)."""
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM urlaub WHERE id = ?", (uid,)).fetchone()
    if r is None:
        return None
    return {"id": r["id"], "person_id": r["person_id"], "datum": r["datum"],
            "anteil": r["anteil"], "typ": r["typ"], "notiz": r["notiz"]}


def _genommen(person: dict, jahr: int) -> float:
    """Im Jahr verbrauchte Urlaubstage, gewichtet mit der echten Soll-Wirkung des Tages
    (Feiertag/freier Tag = 0, Halbtag = halb). Anrechenbare Arten = anrechnen=1."""
    with verbindung() as conn:
        anrechenbar = {
            r["code"] for r in conn.execute("SELECT code FROM abwesenheit_typ WHERE anrechnen = 1").fetchall()
        } or {"urlaub"}
    from . import kalender
    return kalender.urlaub_konto_genommen(person, jahr, anrechenbar)


def urlaubskonto(person_id: str, jahr: int) -> dict | None:
    p = hole_person(person_id)
    if p is None:
        return None
    anspruch = float(p["urlaubsanspruch"] or 0)
    uebertrag = float(p["resturlaub_vorjahr"] or 0)
    genommen = _genommen(p, jahr)
    genommen_vorjahr = _genommen(p, jahr - 1)
    verfuegbar = round(anspruch + uebertrag, 2)
    return {
        "person_id": person_id,
        "jahr": jahr,
        "anspruch": anspruch,
        "uebertrag": uebertrag,
        "verfuegbar": verfuegbar,
        "genommen": genommen,
        "verbleibend": round(verfuegbar - genommen, 2),
        "genommen_vorjahr": genommen_vorjahr,
    }


def urlaubskonten(jahr: int) -> list[dict]:
    return [k for p in liste_personen() if (k := urlaubskonto(p["id"], jahr)) is not None]


# -- Feiertage ------------------------------------------------------------

def liste_feiertage(von: str, bis: str) -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT DISTINCT datum, name, region FROM feiertag WHERE datum >= ? AND datum <= ? ORDER BY datum",
            (von, bis),
        ).fetchall()
    return [{"datum": r["datum"], "name": r["name"], "region": r["region"]} for r in rows]


def feiertage_relevant(von: str, bis: str, bundesland: str | None) -> list[dict]:
    """Feiertage, die für ein Bundesland gelten: bundesweite (Region NULL) plus die
    des eigenen Bundeslands. Ohne Bundesland nur die bundesweiten."""
    return [f for f in liste_feiertage(von, bis) if f["region"] is None or f["region"] == bundesland]


def uebernehme_feiertage(eintraege: list[dict]) -> int:
    """Speichert Feiertage mit ihrer jeweiligen Region (None = bundesweit).

    Vorher denselben Tag/dieselbe Region entfernen - das dedupliziert auch
    bundesweite Einträge (Region NULL gilt im Primärschlüssel als verschieden).
    """
    n = 0
    with verbindung() as conn:
        for e in eintraege:
            reg = e.get("region")
            if reg is None:
                conn.execute("DELETE FROM feiertag WHERE datum = ? AND region IS NULL", (e["datum"],))
            else:
                conn.execute("DELETE FROM feiertag WHERE datum = ? AND region = ?", (e["datum"], reg))
            conn.execute(
                "INSERT INTO feiertag (datum, name, region) VALUES (?, ?, ?)",
                (e["datum"], e["name"], reg),
            )
            n += 1
    return n


def stelle_feiertage_sicher(jahr: int, land: str = "DE") -> int:
    """Sorgt dafür, dass für ein Jahr die nötigen Feiertage vorhanden sind:
    die bundesweiten und - je nach hinterlegten Personen-Bundesländern - die
    regionalen. Pro Region wird nur geladen, wenn sie für das Jahr noch ganz fehlt;
    eigene Anpassungen einer bereits vorhandenen Region bleiben unberührt.
    """
    from . import feiertage
    with verbindung() as conn:
        vorhanden = {
            r["region"]
            for r in conn.execute("SELECT DISTINCT region FROM feiertag WHERE datum LIKE ?", (f"{jahr}-%",)).fetchall()
        }
    erzeugt = 0
    # Bundesweite sicherstellen (Region NULL).
    if None not in vorhanden:
        bund = [e for e in feiertage.vorschau(land, None, jahr) if e.get("region") is None]
        erzeugt += uebernehme_feiertage(bund)
        vorhanden.add(None)
    # Regionale je hinterlegtem Bundesland sicherstellen.
    for region in {p["bundesland"] for p in liste_personen() if p.get("bundesland")}:
        if region in vorhanden:
            continue
        regional = [e for e in feiertage.vorschau(land, region, jahr) if e.get("region") == region]
        erzeugt += uebernehme_feiertage(regional)
        vorhanden.add(region)
    return erzeugt


def _feiertage_nachladen() -> None:
    """Stellt nach einer Bundesland-Aenderung die regionalen Feiertage fuer dieses und
    das naechste Jahr sicher (defensiv - darf nie einen Personen-Schreibvorgang stoeren)."""
    try:
        from datetime import date
        j = date.today().year
        stelle_feiertage_sicher(j)
        stelle_feiertage_sicher(j + 1)
    except Exception:
        pass


def loesche_feiertage(jahr: int, region: str | None) -> int:
    with verbindung() as conn:
        if region:
            cur = conn.execute("DELETE FROM feiertag WHERE datum LIKE ? AND region = ?", (f"{jahr}-%", region))
        else:
            cur = conn.execute("DELETE FROM feiertag WHERE datum LIKE ?", (f"{jahr}-%",))
    return cur.rowcount


# -- Abwesenheits-Arten ---------------------------------------------------

def _abw_typ(r: sqlite3.Row) -> dict:
    return {
        "code": r["code"], "name": r["name"], "farbe": r["farbe"],
        "reduziert_soll": bool(r["reduziert_soll"]), "anrechnen": bool(r["anrechnen"]),
        "anwesend": bool(r["anwesend"]), "reihenfolge": r["reihenfolge"],
    }


def liste_abwesenheitstypen() -> list[dict]:
    with verbindung() as conn:
        rows = conn.execute("SELECT * FROM abwesenheit_typ ORDER BY reihenfolge, name").fetchall()
    return [_abw_typ(r) for r in rows]


def hole_abwesenheitstyp(code: str) -> dict | None:
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM abwesenheit_typ WHERE code = ?", (code,)).fetchone()
    return _abw_typ(r) if r else None


def aktualisiere_abwesenheitstyp(code: str, aenderungen: dict) -> dict | None:
    f = {k: v for k, v in aenderungen.items() if k in AbwesenheitTypUpdate.model_fields}
    if not f:
        return hole_abwesenheitstyp(code)
    for flag in ("reduziert_soll", "anrechnen", "anwesend"):
        if flag in f:
            f[flag] = 1 if f[flag] else 0
    zuweisung = ", ".join(f"{k} = ?" for k in f)
    with verbindung() as conn:
        conn.execute(f"UPDATE abwesenheit_typ SET {zuweisung} WHERE code = ?", (*f.values(), code))
    return hole_abwesenheitstyp(code)


def _anrechenbare_codes() -> set[str]:
    """Codes der Abwesenheits-Arten, die gegen den Urlaubsanspruch zählen."""
    with verbindung() as conn:
        rows = conn.execute("SELECT code FROM abwesenheit_typ WHERE anrechnen = 1").fetchall()
    codes = {r["code"] for r in rows}
    return codes or {"urlaub"}  # Fallback, falls die Tabelle noch leer ist


# -- Tagesregeln (halbe Tage / Sonderregeln) ------------------------------

def _tagesregel(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"], "person_id": r["person_id"], "art": r["art"],
        "monat": r["monat"], "tag": r["tag"], "wochentag": r["wochentag"],
        "anteil": r["anteil"], "notiz": r["notiz"], "aktiv": bool(r["aktiv"]),
    }


def liste_tagesregeln(person_id: str | None = None, nur_person: bool = False) -> list[dict]:
    """Tagesregeln. Standard: globale + die der Person. nur_person=True: nur die der Person."""
    with verbindung() as conn:
        if nur_person:
            rows = conn.execute("SELECT * FROM tagesregel WHERE person_id = ? ORDER BY art, monat, tag", (person_id,)).fetchall()
        elif person_id:
            rows = conn.execute(
                "SELECT * FROM tagesregel WHERE person_id IS NULL OR person_id = ? ORDER BY art, monat, tag",
                (person_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tagesregel ORDER BY person_id IS NOT NULL, art, monat, tag").fetchall()
    return [_tagesregel(r) for r in rows]


def setze_tagesregel(daten: dict) -> dict:
    rid = daten.get("id") or ("r_" + uuid4().hex[:8])
    werte = (
        rid, daten.get("person_id"), daten["art"], daten.get("monat"), daten.get("tag"),
        daten.get("wochentag"), float(daten.get("anteil", 0.5)), daten.get("notiz"),
        1 if daten.get("aktiv", True) else 0,
    )
    with verbindung() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tagesregel (id, person_id, art, monat, tag, wochentag, anteil, notiz, aktiv)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            werte,
        )
        r = conn.execute("SELECT * FROM tagesregel WHERE id = ?", (rid,)).fetchone()
    return _tagesregel(r)


def hole_tagesregel(rid: str) -> dict | None:
    """Einzelne Tagesregel (fuer die Eigentumspruefung beim Loeschen)."""
    with verbindung() as conn:
        r = conn.execute("SELECT * FROM tagesregel WHERE id = ?", (rid,)).fetchone()
    return _tagesregel(r) if r else None


def loesche_tagesregel(rid: str) -> bool:
    with verbindung() as conn:
        cur = conn.execute("DELETE FROM tagesregel WHERE id = ?", (rid,))
    return cur.rowcount > 0


# -- Querschnitt: Feiertags-/Urlaubs-Datumswerte (zentral, genutzt von serien+termine) --

def feiertage_set(von: str, bis: str) -> set[str]:
    """Feiertags-Datumswerte (ISO) im Bereich - zum Ueberspringen in Serien/Terminen."""
    with verbindung() as conn:
        try:
            rows = conn.execute(
                "SELECT DISTINCT datum FROM feiertag WHERE datum >= ? AND datum <= ?", (von, bis)
            ).fetchall()
        except Exception:
            return set()
    return {r["datum"] for r in rows}


def urlaubstage_set(kuerzel: str | None, von: str, bis: str) -> set[str]:
    """Urlaubs-Datumswerte (ISO) der Person mit diesem Kuerzel im Bereich. Defensiv."""
    if not kuerzel:
        return set()
    try:
        pid = next((p["id"] for p in liste_personen() if p.get("kuerzel") == kuerzel), None)
        if not pid:
            return set()
        return {u["datum"] for u in liste_urlaub(pid, von, bis)}
    except Exception:
        return set()
