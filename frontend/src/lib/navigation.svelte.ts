// Geteilter Navigationswunsch: erlaubt z.B. der Suche, gezielt eine Karte zu
// öffnen. App wechselt zum Board, Board öffnet die Karte und räumt den
// Karten-Teil des Wunsches wieder ab.

export interface NavZiel {
  boardId: string
  karteId?: string
  schluessel?: string
}

export const nav = $state<{ ziel: NavZiel | null }>({ ziel: null })

export function oeffneKarte(boardId: string, karteId?: string, schluessel?: string): void {
  nav.ziel = { boardId, karteId, schluessel }
}

// Aktuell im Board geoeffnete Karte (fuer tief verlinkbare URLs /board/{id}/{schluessel}).
export const kartenZeiger = $state<{ offen: { boardId: string; schluessel: string } | null }>({ offen: null })

export function setzeOffeneKarte(boardId: string | null, schluessel?: string | null): void {
  kartenZeiger.offen = boardId && schluessel ? { boardId, schluessel } : null
}

// Wunsch, ein bestimmtes Transkript zu oeffnen (z.B. aus einer verknuepften Karte),
// optional an einer Position (Sekunden) - dann wird dorthin gesprungen.
export const transkriptNav = $state<{ id: string | null; positionSek: number | null }>({ id: null, positionSek: null })

export function oeffneTranskript(id: string, positionSek: number | null = null): void {
  transkriptNav.id = id
  transkriptNav.positionSek = positionSek
}
