// Datenmodelle der Serien (wiederkehrende Termine/Aufgaben auf Boards).

export interface Serie {
  id: string
  board_id: string
  spalte_id?: string | null
  titel: string
  beschreibung?: string | null
  labels: string[]
  zustaendig?: string | null
  typ: 'taeglich' | 'woechentlich' | 'monatlich'
  intervall: number
  wochentage: number[]
  monatstag?: number | null
  monatsregel?: 'tag' | 'erster_werktag' | 'letzter_werktag'
  uhrzeit?: string | null
  dauer_min?: number | null
  wochenenden_ueberspringen: boolean
  feiertage_ueberspringen?: boolean
  vorlauf_tage: number
  start?: string | null
  ende?: string | null
  aktiv: boolean
}
export interface SerienNachtrag {
  karte_id: string
  schluessel: string | null
  titel: string
  datum: string
  serie_titel: string
  soll_min: number | null
}
