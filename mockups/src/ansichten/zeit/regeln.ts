// Regeln der Module Zeiterfassung und Arbeitszeit als reine Funktionen ohne Ein- und Ausgabe (in der App dieselben
// Funktionen im Modul, auf dem Server und in der Oberfläche): Kalendertage, Feiertage je Bundesland, Soll eines Tags
// aus dem Zeitkonto, Urlaubstage, Brückentage, Lesen von Dauer und Datum. Alle Daten als ISO-Zeichenkette (JJJJ-MM-TT).

import type { Abwesenheit, AbwesenheitArt, Zeitkonto } from "../../modell";

// ═══ Kalendertage ════════════════════════════════════════════════════════════════════════════════════════

function alsDatum(iso: string): Date {
  return new Date(iso.slice(0, 10) + "T12:00:00");
}

export function iso(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** ganze Kalendertage von a nach b (gerundet, damit die Zeitumstellung nichts verschiebt) */
export function tageDazwischen(a: string, b: string): number {
  return Math.round((alsDatum(b).getTime() - alsDatum(a).getTime()) / 86400000);
}

export function plusTage(tag: string, n: number): string {
  const d = alsDatum(tag);
  d.setDate(d.getDate() + n);
  return iso(d);
}

/** Wochentag wie Date.getDay(): 0 Sonntag, 1 Montag bis 6 Samstag (so zählt auch Zeitkonto.tage) */
export function wochentag(tag: string): number {
  return alsDatum(tag).getDay();
}

export function montagDer(tag: string): string {
  return plusTage(tag, -((wochentag(tag) + 6) % 7));
}

/** Alle Tage von bis einschließlich bis */
export function tageVonBis(von: string, bis: string): string[] {
  const out: string[] = [];
  for (let t = von; t <= bis; t = plusTage(t, 1)) out.push(t);
  return out;
}

/** Kalenderwoche nach ISO 8601 (Woche mit dem ersten Donnerstag ist KW 1) */
export function kalenderwoche(tag: string): number {
  const donnerstag = plusTage(montagDer(tag), 3);
  const neujahr = `${donnerstag.slice(0, 4)}-01-01`;
  return Math.floor(tageDazwischen(neujahr, donnerstag) / 7) + 1;
}

export function tageImMonat(jahr: number, monat: number): number {
  return new Date(jahr, monat, 0).getDate();
}

export const MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
export const TAGNAMEN = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];

// ═══ Feiertage je Bundesland ═════════════════════════════════════════════════════════════════════════════

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

