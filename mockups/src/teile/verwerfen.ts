// Escape in einem Feld verwirft, was seit dem Betreten getippt wurde, und verlässt das Feld (die alte App übernahm den
// Wert beim Escape, M-125). Das Feld gibt den Fokus an seine Fläche ab, das nächste umgebende Element mit tabindex -1
// (etwa das Kartendetail), damit die Tastatur dort bleibt; ein zweites Escape gilt dann der Fläche.
import type { Action } from "svelte/action";

/** Fokus aus einem Feld in seine Fläche geben, ohne Fläche einfach verlassen */
export function verlassen(feld: HTMLElement): void {
  const flaeche = feld.parentElement?.closest<HTMLElement>('[tabindex="-1"]');
  if (flaeche) flaeche.focus({ preventScroll: true });
  else feld.blur();
}

/** use:verwerfbar an einem Eingabefeld: Escape stellt den Wert beim Betreten wieder her (gebundene Werte ziehen mit) */
export const verwerfbar: Action<HTMLInputElement | HTMLTextAreaElement> = (feld) => {
  let vorher = feld.value;
  const betreten = (): void => { vorher = feld.value; };
  const taste = (e: KeyboardEvent): void => {
    if (e.key !== "Escape" || e.isComposing) return;
    e.preventDefault();
    if (feld.value !== vorher) {
      feld.value = vorher;
      feld.dispatchEvent(new Event("input", { bubbles: true }));
    }
    verlassen(feld);
  };
  const el: HTMLElement = feld;
  el.addEventListener("focus", betreten);
  el.addEventListener("keydown", taste);
  return {
    destroy() {
      el.removeEventListener("focus", betreten);
      el.removeEventListener("keydown", taste);
    },
  };
};
