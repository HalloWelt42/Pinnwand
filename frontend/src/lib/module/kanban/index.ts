// Kanban-Kern (Frontend-Seite): meldet die Board-Ansicht an.
// Wird von main.ts automatisch entdeckt und aufgerufen (Konvention: registriere).

import { registriereAnsicht } from '../registry'
import Board from './Board.svelte'

export function registriere(): void {
  registriereAnsicht({
    id: 'board',
    titel: 'Board',
    icon: 'fa-solid fa-table-columns',
    komponente: Board,
  })
}
