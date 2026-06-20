// Stellt eine gelöschte Karte aus einem Snapshot wieder her (für Rückgängig).

import { erstelleKarte, aktualisiereKarte, anhaengenKommentar } from './api'
import type { Karte } from './types'

export async function neuKarteAus(boardId: string, spalteId: string, k: Karte): Promise<void> {
  const neu = await erstelleKarte({
    board_id: boardId,
    spalte: spalteId,
    titel: k.titel,
    beschreibung: k.beschreibung ?? null,
    labels: k.labels,
    prioritaet: k.prioritaet ?? null,
    cover: k.cover ?? null,
    start: k.start ?? null,
    faellig: k.faellig ?? null,
    zustaendig: k.zustaendig ?? null,
  })
  if (k.checkliste?.length) await aktualisiereKarte(neu.id, { checkliste: k.checkliste })
  for (const km of k.kommentare ?? []) await anhaengenKommentar(neu.id, km.autor, km.text)
}
