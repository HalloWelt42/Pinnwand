// Serien-Modul: meldet die Ansicht "Serien" an (boardgebunden).

import { registriereAnsicht } from '../registry'
import Serien from './Serien.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'serien', titel: 'Serien', icon: 'fa-solid fa-repeat', komponente: Serien })
}
