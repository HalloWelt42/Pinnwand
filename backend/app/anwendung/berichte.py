"""Anwendungsfälle des Moduls Berichte: den Inhalt eines Berichts aus der Auswahl rechnen (Vorschau), die Datei als PDF,
Tabelle oder Markdown erstellen und in der Ablage der Pinnwand ablegen, eine erstellte Datei wieder ausliefern. Die
Arten sind die der Entwürfe (mockups/src/ansichten/zeit/bericht.ts): Stundennachweis je Person, Zeiten je Board und
Karte, erledigte Karten. Was jemand im Bericht sieht, folgt denselben Rechten wie Stand und Team."""

from __future__ import annotations

import tempfile
from collections import defaultdict
from pathlib import Path

from ..berichtsdatei import ENDUNG, INHALTSTYP, Abschnitt, BerichtInhalt, datei_aus
from ..modell import Abwesenheit, Bericht, BerichtArt, BerichtFormat, Board, Karte, Kennung, Konto, Modell, Zeiteintrag, Zeitkonto
from ..regeln.arbeitszeit import art_name, fassung_am, soll_tag
from ..regeln.board import hat_recht
from ..regeln.tage import datum_kurz, ist_tag, spanne_text, tage_von, tage_zwischen
from ..regeln.zeit import dauer_text
from .anhaenge import Ablage, groesse_text
from .rahmen import Abgelehnt, Antwort, Anwendung, Kontext, neue_kennung
from .sicht import mitglieder, sichtbare_personen, sieht_zeit

#: längster Zeitraum eines Berichts (Tage)
ZEITRAUM_HOECHSTENS = 400
#: Ordner der Berichte in der Ablage der Pinnwand
ORDNER = "Berichte"
ARTNAMEN: dict[str, str] = {"stundennachweis": "Stundennachweis je Person", "board": "Zeiten je Board und Karte",
                            "erledigt": "Erledigte Karten"}


class Auswahl(Modell):
    art: BerichtArt
    von: str
    bis: str
    boards: list[Kennung] = []
    personen: list[Kennung] = []
    format: BerichtFormat = "pdf"


def differenz(sek: float) -> str:
    """+1:10 oder -0:02 (das Minuszeichen als einfacher Bindestrich), unter einer Minute 0:00, wie in der Oberfläche."""
    s = round(sek)
    if abs(s) < 60:
        return "0:00"
    return f"{'+' if s > 0 else '-'}{dauer_text(abs(s))}"


class Lage:
    """Was ein Bericht aus dem Verzeichnis braucht, einmal gelesen: Boards, Konten, Zeitkonten, Abwesenheiten und die
    Zeiteinträge des Zeitraums."""

    def __init__(self, ich: Kennung, boards: list[Board], konten: dict[Kennung, Konto], zeitkonten: list[Zeitkonto],
                 abwesenheiten: list[Abwesenheit], eintraege: list[Zeiteintrag], karten: dict[Kennung, dict],
                 termine: dict[Kennung, dict]) -> None:
        self.ich = ich
        self.boards = {b.id: b for b in boards}
        self.konten = konten
        self.zeitkonten = zeitkonten
        self.abwesenheiten = abwesenheiten
        self.eintraege = eintraege
        self.karten = karten
        self.termine = termine

    def name(self, konto: Kennung) -> str:
        return self.konten[konto].name if konto in self.konten else "Unbekannte Person"

    def kuerzel(self, konto: Kennung) -> str:
        return self.konten[konto].kuerzel if konto in self.konten else "?"

    def zeit_sichtbar(self, e: Zeiteintrag) -> bool:
        """Eigene Zeit immer, die anderer nur mit dem Recht "Zeiten anderer sehen" im Board des Eintrags."""
        b = self.boards.get(e.board)
        return e.konto == self.ich or (b is not None and sieht_zeit(b, self.ich))

    def wofuer(self, e: Zeiteintrag) -> str:
        if e.karte:
            return (self.karten.get(e.karte) or {}).get("schluessel", "Karte")
        return f"Termin {(self.termine.get(e.termin or '') or {}).get('titel', '')}".strip()


# ═══ Inhalt je Art ════════════════════════════════════════════════════════════════════════════════════════════════════

