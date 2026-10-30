"""Anwendungsfälle an Karten. Verschieben ist ein Weg für Ziehen, Status im Detail, Telefon, Liste und Sammelaktion:
beim Spaltenwechsel beginnt das Alter neu, verknüpfte Karten desselben Boards ziehen mit, in einer
Erledigt-Spalte gibt es das Abschlussdatum (Serienkarten ihren Termintag); über der Grenze nur eine Warnung. Jede
Bewegung steht im Verlauf der Karte, die Zuständigen bekommen einen Hinweis. Neue Karten bekommen die nächste Nummer
ihres Boards (Schlüssel HAUS-12)."""

from __future__ import annotations

from pydantic import Field

from ..modell import Board, Ereignis, Gruppe, Karte, Kartenart, Kennung, Konto, Modell, Punkt, Spalte
from ..regeln.board import abschluss, spalte_von, uebertragen
from ..regeln.tage import ist_tag
from . import hinweise, zeiterfassung
from .kartenbasis import (
    KURZ_LAENGE, PUNKTE_HOECHSTENS, TEXT_LAENGE, TITEL_LAENGE, gruppen_aufraeumen, karte_lesen, karten_der_spalte, serientag_auslassen, speichern, vermerken,
)
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: so viele Karten legt `mehrere_anlegen` höchstens auf einmal an
MEHRERE_HOECHSTENS = 50
#: Abstand der Reihe zwischen zwei Karten; wird er zu eng, nummeriert die Spalte neu
ABSTAND = 1024.0
ENG = 1e-6


def gruppe_lesen(k: Kontext, gruppe_id: Kennung) -> Gruppe:
    d = k.s.lies("gruppen", gruppe_id)
    if d is None:
        raise Abgelehnt("Diese Verknüpfung gibt es nicht (mehr)", 404)
    return Gruppe.model_validate(d)


def verknuepfbar(a: Karte, b: Karte) -> bool:
    """Eine andere Arbeitskarte desselben Boards, noch nicht in derselben Gruppe (M-74)."""
    return a.id != b.id and a.board == b.board and a.art == "arbeit" and b.art == "arbeit" and not (a.gruppe and a.gruppe == b.gruppe)


def ueber_grenze(k: Kontext, ziel: Spalte) -> str:
    offen = len(karten_der_spalte(k, ziel.id))
    if not ziel.erledigt and ziel.grenze is not None and offen > ziel.grenze:
        return f"{ziel.name} über der Grenze ({offen}/{ziel.grenze})"
    return ""


def einreihen(k: Kontext, ziel: Spalte, karten: list[Karte], platz: int | None) -> None:
    """Gibt den Karten Plätze in der Zielspalte: ab `platz` (ohne: oben, das Neueste steht oben, HELF-50) in dieser
    Reihenfolge; die übrigen Karten der Spalte behalten ihre Reihe. Wird der Raum zu eng, nummeriert die Spalte neu."""
    bewegt = {c.id for c in karten}
    andere = [c for c in karten_der_spalte(k, ziel.id) if c.id not in bewegt]
    p = 0 if platz is None else max(0, min(platz, len(andere)))
    vorher = andere[p - 1].reihe if p > 0 else None
    nachher = andere[p].reihe if p < len(andere) else None
    unten = vorher if vorher is not None else (nachher - ABSTAND * (len(karten) + 1) if nachher is not None else 0.0)
    oben = nachher if nachher is not None else unten + ABSTAND * (len(karten) + 1)
    schritt = (oben - unten) / (len(karten) + 1)
    if schritt < ENG:                                          # zu eng: die ganze Spalte neu nummerieren
        reihe = andere[:p] + karten + andere[p:]
        for i, c in enumerate(reihe):
            c.reihe = (i + 1) * ABSTAND
        for c in andere:
            speichern(k, c)
        return
    for i, c in enumerate(karten):
        c.reihe = unten + schritt * (i + 1)


