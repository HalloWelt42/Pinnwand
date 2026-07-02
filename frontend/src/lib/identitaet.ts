// Die EINE Regel fuer Rolle und Kuerzel der aktiven Identitaet.
// Bei aktivem Login ist die angemeldete Person autoritativ; sonst gilt die
// browser-lokale Personen-Sicht ("Alle" = Admin-Vollsicht, Phase-1-Verhalten).
// Reine Funktionen: die Aufrufer (App, Planung, Board, ...) speisen ihre
// reaktiven Quellen ein und leiten selbst ab - so gibt es keine zweite,
// abweichend driftende Fassung der Regel mehr.

import type { Person } from './types'

interface AuthQuelle {
  erforderlich: boolean
  personId: string | null
  kuerzel: string | null
  rolle: 'admin' | 'mitarbeiter' | null
}

export function aktiveRolle(auth: AuthQuelle, personen: Person[], personSichtId: string): 'admin' | 'mitarbeiter' {
  if (auth.erforderlich) return auth.rolle ?? 'mitarbeiter'
  if (!personSichtId) return 'admin'
  const p = personen.find((x) => x.id === personSichtId)
  return p?.rolle === 'mitarbeiter' ? 'mitarbeiter' : 'admin'
}

export function eigenePersonId(auth: AuthQuelle, personSichtId: string): string | null {
  return auth.erforderlich ? auth.personId : (personSichtId || null)
}

export function eigenesKuerzel(auth: AuthQuelle, personen: Person[], personSichtId: string): string | null {
  if (auth.erforderlich) return auth.kuerzel ?? null
  if (!personSichtId) return null
  return personen.find((p) => p.id === personSichtId)?.kuerzel ?? null
}
