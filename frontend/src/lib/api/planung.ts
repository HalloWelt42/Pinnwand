// HTTP-Aufrufe der Planung: Personen, Urlaub, Feiertage, Plantage,
// Jahreskalender (Abwesenheitsarten, Tagesregeln) und Stunden-Übersicht.

import type {
  Person,
  Urlaubskonto,
  Urlaubstag,
  Feiertag,
  PlanTag,
  WochenOverride,
  Region,
  AbwesenheitTyp,
  Tagesregel,
  KalenderAntwort,
  StundenUebersicht,
} from '../types'
import { hole } from './basis'

export const ladePersonen = (): Promise<Person[]> => hole('/api/planung/personen')
export const ladeUrlaubskonten = (jahr: number): Promise<Urlaubskonto[]> =>
  hole(`/api/planung/urlaubskonten?jahr=${jahr}`)
export const erstellePerson = (d: Partial<Person>): Promise<Person> =>
  hole('/api/planung/personen', { method: 'POST', body: JSON.stringify(d) })
export const aktualisierePerson = (id: string, d: Partial<Person>): Promise<Person> =>
  hole(`/api/planung/personen/${id}`, { method: 'PATCH', body: JSON.stringify(d) })
export const loeschePerson = (id: string): Promise<void> =>
  hole(`/api/planung/personen/${id}`, { method: 'DELETE' })

export const ladeWochenOverride = (personId: string): Promise<WochenOverride[]> =>
  hole(`/api/planung/personen/${personId}/wochen-override`)
export const setzeWochenOverride = (personId: string, jahr: number, kw: number, wochenstunden: number[]): Promise<WochenOverride> =>
  hole(`/api/planung/personen/${personId}/wochen-override`, { method: 'POST', body: JSON.stringify({ jahr, kw, wochenstunden }) })
export const loescheWochenOverride = (personId: string, jahr: number, kw: number): Promise<void> =>
  hole(`/api/planung/personen/${personId}/wochen-override/${jahr}/${kw}`, { method: 'DELETE' })

export const ladeUrlaub = (person: string, von: string, bis: string): Promise<Urlaubstag[]> =>
  hole(`/api/planung/urlaub?person=${person}&von=${von}&bis=${bis}`)
export const setzeUrlaub = (d: { person_id: string; von: string; bis?: string; anteil?: number; typ?: string; notiz?: string; wochenenden_ueberspringen?: boolean; feiertage_ueberspringen?: boolean }): Promise<{ gesetzt: number; uebersprungen: number }> =>
  hole('/api/planung/urlaub', { method: 'POST', body: JSON.stringify(d) })
export const loescheUrlaub = (id: string): Promise<void> =>
  hole(`/api/planung/urlaub/${id}`, { method: 'DELETE' })

export const ladeLaender = (): Promise<{ verfuegbar: boolean; laender: Record<string, Region[]> }> =>
  hole('/api/planung/laender')
export const ladeFeiertage = (von: string, bis: string): Promise<Feiertag[]> =>
  hole(`/api/planung/feiertage?von=${von}&bis=${bis}`)
export const feiertageVorschau = (land: string, region: string | null, jahr: number): Promise<{ eintraege: Feiertag[] }> =>
  hole(`/api/planung/feiertage/vorschau?land=${land}&jahr=${jahr}${region ? `&region=${region}` : ''}`)
export const feiertageUebernehmen = (land: string, region: string | null, jahr: number): Promise<{ uebernommen: number }> =>
  hole('/api/planung/feiertage/uebernehmen', { method: 'POST', body: JSON.stringify({ land, region, jahr }) })
export const loescheFeiertage = (jahr: number, region: string | null): Promise<{ geloescht: number }> =>
  hole(`/api/planung/feiertage?jahr=${jahr}${region ? `&region=${region}` : ''}`, { method: 'DELETE' })

export const ladePlanungsTage = (von: string, bis: string, person?: string): Promise<PlanTag[]> =>
  hole(`/api/planung/tage?von=${von}&bis=${bis}${person ? `&person=${person}` : ''}`)

// --- Jahreskalender: Abwesenheitsarten, Tagesregeln, Aggregation ---

export const ladeKalender = (jahr: number): Promise<KalenderAntwort> =>
  hole(`/api/planung/kalender?jahr=${jahr}`)

export const ladeStundenUebersicht = (personId?: string): Promise<StundenUebersicht> =>
  hole(`/api/planung/stunden-uebersicht${personId ? `?person=${encodeURIComponent(personId)}` : ''}`)
export const ladeAbwesenheitstypen = (): Promise<AbwesenheitTyp[]> =>
  hole('/api/planung/abwesenheitstypen')
export const aktualisiereAbwesenheitstyp = (code: string, d: Partial<AbwesenheitTyp>): Promise<AbwesenheitTyp> =>
  hole(`/api/planung/abwesenheitstypen/${code}`, { method: 'PATCH', body: JSON.stringify(d) })
export const ladeTagesregeln = (person?: string): Promise<Tagesregel[]> =>
  hole(`/api/planung/tagesregeln${person ? `?person=${person}` : ''}`)
export const setzeTagesregel = (d: Partial<Tagesregel>): Promise<Tagesregel> =>
  hole('/api/planung/tagesregeln', { method: 'POST', body: JSON.stringify(d) })
export const loescheTagesregel = (id: string): Promise<void> =>
  hole(`/api/planung/tagesregeln/${id}`, { method: 'DELETE' })
export const leereTag = (person_id: string, datum: string): Promise<{ geloescht: number }> =>
  hole('/api/planung/tag-leeren', { method: 'POST', body: JSON.stringify({ person_id, datum }) })
