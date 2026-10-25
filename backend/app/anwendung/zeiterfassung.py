"""Anwendungsfälle des Moduls Zeiterfassung: der eine Timer je Person (starten, anhalten, fortsetzen, stoppen), Zeit
buchen, eine Tageszeit oder die Ticketzeit setzen, Einträge ändern und löschen, die Rückfrage nach dem Deckel. Gebucht
wird immer als Zeiteintrag; die Zeit einer Karte ist die Summe ihrer Einträge, es gibt keinen zweiten Zähler. Andere
Bereiche halten Timer über `timer_beenden` und `timer_im_board_beenden` an (Erledigen, Idee, Papierkorb, Mitglied
entfernen, Modul aus); die Sitzung wird dabei gebucht und geht nie verloren (M-84)."""

from __future__ import annotations

from datetime import datetime

from ..modell import Board, Deckel, Karte, Kennung, Konto, Sitzung, Timer, Zeiteintrag
from ..regeln.board import hat_recht, modul_an, spalte_von
from ..regeln.tage import datum_kurz, ist_tag
from ..regeln.zeit import Teil, dauer_text, kuerzen, rang, sitzung_teile, verlaengern
from ..uhr import ortszone
from .kartenbasis import karte_lesen, speichern, vermerken
from .rahmen import NAMEN_DER_RECHTE, Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung
from .sicht import sieht_zeit

#: Längste Dauer eines Eintrags und einer Tageszeit
TAG_SEK = 24 * 3600


# ═══ Lesen ════════════════════════════════════════════════════════════════════════════════════════════════════════════

def timer_von(k: Kontext, konto: Kennung) -> Timer | None:
    d = k.s.lies("timer", konto)
    return Timer.model_validate(d) if d else None


def eintrag_lesen(k: Kontext, eintrag_id: Kennung) -> Zeiteintrag:
    d = k.s.lies("zeiteintraege", eintrag_id)
    if d is None:
        raise Abgelehnt("Diesen Zeiteintrag gibt es nicht (mehr)", 404)
    return Zeiteintrag.model_validate(d)


def eintraege(k: Kontext, wo: str, werte: tuple) -> list[Zeiteintrag]:
    return [Zeiteintrag.model_validate(d) for d in k.s.alle("zeiteintraege", wo, werte)]


def schluessel_von(k: Kontext, karte_id: Kennung) -> str:
    """Schlüssel einer Karte für Meldungen, auch wenn sie inzwischen fehlt."""
    d = k.s.lies("karten", karte_id) or k.s.lies("entfernt", karte_id)
    return (d or {}).get("schluessel") or "die Karte"


def wofuer(k: Kontext, e: Zeiteintrag) -> str:
    """Wofür ein Eintrag gebucht ist, für Meldungen: Schlüssel der Karte oder Titel des Termins."""
    if e.karte:
        return schluessel_von(k, e.karte)
    return (k.s.lies("termine", e.termin or "") or {}).get("titel") or "der Termin"


def name_von(k: Kontext, konto: Kennung) -> str:
    return (k.s.lies("konten", konto) or {}).get("name") or "jemand"


# ═══ Rechte ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

def fehlt(b: Board, recht: str) -> Abgelehnt:
    return Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE[recht]}", 403)


def buchen_pruefen(b: Board, c: Karte, konto: Kennung) -> None:
    """Zeit auf eine Karte buchen: Arbeit, Zeiterfassung an, Recht "Eigene Zeit buchen"."""
    if c.art != "arbeit":
        raise Abgelehnt("Eine Idee hat keine Zeiterfassung")
    if not modul_an(b, "zeiterfassung"):
        raise Abgelehnt(f"Im Board {b.name} ist die Zeiterfassung aus")
    if not hat_recht(b, "zeit.buchen", konto):
        raise fehlt(b, "zeit.buchen")


def timer_pruefen(b: Board, c: Karte, konto: Kennung) -> None:
    """Ein Timer läuft wie Buchen, dazu nur außerhalb einer Erledigt-Spalte."""
    buchen_pruefen(b, c, konto)
    spalte = spalte_von(b, c.spalte)
    if spalte and spalte.erledigt:
        raise Abgelehnt("Auf einer erledigten Karte läuft kein Timer")


