// Veränderlicher Zustand der Verwaltung: Einstellungen je Board und die eigenen Hinweise wirken in den Entwürfen bis zum
// Neuladen der Seite, über alle Reiter hinweg. In der App kommen sie aus der Schnittstelle und dem Ereignisstrom.

import { BOARD_EINSTELLUNGEN, HINWEIS_VORGABE, type BoardEinstellung } from "./daten";

export const verwaltung = $state({
  boards: structuredClone(BOARD_EINSTELLUNGEN),
  hinweise: structuredClone(HINWEIS_VORGABE),
});

/** Vorgaben eines neuen Boards (BOARD_MECHANIK 3.1) */
export const VORGABE: BoardEinstellung = { alterungWarnung: 4, alterungGefahr: 8, ladeschritt: 50, archivTage: 365 };

/** Einstellungen eines Boards; ohne Eintrag die Vorgaben */
export function einstellungen(boardId: string): BoardEinstellung {
  return verwaltung.boards[boardId] ?? { ...VORGABE };
}
