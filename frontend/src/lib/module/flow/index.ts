// Flow-Modul: meldet die boardgebundene Ansicht "Flow" (Boxen mit Verbindungspfaden) an.

import { registriereAnsicht } from '../registry'
import Flow from './Flow.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'flow', titel: 'Flow', icon: 'fa-solid fa-diagram-project', komponente: Flow })
}
