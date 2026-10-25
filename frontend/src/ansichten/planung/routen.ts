// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Serien und Termine gibt es, wenn eines deiner
// Boards das Modul an hat; sonst passen die Wege nicht. Kalender und Zeitachse eines Boards laufen über den Weg des
// Boards (/board/<kürzel>/kalender|zeitachse) und board/ansichten.ts.
import { modulIrgendwo } from "../../daten/abfragen";
import type { Route, Treffer } from "../../routen";
import SerieBearbeiten from "./SerieBearbeiten.svelte";
import Serien from "./Serien.svelte";

/** Die Ansicht, wenn eines deiner Boards Serien hat; sonst passt der Weg nicht */
function mitSerien(treffer: Treffer): Treffer | null {
  return modulIrgendwo("serien") ? treffer : null;
}

export const ROUTEN: Route[] = [
  { geraet: "rechner", muster: /^\/serien$/, ansicht: () => mitSerien({ navi: "serien", komponente: Serien, werte: {} }) },
  // eine neue Serie entsteht im selben Formular wie das Bearbeiten (eine Stelle), mit Vorschau der Tage
  {
    geraet: "rechner",
    muster: /^\/serien\/neu$/,
    ansicht: () => mitSerien({ navi: "serien", komponente: SerieBearbeiten, werte: { neu: true, serieId: "" } }),
  },
  // auch eine gelöschte Serie behält ihren Weg: die Ansicht sagt es und führt zurück (Rückgängig bringt sie wieder)
  {
    geraet: "rechner",
    muster: /^\/serien\/([\w-]+)$/,
    ansicht: (m) => mitSerien({ navi: "serien", komponente: SerieBearbeiten, werte: { neu: false, serieId: m[1] } }),
  },
];
