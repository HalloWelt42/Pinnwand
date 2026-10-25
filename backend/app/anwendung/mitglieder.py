"""Anwendungsfälle an Rollen und Mitgliedern, alle mit dem Recht "Mitglieder und Rollen verwalten". Rollen: anlegen als
Kopie einer bestehenden, umbenennen (Namen je Board eindeutig), Rechte setzen, löschen mit Ersatzrolle; die Start-Rollen
Besitzer, Mitglied und Leser bleiben, und Besitzer behalten "Board verwalten" und "Mitglieder verwalten". Mitglieder
stehen mit ihrem Kontonamen der Kellerwolke im Board (wer noch nie angemeldet war, hat noch keine Kennung) und werden
darüber angesprochen: Rolle setzen, entfernen, Besitz übertragen. Ein Board hat immer mindestens einen Besitzer."""

from __future__ import annotations

from collections.abc import Callable

from ..modell import MODULE_DA, Board, Kennung, Konto, Mitglied, Rolle
from ..regeln.board import modul_von, spalte_von
from ..vorlagen import ALLE_RECHTE
from .aufbau import karten_des_boards
from .boards import am_board, anzahl, name_pruefen, vergeben
from . import zeiterfassung
from .kartenbasis import speichern, vermerken
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung

#: Rechte, die Besitzer immer behalten, damit jemand das Board führen kann
BESITZER_FEST = ("board.verwalten", "mitglieder.verwalten")
BESITZER = "besitzer"


def rolle_lesen(b: Board, rolle_id: Kennung) -> Rolle:
    r = next((x for x in b.rollen if x.id == rolle_id), None)
    if r is None:
        raise Abgelehnt("Diese Rolle gibt es in diesem Board nicht (mehr)", 404)
    return r


def rolle_frei(b: Board, name: str, ausser: Kennung = "") -> None:
    doppelt = vergeben(((r.id, r.name) for r in b.rollen), name, ausser)
    if doppelt:
        raise Abgelehnt(f"Die Rolle {doppelt} gibt es schon", 409)


def mitglied_lesen(b: Board, kellerwolke: str) -> Mitglied:
    m = next((x for x in b.mitglieder if x.kellerwolke == kellerwolke), None)
    if m is None:
        raise Abgelehnt(f"{kellerwolke} ist nicht im Board {b.name}", 404)
    return m


def mitglied_name(k: Kontext, m: Mitglied) -> str:
    """Name aus dem Konto; wer noch auf die erste Anmeldung wartet, heißt wie sein Konto der Kellerwolke."""
    d = k.s.lies("konten", m.konto) if m.konto else None
    return d["name"] if d else m.kellerwolke


def besitzer(b: Board) -> list[Mitglied]:
    return [m for m in b.mitglieder if m.rolle == BESITZER]


def einziger_besitzer(b: Board, m: Mitglied) -> bool:
    return m.rolle == BESITZER and len(besitzer(b)) == 1


