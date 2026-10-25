// Was in Heute steht: deine offenen Karten aus allen Boards, in denen du Mitglied bist, nach Fälligkeit geordnet, dazu
// heute fällige Serienkarten und deine Termine der Woche. "Offen" heißt: nicht in einer Erledigt-Spalte. In der App
// liefert das eine Abfrage der Schnittstelle; die Regeln sind dieselben.

import { HEUTE, ICH, TERMINE } from "../../beispiel/daten";
import { tageZwischen } from "../../regeln/tage";
import { stand } from "../../beispiel/stand.svelte";
import type { Prioritaet, Termin } from "../../modell";
import type { HeuteEintrag } from "./modell";

/** "Diese Woche": fällig in den nächsten sieben Tagen (wie bisher) */
export const WOCHE_TAGE = 7;

const RANG: Record<Prioritaet, number> = { dringend: 0, hoch: 1, mittel: 2, niedrig: 3, keine: 4 };

function ordnung(a: HeuteEintrag, b: HeuteEintrag): number {
  return (a.karte.faellig ?? "9999").localeCompare(b.karte.faellig ?? "9999") || RANG[a.karte.prioritaet] - RANG[b.karte.prioritaet];
}

/** Deine offenen Karten aus allen Boards, in denen du Mitglied bist */
export function meineOffenen(): HeuteEintrag[] {
  const boards = stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH));
  return stand.karten.flatMap((karte) => {
    const board = boards.find((b) => b.id === karte.board);
    const spalte = board?.spalten.find((s) => s.id === karte.spalte);
    return board && spalte && !spalte.erledigt && karte.zustaendig.includes(ICH) ? [{ karte, board }] : [];
  }).sort(ordnung);
}

export interface HeuteGruppen {
  ueberfaellig: HeuteEintrag[];
  heute: HeuteEintrag[];
  woche: HeuteEintrag[];
  ohneDatum: HeuteEintrag[];
  /** heute fällige Serienkarten (stehen nur hier, nicht noch einmal unter Heute) */
  serien: HeuteEintrag[];
}

export function heuteGruppen(): HeuteGruppen {
  const g: HeuteGruppen = { ueberfaellig: [], heute: [], woche: [], ohneDatum: [], serien: [] };
  for (const e of meineOffenen()) {
    const f = e.karte.faellig;
    const t = f ? tageZwischen(HEUTE, f) : null;
    if (t === null) g.ohneDatum.push(e);
    else if (t < 0) g.ueberfaellig.push(e);
    else if (t === 0) (e.karte.serie ? g.serien : g.heute).push(e);
    else if (t <= WOCHE_TAGE) g.woche.push(e);
  }
  return g;
}

/** Deine Termine von heute und den nächsten sieben Tagen */
export function meineTermine(): { heute: Termin[]; woche: Termin[] } {
  const meine = TERMINE.filter((t) => t.teilnehmer.includes(ICH))
    .filter((t) => { const d = tageZwischen(HEUTE, t.datum); return d >= 0 && d <= WOCHE_TAGE; })
    .sort((a, b) => (a.datum + a.von).localeCompare(b.datum + b.von));
  return { heute: meine.filter((t) => t.datum === HEUTE), woche: meine.filter((t) => t.datum !== HEUTE) };
}

/** Alter im Status ab dem eine Karte liegengeblieben ist: Warnung und Gefahr (wie auf der Karte im Board; in der App
 *  die Einstellung Alterung des Boards) */
export const ALTER_WARNUNG = 4;
export const ALTER_GEFAHR = 8;
