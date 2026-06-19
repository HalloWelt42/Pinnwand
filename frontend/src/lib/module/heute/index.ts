// Heute-Modul: meldet die globale Ansicht "Heute" (Was steht an) an.

import { registriereAnsicht } from '../registry'
import Heute from './Heute.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'heute', titel: 'Heute', icon: 'fa-solid fa-bolt', komponente: Heute })
}
