"""Commits an Karten (HELF-35). Ein eigenes kleines Programm (sammler/commitsammler.py) liest Commits aus Git-Repos und
spielt sie ein; nur der Besitzer der App darf das. Die Pinnwand merkt sich jeden Commit (Tabelle `commits`, für niemanden
sichtbar) und hängt ihn an jede Karte, deren Schlüssel in seiner Nachricht steht (Tabelle `commitbezuege`, je Commit und
Karte eine Zeile mit allem, was die Karte zeigt; sichtbar für die Mitglieder des Boards). Dazu von Hand verknüpfen und
lösen am Ticket. Ein gelöster Bezug aus der Nachricht bleibt als gelöst stehen, damit der nächste Abgleich ihn nicht
wieder anhängt."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable

from pydantic import Field

from ..modell import Board, Commit, CommitArt, CommitBezug, Karte, Kennung, Konto, Modell
from ..regeln.board import hat_recht
from .kartenbasis import karte_lesen, vermerken
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext

#: so viele Commits nimmt eine Sendung höchstens
SENDUNG_HOECHSTENS = 500
#: Schlüssel einer Karte in einem Text: Kürzel des Boards (2 bis 6 Zeichen, vorn ein Buchstabe), Bindestrich, Nummer
SCHLUESSEL = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{1,5})-([1-9][0-9]{0,6})(?![0-9A-Za-z])")
#: so viele Treffer liefert die Suche nach einem Commit
TREFFER = 20


class RepoAngabe(Modell):
    """Woher die Commits einer Sendung kommen: Kennung (Besitzer/Name oder lokal/Name), Name, Quelle und Muster des
    Verweises mit {hash} (ohne: die Pinnwand zeigt den Commit selbst)."""

    kennung: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    quelle: str = Field(default="lokal", max_length=100)
    verweis: str | None = Field(default=None, max_length=500)


class CommitAngabe(Modell):
    hash: str = Field(pattern=r"^[0-9a-f]{7,64}$")
    autor: str = Field(default="", max_length=200)
    zeit: str = Field(max_length=40)
    nachricht: str = Field(default="", max_length=4000)
    dateien: list[str] = Field(default_factory=list, max_length=100)


class Sendung(Modell):
    repo: RepoAngabe
    commits: list[CommitAngabe] = Field(max_length=SENDUNG_HOECHSTENS)


class Eingespielt(Modell):
    neu: int
    verknuepft: int


def schluessel_in(text: str) -> list[str]:
    """Alle Kartenschlüssel in einem Text, jeder einmal, in der Reihenfolge des Vorkommens."""
    return list(dict.fromkeys(f"{k}-{n}" for k, n in SCHLUESSEL.findall(text)))


def commit_kennung(repo: str, hash: str) -> Kennung:
    return f"{repo}@{hash}"


def bezug_kennung(commit: Kennung, karte: Kennung) -> Kennung:
    """Fest aus Commit und Karte (so findet das Einspielen einen Bezug wieder), ohne Schrägstrich für den Weg."""
    return "cb-" + hashlib.sha1(f"{commit}>{karte}".encode()).hexdigest()[:20]


def kartenverzeichnis(k: Kontext) -> dict[str, Karte]:
    """Jede Karte unter ihrem Schlüssel und unter früheren Schlüsseln (eine umgezogene Karte findet man auch so)."""
    karten: dict[str, Karte] = {}
    for d in k.s.alle("karten"):
        c = Karte.model_validate(d)
        for s in c.frueher:
            karten.setdefault(s, c)
    for d in k.s.alle("karten"):
        karten[d["schluessel"]] = Karte.model_validate(d)
    return karten


def bezug_aus(c: Commit, karte: Karte, art: CommitArt, k: Kontext) -> CommitBezug:
    return CommitBezug(**{**c.model_dump(), "id": bezug_kennung(c.id, karte.id)}, commit=c.id, karte=karte.id,
                       board=karte.board, art=art, von=k.konto.id, am=k.jetzt)


def bezuege_umziehen(k: Kontext, karte: Karte) -> None:
    """Zieht eine Karte in ein anderes Board, gehen ihre Commits mit (und sind dann für dessen Mitglieder zu sehen)."""
    for d in k.s.alle("commitbezuege", "karte=?", (karte.id,)):
        if d.get("board") != karte.board:
            k.s.schreib("commitbezuege", {**d, "board": karte.board})


def bezug_auffrischen(alt: CommitBezug, c: Commit) -> CommitBezug:
    """Ein bestehender Bezug mit den neuen Angaben des Commits (Verweis, Quelle, Name), Art und Lösung bleiben."""
    return alt.model_copy(update={"repo": c.repo, "reponame": c.reponame, "quelle": c.quelle, "autor": c.autor,
                                  "zeit": c.zeit, "nachricht": c.nachricht, "dateien": c.dateien, "verweis": c.verweis})


class Commits:
    def __init__(self, anwendung: Anwendung, besitzer_der_app: Callable[[Konto], bool]) -> None:
        self.a = anwendung
        self.besitzer_der_app = besitzer_der_app

    async def einspielen(self, konto: Konto, sendung: Sendung) -> Eingespielt:
        """Commits eines Repos übernehmen (nur Neues oder Geändertes wird geschrieben) und an die Karten ihrer
        Schlüssel hängen. Nur der Besitzer der App."""
        if not self.besitzer_der_app(konto):
            raise Abgelehnt("Commits spielt nur der Besitzer der App ein", 403)
        r = sendung.repo
        verweis = r.verweis if r.verweis and "{hash}" in r.verweis else None
        zahlen = {"neu": 0, "verknuepft": 0}

        def arbeit(k: Kontext) -> str | None:
            karten: dict[str, Karte] | None = None
            for e in sendung.commits:
                c = Commit(id=commit_kennung(r.kennung, e.hash), repo=r.kennung, reponame=r.name, quelle=r.quelle,
                           hash=e.hash, autor=e.autor, zeit=e.zeit, nachricht=e.nachricht.strip(), dateien=e.dateien,
                           verweis=verweis.replace("{hash}", e.hash) if verweis else None)
                alt = k.s.lies("commits", c.id)
                daten = c.json_daten()
                if alt is None:
                    zahlen["neu"] += 1
                if alt is None or {**alt, "fassung": None} != {**daten, "fassung": None}:
                    k.s.schreib("commits", daten)
                    # bestehende Bezüge (auch von Hand) mit den neuen Angaben
                    for d in k.s.alle("commitbezuege", "commitkennung=?", (c.id,)):
                        b = CommitBezug.model_validate(d)
                        neu = bezug_auffrischen(b, c)
                        if neu != b:
                            k.s.schreib("commitbezuege", neu.json_daten())
                schluessel = schluessel_in(c.nachricht)
                if not schluessel:
                    continue
                if karten is None:
                    karten = kartenverzeichnis(k)
                for s in schluessel:
                    karte = karten.get(s)
                    if karte is None or k.s.lies("commitbezuege", bezug_kennung(c.id, karte.id)) is not None:
                        continue
                    k.s.schreib("commitbezuege", bezug_aus(c, karte, "kennung", k).json_daten())
                    zahlen["verknuepft"] += 1
            if not zahlen["neu"] and not zahlen["verknuepft"]:
                return None
            return f"Commits aus {r.name}: {zahlen['neu']} neu, {zahlen['verknuepft']} an Karten gehängt"

        await self.a.aendern(konto, arbeit, rueckgaengig=False, melden=False, ins_journal=False)
        return Eingespielt(**zahlen)

    async def verknuepfen(self, konto: Konto, karte_id: Kennung, commit_id: Kennung) -> Antwort:
        """Einen bekannten Commit von Hand an die Karte hängen (Recht Karten bearbeiten); war er gelöst, gilt er wieder."""

        def arbeit(k: Kontext) -> str:
            karte = karte_lesen(k, karte_id)
            k.board_mit_recht(karte.board, "karten.bearbeiten")
            d = k.s.lies("commits", commit_id)
            if d is None:
                raise Abgelehnt("Diesen Commit kennt die Pinnwand nicht", 404)
            c = Commit.model_validate(d)
            alt = k.s.lies("commitbezuege", bezug_kennung(c.id, karte.id))
            if alt is not None and not alt.get("geloest"):
                raise Abgelehnt(f"Commit {c.hash[:7]} hängt schon an {karte.schluessel}", 409)
            k.s.schreib("commitbezuege", bezug_aus(c, karte, "hand", k).json_daten())
            vermerken(k, karte, f"hat Commit {c.hash[:7]} aus {c.reponame} verknüpft")
            k.s.schreib("karten", karte.json_daten())
            return f"{karte.schluessel}: Commit {c.hash[:7]} verknüpft"

        return await self.a.aendern(konto, arbeit)

    async def loesen(self, konto: Konto, karte_id: Kennung, bezug_id: Kennung) -> Antwort:
        """Einen Commit von der Karte lösen (Recht Karten bearbeiten). Hing er über den Schlüssel in der Nachricht an
        ihr, bleibt der Bezug als gelöst stehen, damit der nächste Abgleich ihn nicht wieder anhängt."""

        def arbeit(k: Kontext) -> str:
            karte = karte_lesen(k, karte_id)
            k.board_mit_recht(karte.board, "karten.bearbeiten")
            d = k.s.lies("commitbezuege", bezug_id)
            if d is None or d.get("karte") != karte.id or d.get("geloest"):
                raise Abgelehnt("Dieser Commit hängt nicht (mehr) an der Karte", 404)
            b = CommitBezug.model_validate(d)
            if b.art == "kennung":
                k.s.schreib("commitbezuege", b.model_copy(update={"geloest": True, "von": k.konto.id, "am": k.jetzt}).json_daten())
            else:
                k.s.loesch("commitbezuege", b.id)
            vermerken(k, karte, f"hat Commit {b.hash[:7]} gelöst")
            k.s.schreib("karten", karte.json_daten())
            return f"{karte.schluessel}: Commit {b.hash[:7]} gelöst"

        return await self.a.aendern(konto, arbeit)

    async def suchen(self, konto: Konto, karte_id: Kennung, text: str) -> list[Commit]:
        """Bekannte Commits zum Verknüpfen: Anfang des Hashs oder Wörter der Nachricht (alle müssen vorkommen), neueste
        zuerst. Wer die Karte bearbeiten darf."""
        d = await self.a.v.lies("karten", karte_id)
        b = await self.a.v.lies("boards", d["board"]) if d else None
        if d is None or b is None or not hat_recht(Board.model_validate(b), "karten.bearbeiten", konto.id):
            raise Abgelehnt("Diese Karte gibt es nicht oder du darfst sie nicht bearbeiten", 404)
        woerter = text.lower().split()
        if not woerter:
            return []
        hash_anfang = woerter[0] if len(woerter) == 1 and re.fullmatch(r"[0-9a-f]{4,64}", woerter[0]) else None
        if hash_anfang:
            zeilen = await self.a.v.alle("commits", "id LIKE ?", (f"%@{hash_anfang}%",), f"zeit DESC LIMIT {TREFFER}")
        else:
            zeilen = await self.a.v.alle("commits", " AND ".join(["lower(daten) LIKE ?"] * len(woerter)),
                                         tuple(f"%{w}%" for w in woerter), f"zeit DESC LIMIT {TREFFER}")
        return [Commit.model_validate(z) for z in zeilen]
