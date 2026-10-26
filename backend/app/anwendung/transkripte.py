"""Transkripte an der Karte (Modul transkripte, Mechanik M-112 und M-113): Stellen aus der Transkription suchen und als
Marke an die Karte hängen, eine Notiz dazu, entfernen mit Rückgängig; dazu die Spracheingabe beim Erfassen. Die
Transkription ist eine andere App hinter dem Anschluss `Transkription`; gefragt wird im Auftrag der Person (ihre
Sitzung geht mit), suchen, hören und sprechen kann also nur, wer die Transkription selbst nutzen darf. Was an der Karte
steht, sehen alle Mitglieder. Name, Sprecher und Text einer Stelle holt der Server aus dem Transkript, nie aus der
Oberfläche."""

from __future__ import annotations

from typing import Protocol

from ..modell import Board, Karte, Kennung, Konto, Modell, TranskriptMarke
from ..regeln.board import hat_recht, mitglied, modul_an
from .kartenbasis import FELD_LAENGE, karte_lesen, speichern, vermerken
from .rahmen import NAMEN_DER_RECHTE, Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: so viele Marken trägt eine Karte höchstens; so lang darf ein gesuchter Text sein
MARKEN_HOECHSTENS = 100
SUCHE_LAENGE = 200
#: so viel Ton nimmt die Spracheingabe je Stück an (Bytes; die Live-Mitschrift schickt höchstens 15 Sekunden, die
#: Transkription hört bis zwei Minuten)
SPRACHE_HOECHSTENS = 30 * 1024 * 1024


class Fundstelle(Modell):
    zeit: float
    ausschnitt: str


class Treffer(Modell):
    transkript: str
    name: str
    dauer_s: float
    fundstellen: list[Fundstelle]


class Trefferseite(Modell):
    gesamt: int
    ab: int
    treffer: list[Treffer]


class Abschnitt(Modell):
    start: float
    ende: float
    sprecher: str | None = None
    text: str


class Transkriptinhalt(Modell):
    id: str
    name: str
    dauer_s: float
    abschnitte: list[Abschnitt]


class Transkription(Protocol):
    def adresse(self) -> str:
        """Wo die Transkription liegt (leer: nicht eingerichtet); die Oberfläche öffnet dort eine Stelle."""
        ...

    async def suchen(self, sitzung: str, text: str, ab: int, anzahl: int) -> Trefferseite: ...

    async def lesen(self, sitzung: str, transkript: str) -> Transkriptinhalt: ...

    async def hoeren(self, sitzung: str, inhalt: bytes, dateiname: str, typ: str) -> str:
        """Kurzer Ton zu Text; abgelehnt mit Grund, wenn die Transkription nicht kann."""
        ...


