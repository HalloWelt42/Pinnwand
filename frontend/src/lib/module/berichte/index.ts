// Berichte-Modul: meldet die globale Ansicht "Berichte" an.

import { registriereAnsicht } from '../registry'
import Berichte from './Berichte.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'berichte', titel: 'Berichte', icon: 'fa-solid fa-file-pdf', komponente: Berichte })
}
