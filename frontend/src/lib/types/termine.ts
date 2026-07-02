// Datenmodelle der Termine (leichte Meeting-Zeiterfassung mit Bestätigung).

export interface TerminSerie {
  id: string
  titel: string
  beschreibung?: string | null
  kuerzel?: string | null
  typ: 'taeglich' | 'woechentlich' | 'monatlich'
  intervall: number
  wochentage: number[]
  monatstag?: number | null
  monatsregel?: 'tag' | 'erster_werktag' | 'letzter_werktag'
  uhrzeit?: string | null
  dauer_min: number
  wochenenden_ueberspringen: boolean
  feiertage_ueberspringen: boolean
  urlaub_ueberspringen: boolean
  rueckblick_tage: number
  start?: string | null
  ende?: string | null
  aktiv: boolean
}
export interface TerminInstanz {
  id: string
  serie_id: string
  datum: string
  kuerzel?: string | null
  titel: string
  uhrzeit?: string | null
  geplant_min: number
  status: 'schwebend' | 'bestaetigt' | 'abgelehnt'
  effektiv_min?: number | null
  bestaetigt_am?: string | null
}