class Mitglieder:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def _am_board(self, konto: Konto, board_id: Kennung, tun: Callable[[Kontext, Board], str | None]) -> Antwort:
        return await am_board(self.a, konto, board_id, "mitglieder.verwalten", tun)

    # --- Rollen und Rechte --------------------------------------------------------------------------------------

    async def rolle_anlegen(self, konto: Konto, board_id: Kennung, name: str, kopie_von: Kennung) -> Antwort:
        """Neue Rolle mit den Rechten einer bestehenden."""

        def tun(k: Kontext, b: Board) -> str:
            n = name_pruefen(name, "Eine Rolle")
            rolle_frei(b, n)
            vorlage = rolle_lesen(b, kopie_von)
            b.rollen.append(Rolle(id=neue_kennung("r"), name=n, rechte=list(vorlage.rechte)))
            return f"Rolle {n} angelegt, mit den Rechten von {vorlage.name}"

        return await self._am_board(konto, board_id, tun)

    async def rolle_umbenennen(self, konto: Konto, board_id: Kennung, rolle_id: Kennung, name: str) -> Antwort:
        def tun(k: Kontext, b: Board) -> str | None:
            r = rolle_lesen(b, rolle_id)
            n = name_pruefen(name, "Eine Rolle")
            if n == r.name:
                return None
            rolle_frei(b, n, r.id)
            alt, r.name = r.name, n
            return f"Rolle {alt} heißt jetzt {n}"

        return await self._am_board(konto, board_id, tun)

    async def recht_setzen(self, konto: Konto, board_id: Kennung, rolle_id: Kennung, recht: str, an: bool) -> Antwort:
        """Ein Recht einer Rolle an oder aus; wirkt sofort für alle Mitglieder mit dieser Rolle."""

        def tun(k: Kontext, b: Board) -> str | None:
            r = rolle_lesen(b, rolle_id)
            if recht not in ALLE_RECHTE:
                raise Abgelehnt("Dieses Recht gibt es nicht")
            modul = modul_von(recht)
            if modul != "kern" and modul not in MODULE_DA:
                raise Abgelehnt("Dieses Recht gehört zu einem Modul, das diese Pinnwand nicht anbietet")
            if (recht in r.rechte) == an:
                return None
            if r.id == BESITZER and not an and recht in BESITZER_FEST:
                raise Abgelehnt("Besitzer behalten Board verwalten und Mitglieder verwalten")
            r.rechte = [*r.rechte, recht] if an else [x for x in r.rechte if x != recht]
            leute = sum(1 for m in b.mitglieder if m.rolle == r.id)
            return f"{r.name}: Recht {'erteilt' if an else 'entzogen'}, gilt sofort für {anzahl(leute, 'Person', 'Personen')}"

        return await self._am_board(konto, board_id, tun)

    async def rolle_loeschen(self, konto: Konto, board_id: Kennung, rolle_id: Kennung, ersatz: Kennung | None = None) -> Antwort:
        """Eigene Rolle löschen (die Start-Rollen bleiben); wer sie hat, bekommt die Ersatzrolle (nicht Besitzer)."""

        def tun(k: Kontext, b: Board) -> str:
            r = rolle_lesen(b, rolle_id)
            if r.vorgabe:
                raise Abgelehnt("Besitzer, Mitglied und Leser bleiben; umbenennen geht")
            leute = [m for m in b.mitglieder if m.rolle == r.id]
            neu = None
            if leute:
                if not ersatz or ersatz == r.id:
                    raise Abgelehnt("Wähle die Rolle für die Personen, die sie haben")
                neu = rolle_lesen(b, ersatz)
                if neu.id == BESITZER:
                    raise Abgelehnt("Als Ersatz geht jede Rolle außer Besitzer")
                for m in leute:
                    m.rolle = neu.id
            b.rollen = [x for x in b.rollen if x.id != r.id]
            weiter = f"; {anzahl(len(leute), 'Person hat', 'Personen haben')} jetzt {neu.name}" if neu else ""
            return f"Rolle {r.name} gelöscht{weiter}"

        return await self._am_board(konto, board_id, tun)

    # --- Mitglieder ---------------------------------------------------------------------------------------------

    async def rolle_setzen(self, konto: Konto, board_id: Kennung, kellerwolke: str, rolle_id: Kennung) -> Antwort:
        """Der einzige Besitzer gibt seine Rolle erst ab, wenn er den Besitz überträgt."""

        def tun(k: Kontext, b: Board) -> str | None:
            m = mitglied_lesen(b, kellerwolke)
            r = rolle_lesen(b, rolle_id)
            if m.rolle == r.id:
                return None
            if einziger_besitzer(b, m):
                raise Abgelehnt("Ein Board hat immer einen Besitzer: erst den Besitz übertragen")
            m.rolle = r.id
            return f"{mitglied_name(k, m)} ist jetzt {r.name}"

        return await self._am_board(konto, board_id, tun)

    async def mitglied_entfernen(self, konto: Konto, board_id: Kennung, kellerwolke: str) -> Antwort:
        """Das Board verschwindet aus der Seitenleiste der Person (auch aus ihren Ordnern), an offenen Karten fällt ihre
        Zuständigkeit weg; eine wartende Einladung ist damit zurückgenommen. Der einzige Besitzer bleibt."""

        def tun(k: Kontext, b: Board) -> str:
            m = mitglied_lesen(b, kellerwolke)
            if einziger_besitzer(b, m):
                raise Abgelehnt("Der einzige Besitzer bleibt, bis er den Besitz überträgt")
            name = mitglied_name(k, m)
            b.mitglieder = [x for x in b.mitglieder if x.kellerwolke != m.kellerwolke]
            if not m.konto:
                return f"Die Einladung an {name} ist zurückgenommen"
            zeiterfassung.timer_im_board_beenden(k, b.id, m.konto)
            frei = 0
            for c in karten_des_boards(k, b):
                spalte = spalte_von(b, c.spalte)
                if m.konto in c.zustaendig and not (spalte and spalte.erledigt):
                    c.zustaendig = [x for x in c.zustaendig if x != m.konto]
                    vermerken(k, c, f"hat {name} als zuständig entfernt")
                    speichern(k, c)
                    frei += 1
            for d in k.s.alle("ordner", "konto=?", (m.konto,)):
                if b.id in d.get("boards", []):
                    k.s.schreib("ordner", {**d, "boards": [x for x in d["boards"] if x != b.id]})
            return f"{name} aus {b.name} entfernt" + (f"; Zuständigkeit an {anzahl(frei, 'Karte', 'Karten')} frei" if frei else "")

        return await self._am_board(konto, board_id, tun)

    async def besitz_uebertragen(self, konto: Konto, board_id: Kennung, an: str, ich_werde: Kennung) -> Antwort:
        """Die andere Person wird Besitzer, du bekommst die gewählte Rolle. Nur an jemanden, der sich schon angemeldet hat,
        damit das Board nie ohne erreichbaren Besitzer ist."""

        def tun(k: Kontext, b: Board) -> str:
            ich = next((m for m in b.mitglieder if m.konto == konto.id), None)
            if ich is None or ich.rolle != BESITZER:
                raise Abgelehnt("Den Besitz überträgt nur, wer Besitzer ist", 403)
            ziel = mitglied_lesen(b, an)
            if ziel.kellerwolke == ich.kellerwolke:
                raise Abgelehnt("Wähle ein anderes Mitglied als dich")
            if not ziel.konto:
                raise Abgelehnt(f"{ziel.kellerwolke} hat sich noch nie angemeldet; den Besitz übernimmt erst, wer schon da war")
            rolle = rolle_lesen(b, ich_werde)
            if rolle.id == BESITZER:
                raise Abgelehnt("Wähle für dich eine Rolle außer Besitzer")
            ziel.rolle = BESITZER
            ich.rolle = rolle.id
            return f"{mitglied_name(k, ziel)} besitzt jetzt {b.name}; du bist {rolle.name}"

        return await self._am_board(konto, board_id, tun)
