// Anmeldung (echtes Login mit Name/Kuerzel + Passwort). Hier liegt nur der
// reaktive Zustand + der Sitzungs-Token (pro Browser). Die HTTP-Aufrufe und die
// Pflege dieses Zustands liegen in api.ts (eine Richtung: api.ts -> auth, kein Zyklus).
import { leseText, schreibeText, entferne } from './uiSpeicher'

const SCHLUESSEL = 'pw_sitzung'

export const auth = $state<{
  geladen: boolean
  erforderlich: boolean
  angemeldet: boolean
  personId: string | null
  name: string | null
  kuerzel: string | null
  rolle: 'admin' | 'mitarbeiter' | null
}>({
  geladen: false,
  erforderlich: false,
  angemeldet: false,
  personId: null,
  name: null,
  kuerzel: null,
  rolle: null,
})

export function authToken(): string {
  return leseText(SCHLUESSEL)
}

export function setzeAuthToken(t: string): void {
  if (t) schreibeText(SCHLUESSEL, t)
  else entferne(SCHLUESSEL)
}
