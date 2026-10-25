// Ziehen im Board: Während eines Zugs steht in der Liste einer Ablagezone ein Schatten an der Stelle, an der das
// Gezogene landen würde. Die Bibliothek blendet sein Element aus; das Board zeigt darin einen gestrichelten Platzhalter.

import { SHADOW_ITEM_MARKER_PROPERTY_NAME } from "svelte-dnd-action";

export function istSchatten(eintrag: object): boolean {
  return !!(eintrag as Record<string, unknown>)[SHADOW_ITEM_MARKER_PROPERTY_NAME];
}

/** Das gezogene Element hebt sich ab (M-71); die Klasse trägt das Element, das dem Zeiger folgt */
export function abheben(klasse: string, innen = ""): (el?: HTMLElement) => void {
  return (el) => { (innen ? el?.querySelector(innen) : el)?.classList.add(klasse); };
}
