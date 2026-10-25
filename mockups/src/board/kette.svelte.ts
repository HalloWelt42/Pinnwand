// Kette ziehen (Mechanik M-72): eine eigene Zeigergeste, getrennt vom Ziehen der Karten. Die Kette einer Arbeitskarte
// greifen, auf eine andere Arbeitskarte desselben Boards ziehen und loslassen verknüpft beide über verknuepfen();
// daneben loslassen oder Escape bricht ab. Während der Geste ist die Quelle halbtransparent gestrichelt, eine Marke folgt
// dem Zeiger, eine passende Zielkarte ist hervorgehoben. Nur sichtbare Karten sind Ziel (nicht in eingeklappten Spalten).

import { karte } from "../beispiel/stand.svelte";
import type { Karte, Kennung } from "../modell";

export const kette = $state<{ quelle: Kennung | null; ziel: Kennung | null; x: number; y: number }>({ quelle: null, ziel: null, x: 0, y: 0 });

/** Kann b das Ziel der Kette von a sein? Eine andere Arbeitskarte desselben Boards, noch nicht in derselben Gruppe
 *  (dieselbe Bedingung, unter der verknuepfen() wirkt) */
export function verknuepfbar(a: Karte | undefined, b: Karte | undefined): boolean {
  return !!a && !!b && a.id !== b.id && a.board === b.board && a.art === "arbeit" && b.art === "arbeit" && !(a.gruppe && a.gruppe === b.gruppe);
}

export function ketteStarten(quelle: Kennung, x: number, y: number): void {
  Object.assign(kette, { quelle, ziel: null, x, y });
}

/** Der Zeiger bewegt sich: die Karte unter ihm ist Ziel, wenn sie passt */
export function ketteBewegen(x: number, y: number): void {
  if (!kette.quelle) return;
  kette.x = x;
  kette.y = y;
  const id = (document.elementFromPoint(x, y)?.closest("[data-karte]") as HTMLElement | null)?.dataset.karte;
  kette.ziel = id && verknuepfbar(karte(kette.quelle), karte(id)) ? id : null;
}

/** Loslassen: das Ziel, falls eins passt; die Geste endet in jedem Fall */
export function ketteBeenden(): Kennung | null {
  const ziel = kette.ziel;
  ketteAbbrechen();
  return ziel;
}

export function ketteAbbrechen(): void {
  kette.quelle = null;
  kette.ziel = null;
}