def aendern_pruefen(k: Kontext, e: Zeiteintrag) -> None:
    """Eigene Einträge mit "Eigene Zeit buchen", die anderer mit "Zeiten anderer bearbeiten" im Board der Karte."""
    b = k.board(e.board)
    recht = "zeit.buchen" if e.konto == k.konto.id else "zeit.andere.bearbeiten"
    if not hat_recht(b, recht, k.konto.id):
        raise fehlt(b, recht)


# ═══ Buchen einer Sitzung ═════════════════════════════════════════════════════════════════════════════════════════════

def schreiben(k: Kontext, e: Zeiteintrag) -> None:
    k.s.schreib("zeiteintraege", e.json_daten())


def neuer_eintrag(t: Timer, teil: Teil, **mehr) -> Zeiteintrag:
    return Zeiteintrag(id=neue_kennung("z"), karte=t.karte, board=t.board, konto=t.konto, datum=teil.tag, von=teil.von,
                       bis=teil.bis, sekunden=teil.sekunden, herkunft="timer", **mehr)


def teile_buchen(k: Kontext, t: Timer, teile: list[Teil], gedeckelt: Deckel | None) -> None:
    """Teile einer Sitzung als eigene Einträge; über Mitternacht trägt jeder den Tag seines Nachbarn."""
    for i, teil in enumerate(teile):
        nachbar = teile[i + 1] if i + 1 < len(teile) else teile[i - 1]
        schreiben(k, neuer_eintrag(t, teil, zerlegt=nachbar.tag if len(teile) > 1 else None, gedeckelt=gedeckelt))


def in_tageseintrag(k: Kontext, t: Timer, teil: Teil) -> None:
    """Eine Sitzung an einem Tag geht in den Timer-Eintrag der Karte an diesem Tag (je Karte, Person und Tag einer, die
    Sitzungen darin sichtbar)."""
    da = next((e for e in eintraege(k, "konto=? AND karte=? AND datum=?", (t.konto, t.karte, teil.tag))
               if e.herkunft == "timer" and not e.gedeckelt), None)
    if da is None:
        schreiben(k, neuer_eintrag(t, teil))
        return
    bisher = da.sitzungen or ([Sitzung(von=da.von, bis=da.bis)] if da.von and da.bis else [])
    da.sitzungen = [*bisher, Sitzung(von=teil.von, bis=teil.bis)]
    da.sekunden += teil.sekunden
    da.bis = teil.bis
    schreiben(k, da)


def sitzung_buchen(k: Kontext, t: Timer, karte: Karte | None = None) -> int:
    """Die laufende Sitzung eines Timers bis jetzt buchen (über Mitternacht zerlegt, über 12 Stunden gedeckelt mit
    Vermerk). Der Timer hält an; schreiben oder löschen muss ihn der Aufrufer. Der Verlauf geht an `karte`, wenn der
    Aufrufer sie selbst speichert, sonst liest und speichert diese Funktion die Karte. Ergebnis: gebuchte Sekunden."""
    if not t.seit:
        return 0
    teile, gesamt = sitzung_teile(t.seit, k.jetzt, ortszone())
    gebucht = sum(teil.sekunden for teil in teile)
    deckel = Deckel(seit=t.seit, bis=k.jetzt, sekunden=gesamt) if gesamt > gebucht else None
    if len(teile) == 1 and deckel is None:
        in_tageseintrag(k, t, teile[0])
    else:
        teile_buchen(k, t, teile, deckel)
    t.seit = None
    if gebucht:
        wer = "" if t.konto == k.konto.id else f" von {name_von(k, t.konto)}"
        text = f"Timer{wer}: {dauer_text(gebucht)} gebucht" + (" (nach 12 Stunden gedeckelt)" if deckel else "")
        verlauf_an(k, t.karte, karte, text)
    return gebucht


def verlauf_an(k: Kontext, karte_id: Kennung, karte: Karte | None, text: str) -> None:
    if karte is not None and karte.id == karte_id:
        vermerken(k, karte, text)
        return
    d = k.s.lies("karten", karte_id)
    if d is not None:
        c = Karte.model_validate(d)
        vermerken(k, c, text)
        speichern(k, c)


def beenden(k: Kontext, timer: list[Timer], karten: dict[Kennung, Karte]) -> int:
    """Timer buchen und entfernen. Ergebnis: die gebuchte Zeit der handelnden Person."""
    eigene = 0
    for t in timer:
        sek = sitzung_buchen(k, t, karten.get(t.karte))
        k.s.loesch("timer", t.id)
        if t.konto == k.konto.id:
            eigene += sek
    return eigene


