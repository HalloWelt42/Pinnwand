// Stellt eine gelöschte Karte aus einem Snapshot wieder her (für Rückgängig).
// Wiederhergestellt wird alles, was die Karte selbst trägt (inkl. Notizen,
// Schätzung, Typ und Transkript-Verweis). Zeiteinträge und Dokumente werden
// beim Löschen serverseitig entfernt und kommen NICHT zurück - der Undo-Toast
// benennt das ehrlich.

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
    typ: k.typ ?? 'arbeit',
  })
  const rest: Parameters<typeof aktualisiereKarte>[1] = {}
  if (k.checkliste?.length) rest.checkliste = k.checkliste
  if (k.notizen) rest.notizen = k.notizen
  if (k.schaetzung_min != null) rest.schaetzung_min = k.schaetzung_min
  if (k.transkript_id) {
    rest.transkript_id = k.transkript_id
    rest.transkript_name = k.transkript_name ?? null
  }
  if (Object.keys(rest).length) await aktualisiereKarte(neu.id, rest)
  for (const km of k.kommentare ?? []) await anhaengenKommentar(neu.id, km.autor, km.text)
}

// Dupliziert eine Karte als frische Kopiervorlage: gleiche Inhalte, aber ohne
// Zeiten und Kommentare, Checkliste unerledigt, kein Transkript-Verweis und
// keine Blockade - die Kopie startet sauber.
export async function dupliziereKarte(k: Karte): Promise<Karte> {
  const neu = await erstelleKarte({
    board_id: k.board_id,
    spalte: k.spalte,
    titel: `${k.titel} (Kopie)`,
    beschreibung: k.beschreibung ?? null,
    labels: k.labels,
    prioritaet: k.prioritaet ?? null,
    cover: k.cover ?? null,
    start: k.start ?? null,
    faellig: k.faellig ?? null,
    zustaendig: k.zustaendig ?? null,
    typ: k.typ ?? 'arbeit',
  })
  const rest: Parameters<typeof aktualisiereKarte>[1] = {}
  if (k.checkliste?.length) rest.checkliste = k.checkliste.map((p) => ({ text: p.text, erledigt: false }))
  if (k.notizen) rest.notizen = k.notizen
  if (k.schaetzung_min != null) rest.schaetzung_min = k.schaetzung_min
  if (Object.keys(rest).length) return await aktualisiereKarte(neu.id, rest)
  return neu
}

// Ehrlicher Zusatz fuer den Undo-Toast: was der Undo NICHT zurueckbringt.
export function verlustHinweis(k: Karte): string {
  return (k.erfasst_sek ?? 0) > 0 ? ' - erfasste Zeiten gehen verloren' : ''
}