def nachweis(a: Auswahl, lage: Lage) -> BerichtInhalt:
    """Soll, Ist und Differenz je Tag aus dem Zeitkonto; Ist aus allen Boards, die Karten nur, wo du ihre Zeit siehst."""
    abschnitte = []
    for p in a.personen:
        zeilen: list[list[str]] = []
        soll_summe = ist_summe = 0.0
        for t in tage_von(a.von, a.bis):
            sl = soll_tag(lage.zeitkonten, lage.abwesenheiten, p, t)
            if sl is None:
                continue
            am_tag = [e for e in lage.eintraege if e.konto == p and e.datum == t]
            ist = sum(e.sekunden for e in am_tag)
            if not sl.soll_sek and not ist and not sl.feiertag and not sl.abwesenheit:
                continue
            soll_summe += sl.soll_sek
            ist_summe += ist
            wofuer = ", ".join(dict.fromkeys(lage.wofuer(e) for e in am_tag if lage.zeit_sichtbar(e)))
            hinweis = sl.feiertag or (art_name(sl.abwesenheit) if sl.abwesenheit else sl.regel or "")
            zeilen.append([datum_kurz(t), dauer_text(round(sl.soll_sek)), dauer_text(ist), differenz(ist - sl.soll_sek), wofuer,
                           hinweis])
        abschnitte.append(Abschnitt(
            titel=lage.name(p), spalten=["Tag", "Soll", "Ist", "Differenz", "Karten", "Hinweis"], zeilen=zeilen,
            summe=["Summe", dauer_text(round(soll_summe)), dauer_text(round(ist_summe)), differenz(ist_summe - soll_summe), "", ""],
            fuss="Ist ist die gebuchte Zeit aus allen Boards; Soll aus dem Zeitkonto mit Feiertagen und Abwesenheiten."))
    return BerichtInhalt(titel=ARTNAMEN["stundennachweis"], zeitraum=spanne_text(a.von, a.bis), abschnitte=abschnitte)


def je_karte(a: Auswahl, lage: Lage) -> BerichtInhalt:
    """Gebuchte Zeit je Karte (und Termin) eines Boards im Zeitraum, mit Personen und Schätzung."""
    abschnitte = []
    for bid in a.boards:
        b = lage.boards[bid]
        je: dict[str, list] = defaultdict(lambda: [0, set()])
        for e in lage.eintraege:
            if e.board != bid or not lage.zeit_sichtbar(e) or (a.personen and e.konto not in a.personen):
                continue
            x = je[e.karte or f"termin:{e.termin}"]
            x[0] += e.sekunden
            x[1].add(lage.kuerzel(e.konto))
        zeilen = []
        for schluessel, (sek, wer) in sorted(je.items(), key=lambda kv: -kv[1][0]):
            if schluessel.startswith("termin:"):
                t = lage.termine.get(schluessel[7:]) or {}
                zeilen.append(["Termin", t.get("titel", ""), ", ".join(sorted(wer)), dauer_text(sek), ""])
                continue
            k = lage.karten.get(schluessel) or {}
            schaetzung = k.get("schaetzungMin")
            zeilen.append([k.get("schluessel", ""), k.get("titel", ""), ", ".join(sorted(wer)), dauer_text(sek),
                           dauer_text(schaetzung * 60) if schaetzung else ""])
        summe = sum(sek for sek, _ in je.values())
        abschnitte.append(Abschnitt(
            titel=b.name, spalten=["Schlüssel", "Karte", "Personen", "Zeit", "Schätzung"], zeilen=zeilen,
            summe=["", "Summe", "", dauer_text(summe), ""],
            fuss="Zeiten aus den Einträgen im Zeitraum; verknüpfte Karten zählen jede Sekunde einmal."))
    return BerichtInhalt(titel=ARTNAMEN["board"], zeitraum=spanne_text(a.von, a.bis), abschnitte=abschnitte)


def erledigt(a: Auswahl, lage: Lage, erledigte: dict[Kennung, list[Karte]], zeit: dict[Kennung, int]) -> BerichtInhalt:
    """Karten, die im Zeitraum erledigt wurden, mit Zuständigen und der Zeit, die du auf ihnen siehst."""
    abschnitte = []
    for bid in a.boards:
        karten = sorted((k for k in erledigte.get(bid, []) if not a.personen or any(p in a.personen for p in k.zustaendig)),
                        key=lambda k: k.abgeschlossen or "")
        zeilen = [[k.schluessel, k.titel, datum_kurz(k.abgeschlossen or ""), ", ".join(lage.kuerzel(p) for p in k.zustaendig),
                   dauer_text(zeit.get(k.id, 0))] for k in karten]
        abschnitte.append(Abschnitt(
            titel=lage.boards[bid].name, spalten=["Schlüssel", "Karte", "Erledigt", "Zuständig", "Zeit"], zeilen=zeilen,
            summe=["", f"{len(karten)} {'Karte' if len(karten) == 1 else 'Karten'}", "", "",
                   dauer_text(sum(zeit.get(k.id, 0) for k in karten))]))
    return BerichtInhalt(titel=ARTNAMEN["erledigt"], zeitraum=spanne_text(a.von, a.bis), abschnitte=abschnitte)


