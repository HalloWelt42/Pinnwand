"""Konten der Pinnwand: wer sich mit dem Kellerwolke-Konto anmeldet, bekommt beim ersten Mal ein Konto der Pinnwand
(Kennung, Name, Kürzel, Farbe, Kennung der Anlage); Einladungen, die auf den Kontonamen warten, gelten ab dann mit der Kennung.
Ein Konto lässt sich zurücksetzen (danach wie bei der ersten Anmeldung) und löschen (es verschwindet; meldet es sich
wieder an, ist es neu): selbst oder durch den Besitzer der App, bestätigt mit dem Namen des Kontos.

Ein App-Zugang einer Person (HELF-43, etwa der Helfer) ist eine eigene Person der Pinnwand: Name des Zugangs, eigenes
Kürzel und eigene Farbe, eingeladen als "Konto/Zugang" (admin/Helfer); Kommentare, Verlauf, Zeiten, Timer und
Zuständigkeit laufen unter ihr. Beim ersten Anmelden übernimmt sie, was schon unter ihrem Namen lief: Zeiten, deren
Notiz mit "Zugang:" beginnt, und die Mitgliedschaft im Board, das wie der Zugang heißt."""

from __future__ import annotations

import re

from appkern.anmeldung.dienst import Konto as Anmeldekonto
from appkern.push import Push

from ..modell import Board, Kennung, Konto, Mitglied
from ..regeln.kuerzel import person_kuerzel
from .boards import Zugang
from .mitglieder import BESITZER, austragen, einziger_besitzer
from .papierkorb import board_ablegen, endgueltig
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: was einem Konto allein gehört und beim Zurücksetzen und Löschen ganz geht (gebuchte Zeiten eingeschlossen)
EIGENES = ("zeiteintraege", "timer", "zeitkonten", "abwesenheiten", "hinweise", "ordner", "vorlagen", "berichte")

def app_kennung(person: Kennung, zugang: str) -> Kennung:
    """Kennung der Person eines App-Zugangs: die Kennung der Person und der Name des Zugangs."""
    return f"{person}.app-{re.sub(r'[^a-z0-9]+', '-', zugang.lower()).strip('-')}"


def vorlaeufiges_konto(angemeldet: Anmeldekonto) -> Konto:
    """Das Konto zu einer Anmeldung, wie es beim ersten Mal entsteht: ein Mensch, oder die Person eines App-Zugangs
    (angemeldet mit dem App-Schlüssel, nicht im Auftrag eines Menschen)."""
    if angemeldet.app and not angemeldet.im_auftrag:
        return Konto(id=app_kennung(angemeldet.id, angemeldet.app), name=angemeldet.app, kuerzel=person_kuerzel(angemeldet.app),
                     kellerwolke=f"{angemeldet.name}/{angemeldet.app}", app=angemeldet.app, inhaber=angemeldet.id)
    return Konto(id=angemeldet.id, name=angemeldet.name, kuerzel=angemeldet.kuerzel or person_kuerzel(angemeldet.name),
                 kellerwolke=angemeldet.name)


def app_nachtrag(k: Kontext, person: Konto) -> None:
    """Was ein App-Zugang vor seiner eigenen Person unter seinem Inhaber tat, geht einmal auf ihn über, nur das sicher
    Erkennbare: Zeiten des Inhabers, deren Notiz mit "Zugang:" beginnt, und die Mitgliedschaft im Board, das wie der
    Zugang heißt und in dem der Inhaber Mitglied ist (als Mitglied)."""
    vorsatz = f"{person.app}:".lower()
    for d in k.s.alle("zeiteintraege", "konto=?", (person.inhaber,)):
        if (d.get("notiz") or "").strip().lower().startswith(vorsatz):
            k.s.schreib("zeiteintraege", {**d, "konto": person.id})
    for d in k.s.alle("boards"):
        b = Board.model_validate(d)
        if b.name.strip().lower() != (person.app or "").lower() or not any(m.konto == person.inhaber for m in b.mitglieder):
            continue
        if not any(m.konto == person.id or m.kellerwolke == person.kellerwolke for m in b.mitglieder):
            b.mitglieder.append(Mitglied(konto=person.id, kellerwolke=person.kellerwolke, rolle="mitglied", seit=k.heute))
            k.s.schreib("boards", b.json_daten())


FARBEN = ["himmel", "minze", "honig", "rose", "flieder", "petrol", "koralle", "tuerkis", "sand", "violett", "stahl"]


