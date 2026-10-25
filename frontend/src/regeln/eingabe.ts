// Eingaben lesen, überall gleich (Rechner und Telefon): Dauer wie in der alten App und Datum in deutscher Schreibweise.
// Unlesbares ergibt null; die Ansicht zeigt es dann an, statt still nichts zu tun.

import { tageImMonat } from "./tage";

/** Dauer: "1:30" und "1:30:15" (Stunden:Minuten[:Sekunden]), "1,5" oder "1.5" Stunden, "90m" oder "90min", "2h" oder
 *  "2std"; eine Zahl ohne Einheit sind Stunden. Ergebnis in Sekunden. */
export function dauerLesen(text: string): number | null {
  const t = text.trim().toLowerCase().replace(/\s+/g, "");
  if (!t) return null;
  let m = t.match(/^(\d+):([0-5]?\d)(?::([0-5]?\d))?$/);
  if (m) return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3] ?? 0);
  m = t.match(/^(\d+)(?:m|min)$/);
  if (m) return Number(m[1]) * 60;
  m = t.match(/^(\d+(?:[.,]\d+)?)(?:h|std)?$/);
  if (m) return Math.round(Number(m[1].replace(",", ".")) * 3600);
  return null;
}

/** Datum nachsichtig: "3.9.2026", "03.09.26", "3.9." (im gegebenen Jahr), "03092026"; Ergebnis als ISO-Tag */
export function datumLesen(text: string, jahr: number): string | null {
  const t = text.trim();
  let m = t.match(/^(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})?$/);
  if (!m) {
    const z = t.match(/^(\d{2})(\d{2})(\d{4})$/);
    if (z) m = [t, z[1], z[2], z[3]] as unknown as RegExpMatchArray;
  }
  if (!m) return null;
  const tg = Number(m[1]), mo = Number(m[2]);
  const j = m[3] ? (m[3].length === 2 ? 2000 + Number(m[3]) : Number(m[3])) : jahr;
  if (mo < 1 || mo > 12 || tg < 1 || tg > tageImMonat(j, mo)) return null;
  return `${j}-${String(mo).padStart(2, "0")}-${String(tg).padStart(2, "0")}`;
}

/** ISO-Tag als Text eines Datumsfelds: "27.10.2026" */
export function datumText(tag: string): string {
  return `${tag.slice(8, 10)}.${tag.slice(5, 7)}.${tag.slice(0, 4)}`;
}
