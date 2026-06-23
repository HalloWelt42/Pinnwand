// Geteilter Zustand des KI-Assistenten: ist das grosse lokale Modell erreichbar
// und welches greift gerade? Damit blendet die Oberflaeche KI-Knoepfe nur ein,
// wenn der Dienst wirklich da ist - KI bleibt die optionale zweite Option.
import { kiStatus, type KiStatusAntwort } from './api'

export const ki = $state<{ verfuegbar: boolean; modell: string | null; geprueft: boolean }>({
  verfuegbar: false,
  modell: null,
  geprueft: false,
})

let laeuft = false

export async function ladeKiStatus(): Promise<void> {
  if (laeuft) return
  laeuft = true
  try {
    const s: KiStatusAntwort = await kiStatus()
    ki.verfuegbar = !!s.verfuegbar
    ki.modell = s.modell ?? null
  } catch {
    ki.verfuegbar = false
    ki.modell = null
  } finally {
    ki.geprueft = true
    laeuft = false
  }
}
