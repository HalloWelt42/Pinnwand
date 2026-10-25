// Wege der Pinnwand: welcher Pfad welche Ansicht zeigt (wie später in der App). Jeder Bereich trägt seine Wege in
// ansichten/<bereich>/routen.ts ein; die erste passende gilt. Der Zusatz ?entwurf=<name> wählt einen vorgeführten
// Zustand derselben Ansicht, ?geraet=telefon die Telefonansicht.

import type { Component } from "svelte";
import BoardAnsicht from "./board/BoardAnsicht.svelte";
import { ROUTEN as PLANUNG } from "./ansichten/planung/routen";
import { ROUTEN as TELEFON } from "./ansichten/telefon/routen";
import { ROUTEN as UEBERSICHT } from "./ansichten/uebersicht/routen";
import { ROUTEN as VERWALTUNG } from "./ansichten/verwaltung/routen";
import { ROUTEN as ZEIT } from "./ansichten/zeit/routen";
import { stand } from "./beispiel/stand.svelte";

export interface Treffer {
  /** Eintrag der Seitenleiste, der aktiv ist */
  navi: string;
  komponente: Component<any>;
  werte: Record<string, unknown>;
}

export interface Route {
  geraet: "rechner" | "telefon";
  muster: RegExp;
  /** aus den Gruppen des Musters und dem Entwurfszusatz die Ansicht; null: passt doch nicht */
  ansicht: (m: RegExpMatchArray, entwurf: string) => Treffer | null;
}

/** Board aus dem Kürzel im Pfad */
export function boardAusKuerzel(k: string) {
  return stand.boards.find((b) => b.kuerzel.toLowerCase() === k.toLowerCase());
}

const BOARD: Route[] = [
  {
    geraet: "rechner",
    muster: /^\/board\/([a-z0-9]+)(?:\/(\d+|liste|kalender|zeitachse))?$/,
    ansicht: (m, entwurf) => {
      const b = boardAusKuerzel(m[1]);
      if (!b) return null;
      const teil = m[2] ?? "";
      const nr = /^\d+$/.test(teil) ? teil : "";
      const detail = nr ? stand.karten.find((k) => k.board === b.id && k.schluessel === `${b.kuerzel}-${nr}`)?.id : undefined;
      return { navi: b.id, komponente: BoardAnsicht,
               werte: { boardId: b.id, ansicht: nr || !teil ? "board" : teil, detail, entwurf } };
    },
  },
];

export const ROUTEN: Route[] = [...BOARD, ...UEBERSICHT, ...VERWALTUNG, ...ZEIT, ...PLANUNG, ...TELEFON];

export function finden(pfad: string, geraet: "rechner" | "telefon", entwurf: string): Treffer | null {
  for (const r of ROUTEN.filter((x) => x.geraet === geraet)) {
    const m = pfad.match(r.muster);
    if (m) {
      const t = r.ansicht(m, entwurf);
      if (t) return t;
    }
  }
  return null;
}
