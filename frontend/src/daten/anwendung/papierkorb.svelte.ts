// Anwendungsfälle des Papierkorbs über den Server: Karten, Spalten und Boards hineinlegen, an die alte Stelle
// wiederherstellen (mit demselben Recht wie das Hineinlegen), endgültig entfernen (nur mit dem Recht "Papierkorb
// leeren", ohne Rückgängig). Karten und Spalten liegen im Papierkorb ihres Boards, ganze Boards im Papierkorb der App.
// Rechte und Regeln prüft der Server; die Oberfläche blendet nur aus, und eine Ablehnung steht mit Grund in der Meldung.

import type { Geloescht, Kennung } from "../../modell";
import { aendern, senden } from "./meldung.svelte";

export function eintragName(e: Geloescht): string {
  if (e.art === "board") return `Board ${e.inhalt?.board.name ?? ""}`;
  return e.art === "spalte" ? `Spalte ${e.spalte?.name}` : e.karten[0].schluessel;
}

/** Das Recht, mit dem ein Eintrag hineinkam und wieder herauskommt */
export function rechtZumWiederherstellen(e: Geloescht): string {
  return e.art === "karte" ? "karten.loeschen" : "board.verwalten";
}

/** Karten eines Boards in seinen Papierkorb, jede mit ihrer Stelle und allem, was daran hängt */
export function inPapierkorb(ids: Kennung[]): void {
  if (ids.length) void aendern(() => senden("/karten/in-papierkorb", { ids }));
}

/** Wiederherstellen an die alte Stelle: Spalte samt Karten, Karte in ihre Spalte am alten Platz (fehlt die Spalte, in
 *  die erste des Boards), Board mit allem; Schlüssel, Kommentare, Anhänge und Verknüpfung bleiben, wie sie waren */
export function wiederherstellen(id: Kennung): void {
  void aendern(() => senden(`/papierkorb/${id}/wiederherstellen`));
}

/** Gewählte Einträge endgültig entfernen (die Rückfrage steht vorher in der Fläche) */
export function entfernen(ids: Kennung[]): void {
  if (ids.length) void aendern(() => senden("/papierkorb/entfernen", { ids }));
}

/** Den ganzen Papierkorb eines Boards endgültig leeren (die Rückfrage steht vorher in der Fläche) */
export function leeren(boardId: Kennung): void {
  void aendern(() => senden(`/boards/${boardId}/papierkorb/leeren`));
}

/** Board mit allem, was daran hängt, in den Papierkorb der App (Einstellungen, Papierkorb); sein Kürzel bleibt vergeben */
export async function boardInPapierkorb(boardId: Kennung): Promise<boolean> {
  return (await aendern(() => senden(`/boards/${boardId}/in-papierkorb`))) !== null;
}

/** Spalte löschen: die Karten vorher in eine andere Spalte (derselbe Weg wie Ziehen, die Gruppe zieht mit) oder mit
 *  der Spalte in den Papierkorb (Wiederherstellen an der alten Stelle). Die Erledigt-Spalte und die letzte bleiben. */
export async function spalteLoeschen(boardId: Kennung, spalteId: Kennung, kartenNach?: Kennung): Promise<boolean> {
  return (await aendern(() => senden(`/boards/${boardId}/spalten/${spalteId}/loeschen`, { nach: kartenNach }))) !== null;
}
