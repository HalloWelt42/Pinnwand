"""Was eine Person sieht, in einem Zug für den Start der Oberfläche: ihre Boards (Mitglied), deren Karten (offene Spalten
ganz, Erledigt-Spalten bis zur Archivgrenze), Gruppen, Konten, ihre Ordner, Hinweise, Vorlagen und Einstellungen, der
Papierkorb ihrer Boards. Archivierte Karten und einzelne Karten kommen über eigene Abfragen (seitenweise, einzeln)."""

from __future__ import annotations

from ..modell import MODULE_DA, Board, Karte, Kennung, Konto, Modell
from ..regeln.board import hat_recht, im_archiv
from .rahmen import Abgelehnt, Anwendung


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


class Abfragen:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def meine_boards(self, konto: Konto) -> list[Board]:
        return [b for b in (Board.model_validate(d) for d in await self.a.v.alle("boards"))
                if any(m.konto == konto.id for m in b.mitglieder)]

    async def stand(self, konto: Konto) -> Stand:
        heute = self.a.uhr.heute()
        boards = await self.meine_boards(konto)
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
        )

    async def karte(self, konto: Konto, schluessel: str) -> dict:
        """Eine Karte einzeln über ihren Schlüssel, auch eine archivierte (ein direkter Pfad öffnet jede Karte, M-09)."""
        zeilen = await self.a.v.alle("karten", "schluessel=?", (schluessel.upper(),))
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
