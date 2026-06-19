// Planung-Modul: meldet die globale Ansicht "Planung" an.

import { registriereAnsicht } from '../registry'
import Planung from './Planung.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'planung', titel: 'Planung', icon: 'fa-solid fa-users', komponente: Planung })
}