def timer_beenden(k: Kontext, karten: list[Karte]) -> int:
    """Alle Timer auf diesen Karten enden und buchen (Erledigen, Idee, Papierkorb). Der Verlauf geht an die gegebenen
    Karten, der Aufrufer speichert sie. Ergebnis: die gebuchte Zeit der handelnden Person."""
    timer = [Timer.model_validate(d) for c in karten for d in k.s.alle("timer", "karte=?", (c.id,))]
    return beenden(k, timer, {c.id: c for c in karten})


def timer_im_board_beenden(k: Kontext, board_id: Kennung, konto: Kennung | None = None) -> int:
    """Timer in einem Board enden und buchen: alle (Zeiterfassung aus) oder die einer Person (sie verlässt das Board)."""
    timer = [Timer.model_validate(d) for d in k.s.alle("timer", "board=?", (board_id,))]
    return beenden(k, [t for t in timer if konto is None or t.konto == konto], {})


def zeit_umziehen(k: Kontext, karte_id: Kennung, board_id: Kennung) -> None:
    """Die Zeit einer Karte zieht mit ihr in ein anderes Board: ihre Einträge gehören dann dorthin (und sind dort
    sichtbar, wo man Zeiten anderer sehen darf)."""
    for e in eintraege(k, "karte=?", (karte_id,)):
        e.board = board_id
        schreiben(k, e)


def gestoppt(sek: int) -> str:
    """Zusatz für die Meldung, wenn dabei der eigene Timer gestoppt wurde."""
    return f"; dein Timer ist gestoppt, {dauer_text(sek)} gebucht" if sek else ""


# ═══ Tageszeit ════════════════════════════════════════════════════════════════════════════════════════════════════════

def dauer_pruefen(sek: int, null_erlaubt: bool = False) -> None:
    if sek < 0 or (sek == 0 and not null_erlaubt):
        raise Abgelehnt("Die Dauer muss größer als null sein")
    if sek > TAG_SEK:
        raise Abgelehnt("Mehr als 24 Stunden passen nicht in einen Tag")


def tag_pruefen(tag: str) -> None:
    if not ist_tag(tag):
        raise Abgelehnt("Das ist kein gültiger Tag")


def tageszeit_setzen(k: Kontext, c: Karte, tag: str, sek: int) -> str | None:
    """Die eigene Zeit auf einer Karte an einem Tag setzen. Mehr bucht die Differenz auf genau diesen Tag (als Korrektur,
    wenn schon Zeit da war), weniger kürzt die eigenen jüngsten Einträge dieses Tags; fremde bleiben."""
    eigene = eintraege(k, "konto=? AND karte=? AND datum=?", (k.konto.id, c.id, tag))
    bisher = sum(e.sekunden for e in eigene)
    if sek == bisher:
        return None
    if sek > bisher:
        schreiben(k, Zeiteintrag(id=neue_kennung("z"), karte=c.id, board=c.board, konto=k.konto.id, datum=tag,
                                 sekunden=sek - bisher, herkunft="korrektur" if bisher else "hand"))
    else:
        rest = bisher - sek
        for e in sorted(eigene, key=rang, reverse=True):
            if rest <= 0:
                break
            if e.sekunden <= rest:
                rest -= e.sekunden
                k.s.loesch("zeiteintraege", e.id)
            else:
                kuerzen(e, rest)
                schreiben(k, e)
                rest = 0
    vermerken(k, c, f"hat die Zeit am {datum_kurz(tag)} von {dauer_text(bisher)} auf {dauer_text(sek)} gesetzt")
    speichern(k, c)
    return f"{c.schluessel} {datum_kurz(tag)}: {dauer_text(bisher)} auf {dauer_text(sek)} gesetzt"


def zerlegung_loesen(k: Kontext, e: Zeiteintrag) -> None:
    """Der andere Teil einer an Mitternacht zerlegten Sitzung verliert den Bezug auf diesen Eintrag."""
    if not e.zerlegt:
        return
    for teil in eintraege(k, "konto=? AND karte=? AND datum=?", (e.konto, e.karte, e.zerlegt)):
        if teil.zerlegt == e.datum and teil.id != e.id:
            teil.zerlegt = None
            schreiben(k, teil)
    e.zerlegt = None


