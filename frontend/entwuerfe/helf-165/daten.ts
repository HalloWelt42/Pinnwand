// Beispieldaten des Entwurfs: Boards wie die Vorlagen der App, Symbole der Spalten als Vorschlag, Prioritäten mit
// Symbol und Farbe. Nach der Freigabe gehören Prioritäten und Spaltensymbole nach src/anzeige.ts.
import type { Farbe, Prioritaet, Spaltensortierung } from "../../src/modell";
import { SPALTENSORTIERUNGEN } from "../../src/anzeige";
import type { Wahlstufe as Stufe } from "appkern-oberflaeche";

export interface EntwurfSpalte {
  id: string;
  name: string;
  farbe: Farbe;
  erledigt?: boolean;
  /** gewähltes Symbol der Spalte; ohne: Vorgabe nach Rolle */
  symbol?: string;
}

const sp = (id: string, name: string, farbe: Farbe, symbol?: string, erledigt = false): EntwurfSpalte => ({ id, name, farbe, symbol, erledigt });

export const BOARDS: { name: string; spalten: EntwurfSpalte[] }[] = [
  { name: "Helfer", spalten: [sp("o", "Offen", "stahl", "fa-inbox"), sp("d", "Dran", "honig", "fa-person-digging"),
    sp("p", "Prüfung", "flieder", "fa-magnifying-glass"), sp("e", "Erledigt", "minze", "fa-circle-check", true)] },
  { name: "Entwicklung", spalten: [sp("ei", "Eingang", "stahl", "fa-inbox"), sp("g", "Geplant", "himmel", "fa-calendar-days"),
    sp("a", "In Arbeit", "honig", "fa-person-digging"), sp("p", "Prüfung", "flieder", "fa-magnifying-glass"),
    sp("e", "Erledigt", "minze", "fa-circle-check", true)] },
  { name: "Ideen", spalten: [sp("ge", "Gesammelt", "flieder", "fa-lightbulb"), sp("b", "Bewerten", "himmel", "fa-scale-balanced"),
    sp("u", "Umsetzen", "tuerkis", "fa-hammer"), sp("e", "Umgesetzt", "minze", "fa-circle-check", true)] },
  { name: "Großes Board (8 Spalten)", spalten: [sp("ei", "Eingang", "stahl", "fa-inbox"), sp("k", "Klären", "himmel", "fa-circle-question"),
    sp("g", "Geplant", "petrol", "fa-calendar-days"), sp("a", "In Arbeit", "honig", "fa-person-digging"),
    sp("w", "Wartet", "koralle", "fa-hourglass-half"), sp("p", "Prüfung", "flieder", "fa-magnifying-glass"),
    sp("f", "Freigabe", "violett", "fa-user-check"), sp("e", "Erledigt", "minze", "fa-circle-check", true)] },
];

/** Spalten ohne gewähltes Symbol: offene als Farbpunkt, die Erledigt-Spalte mit Haken */
export const ohneSymbol = (spalten: EntwurfSpalte[]): EntwurfSpalte[] => spalten.map((s) => ({ ...s, symbol: undefined }));

export function spaltenStufen(spalten: EntwurfSpalte[]): Stufe<string>[] {
  return spalten.map((s) => ({
    wert: s.id, titel: s.name, farbe: s.farbe,
    symbol: s.symbol ?? (s.erledigt ? "fa-circle-check" : "fa-circle"),
    hinweis: s.erledigt ? "schließt die Karte ab; ein laufender Timer an ihr hält an und bucht" : "verschiebt die Karte in diese Spalte",
  }));
}

/** von wenig nach viel, wie die Klappliste heute */
export function prioritaetsStufen(): Stufe<Prioritaet>[] {
  return [
    { wert: "keine", titel: "Keine", symbol: "fa-minus", hinweis: "ohne Priorität; in Spalten nach Priorität ganz unten" },
    { wert: "niedrig", titel: "Niedrig", symbol: "fa-angle-down", farbe: "stahl", hinweis: "kann warten" },
    { wert: "mittel", titel: "Mittel", symbol: "fa-equals", farbe: "honig", hinweis: "normale Arbeit" },
    { wert: "hoch", titel: "Hoch", symbol: "fa-angle-up", farbe: "warn", hinweis: "bald erledigen" },
    { wert: "dringend", titel: "Dringend", symbol: "fa-angles-up", farbe: "gefahr", hinweis: "zuerst; in Spalten nach Priorität ganz oben" },
  ];
}

/** Auswahl für das Symbol einer Spalte in den Einstellungen des Boards */
export const SPALTENSYMBOLE: [string, string][] = [
  ["fa-inbox", "Eingang"], ["fa-lightbulb", "Idee"], ["fa-circle-question", "Klären"], ["fa-scale-balanced", "Bewerten"],
  ["fa-calendar-days", "Geplant"], ["fa-list-check", "Bereit"], ["fa-person-digging", "In Arbeit"], ["fa-hammer", "Bauen"],
  ["fa-pen", "Schreiben"], ["fa-hourglass-half", "Wartet"], ["fa-pause", "Pausiert"], ["fa-magnifying-glass", "Prüfung"],
  ["fa-user-check", "Freigabe"], ["fa-truck", "Ausliefern"], ["fa-circle-check", "Erledigt"], ["fa-box-archive", "Abgelegt"],
  ["fa-ban", "Verworfen"], ["fa-circle", "Punkt"],
];

export function sortierungsStufen(): Stufe<Spaltensortierung>[] {
  return Object.entries(SPALTENSORTIERUNGEN).map(([w, s]) => ({ wert: w as Spaltensortierung, titel: s.name, symbol: s.symbol, hinweis: s.erklaerung }));
}
