// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Kalender und Zeitachse eines Boards laufen über
// den Weg des Boards (/board/<kürzel>/kalender|zeitachse) und board/ansichten.ts.
import type { Route } from "../../routen";
import SerieBearbeiten from "./SerieBearbeiten.svelte";
import Serien from "./Serien.svelte";

export const ROUTEN: Route[] = [
  {
    geraet: "rechner",
    muster: /^\/serien$/,
    // eine neue Serie entsteht im selben Formular wie das Bearbeiten (eine Stelle), mit Vorschau der Tage
    ansicht: (_m, entwurf) => entwurf === "neu"
      ? { navi: "serien", komponente: SerieBearbeiten, werte: { neu: true, entwurf } }
      : { navi: "serien", komponente: Serien, werte: { entwurf } },
  },
  {
    geraet: "rechner",
    muster: /^\/serien\/([a-z0-9-]+)$/,
    // auch eine gelöschte Serie behält ihren Weg: die Ansicht sagt es und führt zurück (Rückgängig bringt sie wieder)
    ansicht: (m, entwurf) => ({ navi: "serien", komponente: SerieBearbeiten, werte: { serieId: m[1], entwurf } }),
  },
];