def bestaetigung_zuruecknehmen(k: Kontext, e: Zeiteintrag) -> None:
    """Ein gelöschter Eintrag eines Termins nimmt die Bestätigung zurück: der Termin wartet wieder im Nachtrag."""
    d = k.s.lies("termine", e.termin or "")
    if d and e.konto in d.get("bestaetigt", []):
        k.s.schreib("termine", {**d, "bestaetigt": [x for x in d["bestaetigt"] if x != e.konto]})


# ═══ Deckel ═══════════════════════════════════════════════════════════════════════════════════════════════════════════

def gedeckelte_sitzung(k: Kontext, ids: list[Kennung]) -> tuple[Deckel, list[Zeiteintrag]]:
    """Die gedeckelte Sitzung, zu der die genannten Einträge gehören, mit allen ihren Teilen."""
    if not ids:
        raise Abgelehnt("Keine Einträge genannt")
    genannt = [eintrag_lesen(k, i) for i in ids]
    erster = genannt[0]
    deckel = erster.gedeckelt
    if deckel is None or any(e.gedeckelt != deckel or e.konto != erster.konto or e.karte != erster.karte for e in genannt):
        raise Abgelehnt("Diese Einträge gehören nicht zu einer offenen Rückfrage")
    for e in genannt:
        aendern_pruefen(k, e)
    return deckel, [e for e in eintraege(k, "konto=? AND karte=?", (erster.konto, erster.karte)) if e.gedeckelt == deckel]


def ende_lesen(text: str) -> str:
    """Ende als "JJJJ-MM-TTTHH:MM" (Sekunden erlaubt), als Zeitpunkt mit Sekunden."""
    try:
        return datetime.fromisoformat(text).replace(second=0, microsecond=0, tzinfo=None).isoformat()
    except ValueError:
        raise Abgelehnt("Das Ende ist kein gültiger Zeitpunkt") from None


# ═══ Anwendungsfälle ══════════════════════════════════════════════════════════════════════════════════════════════════

