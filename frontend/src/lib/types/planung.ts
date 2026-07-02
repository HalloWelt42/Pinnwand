// Datenmodelle der Planung: Personen, Urlaub, Feiertage, Plantage,
// Jahreskalender und Stunden-Übersicht.

export interface Person {
  id: string
  name: string
  kuerzel?: string | null
  farbe?: string | null
  wochenstunden: number[]
  bundesland?: string | null
  urlaubsanspruch: number
  resturlaub_vorjahr: number
  aktiv: boolean
  rolle: 'admin' | 'mitarbeiter'
  hat_passwort?: boolean
}

export interface Urlaubskonto {
  person_id: string
  jahr: number
  anspruch: number
  uebertrag: number
  verfuegbar: number
  genommen: number
  verbleibend: number
  genommen_vorjahr: number
}
export interface Urlaubstag {
  id: string
  person_id: string
  datum: string
  anteil: number
  typ: string
  notiz?: string | null
}
export interface Feiertag {
  datum: string
  name: string
  region?: string | null
}
export interface PlanTag {
  datum: string
  wochenende: boolean
  feiertag: string | null
  urlaub: number
}
export interface WochenOverride { jahr: number; kw: number; wochenstunden: number[] }
export interface Region {
  code: string
  name: string
}
export interface AbwesenheitTyp {
  code: string
  name: string
  farbe: string
  reduziert_soll: boolean
  anrechnen: boolean
  anwesend: boolean
  reihenfolge: number
}
export interface Tagesregel {
  id: string
  person_id: string | null
  art: 'jahrestag' | 'wochentag' | 'brueckentag'
  monat?: number | null
  tag?: number | null
  wochentag?: number | null
  anteil: number
  notiz?: string | null
  aktiv: boolean
}
export interface KalenderZelle {
  soll: number
  ist_sek: number
  abw: { typ: string; anteil: number } | null
  feiertag: string | null
  regel: number | null
  status: 'anwesend' | 'abwesend' | 'frei' | 'feiertag'
}
export interface KalenderAntwort {
  jahr: number
  personen: { id: string; name: string; kuerzel: string | null; farbe: string | null }[]
  tage: string[]
  zellen: Record<string, Record<string, KalenderZelle>>
}
export interface StundenSumme {
  ist_sek: number
  soll_sek: number
}
export interface StundenUebersicht {
  heute: StundenSumme
  woche: StundenSumme
  monat: StundenSumme
  jahr: StundenSumme
}
