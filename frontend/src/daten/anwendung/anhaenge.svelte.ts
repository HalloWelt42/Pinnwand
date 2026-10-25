// Anwendungsfälle an Anhängen einer Karte (E-15, Mechanik M-63): hochladen legt die Datei in der Kellerwolke ab, in der
// Ablage der Pinnwand mit einem Ordner je Board; aus der eigenen Kellerwolke wird nur verknüpft, die Datei bleibt, wo
// sie ist. Entfernen nimmt den Anhang von der Karte, mit Rückgängig (die alte App löschte sofort und endgültig). Jede
// Änderung steht im Verlauf der Karte. Grenze 25 MB je Datei, leere Dateien werden abgelehnt.
//
// In der App liefert die Kellerwolke die Liste deiner Dateien und öffnet Dateien selbst; in den Entwürfen steht dafür
// eine kleine Ablage im Speicher: Hochgeladenes lässt sich öffnen, solange die Seite steht, für die Beispieldateien
// entsteht beim Öffnen ein schlichter Ersatz.

import type { Anhang, Board, Karte, KellerwolkeDatei, Kennung } from "../../modell";
import { board } from "../stand.svelte";
import { baustelle } from "./baustelle";

/** höchstens so groß darf eine Datei sein (wie in der alten App) */
export const GRENZE_MB = 25;

/** Ort einer hochgeladenen Datei in der Kellerwolke: Ablage der Pinnwand, ein Ordner je Board */
export function ablageOrt(b: Board): string {
  return `Pinnwand/${b.name}`;
}

// ═══ Ablage in der Kellerwolke (in den Entwürfen im Speicher) ═══════════════════════════════════════════

const inhalte = new Map<string, Blob>();
const adressen = new Map<string, string>();

function ablageSchluessel(karteId: Kennung, name: string): string {
  return `${karteId}/${name}`;
}

function svgText(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Ersatz für eine Beispieldatei ohne Inhalt: eine Skizze für Bilder, sonst die Angaben der Datei als Text */
function ersatz(a: Anhang, ort: string): Blob {
  if (a.art === "bild") {
    return new Blob([`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"><rect x="8" y="8" width="784" height="484" rx="8" ` +
      `fill="none" stroke="currentColor" stroke-width="4"/><text x="400" y="260" text-anchor="middle" font-family="sans-serif" ` +
      `font-size="32">${svgText(a.name)}</text></svg>`], { type: "image/svg+xml" });
  }
  return new Blob([`${a.name}\n\n${a.groesse}, ${ort}\n`], { type: "text/plain;charset=utf-8" });
}

/** Adresse zum Öffnen eines Anhangs (die Datei aus der Kellerwolke) */
export function dateiAdresse(k: Karte, a: Anhang): string {
  const schluessel = ablageSchluessel(k.id, a.name);
  const da = adressen.get(schluessel);
  if (da) return da;
  const ort = a.verknuepft ? "aus deiner Kellerwolke verknüpft" : `Kellerwolke, ${ablageOrt(board(k.board))}`;
  const adresse = URL.createObjectURL(inhalte.get(schluessel) ?? ersatz(a, ort));
  adressen.set(schluessel, adresse);
  return adresse;
}

// ═══ Anwendungsfälle ═════════════════════════════════════════════════════════════════════════════════════

/** Dateien hochladen (Dateiwahl oder auf die Fläche gezogen): zu große und leere bleiben draußen, die Meldung sagt es */
export function hochladen(karteId: Kennung, dateien: File[]): void {
  baustelle("Anhänge");
}

/** Dateien aus deiner Kellerwolke verknüpfen; schon verknüpfte kommen nicht doppelt */
export function ausKellerwolke(karteId: Kennung, dateien: KellerwolkeDatei[]): void {
  baustelle("Anhänge");
}

/** Anhang von der Karte nehmen, mit Rückgängig; eine verknüpfte Datei bleibt in deiner Kellerwolke */
export function entfernen(karteId: Kennung, name: string): void {
  baustelle("Anhänge");
}
