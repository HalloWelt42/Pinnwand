"""Der Rahmen jeder Änderung: eine Transaktion, die Rechte und Regeln prüft, schreibt, Vorher und Nachher ins Journal legt
und danach die neuen Stände als Ereignis an alle sendet, die sie sehen dürfen. Rückgängig stellt die Vorher-Stände her,
wenn jede Zeile noch ihren Nachher-Stand hat. Es gibt keinen zweiten Weg zu schreiben."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable

from ..modell import Board, Kennung, Konto, Modell
from ..regeln.board import hat_recht
from ..uhr import Uhr
from ..verzeichnis import Bild, Schreiber, Verzeichnis
from .ereignisse import Ereignisse, Geaendert, Neuigkeit

#: Tabellen, deren Zeilen einem Board gehören (Ereignis an seine Mitglieder)
JE_BOARD = {"karten": "board", "gruppen": "board", "laufnummern": "board", "papierkorb": "board", "entfernt": "board"}
#: Tabellen, deren Zeilen einer Person gehören (Ereignis nur an sie)
JE_KONTO = {"ordner": "konto", "hinweise": "konto", "vorlagen": "konto"}
#: Zähler laufen nur vorwärts: Rückgängig lässt sie stehen (und prüft sie nicht)
NUR_VORWAERTS = {"laufnummern"}

NAMEN_DER_RECHTE = {
    "board.verwalten": "Board verwalten", "mitglieder.verwalten": "Mitglieder und Rollen verwalten",
    "karten.anlegen": "Karten anlegen", "karten.bearbeiten": "Karten bearbeiten", "karten.verschieben": "Karten verschieben",
    "karten.loeschen": "Karten löschen", "kommentieren": "Kommentieren", "papierkorb.leeren": "Papierkorb leeren",
}


class Abgelehnt(Exception):
    """Eine Änderung, die nicht geht, mit Grund für die Meldung. 403 ohne Recht, 404 unbekannt, 409 veraltet, 400 sonst."""

    def __init__(self, meldung: str, status: int = 400, stand: dict | None = None) -> None:
        super().__init__(meldung)
        self.meldung = meldung
        self.status = status
        self.stand = stand


class Antwort(Modell):
    """Ergebnis einer Änderung: die Meldung, die Kennung des Rückwegs (wenn es einen gibt) und die neuen Stände."""

    meldung: str | None = None
    rueckgaengig: Kennung | None = None
    geaendert: list[Geaendert] = []


def neue_kennung(vorsatz: str) -> Kennung:
    """Kennung ohne Zähler: Vorsatz und 16 zufällige Hexzeichen."""
    return f"{vorsatz}-{secrets.token_hex(8)}"


class Kontext:
    """Was ein Anwendungsfall in seiner Transaktion braucht: lesen und schreiben (Schreiber), wer handelt, wann, und die
    Rechte im Board."""

    def __init__(self, s: Schreiber, konto: Konto, uhr: Uhr) -> None:
        self.s = s
        self.konto = konto
        self.jetzt = uhr.jetzt()
        self.heute = self.jetzt[:10]

    def board(self, board_id: Kennung) -> Board:
        d = self.s.lies("boards", board_id)
        if d is None:
            raise Abgelehnt("Dieses Board gibt es nicht (mehr)", 404)
        return Board.model_validate(d)

    def board_mit_recht(self, board_id: Kennung, recht: str) -> Board:
        """Das Board, wenn die handelnde Person dort das Recht hat; sonst abgelehnt mit Grund."""
        b = self.board(board_id)
        if not hat_recht(b, recht, self.konto.id):
            raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE.get(recht, recht)}", 403)
        return b

    def naechste_nummer(self, board_id: Kennung) -> int:
        """Die nächste Kartennummer des Boards; der Zähler steht danach auf ihr."""
        d = self.s.lies("laufnummern", board_id) or {"id": board_id, "board": board_id, "zahl": 0}
        zahl = int(d["zahl"]) + 1
        self.s.schreib("laufnummern", {**d, "zahl": zahl})
        return zahl

    def pruefe_fassung(self, stand: dict, fassung: int | None, was: str) -> None:
        """Schreiben auf veralteter Fassung wird abgelehnt (mit dem aktuellen Stand), nie still überschrieben."""
        if fassung is not None and stand.get("fassung") != fassung:
            raise Abgelehnt(f"{was} wurde inzwischen geändert; deine Änderung ist nicht gespeichert", 409, stand)


class Anwendung:
    def __init__(self, verzeichnis: Verzeichnis, ereignisse: Ereignisse, uhr: Uhr | None = None) -> None:
        self.v = verzeichnis
        self.ereignisse = ereignisse
        self.uhr = uhr or Uhr()

    async def aendern(self, konto: Konto, arbeit: Callable[[Kontext], str | None], *, rueckgaengig: bool = True,
                      melden: bool = True) -> Antwort:
        """Führt `arbeit` in einer Transaktion aus. `arbeit` gibt den Text der Meldung zurück oder None, wenn nichts
        geschah; Ablehnungen kommen als `Abgelehnt`."""
        uhr = self.uhr

        def transaktion(s: Schreiber) -> tuple[str | None, Kennung | None, set[Kennung] | None]:
            k = Kontext(s, konto, uhr)
            text = arbeit(k)
            if text is None or not s.bilder:
                return text, None, set()
            empfaenger = self._empfaenger(s, s.bilder)
            journal = neue_kennung("j")
            s.v.execute("INSERT INTO journal (id, konto, zeit, text, bilder, rueckgaengig) VALUES (?, ?, ?, ?, ?, ?)",
                        (journal, konto.id, k.jetzt, text, json.dumps([b.__dict__ for b in s.bilder], ensure_ascii=False),
                         1 if rueckgaengig else 0))
            return text, journal, empfaenger

        (text, journal, empfaenger), bilder = await self.v.transaktion(transaktion)
        geaendert = [Geaendert(tabelle=b.tabelle, id=b.id, daten=b.nachher) for b in bilder]
        self.ereignisse.senden(Neuigkeit(von=konto.id, text=text if melden else None, geaendert=geaendert), empfaenger)
        return Antwort(meldung=text if melden else None, rueckgaengig=journal if (rueckgaengig and journal) else None,
                       geaendert=geaendert)

    async def rueckgaengig(self, konto: Konto, journal_id: Kennung) -> Antwort:
        """Stellt die Vorher-Stände einer Änderung her, wenn jede Zeile noch ihren Nachher-Stand hat."""

        def arbeit(k: Kontext) -> str:
            z = k.s.v.execute("SELECT konto, text, bilder, rueckgaengig, zurueckgenommen FROM journal WHERE id=?",
                              (journal_id,)).fetchone()
            if z is None or not z["rueckgaengig"]:
                raise Abgelehnt("Das lässt sich nicht rückgängig machen", 404)
            if z["konto"] != k.konto.id:
                raise Abgelehnt("Rückgängig geht nur für deine eigenen Änderungen", 403)
            if z["zurueckgenommen"]:
                raise Abgelehnt("Das ist schon rückgängig gemacht")
            bilder = [b for b in (Bild(**b) for b in json.loads(z["bilder"])) if b.tabelle not in NUR_VORWAERTS]
            for b in bilder:
                jetzt = k.s.lies(b.tabelle, b.id)
                if (jetzt or {}).get("fassung") != (b.nachher or {}).get("fassung"):
                    raise Abgelehnt("Inzwischen hat sich hier etwas geändert; Rückgängig würde es überschreiben", 409)
            for b in bilder:
                k.s.zurueckschreiben(b.tabelle, b.id, {**b.vorher, "fassung": None} if b.vorher else None)
            k.s.v.execute("UPDATE journal SET zurueckgenommen=? WHERE id=?", (k.jetzt, journal_id))
            return f"Rückgängig: {z['text']}"

        return await self.aendern(konto, arbeit, rueckgaengig=False)

    def _empfaenger(self, s: Schreiber, bilder: list[Bild]) -> set[Kennung] | None:
        """Wer die Änderung sehen darf: Mitglieder der berührten Boards, die berührten Personen; None: alle."""
        konten: set[Kennung] = set()
        for b in bilder:
            stande = [d for d in (b.vorher, b.nachher) if d]
            if b.tabelle == "boards":
                for d in stande:
                    konten |= {m["konto"] for m in d.get("mitglieder", []) if m.get("konto")}
            elif b.tabelle in JE_BOARD:
                for d in stande:
                    board = s.lies("boards", d[JE_BOARD[b.tabelle]])
                    if board:
                        konten |= {m["konto"] for m in board.get("mitglieder", []) if m.get("konto")}
            elif b.tabelle in JE_KONTO:
                konten |= {d[JE_KONTO[b.tabelle]] for d in stande if d.get(JE_KONTO[b.tabelle])}
            elif b.tabelle == "person_einstellungen":
                konten.add(b.id)
            else:
                return None                                  # Konten, Gruppen: alle Verbundenen
        return konten
