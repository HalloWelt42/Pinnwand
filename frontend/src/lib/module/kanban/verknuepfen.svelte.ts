// Zustand der Karten-Kopplung per Ziehen.
//
// Bewusst eine EIGENE Pointer-Geste statt nativem HTML5-Drag: Letzteres ist aus einem
// Button heraus und innerhalb einer svelte-dnd-action-Zone unzuverlaessig (die Lib setzt
// draggable=false/ondragstart=()=>false auf die Items). Pointer-Events sind robust,
// liefern klare visuelle Rueckmeldung und laufen getrennt vom Reorder (der mousedown
// nutzt - den der Griff stoppt).
//
// quelle = gerade gezogene Karte, ueber = aktuelle Zielkarte unter dem Zeiger,
// x/y = Zeigerposition fuer die schwebende Anzeige.
export const koppeln = $state<{ quelle: string | null; ueber: string | null; x: number; y: number }>({
  quelle: null,
  ueber: null,
  x: 0,
  y: 0,
})

export function koppelnStart(id: string, x: number, y: number): void {
  koppeln.quelle = id
  koppeln.ueber = null
  koppeln.x = x
  koppeln.y = y
}

export function koppelnBeenden(): void {
  koppeln.quelle = null
  koppeln.ueber = null
}
