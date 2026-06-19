"""Aufbau des semantischen Index aus dem Kartenbestand.

Indiziert pro Karte: Titel, Beschreibung, Labels, Checklistentexte, Kommentare
und die Kommentare der Zeiteintraege. Voll neu aufbaubar (reindex) und einzeln
aktualisierbar (index_eine). Ohne Embeddings/Vektor-DB tut es nichts (no-op).
"""
from __future__ import annotations

import json
import uuid

from app.db import verbindung

from . import embeddings, vektor

_NS = uuid.UUID("8f4a1e2c-0000-4000-8000-000000000001")


def _punkt_id(karte_id: str) -> str:
    return str(uuid.uuid5(_NS, karte_id))


def _text_einer(row) -> str:
    teile = [row["titel"] or "", row["beschreibung"] or "", row["schluessel"] or ""]
    try:
        teile += json.loads(row["labels"] or "[]")
    except Exception:
        pass
    try:
        teile += [c.get("text", "") for c in json.loads(row["checkliste"] or "[]")]
    except Exception:
        pass
    try:
        teile += [k.get("text", "") for k in json.loads(row["kommentare"] or "[]")]
    except Exception:
        pass
    return "\n".join(t for t in teile if t).strip()


def _zeitkommentare(conn, karte_id: str) -> str:
    rows = conn.execute(
        "SELECT kommentar FROM zeiteintrag WHERE karte_id = ? AND kommentar IS NOT NULL AND kommentar != ''",
        (karte_id,),
    ).fetchall()
    return "\n".join(r["kommentar"] for r in rows)


def _karten_dokumente(karte_id: str | None = None) -> list[dict]:
    with verbindung() as conn:
        if karte_id:
            rows = conn.execute("SELECT * FROM karte WHERE id = ?", (karte_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM karte").fetchall()
        docs = []
        for r in rows:
            text = _text_einer(r)
            zk = _zeitkommentare(conn, r["id"])
            if zk:
                text = f"{text}\n{zk}".strip()
            if not text:
                continue
            docs.append({
                "karte_id": r["id"],
                "text": text,
                "payload": {
                    "karte_id": r["id"], "board_id": r["board_id"],
                    "schluessel": r["schluessel"], "titel": r["titel"],
                },
            })
    return docs


def reindex() -> dict:
    """Baut den gesamten Index neu auf. No-op (ok=False), wenn KI-Dienste fehlen."""
    if not embeddings.verfuegbar() or not vektor.verfuegbar():
        return {"ok": False, "grund": "Embeddings oder Vektor-DB nicht konfiguriert", "anzahl": 0}
    docs = _karten_dokumente()
    if not docs:
        return {"ok": True, "anzahl": 0}
    eingebettet = embeddings.einbetten([d["text"] for d in docs])
    if eingebettet is None:
        return {"ok": False, "grund": "Embedding fehlgeschlagen", "anzahl": 0}
    vektoren, modell = eingebettet
    if not vektor.sicherstellen_collection(len(vektoren[0])):
        return {"ok": False, "grund": "Qdrant nicht erreichbar", "anzahl": 0}
    punkte = [
        {"id": _punkt_id(d["karte_id"]), "vector": v, "payload": d["payload"]}
        for d, v in zip(docs, vektoren)
    ]
    if not vektor.upsert(punkte):
        return {"ok": False, "grund": "Upsert fehlgeschlagen", "anzahl": 0}
    return {"ok": True, "anzahl": len(punkte), "modell": modell}


def index_eine(karte_id: str) -> bool:
    """Aktualisiert den Index fuer eine Karte. Still, wenn KI-Dienste fehlen."""
    if not embeddings.verfuegbar() or not vektor.verfuegbar():
        return False
    docs = _karten_dokumente(karte_id)
    if not docs:
        return False
    eingebettet = embeddings.einbetten([docs[0]["text"]])
    if eingebettet is None:
        return False
    vektoren, _ = eingebettet
    if not vektor.sicherstellen_collection(len(vektoren[0])):
        return False
    return vektor.upsert([{"id": _punkt_id(karte_id), "vector": vektoren[0], "payload": docs[0]["payload"]}])
