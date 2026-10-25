// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts). Zeiten (Stundenzettel), Arbeitszeit mit ihren
// Reitern als eigene Adressen und Berichte; vorgeführte Zustände kommen über ?entwurf=.
import type { Route } from "../../routen";
import Arbeitszeit from "./Arbeitszeit.svelte";
import Berichte from "./Berichte.svelte";
import Stundenzettel from "./Stundenzettel.svelte";

export const ROUTEN: Route[] = [
  { geraet: "rechner", muster: /^\/zeiten$/, ansicht: (_m, entwurf) => ({ navi: "zeiten", komponente: Stundenzettel, werte: { entwurf } }) },
  {
    geraet: "rechner",
    muster: /^\/arbeitszeit(?:\/(kalender|urlaub|team))?$/,
    ansicht: (m, entwurf) => ({ navi: "arbeitszeit", komponente: Arbeitszeit, werte: { reiter: m[1] ?? "", entwurf } }),
  },
  { geraet: "rechner", muster: /^\/berichte$/, ansicht: (_m, entwurf) => ({ navi: "berichte", komponente: Berichte, werte: { entwurf } }) },
];
