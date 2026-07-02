// HTTP-Aufrufe der Serien (wiederkehrende Termine/Aufgaben auf Boards)
// inklusive Vorschau, Vorbuchen und Nachträgen.

import type { Serie, SerienNachtrag, Karte } from '../types'
import { hole } from './basis'

export const ladeSerien = (boardId: string): Promise<Serie[]> => hole(`/api/serien?board_id=${boardId}`)
export const erstelleSerie = (daten: Partial<Serie>): Promise<Serie> =>
  hole('/api/serien', { method: 'POST', body: JSON.stringify(daten) })
export const aktualisiereSerie = (id: string, daten: Partial<Serie>): Promise<Serie> =>
  hole(`/api/serien/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheSerie = (id: string): Promise<void> =>
  hole(`/api/serien/${id}`, { method: 'DELETE' })
export const serieVorschau = (id: string, tage = 30): Promise<{ termine: string[] }> =>
  hole(`/api/serien/${id}/vorschau?tage=${tage}`)
export const serieVorbuchen = (id: string): Promise<{ erzeugt: number }> =>
  hole(`/api/serien/${id}/vorbuchen`, { method: 'POST' })
export const serienVorbuchenAlle = (): Promise<{ erzeugt: number }> =>
  hole('/api/serien/vorbuchen', { method: 'POST' })

export const ladeSerienNachtraege = (): Promise<SerienNachtrag[]> => hole('/api/serien/nachtraege')
export const serieNachtragen = (karteId: string, dauerMin: number): Promise<Karte> =>
  hole(`/api/serien/nachtraege/${karteId}`, { method: 'POST', body: JSON.stringify({ dauer_min: dauerMin }) })
