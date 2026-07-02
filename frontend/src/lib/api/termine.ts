// HTTP-Aufrufe der Termine (leichte Meeting-Zeiterfassung mit
// Folgetag-Bestätigung): Serien, Instanzen und Materialisierung.

import type { TerminSerie, TerminInstanz } from '../types'
import { hole } from './basis'

export const ladeTerminSerien = (): Promise<TerminSerie[]> => hole('/api/termine/serien')
export const erstelleTerminSerie = (daten: Partial<TerminSerie>): Promise<TerminSerie> =>
  hole('/api/termine/serien', { method: 'POST', body: JSON.stringify(daten) })
export const aktualisiereTerminSerie = (id: string, daten: Partial<TerminSerie>): Promise<TerminSerie> =>
  hole(`/api/termine/serien/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheTerminSerie = (id: string): Promise<void> =>
  hole(`/api/termine/serien/${id}`, { method: 'DELETE' })
export const ladeTerminInstanzen = (p: { status?: string; von?: string; bis?: string; kuerzel?: string | null } = {}): Promise<TerminInstanz[]> => {
  const q = new URLSearchParams()
  if (p.status) q.set('status', p.status)
  if (p.von) q.set('von', p.von)
  if (p.bis) q.set('bis', p.bis)
  if (p.kuerzel) q.set('kuerzel', p.kuerzel)
  const s = q.toString()
  return hole(`/api/termine/instanzen${s ? '?' + s : ''}`)
}
export const termineOffenAnzahl = (): Promise<{ anzahl: number }> => hole('/api/termine/offen/anzahl')
export const bestaetigeTermin = (id: string, dauerMin?: number): Promise<TerminInstanz> =>
  hole(`/api/termine/instanzen/${id}/bestaetigen`, { method: 'POST', body: JSON.stringify({ dauer_min: dauerMin ?? null }) })
export const lehneTerminAb = (id: string): Promise<TerminInstanz> =>
  hole(`/api/termine/instanzen/${id}/ablehnen`, { method: 'POST' })
export const bestaetigeAlleTermine = (ids?: string[]): Promise<{ bestaetigt: number }> =>
  hole('/api/termine/instanzen/bestaetigen-alle', { method: 'POST', body: JSON.stringify({ ids: ids ?? null }) })
export const materialisiereTermine = (): Promise<{ erzeugt: number }> =>
  hole('/api/termine/materialisieren', { method: 'POST' })
