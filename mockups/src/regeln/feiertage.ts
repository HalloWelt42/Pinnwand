// Gesetzliche Feiertage je Bundesland als reine Regel: feste Tage und die beweglichen nach der Osterformel. Eine Quelle
// für Soll und Urlaub (Arbeitszeit), Vorlauf der Serien und die Kalender.

import { plusTage, wochentag } from "./tage";

export const BUNDESLAENDER = [
  "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern",
  "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
  "Schleswig-Holstein", "Thüringen",
] as const;

/** Ostersonntag nach der Gaußschen Osterformel (gregorianisch) */
function ostersonntag(jahr: number): string {
  const a = jahr % 19, b = Math.floor(jahr / 100), c = jahr % 100, d = Math.floor(b / 4), e = b % 4;
  const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
  const monat = Math.floor((h + l - 7 * m + 114) / 31), tag = ((h + l - 7 * m + 114) % 31) + 1;
  return `${jahr}-${String(monat).padStart(2, "0")}-${String(tag).padStart(2, "0")}`;
}

/** Buß- und Bettag: der Mittwoch vor dem 23. November */
function bussUndBettag(jahr: number): string {
  let t = `${jahr}-11-22`;
  while (wochentag(t) !== 3) t = plusTage(t, -1);
  return t;
}

interface FeiertagRegel {
  name: string;
  tag: (jahr: number) => string;
  /** leer: in allen Ländern */
  laender: string[];
}

const fest = (mmtt: string) => (jahr: number) => `${jahr}-${mmtt}`;
const ostern = (n: number) => (jahr: number) => plusTage(ostersonntag(jahr), n);

const REGELN: FeiertagRegel[] = [
  { name: "Neujahr", tag: fest("01-01"), laender: [] },
  { name: "Heilige Drei Könige", tag: fest("01-06"), laender: ["Baden-Württemberg", "Bayern", "Sachsen-Anhalt"] },
  { name: "Frauentag", tag: fest("03-08"), laender: ["Berlin", "Mecklenburg-Vorpommern"] },
  { name: "Karfreitag", tag: ostern(-2), laender: [] },
  { name: "Ostersonntag", tag: ostern(0), laender: ["Brandenburg"] },
  { name: "Ostermontag", tag: ostern(1), laender: [] },
  { name: "Tag der Arbeit", tag: fest("05-01"), laender: [] },
  { name: "Christi Himmelfahrt", tag: ostern(39), laender: [] },
  { name: "Pfingstsonntag", tag: ostern(49), laender: ["Brandenburg"] },
  { name: "Pfingstmontag", tag: ostern(50), laender: [] },
  { name: "Fronleichnam", tag: ostern(60), laender: ["Baden-Württemberg", "Bayern", "Hessen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland"] },
  { name: "Mariä Himmelfahrt", tag: fest("08-15"), laender: ["Saarland"] },
  { name: "Weltkindertag", tag: fest("09-20"), laender: ["Thüringen"] },
  { name: "Tag der Deutschen Einheit", tag: fest("10-03"), laender: [] },
  { name: "Reformationstag", tag: fest("10-31"), laender: ["Brandenburg", "Bremen", "Hamburg", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"] },
  { name: "Allerheiligen", tag: fest("11-01"), laender: ["Baden-Württemberg", "Bayern", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland"] },
  { name: "Buß- und Bettag", tag: bussUndBettag, laender: ["Sachsen"] },
  { name: "1. Weihnachtstag", tag: fest("12-25"), laender: [] },
  { name: "2. Weihnachtstag", tag: fest("12-26"), laender: [] },
];

const zwischenspeicher = new Map<string, Map<string, string>>();

/** Feiertage eines Jahres in einem Bundesland: Tag auf Name */
export function feiertage(jahr: number, bundesland: string): Map<string, string> {
  const schluessel = `${jahr}|${bundesland}`;
  let m = zwischenspeicher.get(schluessel);
  if (!m) {
    m = new Map();
    for (const f of REGELN) if (!f.laender.length || f.laender.includes(bundesland)) m.set(f.tag(jahr), f.name);
    zwischenspeicher.set(schluessel, m);
  }
  return m;
}

/** Name des Feiertags an diesem Tag im Bundesland, sonst nichts */
export function feiertag(tag: string, bundesland: string): string | undefined {
  return feiertage(Number(tag.slice(0, 4)), bundesland).get(tag);
}
