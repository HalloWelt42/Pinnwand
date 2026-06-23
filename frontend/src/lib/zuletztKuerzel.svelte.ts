// Merkt sich das zuletzt gesetzte Zustaendigkeits-Kuerzel im Browser, damit neue
// Karten nicht versehentlich ohne Person angelegt werden. Fallback hinter der
// aktiven Identitaet (personSicht): erst aktive Person, dann dieser Wert.
const SCHLUESSEL = 'pw_zuletzt_kuerzel'

function laden(): string {
  try {
    return localStorage.getItem(SCHLUESSEL) ?? ''
  } catch {
    return ''
  }
}

export const zuletztKuerzel = $state<{ wert: string }>({ wert: laden() })

export function merkeKuerzel(kuerzel: string | null | undefined): void {
  const w = (kuerzel ?? '').trim()
  if (!w) return
  zuletztKuerzel.wert = w
  try {
    localStorage.setItem(SCHLUESSEL, w)
  } catch {
    /* localStorage nicht verfuegbar */
  }
}
