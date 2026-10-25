// Eingaben am Telefon lesen: Dauer wie bisher (M-90) und Datum im deutschen Format. Unlesbares ergibt null, damit die
// Ansicht einen Hinweis zeigt, statt still nichts zu tun.

import { HEUTE } from "../../beispiel/daten";

/** "1:30", "1:30:00", "1,5" oder "1.5" (Stunden), "90m" oder "90min", "2h" oder "2std"; Zahl ohne Einheit: Stunden */
export function dauerLesen(text: string): number | null {
  const t = text.trim().toLowerCase().replace(/\s+/g, "");
  let m = t.match(/^(\d+):(\d{1,2})(?::(\d{1,2}))?$/);
  if (m) return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3] ?? 0);
  m = t.match(/^(\d+)(?:m|min)$/);
  if (m) return Number(m[1]) * 60;
  m = t.match(/^(\d+(?:[.,]\d+)?)(?:h|std)?$/);
  if (m) return Math.round(Number(m[1].replace(",", ".")) * 3600);
  return null;
}

/** "27.10.2026" oder "27.10." (laufendes Jahr) als ISO-Datum */
export function datumLesen(text: string): string | null {
  const m = text.trim().match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})?$/);
  if (!m) return null;
  const iso = `${m[3] ?? HEUTE.slice(0, 4)}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
  const d = new Date(iso + "T12:00:00");
  return Number.isNaN(d.getTime()) || d.toISOString().slice(0, 10) !== iso ? null : iso;
}

/** ISO-Datum als Eingabetext "27.10.2026" */
export function datumText(iso: string): string {
  return `${iso.slice(8, 10)}.${iso.slice(5, 7)}.${iso.slice(0, 4)}`;
}

/** ISO-Datum n Tage nach einem Tag */
export function tagePlus(iso: string, n: number): string {
  const d = new Date(iso + "T12:00:00");
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Nächster Tag mit diesem Wochentag (0 Sonntag bis 6 Samstag) nach heute */
export function naechster(wochentag: number): string {
  const heute = new Date(HEUTE + "T12:00:00").getDay();
  return tagePlus(HEUTE, ((wochentag - heute + 6) % 7) + 1);
}

/** Montag der Woche eines Tages */
export function wochenanfang(iso: string): string {
  const tag = new Date(iso + "T12:00:00").getDay();
  return tagePlus(iso, -((tag + 6) % 7));
}
