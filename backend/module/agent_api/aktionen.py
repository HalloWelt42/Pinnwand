"""Aktionsschicht der Agenten-API.

Eine objektorientierte Schicht, die alle Operationen bündelt (Zeit buchen,
Karte anlegen, erledigen, kommentieren, suchen, Briefing). Die Protokoll-Adapter
(REST, MCP, OpenAI-Tools) rufen nur diese Schicht auf - sie ist die einzige
Wahrheit. Schreibaktionen unterstützen einen Trockenlauf (Vorschau).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from app.db import verbindung
from module.kanban_kern import persistence as k
from module.kanban_kern.models import Karte

from . import nlp


class AktionsFehler(Exception):
    """Fachlicher Fehler einer Aktion (vom Adapter in einen 4xx-Status übersetzt)."""

    def __init__(self, nachricht: str, status: int = 400) -> None:
        super().__init__(nachricht)
        self.nachricht = nachricht
        self.status = status


def _karte_kompakt(kt: Karte) -> dict:
    return {"id": kt.id, "schluessel": kt.schluessel, "titel": kt.titel, "spalte": kt.spalte, "board_id": kt.board_id}


class Aktionen:
    def __init__(self, akteur: str = "unbekannt", kuerzel: str | None = None,
                 nur_mappen: set[str] | None = None) -> None:
        self.akteur = akteur
        # Identitaet des Bedieners (UI-Weg mit aktivem Login): Zeitbuchungen werden
        # ihm zugeschrieben statt dem Karten-Zustaendigen.
        self.kuerzel = kuerzel
        # Projekt-Scoping (None = ungefiltert, z.B. Agenten-Token/Admin): gefundene
        # Karten ausserhalb der sichtbaren Mappen werden wie "nicht gefunden" behandelt.
        self.nur_mappen = nur_mappen

    # -- Auflösung ------------------------------------------------------

    def _board_id(self, ref: str | None) -> str | None:
        if not ref:
            return None
        with verbindung() as conn:
            r = conn.execute(
                "SELECT id FROM board WHERE id = ? OR LOWER(kuerzel) = LOWER(?) OR LOWER(titel) = LOWER(?) LIMIT 1",
                (ref, ref, ref),
            ).fetchone()
        return r["id"] if r else None

    def _karte_oder_fehler(self, ref: str, board_ref: str | None = None) -> Karte:
        board_id = self._board_id(board_ref) if board_ref else None
        kt = k.finde_karte_per_text(ref, board_id)
        if kt is not None and self.nur_mappen is not None and k.karte_mappe_id(kt.id) not in self.nur_mappen:
            kt = None  # unsichtbares Projekt = wie nicht gefunden (kein Orakel)
        if kt is None:
            raise AktionsFehler(f"Keine Karte zu '{ref}' gefunden", status=404)
        return kt

    # -- Schreibaktionen -------------------------------------------------

    def zeit_buchen(self, karte_ref: str, dauer: str | int, datum: str | None = None,
                    kommentar: str | None = None, dry_run: bool = False) -> dict:
        kt = self._karte_oder_fehler(karte_ref)
        if kt.typ == "idee":
            raise AktionsFehler("Ideentickets erfassen keine Zeit", status=409)
        sek = dauer if isinstance(dauer, int) else nlp.parse_dauer(str(dauer))
        if not sek or sek <= 0:
            raise AktionsFehler(f"Dauer '{dauer}' nicht verstanden (z.B. '1:30', '90min', '1,5h')")
        iso = nlp.parse_datum(datum)
        vorschau = {
            "aktion": "zeit_buchen", "karte": _karte_kompakt(kt),
            "sekunden": sek, "datum": iso, "kommentar": kommentar,
        }
        if dry_run:
            return {"vorschau": True, **vorschau}
        eintrag = k.erstelle_zeiteintrag(f"z_{uuid4().hex[:8]}", kt.id, iso, sek, kommentar, kuerzel=self.kuerzel)
        return {"vorschau": False, **vorschau, "eintrag_id": eintrag.id if eintrag else None}

    def karte_anlegen(self, board_ref: str, titel: str, spalte: str | None = None,
                      beschreibung: str | None = None, labels: list[str] | None = None,
                      prioritaet: str | None = None, faellig: str | None = None,
                      zustaendig: str | None = None, schaetzung_min: int | None = None,
                      dry_run: bool = False) -> dict:
        board_id = self._board_id(board_ref)
        if not board_id:
            raise AktionsFehler(f"Kein Board zu '{board_ref}' gefunden", status=404)
        if not titel or not titel.strip():
            raise AktionsFehler("Titel fehlt")
        with verbindung() as conn:
            if spalte:
                r = conn.execute(
                    "SELECT id FROM spalte WHERE board_id = ? AND (id = ? OR LOWER(titel) = LOWER(?)) LIMIT 1",
                    (board_id, spalte, spalte),
                ).fetchone()
            else:
                r = conn.execute(
                    "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge LIMIT 1", (board_id,)
                ).fetchone()
        if r is None:
            raise AktionsFehler(f"Spalte '{spalte}' im Board nicht gefunden", status=404)
        spalte_id = r["id"]
        vorschau = {
            "aktion": "karte_anlegen", "board_id": board_id, "spalte": spalte_id,
            "titel": titel, "labels": labels or [], "prioritaet": prioritaet,
            "faellig": faellig, "zustaendig": zustaendig, "schaetzung_min": schaetzung_min,
        }
        if dry_run:
            return {"vorschau": True, **vorschau}
        kt = k.erstelle_karte(
            karte_id=f"k_{uuid4().hex[:8]}", board_id=board_id, spalte=spalte_id, titel=titel.strip(),
            beschreibung=beschreibung, labels=labels or [], prioritaet=prioritaet,
            cover=None, start=None, faellig=faellig, zustaendig=zustaendig,
            akteur=self.kuerzel,
        )
        if schaetzung_min is not None:
            k.aktualisiere_karte(kt.id, {"schaetzung_min": schaetzung_min})
            kt = k.hole_karte(kt.id) or kt
        return {"vorschau": False, **vorschau, "karte": _karte_kompakt(kt)}

    def erledigen(self, karte_ref: str, dauer: str | int | None = None,
                  kommentar: str | None = None, dry_run: bool = False) -> dict:
        kt = self._karte_oder_fehler(karte_ref)
        ziel = k.done_spalte_id(kt.board_id)
        if not ziel:
            raise AktionsFehler("Keine Erledigt-Spalte für das Board gefunden", status=409)
        sek = None
        if dauer is not None:
            sek = dauer if isinstance(dauer, int) else nlp.parse_dauer(str(dauer))
        vorschau = {
            "aktion": "erledigen", "karte": _karte_kompakt(kt),
            "ziel_spalte": ziel, "sekunden": sek, "kommentar": kommentar,
        }
        if dry_run:
            return {"vorschau": True, **vorschau}
        if sek and sek > 0:
            k.erstelle_zeiteintrag(f"z_{uuid4().hex[:8]}", kt.id, nlp.parse_datum(None), sek, kommentar, kuerzel=self.kuerzel)
        # An den Anfang der Erledigt-Spalte; verschiebe_karte schiebt die anderen nach.
        k.verschiebe_karte(kt.id, ziel, 0, akteur=self.kuerzel)
        if kommentar and not (sek and sek > 0):
            k.kommentar_anhaengen(kt.id, self.akteur, kommentar, datetime.now().isoformat(timespec="minutes"))
        aktuell = k.hole_karte(kt.id) or kt
        return {"vorschau": False, **vorschau, "karte": _karte_kompakt(aktuell)}

    def kommentieren(self, karte_ref: str, text: str, dry_run: bool = False) -> dict:
        kt = self._karte_oder_fehler(karte_ref)
        if not text or not text.strip():
            raise AktionsFehler("Kommentartext fehlt")
        vorschau = {"aktion": "kommentieren", "karte": _karte_kompakt(kt), "text": text}
        if dry_run:
            return {"vorschau": True, **vorschau}
        k.kommentar_anhaengen(kt.id, self.akteur, text.strip(), datetime.now().isoformat(timespec="minutes"))
        return {"vorschau": False, **vorschau}

    def erfasse_freitext(self, text: str, dry_run: bool = False) -> dict:
        """Natürlichsprachige Zeitbuchung: erst interpretieren, dann (optional) buchen."""
        deutung = nlp.erfasse(text)
        if not deutung.get("karte"):
            raise AktionsFehler("Keine Karte erkannt - bitte Schlüssel (z.B. R3-130) oder Titel nennen")
        if not deutung.get("dauer_sek"):
            raise AktionsFehler("Keine Dauer erkannt - z.B. '1:30', '90min', '2 Std'")
        ergebnis = self.zeit_buchen(
            deutung["karte"], int(deutung["dauer_sek"]), deutung.get("datum"),
            deutung.get("kommentar"), dry_run=dry_run,
        )
        ergebnis["deutung"] = deutung
        return ergebnis

    # -- Leseaktionen ----------------------------------------------------

    def suchen(self, query: str, limit: int = 10) -> dict:
        """Stichwort-Suche über Karteninhalte (semantische Suche folgt in Phase 3)."""
        begriff = (query or "").strip()
        if not begriff:
            return {"treffer": [], "anzahl": 0, "modus": "stichwort"}
        muster = f"%{begriff}%"
        with verbindung() as conn:
            rows = conn.execute(
                "SELECT id, board_id, spalte, schluessel, titel, beschreibung FROM karte "
                "WHERE titel LIKE ? OR beschreibung LIKE ? OR schluessel LIKE ? "
                "ORDER BY bewegt_am DESC LIMIT ?",
                (muster, muster, muster, max(1, min(limit, 50))),
            ).fetchall()
        treffer = [
            {"id": r["id"], "schluessel": r["schluessel"], "titel": r["titel"],
             "board_id": r["board_id"], "spalte": r["spalte"]}
            for r in rows
        ]
        return {"treffer": treffer, "anzahl": len(treffer), "modus": "stichwort"}

    def briefing(self, heute: str | None = None) -> dict:
        """Was steht an: überfällig, heute, diese Woche, laufend."""
        heute_iso = heute or date.today().isoformat()
        heute_d = date.fromisoformat(heute_iso)
        woche = (heute_d + timedelta(days=7)).isoformat()
        with verbindung() as conn:
            done = {r["board_id"]: r["id"] for r in conn.execute(
                "SELECT board_id, id FROM spalte WHERE erledigt = 1").fetchall()}
            rows = conn.execute(
                "SELECT id, board_id, spalte, schluessel, titel, faellig, laeuft_seit FROM karte"
            ).fetchall()

        def offen(r) -> bool:
            return done.get(r["board_id"]) != r["spalte"]

        ueberfaellig, heute_faellig, diese_woche, laufend = [], [], [], []
        for r in rows:
            eintrag = {"id": r["id"], "schluessel": r["schluessel"], "titel": r["titel"], "faellig": r["faellig"]}
            if r["laeuft_seit"]:
                laufend.append(eintrag)
            if r["faellig"] and offen(r):
                if r["faellig"] < heute_iso:
                    ueberfaellig.append(eintrag)
                elif r["faellig"] == heute_iso:
                    heute_faellig.append(eintrag)
                elif r["faellig"] <= woche:
                    diese_woche.append(eintrag)
        return {
            "datum": heute_iso,
            "ueberfaellig": ueberfaellig,
            "heute": heute_faellig,
            "diese_woche": diese_woche,
            "laufend": laufend,
        }
