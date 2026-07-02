// Routing ohne Hashes: echte Pfade /ansicht bzw. /ansicht/boardId/kartenSchluessel.
// Den Zustand (aktive Ansicht, aktives Board) hält die App; dieses Modul kapselt
// das Lesen/Schreiben des Browser-Standorts und das Zerlegen von Deep-Links.

import { kartenZeiger, oeffneKarte } from './navigation.svelte'

// Startpfad frühzeitig sichern (bevor Effekte die URL anfassen können).
export const startPfad = typeof window !== 'undefined' ? window.location.pathname : '/'

// Erst nach dem Anwenden des Start-Deep-Links darf in die History geschrieben
// werden; die App schaltet das Routing nach dem Laden scharf.
export const routing = $state({ bereit: false })

// Aus einem Pfad gelesenes Ziel; die App prüft die Gültigkeit und wendet es
// auf ihren Zustand an.
export interface RoutenZiel {
  ansicht: string | null
  boardId: string | null
}

// Pfad aus dem App-Zustand bauen; eine offene Karte wandert als dritter Teil mit.
export function pfadAusZustand(ansicht: string, boardgebunden: boolean, boardId: string | null): string {
  if (!ansicht) return '/'
  if (!boardgebunden || !boardId) return `/${ansicht}`
  const k = kartenZeiger.offen
  const kartenTeil = k && k.boardId === boardId ? `/${encodeURIComponent(k.schluessel)}` : ''
  return `/${ansicht}/${boardId}${kartenTeil}`
}

// Pfad zerlegen: Ansicht/Board zurückmelden; ein Karten-Schlüssel wird direkt
// als Navigationswunsch hinterlegt (das Board öffnet die Karte anhand des Schlüssels).
export function zerlegePfad(pfad: string): RoutenZiel {
  const [ansicht, boardId, kartenSchluessel] = pfad.split('/').filter(Boolean)
  if (boardId && kartenSchluessel) oeffneKarte(boardId, undefined, decodeURIComponent(kartenSchluessel))
  return { ansicht: ansicht ?? null, boardId: boardId ?? null }
}

// Pfad in die History schreiben (nur bei scharfem Routing und echter Änderung).
export function schreibePfad(pfad: string): void {
  if (!routing.bereit) return
  if (typeof window !== 'undefined' && window.location.pathname !== pfad) {
    window.history.pushState(null, '', pfad)
  }
}

// Zurück/Vor im Browser: den dann aktuellen Pfad wieder auf den Zustand anwenden.
export function beobachteStandort(anwenden: (pfad: string) => void): void {
  window.addEventListener('popstate', () => anwenden(window.location.pathname))
}
