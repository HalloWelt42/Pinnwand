// Transkripte-Modul: meldet die Ansicht "Transkripte" an.

import { registriereAnsicht } from '../registry'
import Transkripte from './Transkripte.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'transkripte', titel: 'Transkripte', icon: 'fa-solid fa-headphones', komponente: Transkripte })
}
