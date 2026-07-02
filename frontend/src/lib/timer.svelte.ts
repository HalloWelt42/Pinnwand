// Geteilter Zeiterfassungs-Zustand: aktive Aufgabe (läuft ODER pausiert) + Live-Uhr.
// Die Leiste oben zeigt die aktive Aufgabe; Pause hält an (Leiste bleibt, Play möglich),
// Stopp beendet die Sitzung und blendet die Leiste aus.

import type { Karte } from './types'
import { ladeLaufend, ladeKarte, timerStart, timerPause } from './api'

export const timer = $state<{ aktiv: Karte | null; jetzt: number; stand: number; kuerzel: string | null }>({
  aktiv: null,
  jetzt: Date.now(),
  stand: 0,
  // Kuerzel der aktiven Identitaet (Timer je Person): App.svelte haelt es aktuell.
  kuerzel: null,
})

let uhrLaeuft = false

export function startUhr(): void {
  if (uhrLaeuft) return
  uhrLaeuft = true
  setInterval(() => {
    timer.jetzt = Date.now()
  }, 1000)
  // Server-Abgleich: ein fremder Browser kann den eigenen Timer gestoppt oder
  // gestartet haben - sonst zaehlt die Leiste optisch weiter, obwohl serverseitig
  // laengst gebucht wurde. Leichtes Intervall plus Abgleich bei Fenster-Fokus.
  setInterval(() => { void aktualisiereLaufend() }, 60_000)
  window.addEventListener('focus', () => { void aktualisiereLaufend() })
}

export async function aktualisiereLaufend(): Promise<void> {
  // Laufende Karte der eigenen Identitaet mit dem Server abgleichen.
  try {
    const l = await ladeLaufend(timer.kuerzel)
    if (l) {
      timer.aktiv = l
    } else if (timer.aktiv?.laeuft_seit) {
      // Lokal laeuft sie noch, serverseitig nicht mehr (Fremd-Stopp): frisch laden,
      // damit die Leiste den pausierten Stand zeigt statt weiterzuzaehlen.
      timer.aktiv = await ladeKarte(timer.aktiv.id).catch(() => null)
      timer.stand++
    }
  } catch {
    /* offline: naechster Abgleich versucht es wieder */
  }
}

export async function timerStarten(id: string): Promise<void> {
  timer.aktiv = await timerStart(id)
  timer.stand++
}

export async function timerPausieren(id: string): Promise<void> {
  // Pausiert, aber bleibt aktiv -> Leiste bleibt sichtbar, Fortsetzen möglich.
  timer.aktiv = await timerPause(id)
  timer.stand++
}

export async function timerStoppen(id: string): Promise<void> {
  await timerPause(id)
  timer.aktiv = null
  timer.stand++
}

export function erfassteSekunden(k: { erfasst_sek?: number | null; laeuft_seit?: string | null }, jetzt: number): number {
  const basis = k.erfasst_sek ?? 0
  if (!k.laeuft_seit) return basis
  const t = new Date(k.laeuft_seit).getTime()
  if (Number.isNaN(t)) return basis
  return basis + Math.max(0, Math.floor((jetzt - t) / 1000))
}

export function formatDauer(sek: number): string {
  const h = Math.floor(sek / 3600)
  const m = Math.floor((sek % 3600) / 60)
  const s = sek % 60
  const zwei = (n: number) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${zwei(m)}:${zwei(s)}` : `${m}:${zwei(s)}`
}

// Immer volles H:MM:SS - sekundengenau und eindeutig rueckuebersetzbar (parseZeit).
// Wird im Karten-Detail genutzt, damit der Wert laufend wie gestoppt identisch aussieht.
export function formatDauerVoll(sek: number): string {
  const h = Math.floor(sek / 3600)
  const m = Math.floor((sek % 3600) / 60)
  const s = sek % 60
  const zwei = (n: number) => String(n).padStart(2, '0')
  return `${h}:${zwei(m)}:${zwei(s)}`
}

// Gegenstueck zu formatDauer/formatDauerVoll: liest "H:MM", "H:MM:SS" oder eine
// Dezimalstunde ("1,5") und liefert Sekunden. null bei leerer/ungueltiger Eingabe.
// Eine zentrale Stelle, damit Karten-Detail und Auswertung identisch parsen.
export function parseZeit(s: string): number | null {
  s = s.trim().replace(',', '.')
  if (!s) return null
  if (s.includes(':')) {
    const [h, m, sek] = s.split(':')
    return (parseInt(h || '0', 10) || 0) * 3600 + (parseInt(m || '0', 10) || 0) * 60 + (parseInt(sek || '0', 10) || 0)
  }
  const std = parseFloat(s)
  return Number.isNaN(std) ? null : Math.round(std * 3600)
}

// Kurze Position als M:SS (ohne Stunden) - fuer Sprechpositionen/Marken im
// Transkript. null/undefined -> leerer String. Zentral, damit Karten-Detail und
// Transkript-Ansicht identisch formatieren.
export function mmss(s?: number | null): string {
  if (s == null) return ''
  const t = Math.max(0, Math.floor(s))
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`
}

export function formatPlan(min: number): string {
  const h = Math.floor(min / 60)
  const m = min % 60
  return h > 0 ? `${h}:${String(m).padStart(2, '0')} Std` : `${m} Min`
}
