// Übergang im Bau: Wege, deren Seite im Server noch entsteht. Jeder Bereich ersetzt seine Marken durch echte Aufrufe;
// vor dem Ausrollen ist diese Datei gelöscht, und die Typprüfung fände jede vergessene Stelle.

import { melden } from "./meldung.svelte";

export function baustelle(was: string): false {
  melden(`${was}: noch nicht an den Server angebunden`);
  return false;
}
