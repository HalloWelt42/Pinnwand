// Schnellwahl der Fälligkeit am Telefon (Erfassen und Bearbeiten): Heute, Morgen, der nächste Freitag; "Ohne" leert.
import { datum } from "../../daten/format";
import { plusTage, wochentag } from "../../regeln/tage";

/** Name und Tag (ISO) der Schnellwahl ab `heute` */
export function faelligWahl(heute: string): [string, string][] {
  const freitag = plusTage(heute, ((5 - wochentag(heute) + 6) % 7) + 1);
  return [["Heute", heute], ["Morgen", plusTage(heute, 1)], [datum(freitag, true), freitag]];
}