def wechseln(k: Kontext, karte: Karte, ziel: Spalte, b: Board, mitgezogen: bool) -> int:
    """Eine Karte kommt in eine andere Spalte: Alter, Abschluss, Verlauf; in einer Erledigt-Spalte enden ihre Timer und
    buchen. Ergebnis: die dabei gebuchte eigene Zeit."""
    alt = spalte_von(b, karte.spalte)
    karte.spalte = ziel.id
    karte.bewegt_am = k.jetzt
    karte.abgeschlossen = abschluss(karte, k.heute) if ziel.erledigt else None
    vermerken(k, karte, f"mit verknüpfter Karte verschoben nach {ziel.name}" if mitgezogen
              else "hat sie erledigt" if ziel.erledigt else f"hat sie von {alt.name if alt else '?'} nach {ziel.name} verschoben")
    return zeiterfassung.timer_beenden(k, [karte]) if ziel.erledigt else 0


def hinein(k: Kontext, b: Board, ids: list[Kennung], ziel: Spalte, platz: int | None) -> str:
    """Karten in eine Spalte bringen: an den Platz (ohne: oben), verknüpfte desselben Boards ziehen mit direkt darunter
    (M-76); Mitglieder auf anderen Boards bleiben stehen. Ergebnis: der Text der Meldung."""
    karten = [karte_lesen(k, i) for i in ids]
    for c in karten:
        if c.board != b.id:
            raise Abgelehnt("Eine Karte kann nur in eine Spalte ihres eigenen Boards", 400)
    gruppen = {c.gruppe for c in karten if c.gruppe}
    mit = [Karte.model_validate(d) for g in gruppen for d in k.s.alle("karten", "board=?", (b.id,))
           if d.get("gruppe") == g and d["id"] not in ids and d["spalte"] != ziel.id]
    mit = list({c.id: c for c in mit}.values())
    wechselnde = {c.id for c in karten if c.spalte != ziel.id}
    einreihen(k, ziel, karten + mit, platz)
    gebucht = 0
    for c in karten:
        if c.id in wechselnde:
            gebucht += wechseln(k, c, ziel, b, False)
            hinweise.verschoben(k, b, c, ziel)
        speichern(k, c)
    for c in mit:
        gebucht += wechseln(k, c, ziel, b, True)
        hinweise.verschoben(k, b, c, ziel, mit=next(x for x in karten if x.gruppe == c.gruppe))
        speichern(k, c)
    erste = karten[0]
    if not wechselnde:
        teile = [f"{ziel.name} neu geordnet"]
    elif len(karten) == 1:
        teile = [f"{erste.schluessel} erledigt" if ziel.erledigt else f"{erste.schluessel} nach {ziel.name}"]
    else:
        teile = [f"{len(karten)} Karten nach {ziel.name}"]
    if mit:
        teile.append(f"{len(mit)} verknüpfte {'zieht' if len(mit) == 1 else 'ziehen'} mit")
    grenze = ueber_grenze(k, ziel)
    if grenze:
        teile.append(grenze)
    return "; ".join(teile) + zeiterfassung.gestoppt(gebucht)


class Kartenentwurf(Modell):
    """Inhalt einer neuen Karte: Titel, Beschreibung (Markdown) und offene Punkte der Checkliste."""

    titel: str
    beschreibung: str | None = None
    checkliste: list[str] = Field(default_factory=list)


