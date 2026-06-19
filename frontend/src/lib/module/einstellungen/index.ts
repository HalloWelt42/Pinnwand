// Einstellungen-Modul: meldet die globale Ansicht "Einstellungen" an (u.a. Datensicherung).

import { registriereAnsicht } from '../registry'
import Einstellungen from './Einstellungen.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'einstellungen', titel: 'Einstellungen', icon: 'fa-solid fa-gear', komponente: Einstellungen })
}
