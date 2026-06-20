// Termine-Modul: meldet die globale Ansicht "Termine" an (Meeting-Zeiterfassung).

import { registriereAnsicht } from '../registry'
import Termine from './Termine.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'termine', titel: 'Termine', icon: 'fa-solid fa-calendar-check', komponente: Termine })
}
