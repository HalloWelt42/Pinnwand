// Neue Fassung auf dem Server: nie ein hartes Neuladen verlangen.
// Die Startseite kommt ohne Zwischenspeicher, Skripte und Gestaltung tragen Prüfsummen im Namen. Meldet der Server
// eine andere Fassung als die eingebaute, lädt die Seite von selbst neu: in den ersten Sekunden nach dem Start sofort,
// später beim nächsten Ortswechsel (Ansicht, Board, Karte, Zurück/Vor) oder wenn das Fenster wieder nach vorn kommt.
// Nie, solange ein Teil der Oberfläche meldet, dass ein Neuladen etwas abbräche (Vorlesen, Wiedergabe, Aufnahme,
// Hochladen, offener Editor mit ungespeichertem Text, offener Dialog oder Assistent); dann wartet sie bis danach.
// Dazwischen steht ein Band mit Knopf (FassungsBand.svelte). Je Server-Fassung nur ein selbsttätiger Versuch (Merker
// in der Sitzung), damit ein hängender Zwischenspeicher keine Schleife auslöst.
import { SvelteSet } from 'svelte/reactivity'

import { hole } from './api/basis'
import { VERSION } from './version'

const MERKER = 'pinnwand.neu_geladen'
const START_FENSTER_MS = 10_000
const PRUEFEN_MS = 60_000

export const fassung = $state<{ neu: string | null }>({ neu: null })

export type Anlass = 'start' | 'takt' | 'ortswechsel' | 'sichtbar'

// Jeder Teil der Oberfläche meldet hier, ob ein Neuladen gerade etwas abbräche (reaktiv, damit das Band mitzieht).
const taetigkeiten = new SvelteSet<() => boolean>()

/** Meldet eine Prüfung "ist gerade etwas im Gange" an; die Rückgabe meldet sie wieder ab (passt zu onMount). */
export function neuLadenAufhalten(beschaeftigt: () => boolean): () => void {
  taetigkeiten.add(beschaeftigt)
  return () => {
    taetigkeiten.delete(beschaeftigt)
  }
}

/** Nichts, was ein Neuladen abbrechen würde. */
export function ruhig(): boolean {
  for (const beschaeftigt of taetigkeiten) if (beschaeftigt()) return false
  return true
}

function erlaubt(neu: string): boolean {
  try {
    if (sessionStorage.getItem(MERKER) === neu) return false
    sessionStorage.setItem(MERKER, neu)
  } catch {
    // ohne Sitzungsspeicher kein Merker: dann lieber einmal laden als nie
  }
  return true
}

export function vielleichtNeuLaden(anlass: Anlass): void {
  const neu = fassung.neu
  if (!neu || anlass === 'takt' || !ruhig()) return
  if (anlass === 'start' && performance.now() > START_FENSTER_MS) return
  if (erlaubt(neu)) location.reload()
}

export async function fassungPruefen(anlass: Anlass): Promise<void> {
  try {
    const server = (await hole<{ version?: string }>('/api/health')).version
    if (!server) return // älterer Server ohne Fassungsangabe
    fassung.neu = server !== VERSION ? server : null
  } catch {
    return // ohne Verbindung kein Vergleich; der nächste Takt versucht es wieder
  }
  vielleichtNeuLaden(anlass)
}

function sichtbar(): void {
  if (document.visibilityState === 'visible') void fassungPruefen('sichtbar')
}

export function fassungVerfolgen(): () => void {
  void fassungPruefen('start')
  const takt = setInterval(() => void fassungPruefen('takt'), PRUEFEN_MS)
  document.addEventListener('visibilitychange', sichtbar)
  return () => {
    clearInterval(takt)
    document.removeEventListener('visibilitychange', sichtbar)
  }
}