const FEIERTAGE: FeiertagRegel[] = [
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

const feiertagsCache = new Map<string, Map<string, string>>();

/** Feiertage eines Jahres in einem Bundesland: Tag auf Name */
export function feiertage(jahr: number, bundesland: string): Map<string, string> {
  const schluessel = `${jahr}|${bundesland}`;
  let m = feiertagsCache.get(schluessel);
  if (!m) {
    m = new Map();
    for (const f of FEIERTAGE) if (!f.laender.length || f.laender.includes(bundesland)) m.set(f.tag(jahr), f.name);
    feiertagsCache.set(schluessel, m);
  }
  return m;
}

export function feiertag(tag: string, bundesland: string): string | undefined {
  return feiertage(Number(tag.slice(0, 4)), bundesland).get(tag);
}

// ═══ Abwesenheiten: Wirkung je Art ═══════════════════════════════════════════════════════════════════════

export interface ArtWirkung {
  name: string;
  /** Wort für schmale Spaltenköpfe */
  knapp: string;
  kurz: string;
  symbol: string;
  /** Faktor auf das Soll des Tags: 0 Soll entfällt, 0,5 halb, 1 bleibt (Ausgleich baut Überstunden ab) */
  soll: number;
  /** Anteil, der als Urlaubstag zählt */
  urlaub: number;
  wirkung: string;
}

/** Eine Wahrheit für die Wirkung jeder Art (in der App Regel des Moduls Arbeitszeit) */
export const ARTEN: Record<AbwesenheitArt, ArtWirkung> = {
  urlaub: { name: "Urlaub", knapp: "Urlaub", kurz: "U", symbol: "fa-umbrella-beach", soll: 0, urlaub: 1, wirkung: "Soll entfällt, zählt als Urlaubstag" },
  halbtag: { name: "Halber Urlaubstag", knapp: "½ Urlaub", kurz: "½", symbol: "fa-circle-half-stroke", soll: 0.5, urlaub: 0.5, wirkung: "Soll halb, zählt als halber Urlaubstag" },
  krank: { name: "Krank", knapp: "Krank", kurz: "K", symbol: "fa-house-medical", soll: 0, urlaub: 0, wirkung: "Soll entfällt, kein Urlaubstag" },
  frei: { name: "Frei (Ausgleich)", knapp: "Ausgleich", kurz: "F", symbol: "fa-mug-hot", soll: 1, urlaub: 0, wirkung: "Soll bleibt, baut Überstunden ab" },
  fortbildung: { name: "Fortbildung", knapp: "Fortbildung", kurz: "Fb", symbol: "fa-graduation-cap", soll: 0, urlaub: 0, wirkung: "Soll entfällt, kein Urlaubstag" },
  feiertag: { name: "Betrieblich frei", knapp: "Betrieb frei", kurz: "B", symbol: "fa-star", soll: 0, urlaub: 0, wirkung: "Soll entfällt wie an einem Feiertag" },
};

// ═══ Soll eines Tags ═════════════════════════════════════════════════════════════════════════════════════

/** Halber Arbeitstag an einem festen Tag im Jahr (Halbtagsregel des Zeitkontos) */
export interface Halbtagsregel {
  monat: number;
  tag: number;
  name: string;
}

export type SollGrund = "arbeitstag" | "wochenende" | "arbeitsfrei" | "feiertag" | "halbtagsregel" | AbwesenheitArt;

export interface TagSoll {
  tag: string;
  /** Soll ohne Abwesenheit (nach Arbeitstag, Feiertag, Halbtagsregel) */
  basisSek: number;
  sollSek: number;
  grund: SollGrund;
  feiertag?: string;
  regel?: string;
  abwesenheit?: Abwesenheit;
  /** verbrauchte Urlaubstage an diesem Tag */
  urlaubstage: number;
}

export function abwesenheitAm(liste: Abwesenheit[], konto: string, tag: string): Abwesenheit | undefined {
  return liste.find((a) => a.konto === konto && a.von <= tag && tag <= a.bis);
}

/** Soll eines Tags in klarer Reihenfolge: Arbeitstag des Kontos, Feiertag des Bundeslands, Halbtagsregel,
 *  Abwesenheit (wie die Kalenderlogik der alten App, jetzt je Konto) */
export function sollAm(k: Zeitkonto, regeln: Halbtagsregel[], abwesenheiten: Abwesenheit[], tag: string): TagSoll {
  const wt = wochentag(tag);
  const tagesSek = k.tage.length ? Math.round((k.wochenstunden * 3600) / k.tage.length) : 0;
  const ft = feiertag(tag, k.bundesland);
  const abw = abwesenheitAm(abwesenheiten, k.konto, tag);
  if (!k.tage.includes(wt)) return { tag, basisSek: 0, sollSek: 0, grund: wt === 0 || wt === 6 ? "wochenende" : "arbeitsfrei", feiertag: ft, urlaubstage: 0 };
  if (ft) return { tag, basisSek: 0, sollSek: 0, grund: "feiertag", feiertag: ft, urlaubstage: 0 };
  const regel = regeln.find((r) => Number(tag.slice(5, 7)) === r.monat && Number(tag.slice(8, 10)) === r.tag);
  const basis = regel ? tagesSek / 2 : tagesSek;
  const anteil = basis / tagesSek;
  if (abw) {
    const w = ARTEN[abw.art];
    return { tag, basisSek: basis, sollSek: basis * w.soll, grund: abw.art, regel: regel?.name, abwesenheit: abw, urlaubstage: w.urlaub * anteil };
  }
  return { tag, basisSek: basis, sollSek: basis, grund: regel ? "halbtagsregel" : "arbeitstag", regel: regel?.name, urlaubstage: 0 };
}

/** Wirkung einer (geplanten) Abwesenheit: Arbeitstage, entfallendes Soll, Urlaubstage */
export function wirkung(k: Zeitkonto, regeln: Halbtagsregel[], a: Abwesenheit): { arbeitstage: number; sollSek: number; urlaubstage: number; tage: TagSoll[] } {
  const tage = tageVonBis(a.von, a.bis).map((t) => sollAm(k, regeln, [a], t));
  const arbeit = tage.filter((t) => t.basisSek > 0);
  return {
    tage,
    arbeitstage: arbeit.reduce((s, t) => s + (t.regel ? 0.5 : 1), 0),
    sollSek: arbeit.reduce((s, t) => s + (t.basisSek - t.sollSek), 0),
    urlaubstage: arbeit.reduce((s, t) => s + t.urlaubstage, 0),
  };
}

/** Urlaubstage eines Jahres bis einschließlich bis (oder nach bis), gewichtet mit der echten Wirkung des Tags */
export function urlaubstage(k: Zeitkonto, regeln: Halbtagsregel[], abwesenheiten: Abwesenheit[], jahr: number, bis: string, danach = false): number {
  let summe = 0;
  for (const a of abwesenheiten.filter((x) => x.konto === k.konto && ARTEN[x.art].urlaub > 0)) {
    for (const t of tageVonBis(a.von, a.bis)) {
      if (Number(t.slice(0, 4)) !== jahr || (danach ? t <= bis : t > bis)) continue;
      summe += sollAm(k, regeln, [a], t).urlaubstage;
    }
  }
  return summe;
}

// ═══ Brückentage ═════════════════════════════════════════════════════════════════════════════════════════

export interface Brueckentag {
  tag: string;
  /** der Feiertag, an den er grenzt */
  feiertag: string;
  /** freie Tage am Stück, wenn man ihn nimmt */
  frei: number;
}

/** Arbeitstage, deren beide Nachbartage frei sind (Feiertag oder kein Arbeitstag), mit einem Feiertag daneben */
export function brueckentage(k: Zeitkonto, von: string, bis: string): Brueckentag[] {
  const frei = (t: string) => !k.tage.includes(wochentag(t)) || !!feiertag(t, k.bundesland);
  const out: Brueckentag[] = [];
  for (const t of tageVonBis(von, bis)) {
    if (frei(t)) continue;
    const vor = plusTage(t, -1), nach = plusTage(t, 1);
    if (!frei(vor) || !frei(nach)) continue;
    const ft = feiertag(vor, k.bundesland) ?? feiertag(nach, k.bundesland);
    if (!ft) continue;
    let a = vor, b = nach;
    while (frei(plusTage(a, -1))) a = plusTage(a, -1);
    while (frei(plusTage(b, 1))) b = plusTage(b, 1);
    out.push({ tag: t, feiertag: ft, frei: tageVonBis(a, b).length });
  }
  return out;
}

// ═══ Eingaben lesen ══════════════════════════════════════════════════════════════════════════════════════

/** Dauer wie bisher: "1:30" und "1:30:15" (Stunden:Minuten[:Sekunden]), "1,5" oder "1.5" Stunden, "90m" oder "90min",
 *  "2h" oder "2std"; eine Zahl ohne Einheit sind Stunden. Unlesbares ergibt null (und wird angezeigt, nie still verworfen). */
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

/** Datum in deutscher Schreibweise, nachsichtig: "3.9.2026", "03.09.26", "3.9." (laufendes Jahr), "03092026" */
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
