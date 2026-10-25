// Kürzel eines Boards: Vorschlag aus dem Namen und Prüfung. Das Kürzel bleibt nach dem Anlegen fest, ist über alle
// Boards eindeutig (der Server prüft auch Boards, die du nicht siehst) und besteht nur aus Großbuchstaben und Ziffern.
// Umlaute werden ausgeschrieben statt verworfen (die alte App machte aus "Übersicht" das Kürzel "BER", M-02).

import type { Board } from "../../modell";

const UMLAUTE: Record<string, string> = { Ä: "AE", Ö: "OE", Ü: "UE" };
export const KUERZEL_MUSTER = /^[A-Z][A-Z0-9]{1,5}$/;
const LAENGE = 6;

/** Großbuchstaben, Umlaute ausgeschrieben (ß wird beim Großschreiben zu SS) */
export function ausschreiben(text: string): string {
  return text.toUpperCase().replace(/[ÄÖÜ]/g, (z) => UMLAUTE[z]);
}

/** Eingabe im Kürzelfeld: nur, was ein Kürzel tragen darf */
export function saeubern(eingabe: string): string {
  return ausschreiben(eingabe).replace(/[^A-Z0-9]/g, "").slice(0, LAENGE);
}

function woerter(name: string): string[] {
  return ausschreiben(name).split(/[^A-Z0-9]+/).filter(Boolean);
}

/** Grundform aus dem Namen: ein Wort gibt seine ersten vier Zeichen, mehrere die Anfänge (Zahlen ganz) */
function grundform(name: string): string {
  const w = woerter(name);
  if (!w.length) return "";
  let k = w.length === 1 ? w[0].slice(0, 4) : w.slice(0, 4).map((x) => (/^\d+$/.test(x) ? x : x[0])).join("").slice(0, LAENGE);
  if (k.length < 2) k = w[0].slice(0, 4);
  return /^\d/.test(k) ? ("B" + k).slice(0, LAENGE) : k;
}

export interface Belegung {
  boards: Board[];
  anderer: string[];
}

/** Wem ein Kürzel gehört: einem sichtbaren Board (Name), einem fremden ("") oder niemandem (undefined) */
export function besitzer(k: string, belegt: Belegung): string | undefined {
  const b = belegt.boards.find((x) => x.kuerzel === k);
  if (b) return b.name;
  return belegt.anderer.includes(k) ? "" : undefined;
}

/** freie Abwandlungen: Ziffer anhängen */
function abwandlungen(k: string, belegt: Belegung): string[] {
  const frei: string[] = [];
  for (let n = 2; n <= 9 && frei.length < 3; n++) {
    const v = k.slice(0, LAENGE - 1) + n;
    if (besitzer(v, belegt) === undefined) frei.push(v);
  }
  return frei;
}

/** Vorschlag aus dem Namen, schon frei */
export function vorschlag(name: string, belegt: Belegung): string {
  const k = grundform(name);
  if (!k || besitzer(k, belegt) === undefined) return k;
  return abwandlungen(k, belegt)[0] ?? k;
}

export interface Pruefung {
  stand: "leer" | "form" | "vergeben" | "frei";
  text: string;
  frei: string[];
}

export function pruefen(k: string, name: string, belegt: Belegung): Pruefung {
  if (!k) return { stand: "leer", text: "Ein Kürzel braucht jedes Board, es steht vor jeder Kartennummer.", frei: [] };
  if (!KUERZEL_MUSTER.test(k)) return { stand: "form", text: "2 bis 6 Zeichen, vorne ein Buchstabe.", frei: [] };
  const wer = besitzer(k, belegt);
  if (wer === undefined) return { stand: "frei", text: `Frei. Karten heißen ${k}-1, ${k}-2 und so weiter.`, frei: [] };
  const aus = vorschlag(name, belegt);
  const frei = [...new Set([...(aus && aus !== k ? [aus] : []), ...abwandlungen(k, belegt)])].slice(0, 3);
  return { stand: "vergeben", frei,
           text: wer ? `${k} ist schon vergeben, an das Board ${wer}.` : `${k} ist schon vergeben, an ein Board, das du nicht siehst.` };
}