def entwurf_pruefen(e: Kartenentwurf) -> None:
    """Titel, Texte und Punkte gegen die Grenzen; säubert Leerraum am Rand."""
    e.titel = e.titel.strip()
    if not e.titel:
        raise Abgelehnt("Eine Karte braucht einen Titel")
    if len(e.titel) > TITEL_LAENGE:
        raise Abgelehnt(f"Der Titel ist länger als {TITEL_LAENGE} Zeichen")
    e.beschreibung = (e.beschreibung or "").strip() or None
    if e.beschreibung and len(e.beschreibung) > TEXT_LAENGE:
        raise Abgelehnt(f"Der Text ist länger als {TEXT_LAENGE} Zeichen")
    e.checkliste = [t.strip() for t in e.checkliste]
    if len(e.checkliste) > PUNKTE_HOECHSTENS:
        raise Abgelehnt(f"Eine Checkliste hat höchstens {PUNKTE_HOECHSTENS} Punkte")
    if any(not t or len(t) > KURZ_LAENGE for t in e.checkliste):
        raise Abgelehnt(f"Ein Punkt der Checkliste braucht Text (höchstens {KURZ_LAENGE} Zeichen)")


def zielspalte(b: Board, spalte: Kennung | None) -> Spalte:
    """Die genannte Spalte des Boards, ohne Angabe die erste offene."""
    ziel = spalte_von(b, spalte) if spalte else next((s for s in b.spalten if not s.erledigt), None)
    if ziel is None:
        raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
    return ziel


def neue_karte(k: Kontext, b: Board, ziel: Spalte, e: Kartenentwurf, art: Kartenart, faellig: str | None = None) -> Karte:
    """Eine neue Karte für die Zielspalte mit der nächsten Nummer des Boards; zuständig ist, wer sie anlegt. Der Entwurf
    ist geprüft; eingereiht und gespeichert wird mit `in_spalte_legen`."""
    schluessel, nummer = k.neue_nummern(b.id)
    c = Karte(id=neue_kennung("c"), board=b.id, schluessel=schluessel, nummer=nummer, spalte=ziel.id, titel=e.titel, art=art,
              beschreibung=e.beschreibung, checkliste=[Punkt(text=t) for t in e.checkliste], zustaendig=[k.konto.id],
              faellig=faellig or None, bewegt_am=k.jetzt, erstellt_am=k.jetzt,
              verlauf=[Ereignis(zeit=k.jetzt, von=k.konto.id, text="hat die Karte angelegt")])
    if ziel.erledigt:
        c.abgeschlossen = abschluss(c, k.heute)
    return c


def in_spalte_legen(k: Kontext, b: Board, ziel: Spalte, karten: list[Karte]) -> None:
    """Neue Karten in dieser Reihenfolge oben in die Spalte, gespeichert; wer in einer Beschreibung erwähnt ist, bekommt
    einen Hinweis."""
    einreihen(k, ziel, karten, None)
    for c in karten:
        speichern(k, c)
        hinweise.erwaehnt(k, b, c, sorted(hinweise.erwaehnte(k, b, c.beschreibung)))


def anzahl(n: int) -> str:
    return f"{n} {'Karte' if n == 1 else 'Karten'}"


