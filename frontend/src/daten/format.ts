// Darstellung von Zeiten, Daten und Dauern, überall gleich (in der App dieselben Funktionen). "Jetzt" ist in den
// Entwürfen fest (daten.ts), in der App die Uhr.

import { kalenderwoche, MONATE, plusTage, TAGE_KURZ, tageZwischen } from "../regeln/tage";
import { uhr } from "./uhr.svelte";

/** 2:35 (Stunden:Minuten); mit Sekunden 2:35:10 */
export function dauer(sek: number, mitSekunden = false): string {
  const h = Math.floor(sek / 3600);
  const m = Math.floor((sek % 3600) / 60);
  const s = Math.floor(sek % 60);
  return mitSekunden ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${h}:${String(m).padStart(2, "0")}`;
}

/** +1:10 oder -0:02 (das Minuszeichen als einfacher Bindestrich) */
export function differenz(sek: number): string {
  const s = Math.round(sek);
  if (Math.abs(s) < 60) return "0:00";
  return `${s > 0 ? "+" : "-"}${dauer(Math.abs(s))}`;
}

/** 27.10. oder mit Wochentag "Di 27.10." */
export function datum(iso: string, mitTag = false): string {
  const t = `${iso.slice(8, 10)}.${iso.slice(5, 7)}.`;
  return mitTag ? `${TAGE_KURZ[new Date(iso.slice(0, 10) + "T12:00:00").getDay()]} ${t}` : t;
}

/** 27.10.2026, mit Wochentag "Di 27.10.2026" */
export function datumJahr(iso: string, mitTag = false): string {
  return `${datum(iso, mitTag)}${iso.slice(0, 4)}`;
}

/** Zeitraum zweier Tage, so kurz wie lesbar: "Di 27.10.2026" oder "Mo 26.10. bis Fr 30.10.2026" */
export function spanne(von: string, bis: string): string {
  if (von === bis) return datumJahr(von, true);
  return `${datum(von, true)} bis ${datumJahr(bis, true)}`;
}

/** "Woche 44, 26.10. bis 01.11.2026" (Kalenderwoche nach ISO) */
export function wocheText(montag: string): string {
  return `Woche ${kalenderwoche(montag)}, ${datum(montag)} bis ${datumJahr(plusTage(montag, 6))}`;
}

/** "Oktober 2026" */
export function monatText(tag: string): string {
  return `${MONATE[Number(tag.slice(5, 7)) - 1]} ${tag.slice(0, 4)}`;
}

/** Tage mit Komma: 0,5 oder 13 */
export function tageZahl(n: number): string {
  return String(Math.round(n * 10) / 10).replace(".", ",");
}

export function uhrzeit(iso: string): string {
  return iso.slice(11, 16);
}

/** Alter im Status in Tagen ab dem letzten Spaltenwechsel */
export function alterTage(bewegtAm: string): number {
  return tageZwischen(bewegtAm.slice(0, 10), uhr.heute);
}

/** Fälligkeit relativ zu heute: "heute", "morgen", "2 Tage über", sonst Datum; rot überfällig, Bernstein von heute bis
 *  in zwei Tagen (Mechanik M-39) */
export function faelligText(iso: string): { text: string; klasse: "" | "warnung" | "gefahr" } {
  const t = tageZwischen(uhr.heute, iso);
  if (t < 0) return { text: `${-t} ${-t === 1 ? "Tag" : "Tage"} über`, klasse: "gefahr" };
  const bald = t <= 2 ? "warnung" : "";
  if (t === 0) return { text: "heute", klasse: bald };
  if (t === 1) return { text: "morgen", klasse: bald };
  return { text: datum(iso, true), klasse: bald };
}

/** Laufende Sekunden seit einem Zeitpunkt bis jetzt */
export function laufendSek(seit: string): number {
  return Math.max(0, (new Date(uhr.jetzt).getTime() - new Date(seit).getTime()) / 1000);
}

/** "vor 5 Minuten", "vor 3 Stunden", "gestern 15:40", "26.10. 15:40" */
export function wann(iso: string): string {
  const t = tageZwischen(iso.slice(0, 10), uhr.heute);
  if (t === 0) {
    const min = Math.round((new Date(uhr.jetzt).getTime() - new Date(iso).getTime()) / 60000);
    if (min < 1) return "gerade eben";
    if (min < 60) return `vor ${min} ${min === 1 ? "Minute" : "Minuten"}`;
    const std = Math.round(min / 60);
    return `vor ${std} ${std === 1 ? "Stunde" : "Stunden"}`;
  }
  if (t === 1) return `gestern ${uhrzeit(iso)}`;
  return `${datum(iso)} ${uhrzeit(iso)}`;
}

/** Gesamtnummer einer Karte, wie sie über dem Titel steht und kopiert wird: "# 101" */
export function gesamtnummer(nummer: number): string {
  return `# ${nummer}`;
}
