// Der Timer einer Person gehört zum Modul Zeiterfassung. Solange der Server das Modul nicht anbietet, lässt es sich in
// keinem Board einschalten und keine Ansicht zeigt einen Timer; diese Wege sagen dann nur, dass es aus ist.

import { nichtEingeschaltet } from "./meldung.svelte";

export function starten(_karteId: string): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function anhalten(): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function fortsetzen(): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function stoppen(): void {
  nichtEingeschaltet("Die Zeiterfassung");
}
