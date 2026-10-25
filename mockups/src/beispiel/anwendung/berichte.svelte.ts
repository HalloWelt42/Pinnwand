// Anwendungsfälle des Moduls Berichte: einen Bericht erstellen und in der Kellerwolke ablegen (Ordner der Pinnwand).
// Die Datei erzeugt in der App der Server; hier entsteht der Eintrag in der Liste, mit Rückgängig.

import type { Bericht } from "../../modell";
import { BERICHTSORDNER } from "../daten-zeit";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { neueKennung } from "./zeiten.svelte";

/** Bericht erstellen; Ergebnis: seine Kennung (oder nichts, wenn es nicht wirkte) */
export function berichtErstellen(neu: Omit<Bericht, "id">): string | undefined {
  const id = neueKennung("r");
  const ok = aendern(() => {
    stand.berichte.unshift({ ...neu, id });
    return `Abgelegt in ${BERICHTSORDNER}: ${neu.datei}`;
  });
  return ok ? id : undefined;
}
