// Lesehilfen der Ansichten der Planung, ohne eigenen Zustand: welche Boards Serien haben, Karten eines Boards mit Suche,
// Abwesenheiten und Feiertage der Mitglieder, Stand einer Person bei einem Termin und der Inhalt eines Kalendertags.
// Gerechnet wird mit den Regeln (regeln/) und dem einen Zustand (daten/stand.svelte.ts); geändert wird nur über die
// Anwendungsfälle.

import { darf, kartenNummer, kartePasst, leererFilter, type Kartenfilter } from "../../daten/abfragen";
import { serienUmfeld } from "../../daten/abfragen";
import { uhr } from "../../daten/uhr.svelte";
import { ICH } from "../../daten/ich";
import { konto, mitKonto, stand } from "../../daten/stand.svelte";
import type { Abwesenheit, Board, Karte, Kennung, Serie, Termin } from "../../modell";
import { abwesenheitAm, ARTEN, artName, fassungAm } from "../../regeln/arbeitszeit";
import { modulAn } from "../../regeln/board";
import { feiertag } from "../../regeln/feiertage";
import { vorkommen, type Vorkommen } from "../../regeln/serien";
import { boardPfad } from "../../weg.svelte";

export { serienUmfeld };

/** Boards, in denen du Mitglied bist und das Modul Serien und Termine an ist */
export function boardsMitSerien(): Board[] {
  return stand.boards.filter((b) => modulAn(b, "serien", stand.moduleDa) && b.mitglieder.some((m) => m.konto === ICH));
}

export function boardVon(id: Kennung): Board | undefined {
  return stand.boards.find((b) => b.id === id);
}

/** Karten eines Boards, bei Suche und Filter nur die passenden (dieselbe Abfrage wie Board und Liste) */
export function kartenDesBoards(b: Board, filter: Kartenfilter = leererFilter()): Karte[] {
  return stand.karten.filter((k) => k.board === b.id && kartePasst(k, b, filter));
}

export function istErledigt(b: Board, k: Karte): boolean {
  return b.spalten.find((s) => s.id === k.spalte)?.erledigt ?? false;
}

export function farbeDerSpalte(b: Board, k: Karte): string {
  return b.spalten.find((s) => s.id === k.spalte)?.farbe ?? "stahl";
}

export function kartenPfad(b: Board, k: Karte): string {
  return boardPfad(b.kuerzel, kartenNummer(k));
}

// ═══ Aktivität aus Zeiteinträgen (HELF-46) ══════════════════════════════════════════════════════════════════

/** Gebuchte Zeit einer Karte an einem Tag, je Person (die eigene und, mit dem Recht, die anderer) */
export interface Aktivitaet {
  tag: string;
  /** je Person die Sekunden, größte zuerst */
  personen: { konto: Kennung; sekunden: number }[];
  sekunden: number;
}

/** Was an den Karten eines Boards zwischen `von` und `bis` gearbeitet wurde: je Karte die Tage mit gebuchter Zeit. Ohne
 *  `person` alle sichtbaren Einträge, sonst nur ihre. Gerechnet aus den Zeiteinträgen im Stand (sie folgen der Sicht). */
export function aktivitaetDesBoards(b: Board, von: string, bis: string, person?: Kennung): Map<Kennung, Aktivitaet[]> {
  const je = new Map<Kennung, Map<string, Map<Kennung, number>>>();
  for (const z of stand.zeiteintraege) {
    if (z.board !== b.id || !z.karte || z.datum < von || z.datum > bis || (person && z.konto !== person) || z.sekunden <= 0) continue;
    const tage = je.get(z.karte) ?? new Map<string, Map<Kennung, number>>();
    const leute = tage.get(z.datum) ?? new Map<Kennung, number>();
    leute.set(z.konto, (leute.get(z.konto) ?? 0) + z.sekunden);
    tage.set(z.datum, leute);
    je.set(z.karte, tage);
  }
  const ergebnis = new Map<Kennung, Aktivitaet[]>();
  for (const [karte, tage] of je) {
    ergebnis.set(karte, [...tage].sort(([a], [b]) => a.localeCompare(b)).map(([tag, leute]) => {
      const personen = [...leute].map(([konto, sekunden]) => ({ konto, sekunden })).sort((x, y) => y.sekunden - x.sekunden);
      return { tag, personen, sekunden: personen.reduce((s, x) => s + x.sekunden, 0) };
    }));
  }
  return ergebnis;
}

// ═══ Abwesenheiten und Feiertage ══════════════════════════════════════════════════════════════════════════

/** Abwesenheiten der Mitglieder sieht nur, wer im Board das Recht hat, und nur mit dem Modul Arbeitszeit */
export function abwesenheitenSichtbar(b: Board): boolean {
  return b.module.arbeitszeit && darf(b, "abwesenheit.sehen");
}

export function abwesenheit(kontoId: Kennung, tag: string): Abwesenheit | undefined {
  return abwesenheitAm(stand.abwesenheiten, kontoId, tag);
}

