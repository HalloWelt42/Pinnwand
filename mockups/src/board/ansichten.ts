// Ansichten eines Boards neben dem Spaltenstreifen (Pfad /board/<kürzel>/<ansicht>): jede bekommt das Board, den
// Entwurfszusatz, die Suche der Werkzeugleiste und ob Ziehen gesperrt ist (bei Suche und Filter), und zeichnet unter dem
// gemeinsamen Kopf und der Werkzeugleiste des Boards.
import type { Component } from "svelte";
import type { Board } from "../modell";
import Liste from "../ansichten/uebersicht/Liste.svelte";
import Kalender from "../ansichten/planung/Kalender.svelte";
import Zeitachse from "../ansichten/planung/Zeitachse.svelte";

/** Was jede Ansicht eines Boards bekommt */
export interface BoardAnsichtWerte {
  board: Board;
  entwurf: string;
  /** Suche der Werkzeugleiste: filtert die Karten wie im Board */
  suche: string;
  /** bei Suche und Filter ist Ziehen gesperrt (wie im Board) */
  ziehenGesperrt: boolean;
}

export const BOARDANSICHTEN: Record<string, Component<any>> = { liste: Liste, kalender: Kalender, zeitachse: Zeitachse };
