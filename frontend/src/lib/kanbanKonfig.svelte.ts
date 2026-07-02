// Geteilte Kanban-Einstellungen (Ladegrenzen, Karten-Alterung): einmal beim
// App-Start geladen, von Karten/Board gelesen und von den Einstellungen
// aktualisiert - statt hart codierter Schwellen in den Komponenten.
import { ladeKanbanEinstellungen } from './api'

export const kanbanKonfig = $state<{
  fertig_seitengroesse: number
  archiv_tage: number
  aging_amber_tage: number
  aging_rot_tage: number
}>({
  fertig_seitengroesse: 50,
  archiv_tage: 365,
  aging_amber_tage: 4,
  aging_rot_tage: 8,
})

export async function ladeKanbanKonfig(): Promise<void> {
  try {
    Object.assign(kanbanKonfig, await ladeKanbanEinstellungen())
  } catch {
    /* Defaults bleiben */
  }
}
