// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Kalender und Zeitachse eines Boards laufen über
// den Weg des Boards (/board/<kürzel>/kalender|zeitachse) und board/ansichten.ts.
import type { Route } from "../../routen";
import { plan } from "./plan.svelte";
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
    ansicht: (m, entwurf) => plan.serien.some((s) => s.id === m[1])
      ? { navi: "serien", komponente: SerieBearbeiten, werte: { serieId: m[1], entwurf } }
      : null,
  },
];
