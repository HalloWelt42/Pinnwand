"""Verzeichnis der Pinnwand: SQLite über appkern.datenbank. Jedes Aggregat (Board, Karte, Ordner, ...) ist eine Zeile mit
Kennung, Fassung und Inhalt als JSON in der Form des Modells, dazu die Spalten, nach denen gesucht oder geordnet wird.
Geschrieben wird nur in einer Transaktion über den `Schreiber`, der jede Zeile mit Vorher und Nachher festhält (Journal,
Rückgängig, Ereignisse)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from appkern.datenbank import Datenbank

BAUSTEIN = "pinnwand"


@dataclass(frozen=True)
class Tabelle:
    """Eine Tabelle von Aggregaten: welche Felder des Inhalts als eigene Spalte stehen (zum Suchen und Ordnen)."""

    name: str
    spalten: tuple[str, ...] = ()
    #: Feld im JSON je Spalte (Vorgabe: gleicher Name)
    felder: dict[str, str] = field(default_factory=dict)
    #: Spalten, die eine spätere Stufe nachträgt (ALTER TABLE); die Stufe der Tabelle selbst legt sie nicht an
    nachgetragen: tuple[str, ...] = ()

    def werte(self, daten: dict) -> list[Any]:
        return [daten.get(self.felder.get(s, s)) for s in self.spalten]


#: Tabellen je Stufe des Schemas; eine Stufe ändert sich nie mehr, sobald sie ausgerollt ist
TABELLEN_DER_STUFEN: tuple[tuple[Tabelle, ...], ...] = ((
    Tabelle("konten", ("kellerwolke",)),
    Tabelle("boards", ("kuerzel",)),
    Tabelle("karten", ("board", "schluessel", "spalte", "reihe", "nummer"), nachgetragen=("nummer",)),
    Tabelle("gruppen", ("board",)),
    Tabelle("laufnummern", ("board",)),
    Tabelle("ordner", ("konto", "reihe")),
    Tabelle("papierkorb", ("board", "am")),
    Tabelle("entfernt", ("board",)),
    Tabelle("vorlagen", ("konto",)),
    Tabelle("hinweise", ("konto", "gelesen", "zeit")),
    Tabelle("person_einstellungen"),
), (
    Tabelle("zeiteintraege", ("konto", "karte", "board", "datum")),
    Tabelle("timer", ("konto", "karte", "board")),
    Tabelle("zeitkonten", ("konto", "ab")),
    Tabelle("abwesenheiten", ("konto", "von", "bis")),
), (
    Tabelle("serien", ("board",)),
    Tabelle("termine", ("board", "datum")),
), (
    Tabelle("berichte", ("konto", "erstellt")),
), (
    Tabelle("zaehler"),
), (
    Tabelle("commits", ("repo", "zeit")),
    # "commit" ist ein Wort von SQL: die Spalte heißt commitkennung
    Tabelle("commitbezuege", ("commitkennung", "karte", "board"), felder={"commitkennung": "commit"}),
))
TABELLEN: dict[str, Tabelle] = {t.name: t for stufe in TABELLEN_DER_STUFEN for t in stufe}


#: Art der Spalten, die keine Texte sind
SPALTENART = {"reihe": "REAL", "nummer": "INTEGER"}


def _tabelle_sql(t: Tabelle) -> str:
    zusatz = "".join(f", {s} {SPALTENART.get(s, 'TEXT')}" for s in t.spalten if s not in t.nachgetragen)
    return f"CREATE TABLE {t.name} (id TEXT PRIMARY KEY, fassung INTEGER NOT NULL DEFAULT 1, daten TEXT NOT NULL{zusatz});"


def _tabellen_sql(stufe: int) -> str:
    return "\n".join(_tabelle_sql(t) for t in TABELLEN_DER_STUFEN[stufe])


STUFEN: list[str] = [
    _tabellen_sql(0) + """
    CREATE UNIQUE INDEX boards_kuerzel ON boards(kuerzel);
    CREATE UNIQUE INDEX karten_schluessel ON karten(schluessel);
    CREATE INDEX karten_board ON karten(board, spalte, reihe);
    CREATE INDEX ordner_konto ON ordner(konto, reihe);
    CREATE INDEX papierkorb_board ON papierkorb(board, am);
    CREATE INDEX hinweise_konto ON hinweise(konto, gelesen, zeit);
    CREATE TABLE journal (
      id TEXT PRIMARY KEY, konto TEXT NOT NULL, zeit TEXT NOT NULL, text TEXT NOT NULL,
      bilder TEXT NOT NULL, rueckgaengig INTEGER NOT NULL DEFAULT 1, zurueckgenommen TEXT
    );
    CREATE INDEX journal_zeit ON journal(zeit);
    """,
    _tabellen_sql(1) + """
    CREATE INDEX zeiteintraege_konto ON zeiteintraege(konto, datum);
    CREATE INDEX zeiteintraege_karte ON zeiteintraege(karte);
    CREATE INDEX zeiteintraege_board ON zeiteintraege(board);
    CREATE INDEX timer_karte ON timer(karte);
    CREATE INDEX timer_board ON timer(board);
    CREATE UNIQUE INDEX zeitkonten_ab ON zeitkonten(konto, ab);
    CREATE INDEX abwesenheiten_konto ON abwesenheiten(konto, von);
    """,
    _tabellen_sql(2) + """
    CREATE INDEX serien_board ON serien(board);
    CREATE INDEX termine_board ON termine(board, datum);
    """,
    _tabellen_sql(3) + """
    CREATE INDEX berichte_konto ON berichte(konto, erstellt);
    """,
    # Gesamtnummer jeder Karte über alle Boards (HELF-49): eindeutig in der Datenbank, vergeben über den Zähler
    # "karten" in zaehler; vorhandene Karten nummeriert der Start einmal nach (anwendung/gesamtnummer.py)
    _tabellen_sql(4) + """
    ALTER TABLE karten ADD COLUMN nummer INTEGER;
    CREATE UNIQUE INDEX karten_nummer ON karten(nummer);
    """,
    # Commits an Karten (HELF-35): jeder bekannte Commit und je Commit und Karte ein Bezug
    _tabellen_sql(5) + """
    CREATE INDEX commits_zeit ON commits(zeit);
    CREATE INDEX commitbezuege_commit ON commitbezuege(commitkennung);
    CREATE INDEX commitbezuege_karte ON commitbezuege(karte);
    CREATE INDEX commitbezuege_board ON commitbezuege(board);
    """,
]


async def einrichten(db: Datenbank) -> None:
    await db.einrichten(BAUSTEIN, STUFEN)


@dataclass
class Bild:
    """Eine geschriebene Zeile: Inhalt vorher und nachher (None: gab es nicht oder gibt es nicht mehr), mit Fassung."""

    tabelle: str
    id: str
    vorher: dict | None
    nachher: dict | None


def _zeile_zu_daten(z: sqlite3.Row | None) -> dict | None:
    if z is None:
        return None
    d = json.loads(z["daten"])
    d["fassung"] = z["fassung"]
    return d


class Schreiber:
    """Lesen und Schreiben in einer Transaktion. Jede Zeile wird beim ersten Schreiben mit ihrem Vorher gemerkt; am Ende
    stehen Vorher und Nachher je Zeile in `bilder` (für Journal, Rückgängig und Ereignisse)."""

    def __init__(self, v: sqlite3.Connection) -> None:
        self.v = v
        self._bilder: dict[tuple[str, str], Bild] = {}

    # --- lesen -----------------------------------------------------------------------------------------------------

    def lies(self, tabelle: str, id: str) -> dict | None:
        return _zeile_zu_daten(self.v.execute(f"SELECT fassung, daten FROM {tabelle} WHERE id=?", (id,)).fetchone())

    def alle(self, tabelle: str, wo: str = "", werte: tuple = (), ordnung: str = "") -> list[dict]:
        sql = f"SELECT fassung, daten FROM {tabelle}" + (f" WHERE {wo}" if wo else "") + (f" ORDER BY {ordnung}" if ordnung else "")
        return [_zeile_zu_daten(z) for z in self.v.execute(sql, werte).fetchall()]  # type: ignore[misc]

    def lies_vorher(self, tabelle: str, id: str) -> dict | None:
        """Der Stand einer Zeile vor dieser Transaktion."""
        b = self._bilder.get((tabelle, id))
        return b.vorher if b else self.lies(tabelle, id)

    def alle_vorher(self, tabelle: str) -> list[dict]:
        """Alle Zeilen einer Tabelle, wie sie vor dieser Transaktion standen."""
        zeilen = {d["id"]: d for d in self.alle(tabelle)}
        for (t, id), b in self._bilder.items():
            if t != tabelle:
                continue
            if b.vorher is None:
                zeilen.pop(id, None)
            else:
                zeilen[id] = b.vorher
        return list(zeilen.values())

    def wert(self, sql: str, werte: tuple = ()) -> Any:
        z = self.v.execute(sql, werte).fetchone()
        return z[0] if z else None

    # --- schreiben -------------------------------------------------------------------------------------------------

    def _merken(self, tabelle: str, id: str) -> Bild:
        schluessel = (tabelle, id)
        if schluessel not in self._bilder:
            self._bilder[schluessel] = Bild(tabelle, id, self.lies(tabelle, id), None)
        return self._bilder[schluessel]

    def schreib(self, tabelle: str, daten: dict) -> dict:
        """Zeile anlegen oder ersetzen; die Fassung zählt hoch. Ergebnis: der neue Stand mit Fassung."""
        t = TABELLEN[tabelle]
        id = daten["id"]
        bild = self._merken(tabelle, id)
        alt = self.lies(tabelle, id)
        fassung = (alt["fassung"] + 1) if alt else 1
        inhalt = {k: v for k, v in daten.items() if k != "fassung"}
        werte = t.werte(inhalt)
        spalten = ", ".join(("id", "fassung", "daten", *t.spalten))
        platz = ", ".join("?" * (3 + len(t.spalten)))
        self.v.execute(f"INSERT OR REPLACE INTO {tabelle} ({spalten}) VALUES ({platz})",
                       (id, fassung, json.dumps(inhalt, ensure_ascii=False), *werte))
        neu = {**inhalt, "fassung": fassung}
        bild.nachher = neu
        return neu

    def journal_vergessen(self, konto: str) -> None:
        """Das Rückgängig eines Kontos verwerfen (beim Zurücksetzen und Löschen des Kontos)."""
        self.v.execute("DELETE FROM journal WHERE konto=?", (konto,))

    def loesch(self, tabelle: str, id: str) -> None:
        bild = self._merken(tabelle, id)
        self.v.execute(f"DELETE FROM {tabelle} WHERE id=?", (id,))
        bild.nachher = None

    def zurueckschreiben(self, tabelle: str, id: str, stand: dict | None) -> None:
        """Einen früheren Stand genau so wiederherstellen (für Rückgängig): die Fassung zählt dabei weiter hoch, damit
        jeder, der den Zwischenstand kennt, eine Änderung sieht."""
        if stand is None:
            self.loesch(tabelle, id)
        else:
            self.schreib(tabelle, stand)

    @property
    def bilder(self) -> list[Bild]:
        return [b for b in self._bilder.values() if b.vorher != b.nachher]


class Verzeichnis:
    """Lesen außerhalb einer Änderung (für `/stand` und Abfragen) und das Schreiben über `transaktion`."""

    def __init__(self, db: Datenbank) -> None:
        self.db = db

    async def lies(self, tabelle: str, id: str) -> dict | None:
        z = await self.db.zeile(f"SELECT fassung, daten FROM {tabelle} WHERE id=?", (id,))
        return _zeile_zu_daten(z)  # type: ignore[arg-type]

    async def alle(self, tabelle: str, wo: str = "", werte: tuple = (), ordnung: str = "") -> list[dict]:
        sql = f"SELECT fassung, daten FROM {tabelle}" + (f" WHERE {wo}" if wo else "") + (f" ORDER BY {ordnung}" if ordnung else "")
        return [_zeile_zu_daten(z) for z in await self.db.zeilen(sql, werte)]  # type: ignore[misc]

    async def transaktion(self, arbeit: Callable[[Schreiber], Any]) -> tuple[Any, list[Bild]]:
        def huelle(v: sqlite3.Connection) -> tuple[Any, list[Bild]]:
            v.row_factory = sqlite3.Row
            s = Schreiber(v)
            ergebnis = arbeit(s)
            return ergebnis, s.bilder

        return await self.db.transaktion(huelle)