class Konten:
    def __init__(self, anwendung: Anwendung, zugang: Zugang | None = None, push: Push | None = None) -> None:
        self.a = anwendung
        self.zugang = zugang
        self.push = push
        self._bekannt: dict[str, Konto] = {}
        anwendung.beobachten("konten", lambda b: self.vergessen(b.id))

    async def ich(self, angemeldet: Anmeldekonto) -> Konto:
        """Das Konto der Pinnwand zur Anmeldung; legt es beim ersten Mal an und löst wartende Einladungen auf. Ein
        App-Zugang (mit seinem App-Schlüssel der Kellerwolke angemeldet) ist eine eigene Person."""
        vorlaeufig = vorlaeufiges_konto(angemeldet)
        if vorlaeufig.id in self._bekannt:
            return self._bekannt[vorlaeufig.id]
        gespeichert = await self.a.v.lies("konten", vorlaeufig.id)
        if gespeichert is None or await self._wartende_einladungen(vorlaeufig.kellerwolke):
            konto = await self._anlegen(vorlaeufig)
        else:
            konto = Konto.model_validate(gespeichert)
        self._bekannt[vorlaeufig.id] = konto
        return konto

    async def _wartende_einladungen(self, name: str) -> bool:
        boards = await self.a.v.alle("boards")
        return any(m.get("kellerwolke") == name and not m.get("konto") for b in boards for m in b.get("mitglieder", []))

    async def _anlegen(self, vorlaeufig: Konto) -> Konto:

        def arbeit(k: Kontext) -> str | None:
            gespeichert = k.s.lies("konten", vorlaeufig.id)
            if gespeichert is None:
                vergeben = {d.get("farbe") for d in k.s.alle("konten")}
                farbe = next((f for f in FARBEN if f not in vergeben), FARBEN[0])
                k.s.schreib("konten", {**vorlaeufig.json_daten(), "farbe": farbe, "anlage": neue_kennung("a")})
                if vorlaeufig.app:
                    app_nachtrag(k, vorlaeufig)
            for d in k.s.alle("boards"):
                b = Board.model_validate(d)
                offen = [m for m in b.mitglieder if m.kellerwolke == vorlaeufig.kellerwolke and not m.konto]
                if offen:
                    for m in offen:
                        m.konto = vorlaeufig.id
                    k.s.schreib("boards", b.json_daten())
            return f"{vorlaeufig.name} ist angemeldet"

        await self.a.aendern(vorlaeufig, arbeit, rueckgaengig=False, melden=False)
        return Konto.model_validate(await self.a.v.lies("konten", vorlaeufig.id))

    def vergessen(self, konto_id: str) -> None:
        """Nach jeder Änderung am Konto (Kürzel, Farbe, auch Rückgängig) beim nächsten Mal neu lesen."""
        self._bekannt.pop(konto_id, None)

    # --- Zurücksetzen und löschen ----------------------------------------------------------------------------------

    def besitzer_der_app(self, konto: Konto) -> bool:
        """Dem Konto gehört der App-Schlüssel; ein App-Zugang zählt wie seine Person (der Commitsammler spielt so ein)."""
        return bool(self.zugang and self.zugang.besitzer() and konto.kellerwolke_konto == self.zugang.besitzer())

    async def zuruecksetzen(self, wer: Konto, ziel_id: Kennung, bestaetigung: str, *, loeschen: bool = False) -> Antwort:
        """Alles, was dem Konto in der Pinnwand gehört, geht ohne Rückweg: Boards, in denen es allein angemeldet ist
        (mit Karten, Serien und Terminen), in geteilten Boards seine Mitgliedschaft (als einziger Besitzer geht der Besitz
        an das nächste angemeldete Mitglied), seine Zeiten, Timer, Zeitkonten, Abwesenheiten, Hinweise, Ordner,
        Vorlagen, Berichte, Einstellungen, sein Rückgängig und seine Geräte für Mitteilungen. Zurücksetzen legt das
        Konto gleich neu an (wie bei der ersten Anmeldung, mit neuer `anlage`, damit die Oberfläche ihre Merker vergisst);
        Löschen nimmt es heraus, seine Oberfläche meldet sich ab. Selbst oder als Besitzer der App, zur Sicherheit mit
        dem Namen des Kontos bestätigt."""
        if wer.id != ziel_id and not self.besitzer_der_app(wer):
            raise Abgelehnt("Andere Konten setzt nur der Besitzer der App zurück oder löscht sie", 403)
        tat = "gelöscht" if loeschen else "zurückgesetzt"

        def arbeit(k: Kontext) -> str:
            d = k.s.lies("konten", ziel_id)
            if d is None:
                raise Abgelehnt("Dieses Konto gibt es nicht (mehr)", 404)
            z = Konto.model_validate(d)
            if bestaetigung.strip().casefold() != z.name.casefold():
                raise Abgelehnt(f"Zur Sicherheit den Namen {z.name} eintippen")
            weg, raus = 0, 0
            for bd in k.s.alle("boards"):
                b = Board.model_validate(bd)
                m = next((x for x in b.mitglieder if x.konto == z.id), None)
                if m is None:
                    continue
                andere = [x for x in b.mitglieder if x.konto and x.konto != z.id]
                if not andere:
                    e, _, _ = board_ablegen(k, b)
                    endgueltig(k, e)
                    weg += 1
                    continue
                if einziger_besitzer(b, m):
                    andere[0].rolle = BESITZER
                austragen(k, b, m)
                k.s.schreib("boards", b.json_daten())
                raus += 1
            for tabelle in EIGENES:
                for zeile in k.s.alle(tabelle, "konto=?", (z.id,)):
                    k.s.loesch(tabelle, zeile["id"])
            if k.s.lies("person_einstellungen", z.id) is not None:
                k.s.loesch("person_einstellungen", z.id)
            k.s.journal_vergessen(z.id)
            if loeschen:
                k.s.loesch("konten", z.id)
            else:
                k.s.schreib("konten", Konto(id=z.id, name=z.name, kuerzel=person_kuerzel(z.name), farbe=z.farbe,
                                            kellerwolke=z.kellerwolke, anlage=neue_kennung("a")).json_daten())
            teile = [f"{weg} {'Board' if weg == 1 else 'Boards'} gelöscht"] if weg else []
            teile += [f"aus {raus} {'Board' if raus == 1 else 'Boards'} ausgetragen"] if raus else []
            return f"Konto {z.name} {tat}" + (f": {', '.join(teile)}" if teile else "")

        antwort = await self.a.aendern(wer, arbeit, rueckgaengig=False)
        self.vergessen(ziel_id)
        if self.push:
            for g in await self.push.geraete(ziel_id):
                await self.push.entfernen(ziel_id, geraet=g.id)
        return antwort
