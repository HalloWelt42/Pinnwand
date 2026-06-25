// Geteilte "aktive Person"-Sicht: filtert die sichtbaren Kennzahlen (Stunden-Leiste,
// Tab-Titel) auf eine Person. Leere id = Alle (Team-Gesamt). Pro Browser gemerkt -
// es ist eine reine Anzeige-Auswahl, kein Login.
import { leseText, schreibeText, entferne } from './uiSpeicher'

const SCHLUESSEL = 'pw_aktive_person'

export const personSicht = $state<{ id: string }>({ id: leseText(SCHLUESSEL) })

export function setzePersonSicht(id: string): void {
  personSicht.id = id
  if (id) schreibeText(SCHLUESSEL, id)
  else entferne(SCHLUESSEL)
}

// Identitaet: wurde die eigene Person schon einmal bewusst gewaehlt? (Erstwahl-Prompt)
const GEWAEHLT = 'pw_person_gewaehlt'

// Eigener Zugriff (nicht uiSpeicher): bei nicht verfuegbarem Speicher gilt die
// Identitaet bewusst als gewaehlt, damit der Erstwahl-Prompt nicht bei jedem Laden
// erscheint (uiSpeicher.leseText kann diesen Fehlerfall nicht von "nie gewaehlt" unterscheiden).
export function identitaetGewaehlt(): boolean {
  try {
    return localStorage.getItem(GEWAEHLT) === '1'
  } catch {
    return true
  }
}

export function merkeIdentitaetGewaehlt(): void {
  schreibeText(GEWAEHLT, '1')
}
