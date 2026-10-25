// Termine gehören zum Modul Serien. Solange der Server das Modul nicht anbietet, lässt es sich in keinem Board
// einschalten und es gibt keine Termine zum Zusagen; dieser Weg sagt dann nur, dass es aus ist.

import type { Kennung } from "../../modell";
import { nichtEingeschaltet } from "./meldung.svelte";

export function zusagen(_id: Kennung, _ja = true): void {
  nichtEingeschaltet("Serien und Termine");
}
