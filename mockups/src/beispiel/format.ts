// Darstellung von Zeiten, Daten und Dauern, überall gleich (in der App dieselben Funktionen).

import { HEUTE, JETZT } from "./daten";

const TAGE = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];

/** 2:35 (Stunden:Minuten); mit Sekunden 2:35:10 */
export function dauer(sek: number, mitSekunden = false): string {
  const h = Math.floor(sek / 3600);
  const m = Math.floor((sek % 3600) / 60);
  const s = Math.floor(sek % 60);
  return mitSekunden ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${h}:${String(m).padStart(2, "0")}`;
}

/** 27.10. oder mit Wochentag "Di 27.10." */
export function datum(iso: string, mitTag = false): string {
  const d = new Date(iso.slice(0, 10) + "T12:00:00");
  const t = `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.`;
  return mitTag ? `${TAGE[d.getDay()]} ${t}` : t;
}

export function uhrzeit(iso: string): string {
  return iso.slice(11, 16);
}

/** Tage zwischen zwei Daten (ganze Kalendertage) */
export function tageZwischen(von: string, bis: string): number {
  const a = new Date(von.slice(0, 10) + "T12:00:00").getTime();
  const b = new Date(bis.slice(0, 10) + "T12:00:00").getTime();
  return Math.round((b - a) / 86400000);
}

/** Alter im Status in Tagen ab dem letzten Spaltenwechsel */
export function alterTage(bewegtAm: string): number {
  return tageZwischen(bewegtAm, HEUTE);
}

/** Fälligkeit relativ zu heute: "heute", "morgen", "überfällig seit 1 Tag", sonst Datum */
export function faelligText(iso: string): { text: string; klasse: "" | "warnung" | "gefahr" } {
  const t = tageZwischen(HEUTE, iso);
  if (t < 0) return { text: `${-t} ${-t === 1 ? "Tag" : "Tage"} über`, klasse: "gefahr" };
  if (t === 0) return { text: "heute", klasse: "warnung" };
  if (t === 1) return { text: "morgen", klasse: "" };
  return { text: datum(iso, true), klasse: "" };
}

/** Laufende Sekunden eines Timers bis jetzt */
export function laufendSek(seit: string): number {
  return Math.max(0, (new Date(JETZT).getTime() - new Date(seit).getTime()) / 1000);
}

/** "vor 3 Std.", "gestern 15:40", "26.10. 15:40" */
export function wann(iso: string): string {
  const t = tageZwischen(iso, HEUTE);
  if (t === 0) {
    const min = Math.round((new Date(JETZT).getTime() - new Date(iso).getTime()) / 60000);
    return min < 60 ? `vor ${min} Min.` : `vor ${Math.round(min / 60)} Std.`;
  }
  if (t === 1) return `gestern ${uhrzeit(iso)}`;
  return `${datum(iso)} ${uhrzeit(iso)}`;
}
