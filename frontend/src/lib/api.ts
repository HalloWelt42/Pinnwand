// HTTP-Client zum Pinnwand-Backend.

import type { Board, BoardDetail, ChecklistPunkt, Karte, Prioritaet, Projektmappe, Spalte, Zeiteintrag } from './types'

const BASIS = import.meta.env.VITE_API ?? 'http://localhost:8420'

async function hole<T>(pfad: string, init?: RequestInit): Promise<T> {
  const antwort = await fetch(`${BASIS}${pfad}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!antwort.ok) throw new Error(`Anfrage fehlgeschlagen: ${antwort.status} ${antwort.statusText}`)
  if (antwort.status === 204) return undefined as T
  return (await antwort.json()) as T
}

export interface AnsichtMeta {
  id: string
  titel: string
  icon: string
}
export interface Erweiterungen {
  views: { modul: string; wert: AnsichtMeta }[]
  cardFields: { modul: string; wert: unknown }[]
  mappeTabs: { modul: string; wert: unknown }[]
  commands: { modul: string; wert: unknown }[]
}

export const ladeErweiterungen = (): Promise<Erweiterungen> => hole('/api/erweiterungen')
export const ladeMappen = (): Promise<Projektmappe[]> => hole('/api/kanban/mappen')
export const ladeBoards = (mappeId: string): Promise<Board[]> => hole(`/api/kanban/mappen/${mappeId}/boards`)
export const ladeBoard = (boardId: string): Promise<BoardDetail> => hole(`/api/kanban/boards/${boardId}`)

// --- Karten ---

export interface KarteEingabe {
  board_id: string
  spalte: string
  titel: string
  beschreibung?: string | null
  labels?: string[]
  prioritaet?: Prioritaet | null
  cover?: string | null
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
}

export const erstelleKarte = (eingabe: KarteEingabe): Promise<Karte> =>
  hole('/api/kanban/karten', { method: 'POST', body: JSON.stringify(eingabe) })

export interface KarteAenderung {
  titel?: string
  beschreibung?: string | null
  labels?: string[]
  prioritaet?: Prioritaet | null
  checkliste?: ChecklistPunkt[]
  cover?: string | null
  spalte?: string
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
  schaetzung_min?: number | null
}

export const aktualisiereKarte = (id: string, daten: KarteAenderung): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const verschiebeKarte = (id: string, spalte: string, reihenfolge: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/move`, { method: 'POST', body: JSON.stringify({ spalte, reihenfolge }) })

export const anhaengenKommentar = (id: string, autor: string, text: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/kommentare`, { method: 'POST', body: JSON.stringify({ autor, text }) })

export const loescheKarte = (id: string): Promise<void> =>
  hole(`/api/kanban/karten/${id}`, { method: 'DELETE' })

// --- Zeiterfassung ---

export const ladeLaufend = (): Promise<Karte | null> => hole('/api/kanban/laufend')

export const timerStart = (id: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/timer/start`, { method: 'POST' })

export const timerPause = (id: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/timer/pause`, { method: 'POST' })

// --- Zeiteintraege (Auswertung) ---

export const ladeZeiteintraege = (von: string, bis: string): Promise<Zeiteintrag[]> =>
  hole(`/api/kanban/zeiteintraege?von=${von}&bis=${bis}`)

export const erstelleZeiteintrag = (eingabe: { karte_id: string; datum: string; sekunden: number; kommentar?: string | null }): Promise<Zeiteintrag> =>
  hole('/api/kanban/zeiteintraege', { method: 'POST', body: JSON.stringify(eingabe) })

export const aktualisiereZeiteintrag = (id: string, daten: { datum?: string; sekunden?: number; kommentar?: string | null }): Promise<Zeiteintrag> =>
  hole(`/api/kanban/zeiteintraege/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const loescheZeiteintrag = (id: string): Promise<void> =>
  hole(`/api/kanban/zeiteintraege/${id}`, { method: 'DELETE' })

// --- Boards ---

export const erstelleBoard = (mappeId: string, titel: string): Promise<BoardDetail> =>
  hole(`/api/kanban/mappen/${mappeId}/boards`, { method: 'POST', body: JSON.stringify({ titel }) })

export const benenneBoard = (boardId: string, titel: string): Promise<Board> =>
  hole(`/api/kanban/boards/${boardId}`, { method: 'PATCH', body: JSON.stringify({ titel }) })

export const loescheBoard = (boardId: string): Promise<void> =>
  hole(`/api/kanban/boards/${boardId}`, { method: 'DELETE' })

export const setzeSpaltenReihenfolge = (boardId: string, spalten: string[]): Promise<void> =>
  hole(`/api/kanban/boards/${boardId}/spalten-reihenfolge`, { method: 'PATCH', body: JSON.stringify({ spalten }) })

// --- Spalten ---

export const erstelleSpalte = (boardId: string, titel: string, wipLimit: number | null = null): Promise<Spalte> =>
  hole(`/api/kanban/boards/${boardId}/spalten`, { method: 'POST', body: JSON.stringify({ titel, wip_limit: wipLimit }) })

export const aktualisiereSpalte = (spalteId: string, daten: { titel?: string; wip_limit?: number | null }): Promise<Spalte> =>
  hole(`/api/kanban/spalten/${spalteId}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const verschiebeSpalte = (spalteId: string, richtung: -1 | 1): Promise<Spalte> =>
  hole(`/api/kanban/spalten/${spalteId}/move`, { method: 'POST', body: JSON.stringify({ richtung }) })

export const loescheSpalte = (spalteId: string): Promise<void> =>
  hole(`/api/kanban/spalten/${spalteId}`, { method: 'DELETE' })

// --- Suche ---

export interface SuchTreffer {
  karte_id: string
  schluessel: string | null
  titel: string
  board_id?: string
  spalte?: string
  score?: number
  quelle: string
}
export interface SuchErgebnis {
  treffer: SuchTreffer[]
  anzahl: number
  modus: string
}
export interface SuchStatus {
  embeddings: boolean
  vektor_konfiguriert: boolean
  vektor_erreichbar: boolean
  mikrofon: boolean
  modus: string
}

export const sucheInhalte = (q: string, limit = 15): Promise<SuchErgebnis> =>
  hole(`/api/suche?q=${encodeURIComponent(q)}&limit=${limit}`)

export const sucheStatus = (): Promise<SuchStatus> => hole('/api/suche/status')

export async function transkribiere(audio: Blob): Promise<{ text: string }> {
  const daten = new FormData()
  daten.append('datei', audio, 'aufnahme.webm')
  const antwort = await fetch(`${BASIS}/api/suche/sprache`, { method: 'POST', body: daten })
  if (!antwort.ok) throw new Error('Spracheingabe nicht verfuegbar')
  return antwort.json()
}

// --- Vorlesen (TTS) ---

export const ttsStatus = (): Promise<{ verfuegbar: boolean }> => hole('/api/tts/status')

export interface Dienst {
  schluessel: string
  name: string
  konfiguriert: boolean
  erreichbar: boolean
}
export const ladeDienste = (): Promise<{ bind: string; dienste: Dienst[] }> => hole('/api/dienste')

export interface Stimmen {
  model?: string
  speakers?: string[]
  custom?: { id: string; name: string }[]
}
export const ttsStimmen = (): Promise<{ stimmen: Stimmen | [] }> => hole('/api/tts/stimmen')

export async function vorleseAudio(text: string, stimme?: string): Promise<Blob> {
  const antwort = await fetch(`${BASIS}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, stimme }),
  })
  if (!antwort.ok) throw new Error('Vorlesen nicht verfuegbar')
  return antwort.blob()
}
