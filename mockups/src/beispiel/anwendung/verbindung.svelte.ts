// Die Verbindung zum Ereignisstrom: in der App meldet sie der Strom selbst (getrennt, wieder da), die Oberfläche schaltet
// nie selbst um. In den Entwürfen führt ein vorgeführter Zustand die Trennung über diese Funktion vor.

import type { Verbindung } from "../../modell";
import { stand } from "../stand.svelte";

/** Ereignis des Stroms: getrennt (letzter Stand bleibt sichtbar, Schreibendes gesperrt) oder wieder verbunden */
export function verbindungGemeldet(v: Verbindung): void {
  stand.verbindung = v;
}
