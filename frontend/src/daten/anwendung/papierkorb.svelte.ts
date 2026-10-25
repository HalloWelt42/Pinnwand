// Anwendungsfälle des Papierkorbs je Board: Karten und Spalten hineinlegen, an die alte Stelle wiederherstellen,
// endgültig entfernen (nur mit dem Recht "Papierkorb leeren"). Gelöschtes liegt nur im Papierkorb; die gebuchte Zeit
// bleibt in den Zeiteinträgen und zählt weiter, auch nach dem Entfernen (dann mit dem gemerkten Namen der Karte).

import type { Geloescht, Kennung } from "../../modell";
import { baustelle } from "./baustelle";

export function eintragName(e: Geloescht): string {
  if (e.art === "board") return `Board ${e.inhalt?.board.name ?? ""}`;
  return e.art === "spalte" ? `Spalte ${e.spalte?.name}` : e.karten[0].schluessel;
}

/** Karten in den Papierkorb ihres Boards, mit allem, was daran hängt; laufende Timer buchen vorher */
export function inPapierkorb(ids: Kennung[]): void {
  baustelle("Papierkorb");
}

/** Spalte mit ihren Karten in den Papierkorb; die letzte Spalte eines Boards bleibt */
export function spalteInPapierkorb(boardId: Kennung, spalteId: Kennung): void {
  baustelle("Papierkorb");
}

/** Wiederherstellen an die alte Stelle: Spalte samt Karten, oder Karte in ihre Spalte am alten Platz (fehlt die Spalte,
 *  in die erste des Boards); Schlüssel, Kommentare, Anhänge und Verknüpfung bleiben, wie sie waren */
export function wiederherstellen(id: Kennung): void {
  baustelle("Papierkorb");
}

/** Endgültig entfernen (nur mit dem Recht; die Rückfrage steht vorher in der Fläche). Die Zeit bleibt gebucht. */
export function entfernen(ids: Kennung[]): void {
  baustelle("Papierkorb");
}

/** Board mit allem, was daran hängt, in den Papierkorb der App (Einstellungen, Papierkorb); laufende Timer buchen */
export async function boardInPapierkorb(boardId: Kennung): Promise<boolean> {
  return baustelle("Papierkorb");
}

/** Spalte löschen: die Karten vorher in eine andere Spalte (derselbe Weg wie Ziehen, die Gruppe zieht mit) oder mit
 *  der Spalte in den Papierkorb (Wiederherstellen an der alten Stelle). Die Erledigt-Spalte und die letzte bleiben. */
export async function spalteLoeschen(boardId: Kennung, spalteId: Kennung, kartenNach?: Kennung): Promise<boolean> {
  return baustelle("Papierkorb");
}
