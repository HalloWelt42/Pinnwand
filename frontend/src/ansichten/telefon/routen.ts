// Wege der Telefonansicht (?geraet=telefon): dieselben Pfade wie am Rechner, eigene Ansichten (siehe src/routen.ts). Zeit
// gibt es, wenn eines deiner Boards Zeit erfasst.
import type { Route } from "../../routen";
import { modulIrgendwo } from "../../daten/abfragen";
import { boardAusKuerzel, karteAusNummer } from "../../daten/stand.svelte";
import Boards from "./Boards.svelte";
import Erfassen from "./Erfassen.svelte";
import Heute from "./Heute.svelte";
import Hinweise from "./Hinweise.svelte";
import TelBoard from "./TelBoard.svelte";
import TelKartendetail from "./TelKartendetail.svelte";
import TelKarteHolen from "./TelKarteHolen.svelte";
import Zeiten from "./Zeiten.svelte";

export const ROUTEN: Route[] = [
  { geraet: "telefon", muster: /^\/heute$/, ansicht: () => ({ navi: "heute", komponente: Heute, werte: {} }) },
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
    ansicht: (m) => {
      const b = boardAusKuerzel(m[1]);
      if (!b) return null;
      const k = karteAusNummer(b, m[2]);
      // nicht im Zustand (archiviert, umgezogen): erst holen, dann zeigt derselbe Weg das Detail
      return k ? { navi: b.id, komponente: TelKartendetail, werte: { kartenId: k.id } }
        : { navi: b.id, komponente: TelKarteHolen, werte: { boardId: b.id, schluessel: `${b.kuerzel}-${m[2]}` } };
    },
  },
  {
    geraet: "telefon",
    muster: /^\/zeiten$/,
    ansicht: () => (modulIrgendwo("zeiterfassung") ? { navi: "zeiten", komponente: Zeiten, werte: {} } : null),
  },
  { geraet: "telefon", muster: /^\/erfassen$/, ansicht: () => ({ navi: "erfassen", komponente: Erfassen, werte: {} }) },
  { geraet: "telefon", muster: /^\/hinweise$/, ansicht: () => ({ navi: "hinweise", komponente: Hinweise, werte: {} }) },
];
