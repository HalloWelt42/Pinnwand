"""Regeln des Moduls Serien als reine Funktionen: an welchen Tagen eine Serie greift, welchen Stand jeder Tag hat
(gezählt, wartet, verworfen, heute, vorgebucht, angefasst, geplant, gelöscht, entfällt, pausiert), der Vorlauf und der
Titel der Karte. Gleich frontend/src/regeln/serien.ts; was die Regeln über Personen und Karten wissen müssen, gibt der
Aufrufer als Umfeld."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..modell import Kennung, Serie
from .tage import ist_wochenende, plus_tage, tage_im_monat, tage_von, wochentag

#: so weit zurück wartet ein Serientag auf Bestätigung; ältere gelten als gezählt
NACHTRAG_TAGE = 31


@dataclass(frozen=True)
class TagKarte:
    """Die Karte eines Serientags, so weit die Regeln sie brauchen."""

    id: Kennung
    zustaendig: list[Kennung]
    #: wer seine Zeit auf ihr gebucht hat
    gebucht: list[Kennung]
    #: angefasst: nicht mehr in der Zielspalte, erledigt, mit Zeit oder mit mehr als der Zeile ihres Anlegens im Verlauf
    angefasst: bool


@dataclass
class Umfeld:
    heute: str
    #: Uhrzeit jetzt ("10:42"): ein Tag heute zählt als nächster, solange seine Uhrzeit noch kommt
    jetzt: str
    #: ganztägige Abwesenheit einer Person an einem Tag als Wort (Urlaub, Krank, ...), sonst None
    abwesend: Callable[[Kennung, str], str | None]
    #: Feiertag im Bundesland der Person an diesem Tag, sonst None
    feiertag: Callable[[Kennung, str], str | None]
    tag_karte: Callable[[Kennung, str], TagKarte | None]

    @property
    def bestaetigt_bis(self) -> str:
        """Bis zu diesem Tag gelten Serientage als bestätigt (ältere führt niemand einzeln nach)."""
        return plus_tage(self.heute, -(NACHTRAG_TAGE + 1))


@dataclass
class Vorkommen:
    serie: Kennung
    tag: str
    stand: str
    #: Teilnehmer, die an diesem Tag fehlen, mit Grund
    ohne: list[tuple[Kennung, str]] = field(default_factory=list)
    #: wer seine Zeit noch nicht bestätigt hat (nur vorbei)
    offen: list[Kennung] = field(default_factory=list)
    karte: Kennung | None = None


def ist_pausiert(s: Serie, tag: str) -> bool:
    return bool(s.pausiert_seit) and tag >= s.pausiert_seit and not (s.fortgesetzt and tag >= s.fortgesetzt)


def vorlauf_ende(s: Serie, heute: str) -> str:
    return plus_tage(heute, s.vorlauf_tage)


def werktag(s: Serie, tag: str, u: Umfeld) -> bool:
    """Montag bis Freitag und für keinen Teilnehmer ein Feiertag."""
    return not ist_wochenende(tag) and not any(u.feiertag(k, tag) for k in s.teilnehmer)


def monatstag_der(s: Serie, tag: str, u: Umfeld) -> str:
    """Der Tag der Serie im Monat eines Tages."""
    jahr, monat = int(tag[:4]), int(tag[5:7])
    n = tage_im_monat(jahr, monat)
    t = lambda d: f"{tag[:8]}{d:02d}"  # noqa: E731 - wie in der Regel der Oberfläche
    if s.monatsregel == "erster-werktag":
        for d in range(1, n + 1):
            if werktag(s, t(d), u):
                return t(d)
    if s.monatsregel == "letzter-werktag":
        for d in range(n, 0, -1):
            if werktag(s, t(d), u):
                return t(d)
    return t(min(s.monatstag or int(s.ab[8:10]), n))


def trifft(s: Serie, tag: str, u: Umfeld) -> bool:
    """Greift der Rhythmus an diesem Tag (vor Abwesenheiten, Auslass und Pause)?"""
    w = wochentag(tag)
    if s.rhythmus == "taeglich":
        return not (s.wochenenden_ueberspringen and ist_wochenende(tag))
    if s.rhythmus == "werktags":
        return 1 <= w <= 5
    if s.rhythmus == "woechentlich":
        return w in (s.tage or [wochentag(s.ab)])
    return tag == monatstag_der(s, tag, u)


def rhythmus_tage(s: Serie, von: str, bis: str, u: Umfeld) -> list[str]:
    a = max(von, s.ab)
    e = min(bis, s.bis) if s.bis else bis
    return [] if a > e else [t for t in tage_von(a, e) if trifft(s, t, u)]


def vorkommen_am(s: Serie, tag: str, u: Umfeld) -> Vorkommen:
    """Stand eines Tages in derselben Reihenfolge wie die Oberfläche: gelöscht, angefasst, entfällt, vorbei (pausiert,
    verworfen, gezählt oder wartet), pausiert, heute, vorgebucht oder geplant."""
    ohne: list[tuple[Kennung, str]] = []
    for k in s.teilnehmer:
        grund = u.abwesend(k, tag) or (u.feiertag(k, tag) if s.feiertage_ueberspringen else None)
        if grund:
            ohne.append((k, grund))
    fehlen = {k for k, _ in ohne}
    da = [k for k in s.teilnehmer if k not in fehlen]
    karte = u.tag_karte(s.id, tag)

    def v(stand: str, offen: list[Kennung] | None = None) -> Vorkommen:
        return Vorkommen(s.id, tag, stand, ohne, offen or [], karte.id if karte else None)

    if any(a.tag == tag for a in s.auslass):
        return v("geloescht")
    if tag > u.heute and karte and karte.angefasst:
        return v("beruehrt")
    if not da:
        return v("ausgelassen")
    pausiert = ist_pausiert(s, tag)
    if tag < u.heute:
        if pausiert:
            return v("pausiert")
        if tag in s.verworfen:
            return v("verworfen")
        if karte is None or tag <= u.bestaetigt_bis:
            return v("gezaehlt")
        offen = [k for k in karte.zustaendig if k not in fehlen and k not in karte.gebucht]
        return v("wartet" if offen else "gezaehlt", offen)
    if pausiert:
        return v("pausiert")
    if tag == u.heute:
        return v("heute")
    return v("vorgebucht" if tag <= vorlauf_ende(s, u.heute) else "geplant")


def vorkommen(s: Serie, von: str, bis: str, u: Umfeld) -> list[Vorkommen]:
    return [vorkommen_am(s, t, u) for t in rhythmus_tage(s, von, bis, u)]


def karten_titel(s: Serie) -> str:
    """Titel der Karte eines Serientags: Uhrzeit vor dem Titel (wie in der alten App)."""
    return f"{s.uhrzeit} {s.titel}" if s.uhrzeit else s.titel
