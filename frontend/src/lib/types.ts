// Spiegelt backend/module/kanban_kern/models.py 1:1. Beide Seiten zusammen pflegen.

export type Prioritaet = 'hoch' | 'mittel' | 'niedrig'

export interface ChecklistPunkt {
  text: string
  erledigt: boolean
}

export interface Kommentar {
  autor: string
  text: string
  zeit: string
}

export interface Karte {
  id: string
  board_id: string
  spalte: string
  titel: string
  schluessel?: string | null
  beschreibung?: string | null
  notizen?: string | null
  labels: string[]
  prioritaet?: Prioritaet | null
  checkliste: ChecklistPunkt[]
  kommentare: Kommentar[]
  cover?: string | null
  reihenfolge: number
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
  erstellt_am?: string | null
  bewegt_am?: string | null
  schaetzung_min?: number | null
  erfasst_sek?: number
  laeuft_seit?: string | null
}

export interface Spalte {
  id: string
  titel: string
  wip_limit?: number | null
  reihenfolge: number
  erledigt?: boolean
}

export interface Board {
  id: string
  mappe_id: string
  titel: string
  kuerzel?: string | null
  spalten: Spalte[]
}

export interface BoardDetail extends Board {
  karten: Karte[]
}

export interface Projektmappe {
  id: string
  titel: string
  beschreibung?: string | null
}

export interface Zeiteintrag {
  id: string
  karte_id: string
  board_id?: string | null
  mappe_id?: string | null
  datum: string
  start?: string | null
  ende?: string | null
  sekunden: number
  kommentar?: string | null
  manuell: boolean
  karte_titel?: string | null
  karte_schluessel?: string | null
}
