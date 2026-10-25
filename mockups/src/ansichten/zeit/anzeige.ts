// Darstellung, die format.ts (gemeinsam) noch nicht kennt: Dauer mit Vorzeichen, Datum mit Jahr, Zeiträume. Gebaut
// aus dauer() und datum() von format.ts; gehört nach der Freigabe dorthin (Bedarf im Bericht).

import { datum, dauer } from "../../beispiel/format";
import { kalenderwoche, MONATE, plusTage } from "./regeln";

/** +1:10 oder −0:02 (echtes Minuszeichen ist ein typografisches Zeichen, darum der Bindestrich) */
export function differenz(sek: number): string {
  const s = Math.round(sek);
  if (Math.abs(s) < 60) return "0:00";
  return `${s > 0 ? "+" : "-"}${dauer(Math.abs(s))}`;
}

/** 27.10.2026, mit Wochentag "Di 27.10.2026" */
export function datumJahr(tag: string, mitTag = false): string {
  return `${datum(tag, mitTag)}${tag.slice(0, 4)}`;
}

/** KW 44, 26.10. bis 01.11.2026 */
export function wocheText(montag: string): string {
  return `KW ${kalenderwoche(montag)}, ${datum(montag)} bis ${datumJahr(plusTage(montag, 6))}`;
}

export function monatText(tag: string): string {
  return `${MONATE[Number(tag.slice(5, 7)) - 1]} ${tag.slice(0, 4)}`;
}

/** Zeitraum zweier Tage, so kurz wie lesbar */
export function spanne(von: string, bis: string): string {
  if (von === bis) return datumJahr(von, true);
  return `${datum(von, true)} bis ${datumJahr(bis, true)}`;
}

/** Urlaubstage mit Komma: 0,5 oder 13 */
export function tageZahl(n: number): string {
  return String(Math.round(n * 10) / 10).replace(".", ",");
}
