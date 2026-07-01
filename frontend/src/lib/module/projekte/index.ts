// Projekte-Modul: meldet die globale Ansicht "Projekte" an (Mappe = Projekt).
// Zeigt den Aufwand je Projekt (Ist/Soll/Budget) mit Aufschluesselung je Phase/Person.

import { registriereAnsicht } from '../registry'
import Projekte from './Projekte.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'projekte', titel: 'Projekte', icon: 'fa-solid fa-diagram-project', komponente: Projekte })
}