export function abwesenheitSymbol(a: Abwesenheit): string {
  return ARTEN[a.art].symbol;
}

export { artName };

export interface FeiertagAm {
  name: string;
  /** betroffene Personen und ihre Bundesländer */
  konten: Kennung[];
  laender: string[];
}

/** Feiertage eines Tages nach den Bundesländern der Personen (aus ihrem Zeitkonto), mit den Betroffenen */
export function feiertageAm(tag: string, konten: Kennung[]): FeiertagAm[] {
  const m = new Map<string, FeiertagAm>();
  for (const k of konten) {
    const land = fassungAm(stand.zeitkonten, k, tag)?.bundesland;
    const name = land ? feiertag(tag, land) : undefined;
    if (!land || !name) continue;
    const f = m.get(name) ?? { name, konten: [], laender: [] };
    f.konten.push(k);
    if (!f.laender.includes(land)) f.laender.push(land);
    m.set(name, f);
  }
  return [...m.values()];
}

/** "Allerheiligen: Feiertag in Nordrhein-Westfalen (Max Paulsen, Anna Berger)" */
export function feiertagTitel(f: FeiertagAm): string {
  return `${f.name}: Feiertag in ${f.laender.join(" und ")} (${f.konten.map((k) => konto(k).name).join(", ")})`;
}

// ═══ Termine ════════════════════════════════════════════════════════════════════════════════════════════════

/** Stand einer Person bei einem Termin, immer mit Wort: vorher zugesagt oder offen, danach bestätigt oder wartet;
 *  abwesend mit dem Wort der Abwesenheit (nur mit Recht) */
export function terminStand(t: Termin, k: Kennung): { text: string; symbol: string; klasse: "gut" | "warnung" | "offen" } {
  const b = boardVon(t.board);
  const a = b && abwesenheitenSichtbar(b) ? abwesenheit(k, t.datum) : undefined;
  if (a) return { text: artName(a), symbol: abwesenheitSymbol(a), klasse: "warnung" };
  if (t.datum < uhr.heute) {
    return t.bestaetigt.includes(k) ? { text: "bestätigt", symbol: "fa-circle-check", klasse: "gut" } : { text: "wartet", symbol: "fa-hourglass-half", klasse: "offen" };
  }
  return t.zugesagt.includes(k) ? { text: "zugesagt", symbol: "fa-circle-check", klasse: "gut" } : { text: "offen", symbol: "fa-circle-question", klasse: "offen" };
}

// ═══ Inhalt eines Kalendertags ══════════════════════════════════════════════════════════════════════════════

export interface Zeigen {
  karten: boolean;
  termine: boolean;
  serien: boolean;
  abwesenheiten: boolean;
}

export interface TagInhalt {
  tag: string;
  karten: Karte[];
  termine: Termin[];
  serien: { serie: Serie; v: Vorkommen }[];
  abwesend: Abwesenheit[];
  feiertage: FeiertagAm[];
}

/** Stände eines Serientags, die im Kalender erscheinen (nicht gelöscht, entfallen, verworfen, pausiert) */
const SICHTBAR: Vorkommen["stand"][] = ["gezaehlt", "wartet", "heute", "vorgebucht", "beruehrt", "geplant"];

/** Inhalte aller Tage eines Zeitraums: Karten nach Fälligkeit, Termine, Serientage (ein Tag mit Karte erscheint nur als
 *  Karte), Abwesenheiten der Mitglieder (mit Recht) und Feiertage ihrer Bundesländer */
export function tageInhalt(b: Board, tage: string[], karten: Karte[], zeigen: Zeigen): Map<string, TagInhalt> {
  const mitglieder = mitKonto(b).map((m) => m.konto);
  const u = serienUmfeld();
  const serientage = b.module.serien && zeigen.serien
    ? stand.serien.filter((s) => s.board === b.id).flatMap((s) => vorkommen(s, tage[0], tage[tage.length - 1], u)
      .filter((v) => SICHTBAR.includes(v.stand)).map((v) => ({ serie: s, v })))
    : [];
  const mitAbwesenheit = zeigen.abwesenheiten && abwesenheitenSichtbar(b);
  const termine = b.module.serien && zeigen.termine ? stand.termine.filter((t) => t.board === b.id) : [];
  const m = new Map<string, TagInhalt>();
  for (const tag of tage) {
    m.set(tag, {
      tag,
      karten: zeigen.karten ? karten.filter((k) => k.faellig === tag) : [],
      termine: termine.filter((t) => t.datum === tag).sort((a, c) => a.von.localeCompare(c.von)),
      serien: serientage.filter((x) => x.v.tag === tag && !x.v.karte).sort((a, c) => (a.serie.uhrzeit ?? "").localeCompare(c.serie.uhrzeit ?? "")),
      abwesend: mitAbwesenheit ? mitglieder.map((k) => abwesenheit(k, tag)).filter((a): a is Abwesenheit => a !== undefined) : [],
      feiertage: feiertageAm(tag, mitglieder),
    });
  }
  return m;
}
