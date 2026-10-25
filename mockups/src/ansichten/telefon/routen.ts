// Wege der Telefonansicht (?geraet=telefon): dieselben Pfade wie am Rechner, eigene Ansichten (siehe src/routen.ts).
import type { Route } from "../../routen";
import { boardAusKuerzel, karteAusNummer } from "../../beispiel/stand.svelte";
import Boards from "./Boards.svelte";
import Erfassen from "./Erfassen.svelte";
import Heute from "./Heute.svelte";
import Hinweise from "./Hinweise.svelte";
import TelBoard from "./TelBoard.svelte";
import TelKartendetail from "./TelKartendetail.svelte";
import Zeiten from "./Zeiten.svelte";

export const ROUTEN: Route[] = [
  { geraet: "telefon", muster: /^\/heute$/, ansicht: (_m, entwurf) => ({ navi: "heute", komponente: Heute, werte: { entwurf } }) },
  { geraet: "telefon", muster: /^\/boards$/, ansicht: () => ({ navi: "boards", komponente: Boards, werte: {} }) },
  {
    geraet: "telefon",
    muster: /^\/board\/([a-z0-9]+)$/,
    ansicht: (m) => {
      const b = boardAusKuerzel(m[1]);
      return b ? { navi: b.id, komponente: TelBoard, werte: { boardId: b.id } } : null;
    },
  },
  {
    geraet: "telefon",
    muster: /^\/board\/([a-z0-9]+)\/(\d+)$/,
    ansicht: (m, entwurf) => {
      const b = boardAusKuerzel(m[1]);
      const k = b ? karteAusNummer(b, m[2]) : undefined;
      return b && k ? { navi: b.id, komponente: TelKartendetail, werte: { kartenId: k.id, entwurf } } : null;
    },
  },
  { geraet: "telefon", muster: /^\/zeiten$/, ansicht: () => ({ navi: "zeiten", komponente: Zeiten, werte: {} }) },
  { geraet: "telefon", muster: /^\/erfassen$/, ansicht: (_m, entwurf) => ({ navi: "erfassen", komponente: Erfassen, werte: { entwurf } }) },
  { geraet: "telefon", muster: /^\/hinweise$/, ansicht: () => ({ navi: "hinweise", komponente: Hinweise, werte: {} }) },
];
