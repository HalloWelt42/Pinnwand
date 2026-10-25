"""Anwendungsfälle des Moduls Arbeitszeit, je Person für sich (E-07): Abwesenheiten eintragen und entfernen, eine neue
Fassung des Zeitkontos. Jede Person ändert nur ihre eigenen, und nur, wenn das Modul in einem ihrer Boards an ist. Eine
neue Abwesenheit ersetzt überlappende derselben Person; frühere Tage behalten bei einer neuen Fassung ihr Soll."""

from __future__ import annotations

from ..modell import Abwesenheit, AbwesenheitArt, Board, Halbtagsregel, Kennung, Konto, Zeitkonto
from ..regeln.arbeitszeit import abwesenheit_fehler, art_name, zeitkonto_fehler
from ..regeln.board import mitglied, modul_an
from ..regeln.tage import datum_text, spanne_text
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung


def eingeschaltet(k: Kontext) -> None:
    """Arbeitszeit und Urlaub gibt es für eine Person, sobald das Modul in einem ihrer Boards an ist."""
    for d in k.s.alle("boards"):
        b = Board.model_validate(d)
        if mitglied(b, k.konto.id) and modul_an(b, "arbeitszeit"):
            return
    raise Abgelehnt("Arbeitszeit und Urlaub sind in keinem deiner Boards eingeschaltet", 403)


def anzahl(n: int) -> str:
    return "1 Abwesenheit" if n == 1 else f"{n} Abwesenheiten"


class Arbeitszeit:
    def __init__(self, anwendung: Anwendung) -> None:
        self.a = anwendung

    async def eintragen(self, konto: Konto, von: str, bis: str, art: AbwesenheitArt, anteil: float | None = None,
                        notiz: str = "") -> Antwort:
        """Eine eigene Abwesenheit; überlappende derselben Person gehen dafür (mit Rückgängig zurück)."""
        fehler = abwesenheit_fehler(von, bis, anteil)
        if fehler:
            raise Abgelehnt(fehler)

        def arbeit(k: Kontext) -> str:
            eingeschaltet(k)
            ersetzt = k.s.alle("abwesenheiten", "konto=? AND von<=? AND bis>=?", (k.konto.id, bis, von))
            for d in ersetzt:
                k.s.loesch("abwesenheiten", d["id"])
            a = Abwesenheit(id=neue_kennung("a"), konto=k.konto.id, von=von, bis=bis, art=art, anteil=anteil,
                            notiz=notiz.strip() or None)
            k.s.schreib("abwesenheiten", a.json_daten())
            return f"{art_name(a)} eingetragen: {spanne_text(von, bis)}" + (f"; ersetzt {anzahl(len(ersetzt))}" if ersetzt else "")

        return await self.a.aendern(konto, arbeit)

    async def entfernen(self, konto: Konto, ids: list[Kennung]) -> Antwort:
        """Eine oder mehrere eigene Abwesenheiten entfernen, mit einem Rückgängig für alle."""

        def arbeit(k: Kontext) -> str | None:
            weg = [Abwesenheit.model_validate(d) for d in (k.s.lies("abwesenheiten", i) for i in dict.fromkeys(ids)) if d]
            if any(a.konto != k.konto.id for a in weg):
                raise Abgelehnt("Du kannst nur deine eigenen Abwesenheiten entfernen", 403)
            if not weg:
                return None
            for a in weg:
                k.s.loesch("abwesenheiten", a.id)
            if len(weg) == 1:
                return f"{art_name(weg[0])} {spanne_text(weg[0].von, weg[0].bis)} entfernt"
            return f"{anzahl(len(weg))} entfernt"

        return await self.a.aendern(konto, arbeit)

    async def zeitkonto_speichern(self, konto: Konto, ab: str, wochenstunden: float, tage: list[int], bundesland: str,
                                  urlaubsanspruch: float, resturlaub_vorjahr: float, halbtage: list[Halbtagsregel]) -> Antwort:
        """Neue Fassung des eigenen Zeitkontos ab einem Tag; eine Fassung mit demselben Tag wird ersetzt."""
        fehler = zeitkonto_fehler(ab, wochenstunden, tage, bundesland, urlaubsanspruch, resturlaub_vorjahr, halbtage)
        if fehler:
            raise Abgelehnt(fehler)

        def arbeit(k: Kontext) -> str | None:
            eingeschaltet(k)
            da = k.s.alle("zeitkonten", "konto=? AND ab=?", (k.konto.id, ab))
            z = Zeitkonto(id=da[0]["id"] if da else neue_kennung("zk"), konto=k.konto.id, ab=ab, wochenstunden=wochenstunden,
                          tage=sorted(tage), bundesland=bundesland, urlaubsanspruch=urlaubsanspruch,
                          resturlaub_vorjahr=resturlaub_vorjahr, halbtage=halbtage)
            if da and Zeitkonto.model_validate(da[0]).json_daten() == z.json_daten():
                return None
            k.s.schreib("zeitkonten", z.json_daten())
            return f"Zeitkonto gespeichert, gilt ab {datum_text(ab)}; frühere Tage behalten ihr Soll"

        return await self.a.aendern(konto, arbeit)
