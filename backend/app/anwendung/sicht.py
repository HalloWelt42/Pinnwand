"""Wer welche Zeile sieht: eine Regel für den Stand, die Ereignisse und die Antwort einer Änderung (BAU.md, Abschnitt 7).

- Boards und ihre Zeilen (Karten, Gruppen, Laufnummern, Papierkorb, Entferntes, Serien, Termine): die Mitglieder des
  Boards.
- Zeilen einer Person (Ordner, Hinweise, eigene Vorlagen, Einstellungen): nur sie.
- Zeiteinträge und Timer: die Person selbst und die Mitglieder des Boards mit dem Recht "Zeiten anderer sehen".
- Zeitkonten und Abwesenheiten: die Person selbst und, wer mit ihr in einem Board ist und dort das Recht
  "Abwesenheiten sehen" hat (das Recht gilt nur mit dem Modul Arbeitszeit).
- Konten: alle.

Die Rechte gelten nur, solange ihr Modul im Board an ist (`hat_recht`)."""

from __future__ import annotations

from collections.abc import Iterable

from ..modell import Board, Kennung
from ..regeln.board import hat_recht
from ..verzeichnis import Schreiber

#: Tabellen, deren Zeilen einem Board gehören, mit dem Feld des Boards
JE_BOARD = {"karten": "board", "gruppen": "board", "laufnummern": "board", "papierkorb": "board", "entfernt": "board",
            "serien": "board", "termine": "board"}
#: Tabellen, deren Zeilen einer Person gehören, mit dem Feld der Person
JE_KONTO = {"ordner": "konto", "hinweise": "konto", "vorlagen": "konto"}
#: Zeit auf Karten: gehört einer Person, liegt in einem Board
ZEIT = {"zeiteintraege", "timer"}
#: Arbeitszeit einer Person, ohne Board
ARBEITSZEIT = {"zeitkonten", "abwesenheiten"}


def mitglieder(b: Board | dict | None) -> set[Kennung]:
    if b is None:
        return set()
    if isinstance(b, Board):
        return {m.konto for m in b.mitglieder if m.konto}
    return {m["konto"] for m in b.get("mitglieder", []) if m.get("konto")}


def sieht_zeit(b: Board, betrachter: Kennung) -> bool:
    """Sieht jemand in diesem Board die Zeiten anderer?"""
    return hat_recht(b, "zeit.andere.sehen", betrachter)


def zeit_seher(b: Board) -> set[Kennung]:
    return {k for k in mitglieder(b) if sieht_zeit(b, k)}


def sieht_abwesenheit(b: Board, betrachter: Kennung) -> bool:
    return hat_recht(b, "abwesenheit.sehen", betrachter)


def abwesenheit_seher(boards: Iterable[Board], person: Kennung) -> set[Kennung]:
    """Wer die Arbeitszeit einer Person sieht: in jedem gemeinsamen Board, wer dort das Recht hat."""
    wer: set[Kennung] = set()
    for b in boards:
        leute = mitglieder(b)
        if person in leute:
            wer |= {k for k in leute if sieht_abwesenheit(b, k)}
    return wer


def sichtbare_personen(boards: Iterable[Board], betrachter: Kennung) -> set[Kennung]:
    """Wessen Arbeitszeit jemand sieht (die Umkehrung von `abwesenheit_seher`), sich selbst eingeschlossen."""
    wer = {betrachter}
    for b in boards:
        if betrachter in mitglieder(b) and sieht_abwesenheit(b, betrachter):
            wer |= mitglieder(b)
    return wer


class Sicht:
    """Die Regel innerhalb einer Transaktion. Wer den alten Stand einer Zeile sah, richtet sich nach den Boards vor der
    Änderung, wer den neuen sieht, nach den Boards danach (wer ein Board verlässt, sah dessen Karten noch)."""

    def __init__(self, s: Schreiber) -> None:
        self.s = s
        self._boards: dict[bool, list[Board]] = {}

    def _alle_boards(self, vorher: bool) -> list[Board]:
        if vorher not in self._boards:
            zeilen = self.s.alle_vorher("boards") if vorher else self.s.alle("boards")
            self._boards[vorher] = [Board.model_validate(d) for d in zeilen]
        return self._boards[vorher]

    def _board(self, board_id: Kennung, vorher: bool) -> dict | None:
        return self.s.lies_vorher("boards", board_id) if vorher else self.s.lies("boards", board_id)

    def wer(self, tabelle: str, d: dict, vorher: bool = False) -> set[Kennung] | None:
        """Wer diesen Stand einer Zeile sieht (`vorher`: ein Stand von vor der Änderung); None: alle."""
        if tabelle == "boards":
            return mitglieder(d)
        if tabelle in JE_BOARD:
            # liegt das Board selbst im Papierkorb, trägt sein Eintrag es mit seinen Mitgliedern
            return mitglieder(self._board(d[JE_BOARD[tabelle]], vorher) or (d.get("inhalt") or {}).get("board"))
        if tabelle in JE_KONTO:
            eigen = d.get(JE_KONTO[tabelle])
            return {eigen} if eigen else set()
        if tabelle == "person_einstellungen":
            return {d["id"]}
        if tabelle in ZEIT:
            b = self._board(d["board"], vorher)
            return {d["konto"]} | (zeit_seher(Board.model_validate(b)) if b else set())
        if tabelle in ARBEITSZEIT:
            return {d["konto"]} | abwesenheit_seher(self._alle_boards(vorher), d["konto"])
        return None
