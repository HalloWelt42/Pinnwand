"""Reine Regeln: Kürzel, Rechte mit Modulen, Alterung, Archiv, Abschluss, Tage."""

from app.modell import Board, BoardEinstellungen, Karte, Mitglied
from app.regeln.board import abschluss, alterung, fenster_ab, hat_recht, im_archiv
from app.regeln.kuerzel import grundform, kuerzel_fehler, kuerzel_vorschlag, person_kuerzel
from app.regeln.tage import ist_tag
from app.vorlagen import start_rollen


def board(**module: bool) -> Board:
    return Board(id="b", name="Haushalt", kuerzel="HAUS", farbe="tuerkis", rollen=start_rollen(),
                 mitglieder=[Mitglied(konto="1", kellerwolke="anna", rolle="besitzer", seit="2026-10-27"),
                             Mitglied(konto="2", kellerwolke="bert", rolle="leser", seit="2026-10-27")],
                 module={"zeiterfassung": False, **module})


def test_kuerzel():
    frei = lambda k: None  # noqa: E731
    assert grundform("Haushalt") == "HAUS" and grundform("Büro Planung") == "BP" and grundform("2026 Umzug") == "B2026U"
    assert kuerzel_vorschlag("Haushalt", lambda k: "Haushalt" if k == "HAUS" else None) == "HAUS2"
    assert kuerzel_fehler("HAUS", frei) is None
    assert kuerzel_fehler("H", frei) == "2 bis 6 Zeichen, vorne ein Buchstabe."
    assert kuerzel_fehler("HAUS", lambda k: "") == "HAUS ist schon vergeben, an ein Board, das du nicht siehst."
    assert person_kuerzel("Anna Berger") == "AB" and person_kuerzel("Ömer") == "OE"


def test_rechte_folgen_rolle_und_modul():
    b = board()
    assert hat_recht(b, "karten.verschieben", "1") and not hat_recht(b, "karten.verschieben", "2")
    assert hat_recht(b, "kommentieren", "2") and not hat_recht(b, "kommentieren", "9")
    assert not hat_recht(b, "zeit.buchen", "1")                      # Modul aus: Recht gilt nicht
    assert hat_recht(board(zeiterfassung=True), "zeit.buchen", "1")


def test_alterung_archiv_abschluss():
    e = BoardEinstellungen(alterung_warnung=4, alterung_gefahr=8, archiv_tage=30)
    assert [alterung(t, e) for t in (3, 4, 8)] == ["flaeche", "warnung", "gefahr"]
    assert alterung(100, BoardEinstellungen(alterung_warnung=0, alterung_gefahr=0)) == "flaeche"
    k = Karte(id="c", board="b", schluessel="HAUS-1", spalte="s", titel="x", bewegt_am="", erstellt_am="",
              abgeschlossen="2026-09-01")
    assert im_archiv(k, e, "2026-10-27") and not im_archiv(k, e, "2026-09-30")
    assert abschluss(k, "2026-10-27") == "2026-10-27"
    serie = k.model_copy(update={"serie": "r1", "faellig": "2026-10-20"})
    assert abschluss(serie, "2026-10-27") == "2026-10-20"
    assert fenster_ab("woche", "2026-10-29") == "2026-10-26" and fenster_ab("monat", "2026-10-29") == "2026-10-01"


def test_tage():
    assert ist_tag("2026-10-27") and not ist_tag("2026-02-30") and not ist_tag("27.10.2026") and not ist_tag("")
