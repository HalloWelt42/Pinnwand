// Wischen nach links oder rechts auf einer Fläche (Spalten des Boards am Telefon). Senkrechtes Rollen bleibt dem
// Rollfeld; erst ein deutlich waagerechter Zug zählt.

export interface Wischen {
  links: () => void;
  rechts: () => void;
  /** Mindestweg in Pixeln */
  weg?: number;
}

export function wischen(feld: HTMLElement, w: Wischen) {
  let ziel = w;
  let start: { x: number; y: number } | null = null;
  const runter = (e: PointerEvent): void => { if (e.isPrimary) start = { x: e.clientX, y: e.clientY }; };
  const hoch = (e: PointerEvent): void => {
    if (!start || !e.isPrimary) return;
    const dx = e.clientX - start.x;
    const dy = e.clientY - start.y;
    start = null;
    if (Math.abs(dx) < (ziel.weg ?? 64) || Math.abs(dx) < 2 * Math.abs(dy)) return;
    if (dx < 0) ziel.links();
    else ziel.rechts();
  };
  const ab = (): void => { start = null; };
  feld.addEventListener("pointerdown", runter);
  feld.addEventListener("pointerup", hoch);
  feld.addEventListener("pointercancel", ab);
  return {
    update(neu: Wischen) { ziel = neu; },
    destroy() {
      feld.removeEventListener("pointerdown", runter);
      feld.removeEventListener("pointerup", hoch);
      feld.removeEventListener("pointercancel", ab);
    },
  };
}
