// Termine-Modul: meldet die globale Ansicht "Wiederkehrendes" an (Serien + Termine
// unter einem Dach, Modus je Eintrag).

import { registriereAnsicht } from '../registry'
import Wiederkehrendes from './Wiederkehrendes.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'wiederkehrendes', titel: 'Wiederkehrendes', icon: 'fa-solid fa-repeat', komponente: Wiederkehrendes })
}
