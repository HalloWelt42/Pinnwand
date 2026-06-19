// Such-Modul: meldet die Ansicht "Suche" (KI-Freifeld) an.

import { registriereAnsicht } from '../registry'
import Suche from './Suche.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'suche', titel: 'Suche', icon: 'fa-solid fa-magnifying-glass', komponente: Suche })
}
