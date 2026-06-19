// Geteilter Navigationswunsch: erlaubt z.B. der Suche, gezielt eine Karte zu
// oeffnen. App wechselt zum Board, Board oeffnet die Karte und raeumt den
// Karten-Teil des Wunsches wieder ab.

export interface NavZiel {
  boardId: string
  karteId?: string
}

export const nav = $state<{ ziel: NavZiel | null }>({ ziel: null })

export function oeffneKarte(boardId: string, karteId?: string): void {
  nav.ziel = { boardId, karteId }
}
