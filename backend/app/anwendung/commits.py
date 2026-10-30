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
#: ein Hash in einem Text: 7 bis 40 Zeichen 0-9a-f, mindestens ein Buchstabe (sonst wäre jedes Datum einer)
HASH = re.compile(r"(?<![0-9A-Za-z])(?=[0-9a-f]*[a-f])([0-9a-f]{7,40})(?![0-9A-Za-z])")
#: eine Zeile im Verlauf, mit der eine Karte die Spalte wechselt (kartenbasis.vermerken in karten.wechseln)
WECHSEL = re.compile(r"^hat sie von (.+) nach (.+) verschoben$")
#: so viele Vorschläge bekommt eine Karte höchstens (je Lauf)
VORSCHLAEGE_JE_KARTE = 20
GRUND_HASH = "Hash im Text der Karte"
#: Suchen und von Hand verknüpfen (Nutzer 30.10.: "Nur Besitzer"); andere sehen nur, was schon an der Karte hängt
NUR_BESITZER = "Commits suchen und von Hand verknüpfen darf nur der Besitzer der App"
GRUND_ARBEIT = "Repo im Titel, Commit während der Arbeit an der Karte"


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


class Vorgeschlagen(Modell):
    vorschlaege: int


def hashes_in(text: str) -> list[str]:
    return list(dict.fromkeys(HASH.findall(text or "")))


def arbeitszeiten(karte: Karte, board: Board, jetzt: str) -> list[tuple[str, str]]:
    """Wann an der Karte gearbeitet wurde: von jedem Wechsel in eine Spalte, die weder die erste noch die Erledigt-Spalte
    ist (etwa Dran), bis zum nächsten Wechsel oder Abschluss (Ende des Tages), sonst bis jetzt."""
    erste = board.spalten[0].name if board.spalten else ""
    erledigt = {s.name for s in board.spalten if s.erledigt}
    spannen: list[tuple[str, str]] = []
    beginn: str | None = None
    for e in sorted(karte.verlauf, key=lambda e: e.zeit):
        m = WECHSEL.match(e.text)
        if not m and e.text != "hat sie erledigt":
            continue
        if beginn:
            spannen.append((beginn, e.zeit))
            beginn = None
        if m and m.group(2) != erste and m.group(2) not in erledigt:
            beginn = e.zeit
    if beginn:
        spannen.append((beginn, f"{karte.abgeschlossen}T23:59:59" if karte.abgeschlossen else jetzt))
    return spannen


