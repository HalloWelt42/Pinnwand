"""Anwendungsfälle an Karten. Verschieben ist ein Weg für Ziehen, Status im Detail, Telefon, Liste und Sammelaktion:
beim Spaltenwechsel beginnt das Alter neu, verknüpfte Karten desselben Boards ziehen mit ans Ende, in einer
Erledigt-Spalte gibt es das Abschlussdatum (Serienkarten ihren Termintag); über der Grenze nur eine Warnung. Jede
Bewegung steht im Verlauf der Karte. Neue Karten bekommen die nächste Nummer ihres Boards (Schlüssel HAUS-12)."""

from __future__ import annotations

from typing import Literal

from ..modell import Board, Ereignis, Gruppe, Karte, Kennung, Konto, Spalte
from ..regeln.board import abschluss, spalte_von
from ..regeln.tage import ist_tag
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: Abstand der Reihe zwischen zwei Karten; wird er zu eng, nummeriert die Spalte neu
ABSTAND = 1024.0
ENG = 1e-6
#: Längster Titel einer Karte (Zeichen)
TITEL_LAENGE = 300


def karte_lesen(k: Kontext, karte_id: Kennung) -> Karte:
    d = k.s.lies("karten", karte_id)
    if d is None:
        raise Abgelehnt("Diese Karte gibt es nicht (mehr)", 404)
    return Karte.model_validate(d)


def karten_der_spalte(k: Kontext, spalte_id: Kennung) -> list[Karte]:
    return [Karte.model_validate(d) for d in k.s.alle("karten", "spalte=?", (spalte_id,), "reihe")]


def vermerken(k: Kontext, karte: Karte, text: str) -> None:
    """Eine Zeile im Verlauf der Karte (M-64)."""
    karte.verlauf.append(Ereignis(zeit=k.jetzt, von=k.konto.id, text=text))


def speichern(k: Kontext, karte: Karte) -> Karte:
    return Karte.model_validate(k.s.schreib("karten", karte.json_daten()))


def verknuepfbar(a: Karte, b: Karte) -> bool:
    """Eine andere Arbeitskarte desselben Boards, noch nicht in derselben Gruppe (M-74)."""
    return a.id != b.id and a.board == b.board and a.art == "arbeit" and b.art == "arbeit" and not (a.gruppe and a.gruppe == b.gruppe)


def ueber_grenze(k: Kontext, ziel: Spalte) -> str:
    offen = len(karten_der_spalte(k, ziel.id))
    if not ziel.erledigt and ziel.grenze is not None and offen > ziel.grenze:
        return f"{ziel.name} über der Grenze ({offen}/{ziel.grenze})"
    return ""


def einreihen(k: Kontext, ziel: Spalte, karten: list[Karte], platz: int | None) -> None:
    """Gibt den Karten Plätze in der Zielspalte: ab `platz` (oder am Ende) in dieser Reihenfolge; die übrigen Karten
    der Spalte behalten ihre Reihe. Wird der Raum zu eng, nummeriert die Spalte neu."""
    bewegt = {c.id for c in karten}
    andere = [c for c in karten_der_spalte(k, ziel.id) if c.id not in bewegt]
    p = len(andere) if platz is None else max(0, min(platz, len(andere)))
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


def wechseln(k: Kontext, karte: Karte, ziel: Spalte, b: Board, mitgezogen: bool) -> None:
    """Eine Karte kommt in eine andere Spalte: Alter, Abschluss, Verlauf (Timer halten mit Stufe 2 an)."""
    alt = spalte_von(b, karte.spalte)
    karte.spalte = ziel.id
    karte.bewegt_am = k.jetzt
    karte.abgeschlossen = abschluss(karte, k.heute) if ziel.erledigt else None
    vermerken(k, karte, f"mit verknüpfter Karte verschoben nach {ziel.name}" if mitgezogen
              else "hat sie erledigt" if ziel.erledigt else f"hat sie von {alt.name if alt else '?'} nach {ziel.name} verschoben")


