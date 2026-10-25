// Der Verlauf einer Karte: jede Zeile entsteht im selben Anwendungsfall wie die Änderung. Protokolliert werden Anlage,
// Verschieben (auch Mitgezogene), Zuständig, Fällig, Priorität, Blockade, Art, Kommentar, Zeitbuchungen und Anhänge,
// bewusst nicht Titel und Beschreibung (Mechanik M-64).

import type { Karte } from "../../modell";
import { uhr } from "../uhr.svelte";
import { ICH } from "../ich";
import { karte } from "../stand.svelte";

/** Eine Zeile im Verlauf einer Karte (Karte oder Kennung) */
export function vermerken(k: Karte | string | undefined, text: string): void {
  const ziel = typeof k === "string" ? karte(k) : k;
  ziel?.verlauf.push({ zeit: uhr.jetzt, von: ICH, text });
}
