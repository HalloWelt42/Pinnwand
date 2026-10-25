// Rechnen mit Kalendertagen (ISO-Datum JJJJ-MM-TT, ohne Zeitzone): reine Funktionen für Serien, Kalender und
// Zeitachse. Die Darstellung von Daten und Dauern bleibt in beispiel/format.ts.

export const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
  "November", "Dezember"];
/** Wochentage ab Sonntag (wie Date.getDay); kurz wie in format.ts */
export const TAGE_KURZ = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
export const TAGE_LANG = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
/** Reihenfolge der Spalten im Kalender: Montag bis Sonntag */
export const WOCHE_AB_MONTAG = [1, 2, 3, 4, 5, 6, 0];

function alsDatum(tag: string): Date {
  return new Date(tag.slice(0, 10) + "T12:00:00");
}

export function alsTag(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function plusTage(tag: string, n: number): string {
  const d = alsDatum(tag);
  d.setDate(d.getDate() + n);
  return alsTag(d);
}

/** 0 Sonntag bis 6 Samstag */
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

export function tageImMonat(tag: string): number {
  const d = alsDatum(monatsanfang(tag));
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
}

/** Kalenderwoche nach ISO 8601 (die Woche mit dem ersten Donnerstag ist Woche 1) */
export function kalenderwoche(tag: string): number {
  const donnerstag = alsDatum(plusTage(montagVon(tag), 3));
  const jahresanfang = new Date(donnerstag.getFullYear(), 0, 1, 12);
  return 1 + Math.floor((donnerstag.getTime() - jahresanfang.getTime()) / 86400000 / 7);
}

/** "Oktober 2026" */
export function monatsname(tag: string): string {
  return `${MONATE[Number(tag.slice(5, 7)) - 1]} ${tag.slice(0, 4)}`;
}

/** alle Tage von bis einschließlich */
export function tageVon(von: string, bis: string): string[] {
  const t: string[] = [];
  for (let d = von; d <= bis; d = plusTage(d, 1)) t.push(d);
  return t;
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

/** "27.10.2026" für Datumsfelder im deutschen Format */
export function tagLang(tag: string): string {
  return `${tag.slice(8, 10)}.${tag.slice(5, 7)}.${tag.slice(0, 4)}`;
}
