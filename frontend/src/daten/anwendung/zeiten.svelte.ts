// Gebuchte Zeiten gehören zum Modul Zeiterfassung. Solange der Server das Modul nicht anbietet, lässt es sich in keinem
// Board einschalten und keine Ansicht zeigt Zeiten zum Ändern; diese Wege sagen dann nur, dass es aus ist.

import { nichtEingeschaltet } from "./meldung.svelte";

export function buchen(_karteId: string, _tag: string, _sek: number, _notiz = ""): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function ticketzeitSetzen(_karteId: string, _sek: number): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function dauerAendern(_id: string, _sek: number): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function datumAendern(_id: string, _tag: string): void {
  nichtEingeschaltet("Die Zeiterfassung");
}

export function loeschen(_id: string): void {
  nichtEingeschaltet("Die Zeiterfassung");
}
