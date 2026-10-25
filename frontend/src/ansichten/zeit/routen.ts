// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Zeiten (Stundenzettel) gibt es, wenn eines
// deiner Boards Zeit erfasst, Arbeitszeit mit ihren Reitern als eigene Adressen, wenn eines das Modul Arbeitszeit an hat;
// sonst passen die Wege nicht. Berichte kommen mit ihrer Stufe.
import { modulIrgendwo } from "../../daten/abfragen";
import type { Route } from "../../routen";
import Arbeitszeit from "./Arbeitszeit.svelte";
import Stundenzettel from "./Stundenzettel.svelte";

export const ROUTEN: Route[] = [
  {
    geraet: "rechner",
    muster: /^\/zeiten$/,
    ansicht: () => (modulIrgendwo("zeiterfassung") ? { navi: "zeiten", komponente: Stundenzettel, werte: {} } : null),
  },
  {
    geraet: "rechner",
    muster: /^\/arbeitszeit(?:\/(kalender|urlaub|team))?$/,
    ansicht: (m) => (modulIrgendwo("arbeitszeit") ? { navi: "arbeitszeit", komponente: Arbeitszeit, werte: { reiter: m[1] ?? "" } } : null),
  },
];
