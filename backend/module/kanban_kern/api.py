"""HTTP-Schnittstelle des Kanban-Moduls."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from . import persistence as db
from .models import (
    Board,
    BoardCreate,
    BoardDetail,
    BoardUpdate,
    Karte,
    KarteCreate,
    KarteMove,
    KarteUpdate,
    KommentarCreate,
    Projektmappe,
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


@router.get("/mappen", response_model=list[Projektmappe])
def mappen() -> list[Projektmappe]:
    return db.liste_mappen()


@router.get("/mappen/{mappe_id}/boards", response_model=list[Board])
def boards(mappe_id: str) -> list[Board]:
    return db.liste_boards(mappe_id)


@router.get("/boards/{board_id}", response_model=BoardDetail)
def board(board_id: str) -> BoardDetail:
    detail = db.board_detail(board_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Board nicht gefunden")
    return detail


@router.get("/heute")
def heute(datum: str | None = None) -> dict:
    from datetime import date

    return db.was_steht_an(datum or date.today().isoformat())


@router.get("/boards/{board_id}/flow")
def flow_graph(board_id: str) -> dict:
    """Abhaengigkeitsgraph des Boards: Schichten, kritischer Pfad, Zyklen, Status."""
    detail = db.board_detail(board_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Board nicht gefunden")
    from . import graph

    return graph.berechne(detail)


# -- Karten ---------------------------------------------------------------

@router.post("/karten", response_model=Karte, status_code=201)
def karte_anlegen(eingabe: KarteCreate) -> Karte:
    return db.erstelle_karte(
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
    )


@router.patch("/karten/{karte_id}", response_model=Karte)
def karte_aendern(karte_id: str, eingabe: KarteUpdate) -> Karte:
    karte = db.aktualisiere_karte(karte_id, eingabe.model_dump(exclude_unset=True, mode="json"))
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
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
    return karte


@router.delete("/karten/{karte_id}", status_code=204)
def karte_loeschen(karte_id: str) -> None:
    db.loesche_karte(karte_id)


# -- Zeiterfassung --------------------------------------------------------

@router.get("/laufend", response_model=Karte | None)
def laufend() -> Karte | None:
    return db.laufende_karte()


@router.post("/karten/{karte_id}/timer/start", response_model=Karte)
def timer_start(karte_id: str) -> Karte:
    karte = db.timer_start(karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


@router.post("/karten/{karte_id}/timer/pause", response_model=Karte)
def timer_pause(karte_id: str) -> Karte:
    karte = db.timer_pause(karte_id)
    if karte is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return karte


# -- Zeiteintraege (Auswertung / Korrektur) -------------------------------

@router.get("/zeiteintraege", response_model=list[Zeiteintrag])
def zeiteintraege(von: str, bis: str) -> list[Zeiteintrag]:
    return db.zeiteintraege_range(von, bis)


@router.post("/zeiteintraege", response_model=Zeiteintrag, status_code=201)
def zeiteintrag_anlegen(eingabe: ZeiteintragCreate) -> Zeiteintrag:
    eintrag = db.erstelle_zeiteintrag(f"z_{uuid4().hex[:8]}", eingabe.karte_id, eingabe.datum, eingabe.sekunden, eingabe.kommentar)
    if eintrag is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    return eintrag


@router.patch("/zeiteintraege/{eintrag_id}", response_model=Zeiteintrag)
def zeiteintrag_aendern(eintrag_id: str, eingabe: ZeiteintragUpdate) -> Zeiteintrag:
    eintrag = db.aktualisiere_zeiteintrag(eintrag_id, eingabe.model_dump(exclude_unset=True))
    if eintrag is None:
        raise HTTPException(status_code=404, detail="Zeiteintrag nicht gefunden")
    return eintrag


@router.delete("/zeiteintraege/{eintrag_id}", status_code=204)
def zeiteintrag_loeschen(eintrag_id: str) -> None:
    if not db.loesche_zeiteintrag(eintrag_id):
        raise HTTPException(status_code=404, detail="Zeiteintrag nicht gefunden")


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
        raise HTTPException(status_code=409, detail="Die letzte Spalte kann nicht geloescht werden")