class Karten:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def anlegen(self, konto: Konto, board_id: Kennung, titel: str, spalte: Kennung | None = None,
                      art: Kartenart | None = None, faellig: str | None = None,
                      beschreibung: str | None = None) -> Antwort:
        """Neue Karte oben in der Spalte (ohne: die erste offene), zuständig ist, wer sie anlegt. Ohne Art: die Kartenart
        des Boards."""
        titel = titel.strip()

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "karten.anlegen")
            entwurf_pruefen(Kartenentwurf(titel=titel, beschreibung=beschreibung))
            if faellig and not ist_tag(faellig):
                raise Abgelehnt(f"{faellig} ist kein Tag (JJJJ-MM-TT)")
            ziel = zielspalte(b, spalte)
            c = neue_karte(k, b, ziel, Kartenentwurf(titel=titel, beschreibung=beschreibung), art or b.kartenart, faellig)
            in_spalte_legen(k, b, ziel, [c])
            grenze = ueber_grenze(k, ziel)
            return f"{c.schluessel} in {ziel.name} angelegt" + (f"; {grenze}" if grenze else "")

        return await self.a.aendern(konto, arbeit)

    async def mehrere_anlegen(self, konto: Konto, board_id: Kennung, entwuerfe: list[Kartenentwurf],
                              spalte: Kennung | None = None, art: Kartenart | None = None) -> Antwort:
        """Mehrere Karten mit Inhalt in einer Änderung oben in der Spalte (ein Rückgängig für alle), etwa aus einem
        Vorschlag der KI; sonst wie `anlegen`."""

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "karten.anlegen")
            if not entwuerfe:
                raise Abgelehnt("Keine Karte zum Anlegen")
            if len(entwuerfe) > MEHRERE_HOECHSTENS:
                raise Abgelehnt(f"Höchstens {MEHRERE_HOECHSTENS} Karten auf einmal")
            for e in entwuerfe:
                entwurf_pruefen(e)
            ziel = zielspalte(b, spalte)
            karten = [neue_karte(k, b, ziel, e, art or b.kartenart) for e in entwuerfe]
            in_spalte_legen(k, b, ziel, karten)
            grenze = ueber_grenze(k, ziel)
            spanne = karten[0].schluessel if len(karten) == 1 else f"{karten[0].schluessel} bis {karten[-1].schluessel}"
            return f"{anzahl(len(karten))} in {ziel.name} angelegt ({spanne})" + (f"; {grenze}" if grenze else "")

        return await self.a.aendern(konto, arbeit)

    async def duplizieren(self, konto: Konto, karte_id: Kennung) -> Antwort:
        """Kopie in derselben Spalte oben: Titel mit "(Kopie)", Inhalt und Angaben gleich, Checkliste unerledigt; ohne
        Kommentare, Blockade, Transkripte, Gruppe, Serie und Anhänge (M-36)."""

        def arbeit(k: Kontext) -> str:
            q = karte_lesen(k, karte_id)
            b = k.board_mit_recht(q.board, "karten.anlegen")
            ziel = spalte_von(b, q.spalte)
            if ziel is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
            schluessel, nummer = k.neue_nummern(b.id)
            titel = f"{q.titel} (Kopie)"[:TITEL_LAENGE]
            c = q.model_copy(deep=True, update={
                "id": neue_kennung("c"), "schluessel": schluessel, "nummer": nummer, "titel": titel,
                "checkliste": [p.model_copy(update={"erledigt": False}) for p in q.checkliste], "kommentare": [],
                "blockiert": None, "transkripte": [], "gruppe": None, "serie": None, "anhaenge": [],
                "abgeschlossen": abschluss(q, k.heute) if ziel.erledigt else None, "bewegt_am": k.jetzt, "erstellt_am": k.jetzt,
                "verlauf": [Ereignis(zeit=k.jetzt, von=konto.id, text=f"hat die Karte aus {q.schluessel} dupliziert")],
                "fassung": 0,
            })
            einreihen(k, ziel, [c], None)
            speichern(k, c)
            return f"{q.schluessel} als {c.schluessel} dupliziert"

        return await self.a.aendern(konto, arbeit)

    async def umziehen(self, konto: Konto, karte_id: Kennung, board_id: Kennung, spalte: Kennung | None = None) -> Antwort:
        """Eine Karte zieht in ein anderes Board (etwa vom Ideenboard aufs Arbeitsboard), oben in die Spalte (ohne: der
        ersten offenen). Sie bekommt dort die nächste Nummer und die Kartenart des Boards; Labels und eigene Felder mit
        gleichem Namen bleiben, Zuständige, wenn sie dort Mitglied sind. Die Verknüpfung endet, laufende Timer buchen,
        ihre Zeit zieht mit; Inhalt, Checkliste, Kommentare, Anhänge und Verlauf bleiben. Der alte Schlüssel führt
        weiter zu ihr. Rechte: Karten löschen im alten Board, Karten anlegen im neuen."""

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            if c.board == board_id:
                raise Abgelehnt("Die Karte liegt schon in diesem Board")
            quelle = k.board_mit_recht(c.board, "karten.loeschen")
            b = k.board_mit_recht(board_id, "karten.anlegen")
            ziel = spalte_von(b, spalte) if spalte else next((s for s in b.spalten if not s.erledigt), None)
            if ziel is None:
                raise Abgelehnt(f"Diese Spalte gibt es im Board {b.name} nicht", 400)
            gebucht = zeiterfassung.timer_beenden(k, [c])
            serientag_auslassen(k, c)                       # ein Serientag zieht als einfache Karte um
            alt, gruppe = c.schluessel, c.gruppe
            entfallen = uebertragen(quelle, b, c)
            c.board, c.gruppe, c.serie, c.art = b.id, None, None, b.kartenart
            c.schluessel = f"{b.kuerzel}-{k.naechste_nummer(b.id)}"
            c.frueher = [*c.frueher, alt]
            c.spalte, c.bewegt_am = ziel.id, k.jetzt
            c.abgeschlossen = abschluss(c, k.heute) if ziel.erledigt else None
            vermerken(k, c, f"hat sie aus {quelle.name} ({alt}) nach {b.name} verschoben")
            einreihen(k, ziel, [c], None)
            speichern(k, c)
            if gruppe:
                gruppen_aufraeumen(k, quelle.id, {gruppe})
            zeiterfassung.zeit_umziehen(k, c.id, b.id)
            teile = [f"{alt} ist jetzt {c.schluessel} in {b.name}, {ziel.name}"]
            if entfallen:
                teile.append(f"{entfallen} {'Label oder Feld' if entfallen == 1 else 'Labels und Felder'} ohne Gegenstück "
                             f"{'entfällt' if entfallen == 1 else 'entfallen'}")
            grenze = ueber_grenze(k, ziel)
            if grenze:
                teile.append(grenze)
            return "; ".join(teile) + zeiterfassung.gestoppt(gebucht)

        return await self.a.aendern(konto, arbeit)

    async def verknuepfen(self, konto: Konto, a_id: Kennung, b_id: Kennung) -> Antwort:
        """Zwei Arbeitskarten desselben Boards verknüpfen: ohne Gruppe entsteht eine mit geteilter Zeit, hat eine eine
        Gruppe, tritt die andere bei, haben beide verschiedene, geht die zweite in der ersten auf."""

        def arbeit(k: Kontext) -> str:
            a, b = karte_lesen(k, a_id), karte_lesen(k, b_id)
            board = k.board_mit_recht(a.board, "karten.bearbeiten")
            if not verknuepfbar(a, b):
                raise Abgelehnt("Verknüpfen geht nur mit einer anderen Arbeitskarte desselben Boards, die noch nicht "
                                "in derselben Gruppe ist")
            hinweis = ""
            if not a.gruppe and not b.gruppe:
                g = Gruppe(id=neue_kennung("g"), board=board.id)
                k.s.schreib("gruppen", g.json_daten())
                a.gruppe = b.gruppe = g.id
            elif a.gruppe and b.gruppe:
                alt = b.gruppe
                if gruppe_lesen(k, alt).zeit_teilen != gruppe_lesen(k, a.gruppe).zeit_teilen:
                    hinweis = f"; es gilt die Einstellung der Verknüpfung von {a.schluessel}"
                for d in k.s.alle("karten", "board=?", (board.id,)):
                    if d.get("gruppe") == alt and d["id"] not in (a.id, b.id):
                        x = Karte.model_validate(d)
                        x.gruppe = a.gruppe
                        speichern(k, x)
                k.s.loesch("gruppen", alt)
                b.gruppe = a.gruppe
            else:
                a.gruppe = b.gruppe = a.gruppe or b.gruppe
            vermerken(k, a, f"hat sie mit {b.schluessel} verknüpft")
            vermerken(k, b, f"hat sie mit {a.schluessel} verknüpft")
            speichern(k, a)
            speichern(k, b)
            teilen = gruppe_lesen(k, a.gruppe or "").zeit_teilen
            return (f"{a.schluessel} und {b.schluessel} verknüpft: ziehen zusammen, "
                    f"Zeit wird {'geteilt' if teilen else 'nicht geteilt'}{hinweis}")

        return await self.a.aendern(konto, arbeit)

    async def zeit_teilen(self, konto: Konto, gruppe_id: Kennung, an: bool) -> Antwort:
        """Gemeinsame Zeit einer Gruppe zeigen oder nicht (gebucht wird immer je Karte)."""

        def arbeit(k: Kontext) -> str | None:
            g = gruppe_lesen(k, gruppe_id)
            k.board_mit_recht(g.board, "karten.bearbeiten")
            if g.zeit_teilen == an:
                return None
            g.zeit_teilen = an
            k.s.schreib("gruppen", g.json_daten())
            return "Die Gruppe zeigt ihre gemeinsame Zeit" if an else "Jede Karte zeigt nur ihre eigene Zeit"

        return await self.a.aendern(konto, arbeit)

    async def loesen(self, konto: Konto, karte_id: Kennung) -> Antwort:
        """Karte aus ihrer Gruppe lösen; bleibt nur eine übrig, endet die Gruppe."""

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            k.board_mit_recht(c.board, "karten.bearbeiten")
            g = c.gruppe
            if not g:
                return None
            c.gruppe = None
            vermerken(k, c, "hat sie aus der Verknüpfung gelöst")
            speichern(k, c)
            rest = [Karte.model_validate(d) for d in k.s.alle("karten", "board=?", (c.board,)) if d.get("gruppe") == g]
            if len(rest) < 2:
                for x in rest:
                    x.gruppe = None
                    speichern(k, x)
                k.s.loesch("gruppen", g)
            return f"{c.schluessel} aus der Verknüpfung gelöst"

        return await self.a.aendern(konto, arbeit)

    async def verschieben(self, konto: Konto, karte_id: Kennung, nach: Kennung, platz: int | None = None) -> Antwort:
        """Karte in eine Spalte ihres Boards, an den Platz (Ziehen) oder oben (Status, Telefon, Liste)."""

        def arbeit(k: Kontext) -> str | None:
            karte = karte_lesen(k, karte_id)
            b = k.board_mit_recht(karte.board, "karten.verschieben")
            ziel = spalte_von(b, nach)
            if ziel is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
            if karte.spalte == nach and platz is None:
                return None
            if ziel.erledigt and karte.spalte == nach:
                return None                                   # in Erledigt steht die Ordnung fest (neueste zuerst)
            return hinein(k, b, [karte_id], ziel, platz)

        return await self.a.aendern(konto, arbeit)

    async def sammel_verschieben(self, konto: Konto, ids: list[Kennung], nach: Kennung) -> Antwort:
        def arbeit(k: Kontext) -> str | None:
            if not ids:
                return None
            erste = karte_lesen(k, ids[0])
            b = k.board_mit_recht(erste.board, "karten.verschieben")
            ziel = spalte_von(b, nach)
            if ziel is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
            weg = [i for i in ids if karte_lesen(k, i).spalte != nach]
            return hinein(k, b, weg, ziel, None) if weg else None

        return await self.a.aendern(konto, arbeit)

    async def erledigen(self, konto: Konto, karte_id: Kennung) -> Antwort:
        """Abhaken: in die Erledigt-Spalte des Boards."""

        def arbeit(k: Kontext) -> str | None:
            karte = karte_lesen(k, karte_id)
            b = k.board_mit_recht(karte.board, "karten.verschieben")
            ziel = next((s for s in b.spalten if s.erledigt), None)
            if ziel is None:
                raise Abgelehnt(f"Das Board {b.name} hat keine Erledigt-Spalte", 400)
            if karte.spalte == ziel.id:
                return None
            return hinein(k, b, [karte_id], ziel, None)

        return await self.a.aendern(konto, arbeit)
