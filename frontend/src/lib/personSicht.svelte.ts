// Geteilte "aktive Person"-Sicht: filtert die sichtbaren Kennzahlen (Stunden-Leiste,
// Tab-Titel) auf eine Person. Leere id = Alle (Team-Gesamt). Pro Browser gemerkt -
// es ist eine reine Anzeige-Auswahl, kein Login.
const SCHLUESSEL = 'pw_aktive_person'

function ladeId(): string {
  try {
    return localStorage.getItem(SCHLUESSEL) ?? ''
  } catch {
    return ''
  }
}

export const personSicht = $state<{ id: string }>({ id: ladeId() })

export function setzePersonSicht(id: string): void {
  personSicht.id = id
  try {
    if (id) localStorage.setItem(SCHLUESSEL, id)
    else localStorage.removeItem(SCHLUESSEL)
  } catch {
    /* localStorage nicht verfuegbar */
  }
}

// Identitaet: wurde die eigene Person schon einmal bewusst gewaehlt? (Erstwahl-Prompt)
const GEWAEHLT = 'pw_person_gewaehlt'

export function identitaetGewaehlt(): boolean {
  try {
    return localStorage.getItem(GEWAEHLT) === '1'
  } catch {
    return true
  }
}

export function merkeIdentitaetGewaehlt(): void {
  try {
    localStorage.setItem(GEWAEHLT, '1')
  } catch {
    /* localStorage nicht verfuegbar */
  }
}