def hinein(k: Kontext, b: Board, ids: list[Kennung], ziel: Spalte, platz: int | None) -> str:
    """Karten in eine Spalte bringen: an den Platz (oder ans Ende), verknüpfte desselben Boards ziehen mit ans Ende
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
    einreihen(k, ziel, karten, platz)
    for c in mit:
        einreihen(k, ziel, [c], None)
    for c in karten:
        if c.id in wechselnde:
            wechseln(k, c, ziel, b, False)
        speichern(k, c)
    for c in mit:
        wechseln(k, c, ziel, b, True)
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
    return "; ".join(teile)


class Karten:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def anlegen(self, konto: Konto, board_id: Kennung, titel: str, spalte: Kennung | None = None,
                      art: Literal["arbeit", "idee"] | None = None, faellig: str | None = None,
                      beschreibung: str | None = None) -> Antwort:
        """Neue Karte am Ende der Spalte (ohne: die erste offene), zuständig ist, wer sie anlegt. Ohne Art: die Kartenart
        des Boards."""
        titel = titel.strip()

        def arbeit(k: Kontext) -> str:
            b = k.board_mit_recht(board_id, "karten.anlegen")
            if not titel:
                raise Abgelehnt("Eine Karte braucht einen Titel")
            if len(titel) > TITEL_LAENGE:
                raise Abgelehnt(f"Der Titel ist länger als {TITEL_LAENGE} Zeichen")
            if faellig and not ist_tag(faellig):
                raise Abgelehnt(f"{faellig} ist kein Tag (JJJJ-MM-TT)")
            ziel = spalte_von(b, spalte) if spalte else next((s for s in b.spalten if not s.erledigt), None)
            if ziel is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
            nummer = k.naechste_nummer(b.id)
            c = Karte(id=neue_kennung("c"), board=b.id, schluessel=f"{b.kuerzel}-{nummer}", spalte=ziel.id, titel=titel,
                      art=art or b.kartenart,
                      beschreibung=(beschreibung or "").strip() or None, zustaendig=[konto.id], faellig=faellig or None,
                      bewegt_am=k.jetzt, erstellt_am=k.jetzt,
                      verlauf=[Ereignis(zeit=k.jetzt, von=konto.id, text="hat die Karte angelegt")])
            if ziel.erledigt:
                c.abgeschlossen = abschluss(c, k.heute)
            einreihen(k, ziel, [c], None)
            speichern(k, c)
            grenze = ueber_grenze(k, ziel)
            return f"{c.schluessel} in {ziel.name} angelegt" + (f"; {grenze}" if grenze else "")

        return await self.a.aendern(konto, arbeit)

    async def duplizieren(self, konto: Konto, karte_id: Kennung) -> Antwort:
        """Kopie in derselben Spalte am Ende: Titel mit "(Kopie)", Inhalt und Angaben gleich, Checkliste unerledigt; ohne
        Kommentare, Blockade, Transkripte, Gruppe, Serie und Anhänge (M-36)."""

        def arbeit(k: Kontext) -> str:
            q = karte_lesen(k, karte_id)
            b = k.board_mit_recht(q.board, "karten.anlegen")
            ziel = spalte_von(b, q.spalte)
            if ziel is None:
                raise Abgelehnt("Diese Spalte gibt es in diesem Board nicht", 400)
            nummer = k.naechste_nummer(b.id)
            titel = f"{q.titel} (Kopie)"[:TITEL_LAENGE]
            c = q.model_copy(deep=True, update={
                "id": neue_kennung("c"), "schluessel": f"{b.kuerzel}-{nummer}", "titel": titel,
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

    async def verknuepfen(self, konto: Konto, a_id: Kennung, b_id: Kennung) -> Antwort:
        """Zwei Arbeitskarten desselben Boards verknüpfen: ohne Gruppe entsteht eine mit geteilter Zeit, hat eine eine
        Gruppe, tritt die andere bei, haben beide verschiedene, geht die zweite in der ersten auf."""

        def arbeit(k: Kontext) -> str:
            a, b = karte_lesen(k, a_id), karte_lesen(k, b_id)
            board = k.board_mit_recht(a.board, "karten.bearbeiten")
            if not verknuepfbar(a, b):
                raise Abgelehnt("Verknüpfen geht nur mit einer anderen Arbeitskarte desselben Boards, die noch nicht "
                                "in derselben Gruppe ist")
            if not a.gruppe and not b.gruppe:
                g = Gruppe(id=neue_kennung("g"), board=board.id)
                k.s.schreib("gruppen", g.json_daten())
                a.gruppe = b.gruppe = g.id
            elif a.gruppe and b.gruppe:
                alt = b.gruppe
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
            return f"{a.schluessel} und {b.schluessel} verknüpft: ziehen zusammen, Zeit wird geteilt"

        return await self.a.aendern(konto, arbeit)

    async def zeit_teilen(self, konto: Konto, gruppe_id: Kennung, an: bool) -> Antwort:
        """Gemeinsame Zeit einer Gruppe zeigen oder nicht (gebucht wird immer je Karte)."""

        def arbeit(k: Kontext) -> str | None:
            d = k.s.lies("gruppen", gruppe_id)
            if d is None:
                raise Abgelehnt("Diese Verknüpfung gibt es nicht (mehr)", 404)
            g = Gruppe.model_validate(d)
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
        """Karte in eine Spalte ihres Boards, an den Platz (Ziehen) oder ans Ende (Status, Telefon, Liste)."""

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
