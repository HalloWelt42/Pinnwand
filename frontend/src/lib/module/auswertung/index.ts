// Auswertungs-Modul: meldet die Ansichten "Zeiten" und "Kalender" an.
// Wird von main.ts automatisch entdeckt (Konvention: registriere).

import { registriereAnsicht } from '../registry'
import Zeiten from './Zeiten.svelte'
import Kalender from './Kalender.svelte'
import Jahreskalender from './Jahreskalender.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'zeiten', titel: 'Zeiten', icon: 'fa-solid fa-table-list', komponente: Zeiten })
  registriereAnsicht({ id: 'kalender', titel: 'Kalender', icon: 'fa-solid fa-calendar-days', komponente: Kalender })
  registriereAnsicht({ id: 'jahreskalender', titel: 'Jahreskalender', icon: 'fa-solid fa-calendar', komponente: Jahreskalender })
}
