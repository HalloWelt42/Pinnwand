// Geteilter Navigationswunsch: erlaubt z.B. der Suche, gezielt eine Karte zu
// öffnen. App wechselt zum Board, Board öffnet die Karte und räumt den
// Karten-Teil des Wunsches wieder ab.

export interface NavZiel {
  boardId: string
  karteId?: string
}

export const nav = $state<{ ziel: NavZiel | null }>({ ziel: null })

export function oeffneKarte(boardId: string, karteId?: string): void {
  nav.ziel = { boardId, karteId }
}
