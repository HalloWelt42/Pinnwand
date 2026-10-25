"""Regeln eines Boards als reine Funktionen: Rechte aus der Rolle, Alterung, Zeitfenster der Erledigt-Spalten, Archiv,
Abschlussdatum. Gleich frontend/src/regeln/board.ts; der Server prüft mit genau diesen Regeln jeden Weg."""

from __future__ import annotations

from ..modell import MODULE_DA, Board, BoardEinstellungen, Karte, Kennung, Spalte
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


def modul_an(b: Board, modul: str) -> bool:
    """Ist ein Modul in diesem Board an? Nur Module, die diese Fassung anbietet, können an sein."""
    return modul in MODULE_DA and b.module.get(modul, False)


def hat_recht(b: Board, recht: str, konto: Kennung) -> bool:
    """Hat die Person in diesem Board das Recht über ihre Rolle? Rechte abgeschalteter Module gelten nicht."""
    m = mitglied(b, konto)
    if m is None:
        return False
    modul = modul_von(recht)
    if modul != "kern" and not modul_an(b, modul):
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


def uebertragen(quelle: Board, ziel: Board, c: Karte) -> int:
    """Eine Karte für ein anderes Board angleichen: Labels und eigene Felder gelten weiter, wenn das Ziel welche mit
    gleichem Namen (und bei Feldern gleicher Art, bei Auswahl mit der Option) hat; Zuständige bleiben, wenn sie dort
    Mitglied sind. Ergebnis: wie viele Labels und Felder ohne Gegenstück entfallen."""
    labels = {l.name.casefold(): l.id for l in ziel.labels}
    namen = {l.id: l.name.casefold() for l in quelle.labels}
    neu_labels = [labels[namen[x]] for x in c.labels if x in namen and namen[x] in labels]
    felder = {f.name.casefold(): f for f in ziel.felder}
    alt_felder = {f.id: f for f in quelle.felder}
    neu_felder: dict[Kennung, str] = {}
    for fid, wert in c.felder.items():
        alt = alt_felder.get(fid)
        f = felder.get(alt.name.casefold()) if alt else None
        if f and f.art == alt.art and (f.art != "auswahl" or wert in (f.optionen or [])):
            neu_felder[f.id] = wert
    entfallen = len(c.labels) - len(neu_labels) + len(c.felder) - len(neu_felder)
    mitglieder = {m.konto for m in ziel.mitglieder if m.konto}
    c.labels = list(dict.fromkeys(neu_labels))
    c.felder = neu_felder
    c.zustaendig = [x for x in c.zustaendig if x in mitglieder]
    return entfallen


#: Erlaubte Werte der Einstellungen eines Boards und der Grenze einer Spalte (ganze Zahlen, einschließlich), gleich
#: EINSTELLUNG_GRENZEN in frontend/src/regeln/board.ts
EINSTELLUNG_GRENZEN: dict[str, tuple[int, int]] = {
    "alterung": (0, 365),
    "ladeschritt": (1, 500),
    "archiv_tage": (1, 100_000),
    "grenze": (1, 999),
}
#: Welche Grenze für welche Einstellung gilt, und wie sie in der Oberfläche heißt
EINSTELLUNGEN: dict[str, tuple[str, str]] = {
    "alterung_warnung": ("alterung", "Warnung ab"),
    "alterung_gefahr": ("alterung", "Gefahr ab"),
    "ladeschritt": ("ladeschritt", "Karten je Ladeschritt"),
    "archiv_tage": ("archiv_tage", "Archiv ab"),
}


def zahl_fehler(art: str, wert: int) -> str | None:
    """Grund, warum eine Zahl nicht in ihre Grenzen passt (wie das Zahlfeld der Oberfläche), sonst None."""
    unten, oben = EINSTELLUNG_GRENZEN[art]
    if unten <= wert <= oben:
        return None
    return f"ganze Zahl von {unten} bis {oben:,}".replace(",", ".")


def einstellung_fehler(feld: str, wert: int) -> str | None:
    """Grund, warum eine Einstellung des Boards so nicht geht, sonst None."""
    art, name = EINSTELLUNGEN[feld]
    fehler = zahl_fehler(art, wert)
    return f"{name}: {fehler}" if fehler else None
