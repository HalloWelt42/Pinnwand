// Wege der Pinnwand: welcher Pfad welche Ansicht zeigt. Jeder Bereich trägt seine Wege in ansichten/<bereich>/routen.ts
// ein; die erste passende gilt. Am Telefon gelten die Wege der Telefonansicht (dieselben Pfade, eigene Ansichten).
// Bereiche späterer Stufen (Planung, Berichte) kommen mit ihrer Stufe dazu.

import type { Component } from "svelte";
import BoardAnsicht from "./board/BoardAnsicht.svelte";
import { ROUTEN as TELEFON } from "./ansichten/telefon/routen";
import { ROUTEN as UEBERSICHT } from "./ansichten/uebersicht/routen";
import { ROUTEN as VERWALTUNG } from "./ansichten/verwaltung/routen";
import { ROUTEN as ZEIT } from "./ansichten/zeit/routen";
import { boardAusKuerzel } from "./daten/stand.svelte";

export interface Treffer {
  /** Eintrag der Seitenleiste, der aktiv ist */
  navi: string;
  komponente: Component<any>;
  werte: Record<string, unknown>;
}

export interface Route {
  geraet: "rechner" | "telefon";
  muster: RegExp;
  /** aus den Gruppen des Musters die Ansicht; null: passt doch nicht */
  ansicht: (m: RegExpMatchArray) => Treffer | null;
}

/** Board aus dem Kürzel im Pfad: steht im gemeinsamen Zustand, hier nur weitergereicht, bis alle Bereiche dort lesen */
export { boardAusKuerzel };

const BOARD: Route[] = [
  {
    geraet: "rechner",
    muster: /^\/board\/([a-z0-9]+)(?:\/(\d+|liste|kalender|zeitachse))?$/,
    ansicht: (m) => {
      const b = boardAusKuerzel(m[1]);
      if (!b) return null;
      const teil = m[2] ?? "";
      const nr = /^\d+$/.test(teil) ? teil : "";
      // ein direkter Pfad öffnet jede Karte des Boards, auch eine archivierte (das Board holt sie einzeln)
      return { navi: b.id, komponente: BoardAnsicht, werte: { boardId: b.id, ansicht: nr || !teil ? "board" : teil, nummer: nr } };
    },
  },
];

export const ROUTEN: Route[] = [...BOARD, ...UEBERSICHT, ...VERWALTUNG, ...ZEIT, ...TELEFON];

export function finden(pfad: string, geraet: "rechner" | "telefon"): Treffer | null {
  for (const r of ROUTEN.filter((x) => x.geraet === geraet)) {
    const m = pfad.match(r.muster);
    if (m) {
      const t = r.ansicht(m);
      if (t) return t;
    }
  }
  return null;
}
