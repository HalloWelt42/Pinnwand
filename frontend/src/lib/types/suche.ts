// Datenmodelle der Suche und der Transkript-Anbindung (Treffer, Details,
// Marken und deren Eingaben).

// -- Suche --
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

// -- Transkripte --
export interface TranskriptTreffer {
  id: string
  name: string
  snippet: string
  speaker_names: string[]
  language?: string
  start?: number | null
}
export interface TranskriptDetail {
  id: string
  name: string
  full_text: string
  speaker_names: string[]
  language?: string
  audio_url?: string | null
  segment_count?: number
  segmente?: TranskriptSegment[]
}
export interface TranskriptSegment {
  start: number
  text: string
  speaker?: string | null
}
// Transkript-Marke: verbindet eine Karte mit einer Stelle im Transkript.
export interface TranskriptMarke {
  id: string
  karte_id: string
  transkript_id: string
  transkript_name?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
  titel?: string | null
  zusammenfassung?: string | null
  reihenfolge: number
  erstellt_am?: string | null
  // nur bei marken-je-Transkript mitgeliefert:
  karte_schluessel?: string | null
  karte_titel?: string | null
  karte_board?: string | null
}
export interface MarkeEingabe {
  karte_id: string
  transkript_id: string
  transkript_name?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
  titel?: string | null
  zusammenfassung?: string | null
}
export interface MarkeAenderung {
  titel?: string | null
  zusammenfassung?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
}
