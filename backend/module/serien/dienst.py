"""Vorbuchung: erzeugt aus Serien die kommenden Karten-Instanzen.

Idempotent: pro Serie und Datum entsteht höchstens eine Karte (Markierung an
der Karte). Die Instanzen sind normale Karten - mit Fälligkeit, geplanter Zeit
(Soll) und damit Timer-fähig.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from app.db import verbindung
from module.kanban_kern import persistence as k

from . import persistence as db, wiederholung
from .models import Serie, SerienNachtrag


def _zielspalte(serie: Serie) -> str | None:
    if serie.spalte_id:
        return serie.spalte_id
    with verbindung() as conn:
        r = conn.execute(
            "SELECT id FROM spalte WHERE board_id = ? ORDER BY reihenfolge LIMIT 1", (serie.board_id,)
        ).fetchone()
    return r["id"] if r else None


def _feiertage(von: date, bis: date) -> set[str]:
    """Feiertags-Datumswerte im Bereich. Logik zentral in planung (feiertage_set)."""
    from module.planung import persistence as pdb
    return pdb.feiertage_set(von.isoformat(), bis.isoformat())


def _urlaubstage(kuerzel: str | None, von: date, bis: date) -> set[str]:
    """Urlaubs-Datumswerte der zustaendigen Person. Logik zentral in planung (urlaubstage_set)."""
    from module.planung import persistence as pdb
    return pdb.urlaubstage_set(kuerzel, von.isoformat(), bis.isoformat())


def materialisiere(serie: Serie, heute: date | None = None) -> int:
    """Legt fehlende Instanzen der Serie im Vorlauf-Zeitraum an. Gibt die Anzahl zurück."""
    if not serie.aktiv:
        return 0
    heute = heute or date.today()
    # 0 ist ein gueltiger Wert (nur heute) - daher kein "or 14", das 0 verschlucken wuerde.
    vorlauf = serie.vorlauf_tage
    vorlauf = 14 if vorlauf is None else int(vorlauf)
    bis = heute + timedelta(days=max(0, vorlauf))
    spalte = _zielspalte(serie)
    if not spalte:
        return 0
    # Verpasste Werktage nachbilden: ab dem Tag nach der letzten erzeugten Instanz
    # (bzw. ab serie.start), aber hoechstens RUECKBLICK Tage zurueck, damit nach
    # laengerer Abwesenheit kein Riesenstapel entsteht. Vorhandene Tage werden ohnehin
    # ueber die Dedup-Pruefung uebersprungen.
    RUECKBLICK = 31
    letzte = k.letztes_serie_datum(serie.id)
    if letzte:
        von = date.fromisoformat(letzte) + timedelta(days=1)
    elif serie.start:
        von = date.fromisoformat(serie.start)
    else:
        von = heute
    von = max(von, heute - timedelta(days=RUECKBLICK))
    # Nach einer Pause nicht rueckwirkend materialisieren: die Pausenzeit soll
    # nicht als Karten-Stapel nachgebucht werden.
    if serie.reaktiviert_am:
        von = max(von, date.fromisoformat(serie.reaktiviert_am))
    if von > bis:
        return 0
    feiertage = _feiertage(von, bis) if serie.feiertage_ueberspringen else None
    urlaub = _urlaubstage(serie.zustaendig, von, bis)
    erzeugt = 0
    auslaesse = _auslaesse(serie.id)
    for d in wiederholung.termine(serie, von, bis, feiertage):
        iso = d.isoformat()
        if iso in urlaub:
            continue
        if iso in auslaesse:
            continue  # Instanz wurde bewusst geloescht - nicht wieder anlegen
        if k.serien_instanz_existiert(serie.id, iso):
            continue
        titel = serie.titel
        if serie.uhrzeit:
            titel = f"{serie.uhrzeit} {titel}"
        karte = k.erstelle_karte(
            karte_id="k_" + uuid4().hex[:8], board_id=serie.board_id, spalte=spalte,
            titel=titel, beschreibung=serie.beschreibung, labels=serie.labels or [],
            prioritaet=None, cover=None, start=None, faellig=iso, zustaendig=serie.zustaendig,
        )
        if serie.dauer_min:
            k.aktualisiere_karte(karte.id, {"schaetzung_min": serie.dauer_min})
        try:
            k.markiere_serie(karte.id, serie.id, iso)
        except Exception:
            # Paralleler Lauf hat dieselbe Instanz bereits angelegt (UNIQUE-Index)
            # -> die eben erzeugte Doppel-Karte wieder verwerfen.
            k.loesche_karte(karte.id)
            continue
        erzeugt += 1
    return erzeugt


def _auslaesse(serie_id: str) -> set[str]:
    with verbindung() as conn:
        rows = conn.execute("SELECT datum FROM serie_auslass WHERE serie_id = ?", (serie_id,)).fetchall()
    return {r[0] for r in rows}


def pausiere_aufraeumen(serie_id: str, heute: date | None = None) -> int:
    """Beim Pausieren: offene, zeitlose Zukunfts-Vorbuchungen entfernen (der Rest
    bleibt als Verlauf). Gibt die Anzahl geloeschter Karten zurueck."""
    heute_iso = (heute or date.today()).isoformat()
    with verbindung() as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT k.id FROM karte k"
            " LEFT JOIN spalte s ON s.id = k.spalte"
            " WHERE k.serie_id = ? AND k.faellig >= ? AND COALESCE(k.erfasst_sek, 0) = 0"
            " AND COALESCE(s.erledigt, 0) = 0",
            (serie_id, heute_iso),
        ).fetchall()]
    for kid in ids:
        k.loesche_karte(kid, auslass_merken=False)
    return len(ids)


def ziehe_offene_vorbuchungen_nach(serie: Serie) -> int:
    """Nach einem Serien-PATCH: offene, unveraenderte Vorbuchungen (keine Zeit,
    nicht erledigt) auf die neuen Serienwerte bringen (Titel/Uhrzeit, Person,
    Beschreibung, Soll). Erledigtes bleibt als Verlauf unangetastet."""
    titel = f"{serie.uhrzeit} {serie.titel}" if serie.uhrzeit else serie.titel
    with verbindung() as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT k.id FROM karte k"
            " LEFT JOIN spalte s ON s.id = k.spalte"
            " WHERE k.serie_id = ? AND COALESCE(k.erfasst_sek, 0) = 0 AND COALESCE(s.erledigt, 0) = 0",
            (serie.id,),
        ).fetchall()]
    for kid in ids:
        k.aktualisiere_karte(kid, {
            "titel": titel,
            "beschreibung": serie.beschreibung,
            "zustaendig": serie.zustaendig,
            "schaetzung_min": serie.dauer_min,
        })
    return len(ids)


def raeume_vorbuchungen_bei_urlaub(kuerzel: str, tage: list[str]) -> int:
    """Nachtraeglich eingetragener Urlaub: offene, zeitlose Serien-Vorbuchungen
    der Person an diesen Tagen entfernen (mit Auslass, damit sie nicht
    wiederkommen)."""
    if not kuerzel or not tage:
        return 0
    platz = ",".join("?" for _ in tage)
    with verbindung() as conn:
        ids = [r["id"] for r in conn.execute(
            f"SELECT k.id FROM karte k"
            f" LEFT JOIN spalte s ON s.id = k.spalte"
            f" WHERE k.serie_id IS NOT NULL AND k.zustaendig = ? AND k.faellig IN ({platz})"
            f" AND COALESCE(k.erfasst_sek, 0) = 0 AND COALESCE(s.erledigt, 0) = 0",
            (kuerzel, *tage),
        ).fetchall()]
    for kid in ids:
        k.loesche_karte(kid)
    return len(ids)


def materialisiere_alle(heute: date | None = None) -> int:
    return sum(materialisiere(s, heute) for s in db.liste())


def loesche(sid: str) -> bool:
    """Loescht die Serie und raeumt ihre Instanzen auf.

    Karten ohne erfasste Zeit (reine Vorbuchungen) werden geloescht; Karten mit
    erfasster Zeit bleiben als Verlauf erhalten, werden aber von der Serie
    geloest (serie_id/serie_datum entfernt). So entstehen beim Loeschen oder
    Ersetzen einer Serie keine verwaisten Doppel-Karten.
    """
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT k.id, COALESCE(s.erledigt, 0) AS erledigt,"
            " EXISTS (SELECT 1 FROM zeiteintrag z WHERE z.karte_id = k.id) AS hat_zeit"
            " FROM karte k LEFT JOIN spalte s ON s.id = k.spalte WHERE k.serie_id = ?",
            (sid,),
        ).fetchall()
    for r in rows:
        # Verlauf erhalten: Karten mit erfasster Zeit ODER bereits erledigte
        # Karten (per Drag abgeschlossen, auch ohne Timer) nur abkoppeln.
        if r["hat_zeit"] or r["erledigt"]:
            with verbindung() as conn:
                conn.execute("UPDATE karte SET serie_id = NULL, serie_datum = NULL WHERE id = ?", (r["id"],))
        else:
            k.loesche_karte(r["id"], auslass_merken=False)
    return db.loesche(sid)


def offene_nachtraege(heute: date | None = None) -> list[SerienNachtrag]:
    """Serien-Karten vergangener Tage, die nicht erfasst und nicht erledigt sind.

    Das sind die Vorkommen, die der Nutzer ignoriert hat - dafuer wird am
    Folgetag gefragt, ob die Stunden nachgetragen werden sollen.
    """
    heute = heute or date.today()
    with verbindung() as conn:
        rows = conn.execute(
            "SELECT k.id, k.schluessel, k.titel, k.faellig, s.titel AS serie_titel, s.dauer_min "
            "FROM karte k "
            "JOIN serie s ON s.id = k.serie_id "
            "JOIN spalte sp ON sp.id = k.spalte "
            "WHERE k.serie_id IS NOT NULL AND k.faellig IS NOT NULL AND k.faellig < ? "
            "AND k.erfasst_sek = 0 AND sp.erledigt = 0 "
            "ORDER BY k.faellig",
            (heute.isoformat(),),
        ).fetchall()
    return [
        SerienNachtrag(
            karte_id=r["id"], schluessel=r["schluessel"], titel=r["titel"],
            datum=r["faellig"], serie_titel=r["serie_titel"], soll_min=r["dauer_min"],
        )
        for r in rows
    ]


def nachtragen(karte_id: str, dauer_min: int | None = None) -> "object | None":
    """Traegt fuer eine ignorierte Serien-Karte die Stunden ihres Tages nach und
    verschiebt sie in die Erledigt-Spalte. Ohne Dauer wird das Serien-Soll genutzt."""
    with verbindung() as conn:
        row = conn.execute("SELECT board_id, faellig, serie_id FROM karte WHERE id = ?", (karte_id,)).fetchone()
        if row is None:
            return None
        if dauer_min is None and row["serie_id"]:
            s = conn.execute("SELECT dauer_min FROM serie WHERE id = ?", (row["serie_id"],)).fetchone()
            dauer_min = (s["dauer_min"] if s else None) or 60
    datum = row["faellig"] or date.today().isoformat()
    sek = max(0, int(dauer_min or 0)) * 60
    if sek > 0:
        k.erstelle_zeiteintrag("z_" + uuid4().hex[:8], karte_id, datum, sek, "Nachgetragen")
    # Erledigt-Spalte mit Rueckfall auf die letzte Spalte - so bleibt die Karte
    # auch auf Boards ohne explizite Erledigt-Spalte nicht in einer aktiven Spalte stehen.
    done = k.done_spalte_id(row["board_id"])
    if done:
        k.verschiebe_karte(karte_id, done, 1_000_000)
    return k.hole_karte(karte_id)


def init() -> None:
    """Schema anlegen und beim Start die anstehenden Instanzen vorbuchen."""
    db.init_db()
    try:
        materialisiere_alle()
    except Exception:
        # Vorbuchung darf den Start nie verhindern.
        pass
