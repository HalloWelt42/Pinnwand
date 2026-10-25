"""Regeln eines Boards als reine Funktionen: Rechte aus der Rolle, Alterung, Zeitfenster der Erledigt-Spalten, Archiv,
Abschlussdatum. Gleich frontend/src/regeln/board.ts; der Server prüft mit genau diesen Regeln jeden Weg."""

from __future__ import annotations

from ..modell import Board, BoardEinstellungen, Karte, Kennung, Spalte
from .tage import montag_von, plus_tage, tage_zwischen

#: Rechte jedes Moduls; ein Recht eines abgeschalteten Moduls gilt nicht
RECHTE_DER_MODULE: dict[str, tuple[str, ...]] = {
    "kern": ("board.verwalten", "mitglieder.verwalten", "karten.anlegen", "karten.bearbeiten", "karten.verschieben",
             "karten.loeschen", "kommentieren", "papierkorb.leeren"),
    "zeiterfassung": ("zeit.buchen", "zeit.andere.sehen", "zeit.andere.bearbeiten"),
    "arbeitszeit": ("abwesenheit.sehen",),
    "serien": ("serien.verwalten",),
    "berichte": ("berichte.erstellen",),
}


def modul_von(recht: str) -> str:
    for modul, rechte in RECHTE_DER_MODULE.items():
        if recht in rechte:
            return modul
    return "kern"


def mitglied(b: Board, konto: Kennung):
    return next((m for m in b.mitglieder if m.konto == konto), None)


def hat_recht(b: Board, recht: str, konto: Kennung) -> bool:
    """Hat die Person in diesem Board das Recht über ihre Rolle? Rechte abgeschalteter Module gelten nicht."""
    m = mitglied(b, konto)
    if m is None:
        return False
    modul = modul_von(recht)
    if modul != "kern" and not b.module.get(modul, False):
        return False
    rolle = next((r for r in b.rollen if r.id == m.rolle), None)
    return rolle is not None and recht in rolle.rechte


def alterung(tage: int, e: BoardEinstellungen) -> str:
    """Stufe der Sanduhr nach Tagen im Status; 0 schaltet eine Stufe aus, die Stufen sind unabhängig."""
    if e.alterung_gefahr > 0 and tage >= e.alterung_gefahr:
        return "gefahr"
    if e.alterung_warnung > 0 and tage >= e.alterung_warnung:
        return "warnung"
    return "flaeche"


def fenster_ab(f: str, heute: str) -> str:
    """Erster Tag eines Zeitfensters (einschließlich); "alle": ohne Grenze."""
    return {
        "heute": heute, "gestern": plus_tage(heute, -1), "woche": montag_von(heute), "monat": heute[:8] + "01",
        "jahr": heute[:5] + "01-01", "alle": "",
    }[f]


def im_archiv(k: Karte, e: BoardEinstellungen, heute: str) -> bool:
    """Liegt eine erledigte Karte im Archiv (Abschluss älter als die Archivgrenze)?"""
    return bool(k.abgeschlossen) and tage_zwischen(k.abgeschlossen, heute) > e.archiv_tage


def abschluss(k: Karte, heute: str) -> str:
    """Abschlussdatum in einer Erledigt-Spalte: eine Serienkarte hat fest ihren Termintag, alle anderen den Tag des
    Ablegens (Mechanik M-23)."""
    return k.faellig if k.serie and k.faellig else heute


def spalte_von(b: Board, spalte: Kennung) -> Spalte | None:
    return next((s for s in b.spalten if s.id == spalte), None)


def erledigt_spalte(b: Board) -> Spalte | None:
    return next((s for s in b.spalten if s.erledigt), None)
