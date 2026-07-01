"""HTTP-Schnittstelle des Kanban-Moduls."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from module.auth.akteur import Akteur, aktueller_akteur
from module.auth.rechte import darf_zeiteintrag_bearbeiten, verlange

from . import persistence as db
from .models import (
    Board,
    BoardCreate,
    BoardDetail,
    BoardUpdate,
    Dokument,
    DokumentCreate,
    DokumentUpdate,
    GruppeUpdate,
    HeuteUebersicht,
    KanbanEinstellungen,
    KanbanEinstellungenUpdate,
    Karte,
    KarteCreate,
    KarteMove,
    KartenSeite,
    KarteUpdate,
    KarteVerknuepfen,
    KommentarCreate,
    LabelCreate,
    LabelDefinition,
    LabelUpdate,
    MappeCreate,
    MappeUpdate,
    Projektmappe,
    SchnellErfassen,
    Spalte,
    SpalteCreate,
    SpalteMove,
    SpaltenReihenfolge,
    SpalteUpdate,
    Zeiteintrag,
    ZeiteintragCreate,
    ZeiteintragUpdate,
)

router = APIRouter(prefix="/api/kanban", tags=["kanban"])


def _index(karte_id: str | None) -> None:
    """Best-effort: Suchindex einer Karte aktualisieren (no-op ohne KI-Dienste)."""
    if not karte_id:
        return
    try:
        from module.suche import indexer
        indexer.index_eine(karte_id)
    except Exception:
        pass


def _index_weg(karte_id: str) -> None:
    try:
        from module.suche import indexer
        indexer.entferne(karte_id)
    except Exception:
        pass


@router.get("/mappen", response_model=list[Projektmappe])
def mappen(akteur: Akteur = Depends(aktueller_akteur)) -> list[Projektmappe]:
    # Mitarbeiter sehen nur ihre Projekte (Mappen ohne Mitglieder bleiben geteilt); Admin alle.
    return db.liste_mappen(person_id=akteur.person_id, alle=akteur.ist_admin)


@router.get("/mappen/{mappe_id}/boards", response_model=list[Board])
def boards(mappe_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> list[Board]:
    verlange(akteur.ist_admin or db.mappe_sichtbar_fuer(mappe_id, akteur.person_id), "Kein Zugriff auf dieses Projekt.")
    return db.liste_boards(mappe_id)


@router.post("/mappen", response_model=Projektmappe, status_code=201)
def mappe_anlegen(eingabe: MappeCreate, akteur: Akteur = Depends(aktueller_akteur)) -> Projektmappe:
    titel = eingabe.titel.strip()
    if not titel:
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")
    mappe = db.erstelle_mappe(f"m_{uuid4().hex[:8]}", titel, eingabe.beschreibung)
    # Die anlegende Person wird Mitglied ihres neuen Projekts (im offenen Modus ohne
    # Person bleibt es memberlos = geteilt). Andere kommen ueber die Mitglieder-Verwaltung dazu.
    if akteur.person_id:
        db.setze_mappe_mitglied(mappe.id, akteur.person_id)
    return mappe


# -- Projekt-Mitglieder (wer sieht das Projekt) - Verwaltung nur fuer Admins -------

@router.get("/mappen/{mappe_id}/mitglieder", response_model=list[str])
def mappe_mitglieder(mappe_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> list[str]:
    verlange(akteur.ist_admin or db.mappe_sichtbar_fuer(mappe_id, akteur.person_id), "Kein Zugriff auf dieses Projekt.")
    return db.mappe_mitglieder(mappe_id)


@router.put("/mappen/{mappe_id}/mitglieder/{person_id}", status_code=204)
def mappe_mitglied_setzen(mappe_id: str, person_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    verlange(akteur.ist_admin, "Nur Admins verwalten Projekt-Mitglieder.")
    db.setze_mappe_mitglied(mappe_id, person_id)


@router.delete("/mappen/{mappe_id}/mitglieder/{person_id}", status_code=204)
def mappe_mitglied_entfernen(mappe_id: str, person_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    verlange(akteur.ist_admin, "Nur Admins verwalten Projekt-Mitglieder.")
    db.entferne_mappe_mitglied(mappe_id, person_id)


@router.patch("/mappen/{mappe_id}", response_model=Projektmappe)
def mappe_aendern(mappe_id: str, eingabe: MappeUpdate) -> Projektmappe:
    felder = eingabe.model_dump(exclude_unset=True)
    if "titel" in felder and not (felder["titel"] or "").strip():
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")
    mappe = db.aktualisiere_mappe(mappe_id, felder)
    if mappe is None:
        raise HTTPException(status_code=404, detail="Mappe nicht gefunden")
    return mappe


@router.delete("/mappen/{mappe_id}", status_code=204)
def mappe_loeschen(mappe_id: str) -> None:
    if not db.loesche_mappe(mappe_id):
        raise HTTPException(status_code=400, detail="Die letzte Mappe kann nicht geloescht werden")


@router.get("/boards/{board_id}", response_model=BoardDetail)
def board(board_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> BoardDetail:
    # Zugriff nur, wenn das Projekt (Mappe) fuer den Nutzer sichtbar ist.
    if not akteur.ist_admin:
        mid = db.board_mappe_id(board_id)
        if mid is not None and not db.mappe_sichtbar_fuer(mid, akteur.person_id):
            raise HTTPException(status_code=403, detail="Kein Zugriff auf dieses Projekt.")
    detail = db.board_detail(board_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Board nicht gefunden")
    return detail


def _als_seite(karten: list[Karte], gesamt: int, offset: int) -> KartenSeite:
    return KartenSeite(karten=karten, gesamt=gesamt, hat_mehr=(offset + len(karten)) < gesamt)


@router.get("/spalten/{spalte_id}/fertige", response_model=KartenSeite)
def fertige(
    spalte_id: str,
    zeitraum: str = "heute",
    offset: int = 0,
    limit: int | None = None,
    q: str | None = None,
    labels: str | None = None,
    prioritaet: str | None = None,
) -> KartenSeite:
    """Eine gefensterte Seite fertiger Karten einer Erledigt-Spalte (nur nicht-archivierte)."""
    lab = [t.strip() for t in labels.split(",") if t.strip()] if labels else None
    karten, gesamt = db.fertige_seite(spalte_id, zeitraum, offset, limit, q, lab, prioritaet)
    return _als_seite(karten, gesamt, max(0, offset))


@router.get("/boards/{board_id}/archiv", response_model=KartenSeite)
def archiv(board_id: str, offset: int = 0, limit: int | None = None, q: str | None = None) -> KartenSeite:
    """Archivierte fertige Karten eines Boards (Abschluss aelter als die Schwelle)."""
    karten, gesamt = db.archiv_seite(board_id, offset, limit, q)
    return _als_seite(karten, gesamt, max(0, offset))


@router.get("/einstellungen", response_model=KanbanEinstellungen)
def kanban_einstellungen() -> KanbanEinstellungen:
    return KanbanEinstellungen(**db.hole_kanban_einstellungen())


@router.put("/einstellungen", response_model=KanbanEinstellungen)
def kanban_einstellungen_setzen(eingabe: KanbanEinstellungenUpdate) -> KanbanEinstellungen:
    werte = db.setze_kanban_einstellungen(eingabe.fertig_seitengroesse, eingabe.archiv_tage)
    return KanbanEinstellungen(**werte)


@router.get("/heute", response_model=HeuteUebersicht)
def heute(datum: str | None = None) -> HeuteUebersicht:
    from datetime import date

    return db.was_steht_an(datum or date.today().isoformat())


# -- Dokumente (Karten- und Mappen-Dokumente) -----------------------------

@router.get("/dokumente", response_model=list[Dokument])
def dokumente(kontext: str, kontext_id: str) -> list[Dokument]:
    if kontext not in ("karte", "mappe"):
        raise HTTPException(status_code=400, detail="Unbekannter Kontext")
    return db.liste_dokumente(kontext, kontext_id)


@router.post("/dokumente", response_model=Dokument, status_code=201)
def dokument_anlegen(eingabe: DokumentCreate) -> Dokument:
    titel = eingabe.titel.strip()
    if not titel:
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")
    d = db.erstelle_dokument(f"d_{uuid4().hex[:8]}", eingabe.kontext, eingabe.kontext_id, titel)
    if d.kontext == "karte":
        _index(d.kontext_id)
    return d


@router.get("/dokumente/{dokument_id}", response_model=Dokument)
def dokument(dokument_id: str) -> Dokument:
    d = db.hole_dokument(dokument_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    return d


@router.patch("/dokumente/{dokument_id}", response_model=Dokument)
def dokument_aendern(dokument_id: str, eingabe: DokumentUpdate) -> Dokument:
    felder = eingabe.model_dump(exclude_unset=True)
    if "titel" in felder and not (felder["titel"] or "").strip():
        raise HTTPException(status_code=400, detail="Titel darf nicht leer sein")
    d = db.aktualisiere_dokument(dokument_id, felder)
    if d is None:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    if d.kontext == "karte":
        _index(d.kontext_id)
    return d


@router.delete("/dokumente/{dokument_id}", status_code=204)
def dokument_loeschen(dokument_id: str) -> None:
    vorher = db.hole_dokument(dokument_id)
    if not db.loesche_dokument(dokument_id):
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    if vorher and vorher.kontext == "karte":
        _index(vorher.kontext_id)


# -- Schnell-Erfassung (natuersprachlich, lokal, mit Vorschau) ------------

@router.post("/schnell-erfassen")
def schnell_erfassen(e: SchnellErfassen) -> dict:
    """Deutet einen Freitext (z.B. 'R3-130 1:30 Doku geschrieben') und bucht Zeit.

    Mit dry_run nur Vorschau (deterministische Deutung), ohne dry_run wird gebucht.
    Lokaler UI-Endpunkt ohne Token (die App ist lokal); die Logik teilt sich mit der Agenten-API.
    """
    from module.agent_api.aktionen import Aktionen, AktionsFehler
    try:
        ergebnis = Aktionen("ui").erfasse_freitext(e.text, dry_run=e.dry_run)
    except AktionsFehler as ex:
        raise HTTPException(status_code=getattr(ex, "status", 400), detail=str(ex))
    if not e.dry_run and ergebnis.get("karte", {}).get("id"):
        _index(ergebnis["karte"]["id"])
    return ergebnis


# -- Karten ---------------------------------------------------------------

@router.post("/karten", response_model=Karte, status_code=201)
def karte_anlegen(eingabe: KarteCreate) -> Karte:
    # Board und Spalte muessen existieren und zusammenpassen - sonst entstuenden
    # Waisen-Karten ohne gueltiges Board, die in keiner Ansicht erscheinen.
    detail = db.board_detail(eingabe.board_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Board nicht gefunden")
    if eingabe.spalte not in {s.id for s in detail.spalten}:
        raise HTTPException(status_code=400, detail="Spalte gehoert nicht zum Board")
    karte = db.erstelle_karte(
        karte_id=f"k_{uuid4().hex[:8]}",
        board_id=eingabe.board_id,
        spalte=eingabe.spalte,
        titel=eingabe.titel,
        beschreibung=eingabe.beschreibung,
        labels=eingabe.labels,
        prioritaet=eingabe.prioritaet,
        cover=eingabe.cover,
        start=eingabe.start.isoformat() if eingabe.start else None,
        faellig=eingabe.faellig.isoformat() if eingabe.faellig else None,
        zustaendig=eingabe.zustaendig,
        typ=eingabe.typ,
    )
    _index(karte.id)
    return karte


@router.patch("/karten/{karte_id}", response_model=Karte)
def karte_aendern(karte_id: str, eingabe: KarteUpdate) -> Karte:
    karte = db.aktualisiere_karte(karte_id, eingabe.model_dump(exclude_unset=True, mode="json"))
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    _index(karte_id)
    return karte


@router.post("/karten/{karte_id}/move", response_model=Karte)
def karte_verschieben(karte_id: str, ziel: KarteMove) -> Karte:
    karte = db.verschiebe_karte(karte_id, ziel.spalte, ziel.reihenfolge)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


@router.post("/karten/{karte_id}/kommentare", response_model=Karte, status_code=201)
def kommentar_anlegen(karte_id: str, eingabe: KommentarCreate) -> Karte:
    karte = db.kommentar_anhaengen(karte_id, eingabe.autor, eingabe.text, datetime.now().isoformat(timespec="minutes"))
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    _index(karte_id)
    return karte


@router.delete("/karten/{karte_id}", status_code=204)
def karte_loeschen(karte_id: str) -> None:
    db.loesche_karte(karte_id)
    _index_weg(karte_id)


# -- Zeiterfassung --------------------------------------------------------

@router.get("/karten/{karte_id}", response_model=Karte)
def karte_holen(karte_id: str) -> Karte:
    """Einzelne Karte - Fallback fuer Deep-Links auf fertige Karten, die nicht im
    gefensterten Board geladen sind."""
    k = db.hole_karte(karte_id)
    if k is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return k


@router.get("/laufend", response_model=Karte | None)
def laufend() -> Karte | None:
    return db.laufende_karte()


@router.post("/karten/{karte_id}/timer/start", response_model=Karte)
def timer_start(karte_id: str) -> Karte:
    vorhanden = db.hole_karte(karte_id)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    if vorhanden.typ == "idee":
        raise HTTPException(status_code=409, detail="Ideentickets erfassen keine Zeit")
    karte = db.timer_start(karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


@router.post("/karten/{karte_id}/verknuepfen", response_model=Karte)
def karte_verknuepfen(karte_id: str, eingabe: KarteVerknuepfen) -> Karte:
    """Legt diese Karte und die Ziel-Karte in eine gemeinsame Zeitgruppe."""
    karte = db.verknuepfe_karten(karte_id, eingabe.ziel_karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


@router.post("/karten/{karte_id}/verknuepfung-loesen", response_model=Karte)
def karte_verknuepfung_loesen(karte_id: str) -> Karte:
    karte = db.loese_verknuepfung(karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


@router.patch("/gruppen/{gruppe_id}", status_code=204)
def gruppe_aendern(gruppe_id: str, eingabe: GruppeUpdate) -> None:
    """Spezialfall-Schalter: teilt die Gruppe die Zeit (Anzeige) oder zaehlt getrennt?"""
    if not db.setze_gruppe_zeit_geteilt(gruppe_id, eingabe.zeit_geteilt):
        raise HTTPException(status_code=404, detail="Gruppe nicht gefunden")


@router.post("/karten/{karte_id}/timer/pause", response_model=Karte)
def timer_pause(karte_id: str) -> Karte:
    karte = db.timer_pause(karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


# -- Zeiteinträge (Auswertung / Korrektur) -------------------------------

@router.get("/zeiteintraege", response_model=list[Zeiteintrag])
def zeiteintraege(von: str | None = None, bis: str | None = None, karte_id: str | None = None) -> list[Zeiteintrag]:
    return db.zeiteintraege_range(von, bis, karte_id)


@router.post("/zeiteintraege", response_model=Zeiteintrag, status_code=201)
def zeiteintrag_anlegen(eingabe: ZeiteintragCreate, akteur: Akteur = Depends(aktueller_akteur)) -> Zeiteintrag:
    # Zeit bucht man nur auf eigene Karten (Eigentum ueber karte.zustaendig) oder als Admin.
    karte = db.hole_karte(eingabe.karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, karte.zustaendig), "Zeit nur auf eigene Karten buchen.")
    eintrag = db.erstelle_zeiteintrag(f"z_{uuid4().hex[:8]}", eingabe.karte_id, eingabe.datum, eingabe.sekunden, eingabe.kommentar)
    if eintrag is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return eintrag


@router.patch("/zeiteintraege/{eintrag_id}", response_model=Zeiteintrag)
def zeiteintrag_aendern(eintrag_id: str, eingabe: ZeiteintragUpdate, akteur: Akteur = Depends(aktueller_akteur)) -> Zeiteintrag:
    vorhanden = db.hole_zeiteintrag(eintrag_id)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Zeiteintrag nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, vorhanden.karte_zustaendig), "Nur eigene Zeiteinträge ändern.")
    eintrag = db.aktualisiere_zeiteintrag(eintrag_id, eingabe.model_dump(exclude_unset=True))
    if eintrag is None:
        raise HTTPException(status_code=404, detail="Zeiteintrag nicht gefunden")
    return eintrag


@router.delete("/zeiteintraege/{eintrag_id}", status_code=204)
def zeiteintrag_loeschen(eintrag_id: str, akteur: Akteur = Depends(aktueller_akteur)) -> None:
    vorhanden = db.hole_zeiteintrag(eintrag_id)
    if vorhanden is None:
        raise HTTPException(status_code=404, detail="Zeiteintrag nicht gefunden")
    verlange(darf_zeiteintrag_bearbeiten(akteur, vorhanden.karte_zustaendig), "Nur eigene Zeiteinträge löschen.")
    db.loesche_zeiteintrag(eintrag_id)


# -- Boards ---------------------------------------------------------------

@router.post("/mappen/{mappe_id}/boards", response_model=BoardDetail, status_code=201)
def board_anlegen(mappe_id: str, eingabe: BoardCreate) -> BoardDetail:
    detail = db.erstelle_board(f"b_{uuid4().hex[:8]}", mappe_id, eingabe.titel)
    assert detail is not None
    return detail


@router.patch("/boards/{board_id}", response_model=Board)
def board_aendern(board_id: str, eingabe: BoardUpdate) -> Board:
    if eingabe.titel is None:
        bestehend = db.board_detail(board_id)
        if bestehend is None:
            raise HTTPException(status_code=404, detail="Board nicht gefunden")
        return bestehend
    board = db.aktualisiere_board(board_id, eingabe.titel)
    if board is None:
        raise HTTPException(status_code=404, detail="Board nicht gefunden")
    return board


@router.delete("/boards/{board_id}", status_code=204)
def board_loeschen(board_id: str) -> None:
    db.loesche_board(board_id)


@router.patch("/boards/{board_id}/spalten-reihenfolge", status_code=204)
def spalten_reihenfolge(board_id: str, eingabe: SpaltenReihenfolge) -> None:
    if not db.setze_spalten_reihenfolge(board_id, eingabe.spalten):
        raise HTTPException(status_code=400, detail="Spalten-Liste passt nicht zum Board")


# -- Spalten --------------------------------------------------------------

@router.post("/boards/{board_id}/spalten", response_model=Spalte, status_code=201)
def spalte_anlegen(board_id: str, eingabe: SpalteCreate) -> Spalte:
    return db.erstelle_spalte(f"s_{uuid4().hex[:8]}", board_id, eingabe.titel, eingabe.wip_limit)


@router.patch("/spalten/{spalte_id}", response_model=Spalte)
def spalte_aendern(spalte_id: str, eingabe: SpalteUpdate) -> Spalte:
    spalte = db.aktualisiere_spalte(spalte_id, eingabe.model_dump(exclude_unset=True))
    if spalte is None:
        raise HTTPException(status_code=404, detail="Spalte nicht gefunden")
    return spalte


@router.post("/spalten/{spalte_id}/erledigt", response_model=Spalte)
def spalte_als_erledigt(spalte_id: str) -> Spalte:
    """Markiert die Spalte als Erledigt-Spalte des Boards (genau eine pro Board)."""
    spalte = db.setze_erledigt_spalte(spalte_id)
    if spalte is None:
        raise HTTPException(status_code=404, detail="Spalte nicht gefunden")
    return spalte


@router.post("/spalten/{spalte_id}/move", response_model=Spalte)
def spalte_verschieben(spalte_id: str, ziel: SpalteMove) -> Spalte:
    spalte = db.verschiebe_spalte(spalte_id, ziel.richtung)
    if spalte is None:
        raise HTTPException(status_code=404, detail="Spalte nicht gefunden")
    return spalte


@router.delete("/spalten/{spalte_id}", status_code=204)
def spalte_loeschen(spalte_id: str) -> None:
    ergebnis = db.loesche_spalte(spalte_id)
    if ergebnis == "fehlt":
        raise HTTPException(status_code=404, detail="Spalte nicht gefunden")
    if ergebnis == "letzte":
        raise HTTPException(status_code=409, detail="Die letzte Spalte kann nicht gelöscht werden")


# -- Label-Verwaltung -----------------------------------------------------

@router.get("/labels", response_model=list[LabelDefinition])
def labels_liste() -> list[LabelDefinition]:
    return db.liste_labels()


@router.post("/labels", response_model=LabelDefinition, status_code=201)
def label_anlegen(eingabe: LabelCreate) -> LabelDefinition:
    name = eingabe.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Der Label-Name darf nicht leer sein")
    label = db.erstelle_label(f"lbl_{uuid4().hex[:8]}", name, eingabe.familie)
    if label is None:
        raise HTTPException(status_code=409, detail="Ein Label mit diesem Namen existiert bereits")
    return label


@router.patch("/labels/{label_id}", response_model=LabelDefinition)
def label_aendern(label_id: str, eingabe: LabelUpdate) -> LabelDefinition:
    try:
        label = db.aktualisiere_label(label_id, eingabe.model_dump(exclude_unset=True))
    except db.LabelNameBelegt:
        raise HTTPException(status_code=409, detail="Ein Label mit diesem Namen existiert bereits")
    if label is None:
        raise HTTPException(status_code=404, detail="Label nicht gefunden")
    return label


@router.delete("/labels/{label_id}", status_code=204)
def label_loeschen(label_id: str) -> None:
    if not db.loesche_label(label_id):
        raise HTTPException(status_code=404, detail="Label nicht gefunden")
