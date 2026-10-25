// Ansichten eines Boards neben dem Spaltenstreifen (Pfad /board/<kürzel>/<ansicht>): jede bekommt das Board, Suche
// und Filter der Werkzeugleiste und ob Ziehen gesperrt ist (bei Suche und Filter), und zeichnet
// unter dem gemeinsamen Kopf und der Werkzeugleiste des Boards.
import type { Component } from "svelte";
import type { Kartenfilter } from "../daten/abfragen";
import type { Board } from "../modell";
import Liste from "../ansichten/uebersicht/Liste.svelte";
import Kalender from "../ansichten/planung/Kalender.svelte";
import Zeitachse from "../ansichten/planung/Zeitachse.svelte";

/** Was jede Ansicht eines Boards bekommt */
export interface BoardAnsichtWerte {
  board: Board;
  /** Suche und Filter der Werkzeugleiste (Personen, Prioritäten, Labels, eigene Felder): jede Ansicht wendet sie mit
   *  kartePasst(karte, board, filter) aus daten/abfragen.ts an, derselben Abfrage wie das Board */
  filter: Kartenfilter;
  /** bei Suche und Filter ist Ziehen gesperrt (wie im Board) */
  ziehenGesperrt: boolean;
}

export const BOARDANSICHTEN: Record<string, Component<any>> = { liste: Liste, kalender: Kalender, zeitachse: Zeitachse };
