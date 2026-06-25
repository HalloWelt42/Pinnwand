// Merkt sich das zuletzt gesetzte Zustaendigkeits-Kuerzel im Browser, damit neue
// Karten nicht versehentlich ohne Person angelegt werden. Fallback hinter der
// aktiven Identitaet (personSicht): erst aktive Person, dann dieser Wert.
import { leseText, schreibeText } from './uiSpeicher'

const SCHLUESSEL = 'pw_zuletzt_kuerzel'

export const zuletztKuerzel = $state<{ wert: string }>({ wert: leseText(SCHLUESSEL) })

export function merkeKuerzel(kuerzel: string | null | undefined): void {
  const w = (kuerzel ?? '').trim()
  if (!w) return
  zuletztKuerzel.wert = w
  schreibeText(SCHLUESSEL, w)
}
