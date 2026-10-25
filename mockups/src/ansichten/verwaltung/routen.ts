// Wege dieses Bereichs: Pfad der App auf Ansicht (siehe src/routen.ts).
// /board/<kürzel>/einstellungen[/<reiter>] (ohne Reiter: allgemein), /boards/neu, /einstellungen[/<reiter>] (ohne: darstellung)
import type { Route } from "../../routen";
import { boardAusKuerzel } from "../../routen";
import BoardEinstellungen from "./BoardEinstellungen.svelte";
import BoardNeu from "./BoardNeu.svelte";
import { BOARD_REITER, PERSON_REITER } from "./daten";
import Einstellungen from "./Einstellungen.svelte";

const boardReiter = new Set<string>(BOARD_REITER.map((r) => r.id));
const personReiter = new Set<string>(PERSON_REITER.map((r) => r.id));

export const ROUTEN: Route[] = [
  {
    geraet: "rechner",
    muster: /^\/board\/([a-z0-9]+)\/einstellungen(?:\/([a-z]+))?$/,
    ansicht: (m, entwurf) => {
      const b = boardAusKuerzel(m[1]);
      const reiter = m[2] ?? "allgemein";
      if (!b || !boardReiter.has(reiter)) return null;
      return { navi: b.id, komponente: BoardEinstellungen, werte: { boardId: b.id, reiter, entwurf } };
    },
  },
  {
    geraet: "rechner",
    muster: /^\/boards\/neu$/,
    ansicht: (_m, entwurf) => ({ navi: "board-neu", komponente: BoardNeu, werte: { entwurf } }),
  },
  {
    geraet: "rechner",
    muster: /^\/einstellungen(?:\/([a-z]+))?$/,
    ansicht: (m, entwurf) => {
      const reiter = m[1] ?? "darstellung";
      if (!personReiter.has(reiter)) return null;
      return { navi: "einstellungen", komponente: Einstellungen, werte: { reiter, entwurf } };
    },
  },
];
