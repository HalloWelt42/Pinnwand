"""Was eine Person sieht, in einem Zug für den Start der Oberfläche: ihre Boards (Mitglied), deren Karten (offene Spalten
ganz, Erledigt-Spalten bis zur Archivgrenze), Gruppen, Konten, ihre Ordner, Hinweise, Vorlagen und Einstellungen, der
Papierkorb ihrer Boards; dazu Timer, Zeiteinträge, Zeitkonten und Abwesenheiten nach der Regel in sicht.py. Archivierte
Karten und einzelne Karten kommen über eigene Abfragen (seitenweise, einzeln), die Tagessummen des Teams ebenso."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from ..modell import MODULE_DA, Board, Karte, Kartenname, Kennung, Konto, Modell, Terminname
from ..regeln.board import hat_recht, im_archiv
from ..regeln.tage import ist_tag, tage_zwischen
from .hinweise import ARTEN_DA, WEGE_DA, vorgabe
from .rahmen import Abgelehnt, Anwendung
from .sicht import mitglieder, sichtbare_personen, sieht_abwesenheit, sieht_zeit

#: längster Zeitraum einer Abfrage des Teams (Tage)
TEAM_TAGE = 62


class Stand(Modell):
    jetzt: str
    ich: Kennung
    #: Module, die sich einschalten lassen (die übrigen bietet diese Fassung nicht an)
    module_da: list[str]
    konten: list[dict]
    boards: list[dict]
    karten: list[dict]
    gruppen: list[dict]
    laufnummern: list[dict]
    ordner: list[dict]
    hinweise: list[dict]
    vorlagen: list[dict]
    papierkorb: list[dict]
    entfernt: list[dict]
    einstellungen: dict
    timer: list[dict]
    zeiteintraege: list[dict]
    zeitkonten: list[dict]
    abwesenheiten: list[dict]
    kartennamen: list[Kartenname]
    serien: list[dict]
    termine: list[dict]
    terminnamen: list[Terminname]
    berichte: list[dict]
    #: Commits an den Karten deiner Boards (HELF-35)
    commitbezuege: list[dict] = []
    hinweiswege: Hinweiswege
    #: ob die Vorschläge der KI gehen (Leitstelle eingerichtet); sonst zeigt die Oberfläche keine
    ki_bereit: bool
    #: du bist Besitzer der App (dir gehört ihr App-Schlüssel): du kannst alle Konten zurücksetzen und löschen
    app_besitzer: bool = False
    #: wo die Transkription liegt (leer: nicht eingerichtet, die Oberfläche zeigt keine Transkripte)
    transkription_adresse: str
    #: wo die App Vorlesen liegt (leer: nicht eingerichtet, die Oberfläche zeigt kein Vorlesen)
    vorlesen_adresse: str


class Hinweiswege(Modell):
    """Welche Wege diese Fassung für Hinweise anbietet und was je Art gilt, solange die Person nichts schaltet."""

    da: list[str]
    vorgabe: dict[str, dict[str, bool]]


class Team(Modell):
    """Tagessummen gebuchter Zeit aus allen Boards je Person, die du in einem Board siehst."""

    personen: list[Kennung]
    ist: dict[Kennung, dict[str, int]]


class Abfragen:
    def __init__(self, anwendung: Anwendung, ki_bereit: Callable[[], bool] = lambda: False,
                 transkription_adresse: Callable[[], str] = lambda: "", vorlesen_adresse: Callable[[], str] = lambda: "",
                 besitzer: Callable[[], str | None] = lambda: None) -> None:
        self.a = anwendung
        self.besitzer = besitzer
        self.ki_bereit = ki_bereit
        self.transkription_adresse = transkription_adresse
        self.vorlesen_adresse = vorlesen_adresse

    async def alle_boards(self) -> list[Board]:
        return [Board.model_validate(d) for d in await self.a.v.alle("boards")]

    async def stand(self, konto: Konto) -> Stand:
        heute = self.a.uhr.heute()
        alle_boards = await self.alle_boards()
        boards = [b for b in alle_boards if konto.id in mitglieder(b)]
        ids = [b.id for b in boards]
        frage = ",".join("?" * len(ids))
        karten: list[dict] = []
        gruppen: list[dict] = []
        laufnummern: list[dict] = []
        papierkorb: list[dict] = []
        entfernt: list[dict] = []
        if ids:
            einstellungen = {b.id: b.einstellungen for b in boards}
            karten = [d for d in await self.a.v.alle("karten", f"board IN ({frage})", tuple(ids), "spalte, reihe")
                      if not (d.get("abgeschlossen") and im_archiv(_karte(d), einstellungen[d["board"]], heute))]
            gruppen = await self.a.v.alle("gruppen", f"board IN ({frage})", tuple(ids))
            laufnummern = await self.a.v.alle("laufnummern", f"board IN ({frage})", tuple(ids))
            papierkorb = await self.a.v.alle("papierkorb", f"board IN ({frage})", tuple(ids), "am DESC")
            entfernt = await self.a.v.alle("entfernt", f"board IN ({frage})", tuple(ids))
        # gelöschte Boards, die ich wiederherstellen könnte, liegen im Papierkorb der App
        papierkorb += [d for d in await self.a.v.alle("papierkorb", "board NOT IN (" + frage + ")" if ids else "", tuple(ids), "am DESC")
                       if d.get("art") == "board" and _darf_board_zurueck(d, konto.id)]
        vorlagen = [d for d in await self.a.v.alle("vorlagen") if not d.get("konto") or d.get("konto") == konto.id]
        timer, zeiteintraege = await self._zeit(konto, boards)
        serien = await self.a.v.alle("serien", f"board IN ({frage})", tuple(ids)) if ids else []
        termine = await self.a.v.alle("termine", f"board IN ({frage})", tuple(ids), "datum") if ids else []
        personen = sichtbare_personen(alle_boards, konto.id)
        return Stand(
            jetzt=self.a.uhr.jetzt(), ich=konto.id, module_da=list(MODULE_DA),
            konten=await self.a.v.alle("konten"),
            boards=[b.json_daten() for b in boards],
            karten=karten,
            gruppen=gruppen,
            laufnummern=laufnummern,
            ordner=await self.a.v.alle("ordner", "konto=?", (konto.id,), "reihe"),
            hinweise=await self.a.v.alle("hinweise", "konto=?", (konto.id,), "zeit DESC"),
            vorlagen=vorlagen,
            papierkorb=papierkorb,
            entfernt=entfernt,
            einstellungen=(await self.a.v.lies("person_einstellungen", konto.id)) or {"id": konto.id, "hinweise": {}},
            timer=timer,
            zeiteintraege=zeiteintraege,
            zeitkonten=await self._von_personen("zeitkonten", personen),
            abwesenheiten=await self._von_personen("abwesenheiten", personen),
            kartennamen=await self._kartennamen({d["karte"] for d in [*zeiteintraege, *timer] if d.get("karte")}
                                                - {d["id"] for d in karten}),
            serien=serien,
            termine=termine,
            berichte=await self.a.v.alle("berichte", "konto=?", (konto.id,), "erstellt DESC"),
            commitbezuege=await self.a.v.alle("commitbezuege", f"board IN ({frage})", tuple(ids)) if ids else [],
            hinweiswege=Hinweiswege(da=list(WEGE_DA), vorgabe={a: {w: vorgabe(a, w) for w in WEGE_DA} for a in ARTEN_DA}),
            ki_bereit=self.ki_bereit(),
            app_besitzer=bool(self.besitzer()) and konto.kellerwolke_konto == self.besitzer(),
            transkription_adresse=self.transkription_adresse(),
            vorlesen_adresse=self.vorlesen_adresse(),
            terminnamen=await self._terminnamen({d["termin"] for d in zeiteintraege if d.get("termin")}
                                                - {d["id"] for d in termine}),
        )

    async def _zeit(self, konto: Konto, boards: list[Board]) -> tuple[list[dict], list[dict]]:
        """Timer und Zeiteinträge: eigene überall, fremde in Boards mit dem Recht "Zeiten anderer sehen"."""
        sehen = [b.id for b in boards if sieht_zeit(b, konto.id)]
        frage = ",".join("?" * len(sehen))
        fremd = f" OR board IN ({frage})" if sehen else ""
        timer = await self.a.v.alle("timer", f"konto=?{fremd}", (konto.id, *sehen))
        zeiteintraege = await self.a.v.alle("zeiteintraege", f"konto=?{fremd}", (konto.id, *sehen), "datum, id")
        return timer, zeiteintraege

    async def _von_personen(self, tabelle: str, personen: set[Kennung]) -> list[dict]:
        liste = sorted(personen)
        return await self.a.v.alle(tabelle, f"konto IN ({','.join('?' * len(liste))})", tuple(liste))

    async def _kartennamen(self, fehlend: set[Kennung]) -> list[Kartenname]:
        """Namen der Karten, auf die Einträge zeigen, die nicht im Stand sind: archiviert, in einem Board, das man
        verlassen hat, im Papierkorb oder entfernt."""
        if not fehlend:
            return []
        liste = sorted(fehlend)
        frage = ",".join("?" * len(liste))
        gefunden = {d["id"]: (d, "da") for d in await self.a.v.alle("karten", f"id IN ({frage})", tuple(liste))}
        gefunden |= {d["id"]: (d, "entfernt") for d in await self.a.v.alle("entfernt", f"id IN ({frage})", tuple(liste))}
        for eintrag in await self.a.v.alle("papierkorb"):
            gefunden |= {c["id"]: (c, "papierkorb") for c in eintrag.get("karten", []) if c["id"] in fehlend}
        return [Kartenname(karte=i, board=d["board"], schluessel=d["schluessel"], titel=d["titel"], zustand=z)
                for i, (d, z) in gefunden.items()]

    async def _terminnamen(self, fehlend: set[Kennung]) -> list[Terminname]:
        """Namen der Termine, auf die eigene Einträge zeigen, die nicht im Stand sind (Board verlassen)."""
        if not fehlend:
            return []
        liste = sorted(fehlend)
        zeilen = await self.a.v.alle("termine", f"id IN ({','.join('?' * len(liste))})", tuple(liste))
        return [Terminname(termin=d["id"], board=d["board"], titel=d["titel"], datum=d["datum"]) for d in zeilen]

    async def team(self, konto: Konto, board_id: Kennung, von: str, bis: str) -> Team:
        """Gebuchte Stunden je Tag aus allen Boards: mit dem Recht "Abwesenheiten sehen" für alle Mitglieder des Boards,
        sonst nur für dich; keine Einträge, nur Summen."""
        d = await self.a.v.lies("boards", board_id)
        if d is None or konto.id not in mitglieder(d):
            raise Abgelehnt("Dieses Board siehst du nicht", 403)
        if not (ist_tag(von) and ist_tag(bis)) or not 0 <= tage_zwischen(von, bis) < TEAM_TAGE:
            raise Abgelehnt(f"Ein Zeitraum von höchstens {TEAM_TAGE} Tagen, von vor bis")
        b = Board.model_validate(d)
        personen = [m.konto for m in b.mitglieder if m.konto] if sieht_abwesenheit(b, konto.id) else [konto.id]
        ist: dict[Kennung, dict[str, int]] = {p: defaultdict(int) for p in personen}
        frage = ",".join("?" * len(personen))
        for e in await self.a.v.alle("zeiteintraege", f"konto IN ({frage}) AND datum>=? AND datum<=?", (*personen, von, bis)):
            ist[e["konto"]][e["datum"]] += e["sekunden"]
        return Team(personen=personen, ist={p: dict(t) for p, t in ist.items()})

    async def karte(self, konto: Konto, schluessel: str) -> dict:
        """Eine Karte einzeln über ihren Schlüssel, auch eine archivierte oder umgezogene (ein direkter Pfad öffnet jede
        Karte, M-09)."""
        gesucht = schluessel.upper()
        zeilen = await self.a.v.alle("karten", "schluessel=?", (gesucht,))
        if not zeilen:
            # in ein anderes Board gezogen: der alte Schlüssel führt weiter zu ihr
            zeilen = [d for d in await self.a.v.alle("karten", "daten LIKE ?", (f'%"{gesucht}"%',))
                      if gesucht in d.get("frueher", [])]
        if not zeilen:
            raise Abgelehnt(f"Die Karte {schluessel} gibt es nicht", 404)
        d = zeilen[0]
        b = await self.a.v.lies("boards", d["board"])
        if b is None or not any(m.get("konto") == konto.id for m in b.get("mitglieder", [])):
            raise Abgelehnt(f"Die Karte {schluessel} liegt in einem Board, in dem du nicht Mitglied bist", 403)
        return d

    async def archiv(self, konto: Konto, board_id: Kennung, versatz: int = 0, grenze: int = 50) -> dict:
        """Archivierte Karten eines Boards, neueste zuerst, seitenweise, mit der Gesamtzahl."""
        b = await self.a.v.lies("boards", board_id)
        if b is None or not any(m.get("konto") == konto.id for m in b.get("mitglieder", [])):
            raise Abgelehnt("Dieses Board siehst du nicht", 403)
        board = Board.model_validate(b)
        heute = self.a.uhr.heute()
        alle = [d for d in await self.a.v.alle("karten", "board=?", (board_id,)) if d.get("abgeschlossen")
                and im_archiv(_karte(d), board.einstellungen, heute)]
        alle.sort(key=lambda d: d["abgeschlossen"], reverse=True)
        return {"gesamt": len(alle), "karten": alle[versatz:versatz + grenze]}


def _karte(d: dict) -> Karte:
    return Karte.model_validate(d)


def _darf_board_zurueck(eintrag: dict, konto: Kennung) -> bool:
    inhalt = eintrag.get("inhalt") or {}
    board = inhalt.get("board")
    return bool(board) and hat_recht(Board.model_validate(board), "board.verwalten", konto)