def dateiname(a: Auswahl, lage: Lage) -> str:
    """Wie in den Entwürfen: Art, wer oder welche Boards, Zeitraum, Endung des Formats."""
    if a.art == "stundennachweis":
        wer = "_".join(lage.name(a.personen[0]).split()) if len(a.personen) == 1 else "Team"
    else:
        wer = "_".join(lage.boards[b].kuerzel for b in a.boards)
    art = {"stundennachweis": "Stundennachweis", "board": "Zeiten", "erledigt": "Erledigt"}[a.art]
    return f"{art}_{wer}_{a.von}_{a.bis}.{ENDUNG[a.format]}"


def titel_von(a: Auswahl, lage: Lage) -> str:
    if a.art == "stundennachweis":
        return f"Stundennachweis {', '.join(lage.name(p) for p in a.personen)}"
    namen = ", ".join(lage.boards[b].name for b in a.boards)
    return f"{'Zeiten je Karte' if a.art == 'board' else 'Erledigte Karten'}: {namen}"


# ═══ Anwendungsfälle ══════════════════════════════════════════════════════════════════════════════════════════════════

class Berichte:
    def __init__(self, anwendung: Anwendung, ablage: Ablage) -> None:
        self.a = anwendung
        self.ablage = ablage

    async def _pruefen(self, konto: Konto, a: Auswahl) -> tuple[Auswahl, list[Board]]:
        """Die Auswahl, wie sie gehen darf, mit allen Boards; sonst abgelehnt mit Grund."""
        if not (ist_tag(a.von) and ist_tag(a.bis)) or a.bis < a.von:
            raise Abgelehnt("Von und bis sind Tage, bis nicht vor von")
        if tage_zwischen(a.von, a.bis) >= ZEITRAUM_HOECHSTENS:
            raise Abgelehnt(f"Ein Bericht umfasst höchstens {ZEITRAUM_HOECHSTENS} Tage")
        alle = [Board.model_validate(d) for d in await self.a.v.alle("boards")]
        moeglich = {b.id for b in alle if hat_recht(b, "berichte.erstellen", konto.id)}
        if not moeglich:
            raise Abgelehnt("Berichte sind in keinem deiner Boards eingeschaltet, oder dir fehlt das Recht dazu", 403)
        personen = list(dict.fromkeys(a.personen))
        boards = list(dict.fromkeys(a.boards))
        if a.art == "stundennachweis":
            erlaubt = sichtbare_personen(alle, konto.id)
            mit_konto = {d["konto"] for d in await self.a.v.alle("zeitkonten")}
            if not personen or any(p not in erlaubt or p not in mit_konto for p in personen):
                raise Abgelehnt("Ein Stundennachweis geht für dich und, wessen Abwesenheiten du siehst, mit Zeitkonto", 403)
            boards = []
        else:
            if not boards or any(b not in moeglich for b in boards):
                raise Abgelehnt("Board-Berichte gehen für Boards mit dem Modul Berichte und deinem Recht dazu", 403)
            sichtbar = {k for b in alle if b.id in boards for k in mitglieder(b)}
            personen = [p for p in personen if p in sichtbar]
        return a.model_copy(update={"personen": personen, "boards": boards}), alle

    async def _lage(self, konto: Konto, a: Auswahl, alle: list[Board]) -> Lage:
        if a.art == "stundennachweis":
            frage = ",".join("?" * len(a.personen))
            zeilen = await self.a.v.alle("zeiteintraege", f"konto IN ({frage}) AND datum>=? AND datum<=?", (*a.personen, a.von, a.bis))
        else:
            frage = ",".join("?" * len(a.boards))
            zeilen = await self.a.v.alle("zeiteintraege", f"board IN ({frage}) AND datum>=? AND datum<=?", (*a.boards, a.von, a.bis))
        eintraege = [Zeiteintrag.model_validate(d) for d in zeilen]
        karten = await self._nach_id("karten", {e.karte for e in eintraege if e.karte})
        karten |= await self._nach_id("entfernt", {e.karte for e in eintraege if e.karte} - set(karten))
        termine = await self._nach_id("termine", {e.termin for e in eintraege if e.termin})
        return Lage(konto.id, alle, {d["id"]: Konto.model_validate(d) for d in await self.a.v.alle("konten")},
                    [Zeitkonto.model_validate(d) for d in await self.a.v.alle("zeitkonten")],
                    [Abwesenheit.model_validate(d) for d in await self.a.v.alle("abwesenheiten")], eintraege, karten, termine)

    async def _nach_id(self, tabelle: str, ids: set[Kennung]) -> dict[Kennung, dict]:
        if not ids:
            return {}
        liste = sorted(ids)
        return {d["id"]: d for d in await self.a.v.alle(tabelle, f"id IN ({','.join('?' * len(liste))})", tuple(liste))}

    async def _erledigte(self, a: Auswahl, lage: Lage) -> tuple[dict[Kennung, list[Karte]], dict[Kennung, int]]:
        """Erledigte Karten der Boards im Zeitraum (auch archivierte) und die Zeit, die du auf ihnen siehst."""
        erledigte: dict[Kennung, list[Karte]] = {}
        for bid in a.boards:
            erledigte[bid] = [Karte.model_validate(d) for d in await self.a.v.alle(
                "karten", "board=? AND json_extract(daten, '$.abgeschlossen') BETWEEN ? AND ?", (bid, a.von, a.bis))]
        ids = {k.id for karten in erledigte.values() for k in karten}
        zeit: dict[Kennung, int] = defaultdict(int)
        if ids:
            liste = sorted(ids)
            for d in await self.a.v.alle("zeiteintraege", f"karte IN ({','.join('?' * len(liste))})", tuple(liste)):
                e = Zeiteintrag.model_validate(d)
                if lage.zeit_sichtbar(e):
                    zeit[e.karte or ""] += e.sekunden
        return erledigte, zeit

    async def inhalt(self, konto: Konto, auswahl: Auswahl) -> tuple[Auswahl, Lage, BerichtInhalt]:
        a, alle = await self._pruefen(konto, auswahl)
        lage = await self._lage(konto, a, alle)
        if a.art == "stundennachweis":
            return a, lage, nachweis(a, lage)
        if a.art == "board":
            return a, lage, je_karte(a, lage)
        return a, lage, erledigt(a, lage, *await self._erledigte(a, lage))

    async def vorschau(self, konto: Konto, auswahl: Auswahl) -> BerichtInhalt:
        """Genau das, was die Datei enthält, ohne sie zu erstellen."""
        return (await self.inhalt(konto, auswahl))[2]

    async def erstellen(self, konto: Konto, auswahl: Auswahl) -> Antwort:
        """Die Datei erstellen und in der Ablage der Pinnwand ablegen (Ordner Berichte); der Eintrag gehört dir. Eine
        Datei lässt sich nicht zurücknehmen, darum ohne Rückgängig."""
        a, lage, inhalt = await self.inhalt(konto, auswahl)
        name = dateiname(a, lage)
        with tempfile.TemporaryDirectory() as ordner:
            pfad = Path(ordner) / name
            pfad.write_bytes(datei_aus(inhalt, a.format, erstellt=self.a.uhr.jetzt()))
            datei = await self.ablage.ablegen(ORDNER, name, pfad, INHALTSTYP[a.format])

        def arbeit(k: Kontext) -> str:
            b = Bericht(id=neue_kennung("r"), konto=k.konto.id, art=a.art, titel=titel_von(a, lage), zeitraum=inhalt.zeitraum,
                        format=a.format, datei=datei.name, datei_id=datei.kennung, erstellt=k.jetzt,
                        groesse=groesse_text(datei.groesse))
            k.s.schreib("berichte", b.json_daten())
            return f"Abgelegt in der Kellerwolke unter {datei.pfad}"

        try:
            return await self.a.aendern(konto, arbeit, rueckgaengig=False)
        except Exception:
            await self.ablage.verwerfen(datei, "Der Eintrag des Berichts ließ sich nicht speichern")
            raise

    async def eigener(self, konto: Konto, bericht_id: Kennung) -> Bericht:
        """Ein eigener Bericht, zum Herunterladen."""
        d = await self.a.v.lies("berichte", bericht_id)
        if d is None or d.get("konto") != konto.id:
            raise Abgelehnt("Diesen Bericht gibt es nicht oder er gehört dir nicht", 404)
        return Bericht.model_validate(d)