def repo_im_titel(titel: str) -> str | None:
    """Ein Repo, das der Titel vorn nennt ("Pinnwand: ..."), klein geschrieben."""
    vorn, trenner, _ = titel.partition(":")
    return vorn.strip().lower() if trenner and 0 < len(vorn.strip()) <= 60 else None


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

    async def vorschlaege(self, konto: Konto) -> Vorgeschlagen:
        """Unsichere Zuordnungen als Vorschlag zum Bestätigen (Nachtrag, "automatisch, dann prüfen"): ein bekannter
        Commit-Hash in Beschreibung oder Kommentaren einer Karte, und Commits ohne Kartenschlüssel aus dem Repo, das der
        Titel vorn nennt, aus der Zeit, in der an der Karte gearbeitet wurde. Was schon an der Karte hängt, gelöst oder
        verworfen ist, kommt nicht wieder. Nur der Besitzer der App (der Commitsammler ruft es nach jedem Lauf)."""
        if not self.besitzer_der_app(konto):
            raise Abgelehnt("Vorschläge rechnet nur der Besitzer der App", 403)
        zahl = {"neu": 0}

        def vorschlagen(k: Kontext, karte: Karte, c: Commit, grund: str, je_karte: dict[str, int]) -> None:
            if je_karte.get(karte.id, 0) >= VORSCHLAEGE_JE_KARTE:
                return
            if k.s.lies("commitbezuege", bezug_kennung(c.id, karte.id)) is not None:
                return
            b = bezug_aus(c, karte, "vorschlag", k)
            b.grund = grund
            k.s.schreib("commitbezuege", b.json_daten())
            je_karte[karte.id] = je_karte.get(karte.id, 0) + 1
            zahl["neu"] += 1

        def arbeit(k: Kontext) -> str | None:
            je_karte: dict[str, int] = {}
            boards = {d["id"]: Board.model_validate(d) for d in k.s.alle("boards")}
            for d in k.s.alle("karten"):
                karte = Karte.model_validate(d)
                board = boards.get(karte.board)
                if board is None:
                    continue
                texte = " ".join([karte.beschreibung or "", *(c.text for c in karte.kommentare)])
                for h in hashes_in(texte):
                    treffer = k.s.alle("commits", "id LIKE ?", (f"%@{h}%",), "zeit DESC LIMIT 3")
                    if len({z["hash"] for z in treffer}) == 1:           # nur eindeutige
                        for z in treffer:
                            vorschlagen(k, karte, Commit.model_validate(z), GRUND_HASH, je_karte)
                repo = repo_im_titel(karte.titel)
                if not repo:
                    continue
                for von, bis in arbeitszeiten(karte, board, k.jetzt):
                    for z in k.s.alle("commits", "zeit BETWEEN ? AND ? AND lower(json_extract(daten, '$.reponame')) = ?",
                                      (von, bis, repo), "zeit"):
                        c = Commit.model_validate(z)
                        if not schluessel_in(c.nachricht):
                            vorschlagen(k, karte, c, GRUND_ARBEIT, je_karte)
            return f"{zahl['neu']} Vorschläge für Commits an Karten" if zahl["neu"] else None

        await self.a.aendern(konto, arbeit, rueckgaengig=False, melden=False, ins_journal=False)
        return Vorgeschlagen(vorschlaege=zahl["neu"])

    async def bestaetigen(self, konto: Konto, karte_id: Kennung, bezug_id: Kennung) -> Antwort:
        """Einen Vorschlag übernehmen: der Commit hängt dann wie von Hand verknüpft an der Karte (Recht Karten
        bearbeiten, mit Rückgängig)."""

        def arbeit(k: Kontext) -> str:
            karte = karte_lesen(k, karte_id)
            k.board_mit_recht(karte.board, "karten.bearbeiten")
            d = k.s.lies("commitbezuege", bezug_id)
            if d is None or d.get("karte") != karte.id or d.get("geloest") or d.get("art") != "vorschlag":
                raise Abgelehnt("Diesen Vorschlag gibt es nicht (mehr)", 404)
            b = CommitBezug.model_validate(d)
            k.s.schreib("commitbezuege", b.model_copy(update={"art": "hand", "grund": None, "von": k.konto.id, "am": k.jetzt}).json_daten())
            vermerken(k, karte, f"hat Commit {b.hash[:7]} aus {b.reponame} übernommen")
            k.s.schreib("karten", karte.json_daten())
            return f"{karte.schluessel}: Commit {b.hash[:7]} übernommen"

        return await self.a.aendern(konto, arbeit)

    async def verknuepfen(self, konto: Konto, karte_id: Kennung, commit_id: Kennung) -> Antwort:
        """Einen bekannten Commit von Hand an die Karte hängen (nur der Besitzer der App, wie die Suche, und mit dem Recht
        Karten bearbeiten); war er gelöst, gilt er wieder."""
        if not self.besitzer_der_app(konto):
            raise Abgelehnt(NUR_BESITZER, 403)

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
        """Einen Commit von der Karte lösen oder einen Vorschlag verwerfen (Recht Karten bearbeiten). Hing er über den
        Schlüssel in der Nachricht an ihr oder war er ein Vorschlag, bleibt der Bezug als gelöst stehen, damit der nächste
        Abgleich ihn nicht wiederbringt."""

        def arbeit(k: Kontext) -> str:
            karte = karte_lesen(k, karte_id)
            k.board_mit_recht(karte.board, "karten.bearbeiten")
            d = k.s.lies("commitbezuege", bezug_id)
            if d is None or d.get("karte") != karte.id or d.get("geloest"):
                raise Abgelehnt("Dieser Commit hängt nicht (mehr) an der Karte", 404)
            b = CommitBezug.model_validate(d)
            if b.art in ("kennung", "vorschlag"):
                k.s.schreib("commitbezuege", b.model_copy(update={"geloest": True, "von": k.konto.id, "am": k.jetzt}).json_daten())
            else:
                k.s.loesch("commitbezuege", b.id)
            wort = "verworfen" if b.art == "vorschlag" else "gelöst"
            vermerken(k, karte, f"hat Commit {b.hash[:7]} {wort}")
            k.s.schreib("karten", karte.json_daten())
            return f"{karte.schluessel}: Commit {b.hash[:7]} {wort}"

        return await self.a.aendern(konto, arbeit)

    async def suchen(self, konto: Konto, karte_id: Kennung, text: str) -> list[Commit]:
        """Bekannte Commits zum Verknüpfen: Anfang des Hashs oder Wörter der Nachricht (alle müssen vorkommen), neueste
        zuerst. Nur der Besitzer der App (Nutzer 30.10.: "Nur Besitzer"; die Suche reicht über alle eingespielten Repos,
        auch private), und nur an einer Karte, die er bearbeiten darf."""
        if not self.besitzer_der_app(konto):
            raise Abgelehnt(NUR_BESITZER, 403)
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