class Zeiterfassung:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    # --- Timer ------------------------------------------------------------------------------------------------------

    async def starten(self, konto: Konto, karte_id: Kennung) -> Antwort:
        """Timer auf einer Karte starten; der eigene Timer auf einer anderen Karte endet dabei (gebucht), fremde laufen
        weiter (M-80). Der erste Start setzt den Starttag der Karte."""

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            timer_pruefen(k.board(c.board), c, k.konto.id)
            vorher = timer_von(k, k.konto.id)
            if vorher and vorher.karte == c.id and vorher.seit:
                return None
            if vorher and vorher.karte != c.id:
                sek = sitzung_buchen(k, vorher)
                text = f"Timer läuft auf {c.schluessel}; {schluessel_von(k, vorher.karte)} beendet" + (
                    f", {dauer_text(sek)} gebucht" if sek else "")
            else:
                text = f"Timer auf {c.schluessel} fortgesetzt" if vorher else f"Timer läuft auf {c.schluessel}"
            k.s.schreib("timer", Timer(id=k.konto.id, konto=k.konto.id, karte=c.id, board=c.board, seit=k.jetzt).json_daten())
            c.start = c.start or k.heute
            vermerken(k, c, "hat den Timer gestartet")
            speichern(k, c)
            return text

        return await self.a.aendern(konto, arbeit)

    async def anhalten(self, konto: Konto) -> Antwort:
        """Die Sitzung wird gebucht, der Timer bleibt auf der Karte und lässt sich fortsetzen."""

        def arbeit(k: Kontext) -> str | None:
            t = timer_von(k, k.konto.id)
            if t is None or not t.seit:
                return None
            sek = sitzung_buchen(k, t)
            k.s.schreib("timer", t.json_daten())
            return f"{schluessel_von(k, t.karte)} angehalten, {dauer_text(sek)} gebucht"

        return await self.a.aendern(konto, arbeit)

    async def fortsetzen(self, konto: Konto) -> Antwort:
        def arbeit(k: Kontext) -> str | None:
            t = timer_von(k, k.konto.id)
            if t is None or t.seit:
                return None
            c = karte_lesen(k, t.karte)
            timer_pruefen(k.board(c.board), c, k.konto.id)
            t.seit = k.jetzt
            k.s.schreib("timer", t.json_daten())
            return f"Timer auf {c.schluessel} fortgesetzt"

        return await self.a.aendern(konto, arbeit)

    async def stoppen(self, konto: Konto) -> Antwort:
        """Die Sitzung wird gebucht, der Timer endet. Den eigenen Timer stoppen geht immer, auch ohne Recht."""

        def arbeit(k: Kontext) -> str | None:
            t = timer_von(k, k.konto.id)
            if t is None:
                return None
            sek = sitzung_buchen(k, t)
            k.s.loesch("timer", t.id)
            return f"{schluessel_von(k, t.karte)} gestoppt" + (f", {dauer_text(sek)} gebucht" if sek else "")

        return await self.a.aendern(konto, arbeit)

    # --- Buchen und setzen ------------------------------------------------------------------------------------------

    async def buchen(self, konto: Konto, karte_id: Kennung, tag: str, sek: int, notiz: str = "") -> Antwort:
        """Zeit nachtragen: ein eigener Eintrag auf diese Karte an diesem Tag (M-86)."""
        dauer_pruefen(sek)
        tag_pruefen(tag)

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            buchen_pruefen(k.board(c.board), c, k.konto.id)
            schreiben(k, Zeiteintrag(id=neue_kennung("z"), karte=c.id, board=c.board, konto=k.konto.id, datum=tag,
                                     sekunden=sek, herkunft="hand", notiz=notiz.strip() or None))
            vermerken(k, c, f"hat {dauer_text(sek)} nachgetragen ({datum_kurz(tag)})")
            speichern(k, c)
            return f"{dauer_text(sek)} auf {c.schluessel} gebucht ({datum_kurz(tag)})"

        return await self.a.aendern(konto, arbeit)

    async def tag_setzen(self, konto: Konto, karte_id: Kennung, tag: str, sek: int) -> Antwort:
        """Zelle des Stundenzettels: die eigene Zeit auf der Karte an diesem Tag."""
        dauer_pruefen(sek, null_erlaubt=True)
        tag_pruefen(tag)

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            buchen_pruefen(k.board(c.board), c, k.konto.id)
            return tageszeit_setzen(k, c, tag, sek)

        return await self.a.aendern(konto, arbeit)

    async def ticketzeit_setzen(self, konto: Konto, karte_id: Kennung, sek: int) -> Antwort:
        """Die Zeit der Karte direkt setzen: die Differenz zur Summe der Einträge, die du siehst, wird heute bei dir
        gebucht oder von deinen heutigen Einträgen genommen (M-87). Gesperrt, solange dein Timer auf ihr läuft."""
        if sek < 0:
            raise Abgelehnt("Die Dauer kann nicht negativ sein")

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            b = k.board(c.board)
            buchen_pruefen(b, c, k.konto.id)
            t = timer_von(k, k.konto.id)
            if t and t.karte == c.id and t.seit:
                raise Abgelehnt("Solange dein Timer auf dieser Karte läuft, lässt sich ihre Zeit nicht setzen")
            alle = eintraege(k, "karte=?", (c.id,))
            sichtbar = alle if sieht_zeit(b, k.konto.id) else [e for e in alle if e.konto == k.konto.id]
            bisher = sum(e.sekunden for e in sichtbar)
            heute = sum(e.sekunden for e in alle if e.konto == k.konto.id and e.datum == k.heute)
            ziel = max(0, heute + sek - bisher)
            dauer_pruefen(ziel, null_erlaubt=True)
            return tageszeit_setzen(k, c, k.heute, ziel)

        return await self.a.aendern(konto, arbeit)

    # --- Einträge ändern --------------------------------------------------------------------------------------------

    async def dauer_aendern(self, konto: Konto, eintrag_id: Kennung, sek: int) -> Antwort:
        dauer_pruefen(sek)

        def arbeit(k: Kontext) -> str | None:
            e = eintrag_lesen(k, eintrag_id)
            aendern_pruefen(k, e)
            alt = e.sekunden
            if sek == alt:
                return None
            if sek < alt:
                kuerzen(e, alt - sek)
            else:
                verlaengern(e, sek)
            schreiben(k, e)
            return f"{wofuer(k, e)} {datum_kurz(e.datum)}: {dauer_text(alt)} auf {dauer_text(sek)} geändert"

        return await self.a.aendern(konto, arbeit)

    async def datum_aendern(self, konto: Konto, eintrag_id: Kennung, tag: str) -> Antwort:
        """Der Eintrag zieht auf einen anderen Tag; Dauer, Uhrzeiten und Herkunft bleiben (M-88). War die Sitzung an
        Mitternacht zerlegt, verlieren beide Teile den Bezug aufeinander."""
        tag_pruefen(tag)

        def arbeit(k: Kontext) -> str | None:
            e = eintrag_lesen(k, eintrag_id)
            aendern_pruefen(k, e)
            alt = e.datum
            if alt == tag:
                return None
            zerlegung_loesen(k, e)
            e.datum = tag
            schreiben(k, e)
            text = f"Zeiteintrag ({dauer_text(e.sekunden)}) von {datum_kurz(alt)} auf {datum_kurz(tag)} gelegt"
            if e.karte:
                verlauf_an(k, e.karte, None, f"hat einen {text}")
            return f"{wofuer(k, e)}: {text}"

        return await self.a.aendern(konto, arbeit)

    async def notiz_aendern(self, konto: Konto, eintrag_id: Kennung, notiz: str) -> Antwort:
        """Still und ohne Rückweg, wie das Tippen in einem Feld."""

        def arbeit(k: Kontext) -> str | None:
            e = eintrag_lesen(k, eintrag_id)
            aendern_pruefen(k, e)
            neu = notiz.strip() or None
            if e.notiz == neu:
                return None
            e.notiz = neu
            schreiben(k, e)
            return "Notiz geändert"

        return await self.a.aendern(konto, arbeit, rueckgaengig=False, melden=False)

    async def loeschen(self, konto: Konto, eintrag_id: Kennung) -> Antwort:
        """Löschen mit Rückgängig: der Eintrag kommt genau so zurück (Person, Zeiten, Herkunft)."""

        def arbeit(k: Kontext) -> str:
            e = eintrag_lesen(k, eintrag_id)
            aendern_pruefen(k, e)
            zerlegung_loesen(k, e)
            k.s.loesch("zeiteintraege", e.id)
            text = f"Zeiteintrag ({dauer_text(e.sekunden)}, {datum_kurz(e.datum)})"
            if e.karte:
                verlauf_an(k, e.karte, None, f"hat einen {text} gelöscht")
            if e.termin:
                bestaetigung_zuruecknehmen(k, e)
            return f"{text} gelöscht"

        return await self.a.aendern(konto, arbeit)

    # --- Rückfrage nach dem Deckel ----------------------------------------------------------------------------------

    async def deckel_korrigieren(self, konto: Konto, ids: list[Kennung], ende: str) -> Antwort:
        """Das echte Ende der Sitzung übernehmen: sie wird von ihrem Beginn bis dahin neu gebucht, ohne Deckel."""
        bis = ende_lesen(ende)

        def arbeit(k: Kontext) -> str:
            deckel, sitzung = gedeckelte_sitzung(k, ids)
            if not deckel.seit < bis <= deckel.bis:
                raise Abgelehnt("Das Ende muss zwischen Beginn und Stopp der Sitzung liegen")
            for e in sitzung:
                k.s.loesch("zeiteintraege", e.id)
            erster = sitzung[0]
            teile, _ = sitzung_teile(deckel.seit, bis, ortszone(), deckeln=False)
            t = Timer(id=erster.konto, konto=erster.konto, karte=erster.karte, board=erster.board)
            teile_buchen(k, t, teile, None)
            gebucht = sum(teil.sekunden for teil in teile)
            verlauf_an(k, erster.karte, None, f"hat das Ende der Sitzung auf {datum_kurz(bis)} {bis[11:16]} gesetzt, "
                                                f"{dauer_text(gebucht)} gebucht")
            return f"Ende auf {bis[11:16]} gesetzt, {dauer_text(gebucht)} gebucht; Rückfrage erledigt"

        return await self.a.aendern(konto, arbeit)

    async def deckel_bestaetigen(self, konto: Konto, ids: list[Kennung]) -> Antwort:
        def arbeit(k: Kontext) -> str:
            for e in gedeckelte_sitzung(k, ids)[1]:
                e.gedeckelt = None
                schreiben(k, e)
            return "12 Stunden bleiben gebucht, Rückfrage erledigt"

        return await self.a.aendern(konto, arbeit)
