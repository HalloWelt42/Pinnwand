// Rechnen mit Kalendertagen als reine Funktionen: Tage als ISO-Zeichenkette (JJJJ-MM-TT) ohne Zeitzone, Uhrzeiten als
// "HH:MM". Gerechnet wird mittags, damit die Zeitumstellung keinen Tag verschiebt. Die Darstellung für Menschen steht in
// beispiel/format.ts, das Lesen von Eingaben in regeln/eingabe.ts.

export const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
  "November", "Dezember"];
/** Wochentage ab Sonntag wie Date.getDay(); so zählen auch Zeitkonto.tage und Serie.tage */
export const TAGE_KURZ = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
export const TAGE_LANG = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
/** Reihenfolge der Tage in Wochenansichten: Montag bis Sonntag */
export const WOCHE_AB_MONTAG = [1, 2, 3, 4, 5, 6, 0];

function alsDatum(tag: string): Date {
  return new Date(tag.slice(0, 10) + "T12:00:00");
}

export function alsTag(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Ganze Kalendertage von a nach b (negativ, wenn b vor a liegt) */
export function tageZwischen(a: string, b: string): number {
  return Math.round((alsDatum(b).getTime() - alsDatum(a).getTime()) / 86400000);
}

export function plusTage(tag: string, n: number): string {
  const d = alsDatum(tag);
  d.setDate(d.getDate() + n);
  return alsTag(d);
}

/** 0 Sonntag, 1 Montag bis 6 Samstag */
export function wochentag(tag: string): number {
  return alsDatum(tag).getDay();
}

export function istWochenende(tag: string): boolean {
  const w = wochentag(tag);
  return w === 0 || w === 6;
}

export function montagVon(tag: string): string {
  return plusTage(tag, -((wochentag(tag) + 6) % 7));
}

export function monatsanfang(tag: string): string {
  return tag.slice(0, 8) + "01";
}

export function plusMonate(tag: string, n: number): string {
  const d = alsDatum(monatsanfang(tag));
  d.setMonth(d.getMonth() + n);
  return alsTag(d);
}

/** Tage im Monat (Monat 1 bis 12) */
export function tageImMonat(jahr: number, monat: number): number {
  return new Date(jahr, monat, 0).getDate();
}

/** Letzter Tag des Monats, in dem der Tag liegt */
export function monatsende(tag: string): string {
  const jahr = Number(tag.slice(0, 4)), monat = Number(tag.slice(5, 7));
  return `${tag.slice(0, 8)}${String(tageImMonat(jahr, monat)).padStart(2, "0")}`;
}

/** Kalenderwoche nach ISO 8601: die Woche mit dem ersten Donnerstag des Jahres ist Woche 1 */
export function kalenderwoche(tag: string): number {
  const donnerstag = plusTage(montagVon(tag), 3);
  return Math.floor(tageZwischen(`${donnerstag.slice(0, 4)}-01-01`, donnerstag) / 7) + 1;
}

/** Alle Tage von bis einschließlich bis */
export function tageVon(von: string, bis: string): string[] {
  const tage: string[] = [];
  for (let t = von; t <= bis; t = plusTage(t, 1)) tage.push(t);
  return tage;
}

/** "07:30" in Minuten seit Mitternacht */
export function minutenAus(uhrzeit: string): number {
  const [h, m] = uhrzeit.split(":").map(Number);
  return h * 60 + m;
}

/** Minuten seit Mitternacht als "07:30" */
export function uhrzeitAus(minuten: number): string {
  return `${String(Math.floor(minuten / 60)).padStart(2, "0")}:${String(minuten % 60).padStart(2, "0")}`;
}
