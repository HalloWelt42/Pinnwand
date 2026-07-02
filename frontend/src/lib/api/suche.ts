// HTTP-Aufrufe der Suche und der Transkript-Anbindung: Volltext-/Vektor-Suche,
// Spracheingabe, Transkript-Details, Marken und Arbeitspool.

import type {
  SuchErgebnis,
  SuchStatus,
  TranskriptTreffer,
  TranskriptDetail,
  TranskriptMarke,
  MarkeEingabe,
  MarkeAenderung,
} from '../types'
import { BASIS, hole, authKopf } from './basis'

// --- Suche ---

export const sucheInhalte = (q: string, limit = 15): Promise<SuchErgebnis> =>
  hole(`/api/suche?q=${encodeURIComponent(q)}&limit=${limit}`)

export const sucheStatus = (): Promise<SuchStatus> => hole('/api/suche/status')

export async function transkribiere(audio: Blob): Promise<{ text: string }> {
  const daten = new FormData()
  daten.append('datei', audio, 'aufnahme.webm')
  const antwort = await fetch(`${BASIS}/api/suche/sprache`, { method: 'POST', headers: authKopf(), body: daten })
  if (!antwort.ok) throw new Error('Spracheingabe nicht verfügbar')
  return antwort.json()
}

// --- Transkripte ---

export const transkripteStatus = (): Promise<{ erreichbar: boolean; konfiguriert: boolean }> =>
  hole('/api/transkripte/status')
export const transkripteSuche = (q: string, limit = 30): Promise<{ treffer: TranskriptTreffer[] }> =>
  hole(`/api/transkripte/suche?q=${encodeURIComponent(q)}&limit=${limit}`)
export const transkriptDetail = (id: string): Promise<TranskriptDetail> =>
  hole(`/api/transkripte/${id}`)

export const ladeMarken = (karteId: string): Promise<{ marken: TranskriptMarke[] }> =>
  hole(`/api/transkripte/marken?karte_id=${encodeURIComponent(karteId)}`)
export const markenJeTranskript = (tid: string): Promise<{ marken: TranskriptMarke[] }> =>
  hole(`/api/transkripte/${tid}/marken`)
export const erstelleMarke = (eingabe: MarkeEingabe): Promise<TranskriptMarke> =>
  hole('/api/transkripte/marken', { method: 'POST', body: JSON.stringify(eingabe) })
export const aktualisiereMarke = (id: string, daten: MarkeAenderung): Promise<TranskriptMarke> =>
  hole(`/api/transkripte/marken/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheMarke = (id: string): Promise<void> =>
  hole(`/api/transkripte/marken/${id}`, { method: 'DELETE' })
export const zusammenfassungVorschlag = (transkriptId: string, positionSek: number | null): Promise<{ zusammenfassung: string }> =>
  hole('/api/transkripte/zusammenfassung-vorschlag', { method: 'POST', body: JSON.stringify({ transkript_id: transkriptId, position_sek: positionSek }) })

// Arbeitspool: ausgewaehlte, fuer die Arbeit relevante Transkripte (Vorfilter).
export const ladePool = (): Promise<{ pool: { transkript_id: string; transkript_name?: string | null }[] }> =>
  hole('/api/transkripte/pool')
export const poolAufnehmen = (transkriptId: string, name: string | null): Promise<{ ok: boolean }> =>
  hole('/api/transkripte/pool', { method: 'POST', body: JSON.stringify({ transkript_id: transkriptId, transkript_name: name }) })
export const poolEntfernen = (transkriptId: string): Promise<void> =>
  hole(`/api/transkripte/pool/${encodeURIComponent(transkriptId)}`, { method: 'DELETE' })