class KeineTranskription:
    """Ohne Anschluss: nichts eingerichtet, jede Frage abgelehnt."""

    def adresse(self) -> str:
        return ""

    async def suchen(self, sitzung: str, text: str, ab: int, anzahl: int) -> Trefferseite:
        raise Abgelehnt("Die Transkription ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)

    async def lesen(self, sitzung: str, transkript: str) -> Transkriptinhalt:
        raise Abgelehnt("Die Transkription ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)

    async def hoeren(self, sitzung: str, inhalt: bytes, dateiname: str, typ: str) -> str:
        raise Abgelehnt("Die Transkription ist nicht eingerichtet (Einstellungen, Verbindungen)", 503)


class Gehoert(Modell):
    text: str


def stelle_text(sekunde: float | None) -> str:
    """Eine Stelle wie im Spieler: "4:12", ab einer Stunde "1:04:12"; ohne Sekunde das ganze Transkript."""
    if sekunde is None:
        return "ganzes Transkript"
    s = int(sekunde)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def abschnitt_an(t: Transkriptinhalt, sekunde: float) -> Abschnitt | None:
    """Der Abschnitt, in dem die Stelle liegt; zwischen zwei Abschnitten der davor, vor dem ersten der erste."""
    vorher = [a for a in t.abschnitte if a.start <= sekunde]
    return vorher[-1] if vorher else (t.abschnitte[0] if t.abschnitte else None)


def benennen(m: TranskriptMarke) -> str:
    return f"{m.name} bei {stelle_text(m.sekunde)}" if m.sekunde is not None else m.name


def marke_von(c: Karte, marke_id: Kennung) -> TranskriptMarke:
    m = next((x for x in c.transkripte if x.id == marke_id), None)
    if m is None:
        raise Abgelehnt(f"Diese Stelle hängt nicht (mehr) an {c.schluessel}", 404)
    return m


def board_pruefen(b: Board, konto: Konto, recht: str | None) -> None:
    """Mitglied, Modul an und, wenn genannt, das Recht; sonst abgelehnt mit Grund."""
    if mitglied(b, konto.id) is None:
        raise Abgelehnt(f"Im Board {b.name} bist du nicht Mitglied", 403)
    if not modul_an(b, "transkripte"):
        raise Abgelehnt(f"Transkripte sind im Board {b.name} aus", 403)
    if recht and not hat_recht(b, recht, konto.id):
        raise Abgelehnt(f"Dir fehlt im Board {b.name} das Recht {NAMEN_DER_RECHTE[recht]}", 403)


class Transkripte:
    def __init__(self, anwendung: Anwendung, transkription: Transkription) -> None:
        self.a = anwendung
        self.t = transkription

    async def _board(self, konto: Konto, board_id: Kennung, recht: str | None) -> Board:
        d = await self.a.v.lies("boards", board_id)
        if d is None:
            raise Abgelehnt("Dieses Board gibt es nicht (mehr)", 404)
        b = Board.model_validate(d)
        board_pruefen(b, konto, recht)
        return b

    async def karte(self, konto: Konto, karte_id: Kennung, recht: str | None = None) -> Karte:
        """Die Karte, wenn die Person sie mit diesem Recht in einem Board mit Transkripten sieht."""
        d = await self.a.v.lies("karten", karte_id)
        if d is None:
            raise Abgelehnt("Diese Karte gibt es nicht (mehr)", 404)
        c = Karte.model_validate(d)
        await self._board(konto, c.board, recht)
        return c

    async def suchen(self, konto: Konto, karte_id: Kennung, sitzung: str, text: str, ab: int = 0) -> Trefferseite:
        """Transkripte zum Verknüpfen: wie die Suche der Transkription (Name und Text, Fundstellen mit Zeit)."""
        await self.karte(konto, karte_id, "karten.bearbeiten")
        return await self.t.suchen(sitzung, text.strip()[:SUCHE_LAENGE], max(0, ab), 12)

    async def verknuepfen(self, konto: Konto, karte_id: Kennung, sitzung: str, transkript: str,
                          sekunde: float | None) -> Antwort:
        """Eine Stelle (oder das ganze Transkript) an die Karte: Name, Sprecher und Text aus dem Transkript."""
        await self.karte(konto, karte_id, "karten.bearbeiten")
        t = await self.t.lesen(sitzung, transkript)
        abschnitt = None
        if sekunde is not None:
            sekunde = round(min(max(0.0, sekunde), t.dauer_s or sekunde), 2)
            abschnitt = abschnitt_an(t, sekunde)

        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            b = k.board_mit_recht(c.board, "karten.bearbeiten")
            board_pruefen(b, konto, None)
            if any(m.transkript == t.id and m.sekunde == sekunde for m in c.transkripte):
                raise Abgelehnt("Diese Stelle hängt schon an der Karte")
            if len(c.transkripte) >= MARKEN_HOECHSTENS:
                raise Abgelehnt(f"Eine Karte trägt höchstens {MARKEN_HOECHSTENS} Stellen")
            m = TranskriptMarke(id=neue_kennung("tm"), transkript=t.id, name=t.name, sekunde=sekunde,
                                sprecher=abschnitt.sprecher if abschnitt else None,
                                text=abschnitt.text if abschnitt else None, von=konto.id, am=k.jetzt)
            c.transkripte.append(m)
            vermerken(k, c, f"hat {benennen(m)} verknüpft")
            speichern(k, c)
            return f"{c.schluessel}: {benennen(m)} verknüpft"

        return await self.a.aendern(konto, arbeit)

    async def notiz_setzen(self, konto: Konto, karte_id: Kennung, marke_id: Kennung, notiz: str) -> Antwort:
        notiz = notiz.strip()
        if len(notiz) > FELD_LAENGE:
            raise Abgelehnt(f"Eine Notiz hat höchstens {FELD_LAENGE} Zeichen")

        def arbeit(k: Kontext) -> str | None:
            c = karte_lesen(k, karte_id)
            board_pruefen(k.board_mit_recht(c.board, "karten.bearbeiten"), konto, None)
            m = marke_von(c, marke_id)
            if (m.notiz or "") == notiz:
                return None
            m.notiz = notiz or None
            vermerken(k, c, f"hat die Notiz zu {benennen(m)} {'geändert' if notiz else 'entfernt'}")
            speichern(k, c)
            return f"{c.schluessel}: Notiz zu {benennen(m)} {'gespeichert' if notiz else 'entfernt'}"

        return await self.a.aendern(konto, arbeit)

    async def entfernen(self, konto: Konto, karte_id: Kennung, marke_id: Kennung) -> Antwort:
        def arbeit(k: Kontext) -> str:
            c = karte_lesen(k, karte_id)
            board_pruefen(k.board_mit_recht(c.board, "karten.bearbeiten"), konto, None)
            m = marke_von(c, marke_id)
            c.transkripte = [x for x in c.transkripte if x.id != marke_id]
            vermerken(k, c, f"hat {benennen(m)} gelöst")
            speichern(k, c)
            return f"{c.schluessel}: {benennen(m)} gelöst"

        return await self.a.aendern(konto, arbeit)

    async def zum_abspielen(self, konto: Konto, karte_id: Kennung, marke_id: Kennung) -> TranskriptMarke:
        """Die Marke, deren Ton die Person hören will; die Transkription prüft danach ihren Zugang."""
        return marke_von(await self.karte(konto, karte_id), marke_id)

    async def hoeren(self, konto: Konto, board_id: Kennung, sitzung: str, inhalt: bytes, dateiname: str,
                     typ: str) -> Gehoert:
        """Spracheingabe beim Erfassen einer Karte in diesem Board: der Text eines gesprochenen Stücks."""
        await self._board(konto, board_id, "karten.anlegen")
        if not inhalt:
            raise Abgelehnt("Es kam kein Ton an")
        if len(inhalt) > SPRACHE_HOECHSTENS:
            raise Abgelehnt("Das Stück der Aufnahme ist zu lang; höchstens zwei Minuten", 413)
        return Gehoert(text=(await self.t.hoeren(sitzung, inhalt, dateiname, typ)).strip())
