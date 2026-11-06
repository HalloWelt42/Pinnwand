// Namen und Zeichen für Menschen, eine Quelle für alle Ansichten: Farben, Zeitfenster, Prioritäten, Herkunft von Zeiten,
// Hinweise und Module. Schlüssel werden nie gedruckt, immer ihr Name von hier.

import type { Wahlstufe } from "appkern-oberflaeche";
import type { Farbe, Herkunft, HinweisArt, HinweisWeg, Kennung, ModulKennung, Prioritaet, Spalte, Spaltensortierung, Zeitfenster } from "./modell";

/** Palette in der Reihenfolge jeder Farbwahl; Wort und Farbe gehören zusammen */
export const FARBEN: Farbe[] = ["koralle", "rose", "violett", "flieder", "himmel", "petrol", "tuerkis", "minze", "honig", "sand", "stahl"];

export const FARBNAMEN: Record<Farbe, string> = {
  koralle: "Koralle", rose: "Rose", violett: "Violett", flieder: "Flieder", himmel: "Himmel", petrol: "Petrol",
  tuerkis: "Türkis", minze: "Minze", honig: "Honig", sand: "Sand", stahl: "Stahl",
};

/** Zeitfenster einer Erledigt-Spalte; die Vorgabe neuer Spalten ist "heute" (wie in der alten App) */
export const ZEITFENSTER: Record<Zeitfenster, string> = {
  heute: "Heute", gestern: "Gestern", woche: "Diese Woche", monat: "Dieser Monat", jahr: "Dieses Jahr", alle: "Alle",
};
export const ZEITFENSTER_VORGABE: Zeitfenster = "heute";

/** Sortierungen einer Spalte (HELF-50) mit Namen, Symbol im Kopf der Spalte und Erklärung beim Überfahren */
export const SPALTENSORTIERUNGEN: Record<Spaltensortierung, { name: string; symbol: string; erklaerung: string }> = {
  prioritaet: { name: "Priorität", symbol: "fa-flag", erklaerung: "Dringend oben, dann Hoch, Mittel, Niedrig, ohne; bei gleicher Priorität die neueste oben" },
  faellig: { name: "Fälligkeit", symbol: "fa-calendar-day", erklaerung: "Früheste Fälligkeit oben, Karten ohne Datum unten" },
  arbeitsbeginn: { name: "Arbeitsbeginn", symbol: "fa-play", erklaerung: "Zuletzt in die Spalte gekommen oben, also zuletzt begonnen" },
  erledigung: { name: "Erledigung", symbol: "fa-clock-rotate-left", erklaerung: "Zuletzt erledigt oben, am selben Tag die zuletzt abgelegte" },
  anlage: { name: "Anlage", symbol: "fa-plus", erklaerung: "Zuletzt angelegt oben" },
  hand: { name: "Von Hand", symbol: "fa-hand", erklaerung: "Reihenfolge von Hand; nur so lässt sich in der Spalte umsortieren, neue Karten kommen oben hin" },
};

/** Prioritäten von wenig nach viel (HELF-165): Name, Symbol und Farbmarke, eine Wahrheit für Kartendetail, Karte, Filter
    und Liste; der Hinweis sagt beim Überfahren, was die Wahl bedeutet */
export interface PrioritaetAnzeige { wert: Prioritaet; name: string; symbol: string; farbe: string; hinweis: string }
export const PRIORITAETEN: PrioritaetAnzeige[] = [
  { wert: "keine", name: "Keine", symbol: "fa-minus", farbe: "text-2", hinweis: "ohne Priorität; in Spalten nach Priorität ganz unten" },
  { wert: "niedrig", name: "Niedrig", symbol: "fa-angle-down", farbe: "stahl", hinweis: "kann warten" },
  { wert: "mittel", name: "Mittel", symbol: "fa-equals", farbe: "honig", hinweis: "normale Arbeit" },
  { wert: "hoch", name: "Hoch", symbol: "fa-angle-up", farbe: "warn", hinweis: "bald erledigen" },
  { wert: "dringend", name: "Dringend", symbol: "fa-angles-up", farbe: "gefahr", hinweis: "zuerst; in Spalten nach Priorität ganz oben" },
];

export function prioritaet(p: Prioritaet): PrioritaetAnzeige {
  return PRIORITAETEN.find((x) => x.wert === p) ?? PRIORITAETEN[0];
}

/** die Farbe einer Priorität als Wert für --prio (Punkt auf der Karte, Filter, Liste) */
export const prioFarbe = (p: Prioritaet): string => `--prio: var(--${prioritaet(p).farbe})`;

/** Priorität als Knopfleiste (Kartendetail) */
export function prioritaetsStufen(): Wahlstufe<Prioritaet>[] {
  return PRIORITAETEN.map((p) => ({ wert: p.wert, titel: p.name, symbol: p.symbol, farbe: p.farbe, hinweis: p.hinweis }));
}

/** Auswahl für das Symbol einer Spalte (Einstellungen des Boards); die Vorlagen des Servers nehmen ihre Symbole von hier */
export const SPALTENSYMBOLE: { symbol: string; name: string }[] = [
  { symbol: "fa-inbox", name: "Eingang" }, { symbol: "fa-lightbulb", name: "Idee" }, { symbol: "fa-circle-question", name: "Klären" },
  { symbol: "fa-scale-balanced", name: "Bewerten" }, { symbol: "fa-calendar-days", name: "Geplant" }, { symbol: "fa-list-check", name: "Bereit" },
  { symbol: "fa-person-digging", name: "In Arbeit" }, { symbol: "fa-hammer", name: "Bauen" }, { symbol: "fa-pen", name: "Schreiben" },
  { symbol: "fa-hourglass-half", name: "Wartet" }, { symbol: "fa-pause", name: "Pausiert" }, { symbol: "fa-magnifying-glass", name: "Prüfung" },
  { symbol: "fa-user-check", name: "Freigabe" }, { symbol: "fa-truck", name: "Ausliefern" }, { symbol: "fa-circle-check", name: "Erledigt" },
  { symbol: "fa-box-archive", name: "Abgelegt" }, { symbol: "fa-ban", name: "Verworfen" }, { symbol: "fa-circle", name: "Punkt" },
];

/** die Symbole als Knopfleiste in der Farbe der Spalte (Einstellungen, Spalten) */
export function spaltensymbolStufen(farbe: Farbe): Wahlstufe<string>[] {
  return SPALTENSYMBOLE.map((x) => ({ wert: x.symbol, titel: x.name, symbol: x.symbol, farbe }));
}

/** Symbol einer Spalte: das gewählte, sonst ein Farbpunkt, die Erledigt-Spalte mit Haken */
export const spaltenSymbol = (s: Spalte): string => s.symbol ?? (s.erledigt ? "fa-circle-check" : "fa-circle");

/** Status als Knopfleiste (Kartendetail): je Spalte des Boards Name, Symbol und Farbe der Spalte */
export function statusStufen(spalten: Spalte[]): Wahlstufe<Kennung>[] {
  return spalten.map((s) => ({
    wert: s.id, titel: s.name, symbol: spaltenSymbol(s), farbe: s.farbe,
    hinweis: s.erledigt ? "schließt die Karte ab; ein laufender Timer an ihr hält an und bucht" : "verschiebt die Karte in diese Spalte",
  }));
}

export const HERKUNFT: Record<Herkunft, string> = { timer: "Timer", hand: "nachgetragen", korrektur: "Korrektur", serie: "Serie", termin: "Termin" };

export const HINWEIS_WEGE: { id: HinweisWeg; name: string; symbol: string; text: string }[] = [
  { id: "pinnwand", name: "In der Pinnwand", symbol: "fa-bell", text: "Glocke und Seite Hinweise; gelesen gilt auf allen Geräten" },
  { id: "push", name: "Push aufs Telefon", symbol: "fa-mobile-screen", text: "Mitteilung auf dem Telefon über die Web-App" },
  { id: "assistent", name: "Über den Assistenten", symbol: "fa-comment-dots", text: "Der Assistent nennt es in seinen Hinweisen" },
];

export const HINWEIS_ARTEN: { art: HinweisArt; name: string; symbol: string; farbe: Farbe; text: string }[] = [
  { art: "zugewiesen", name: "Zugewiesen", symbol: "fa-user-plus", farbe: "himmel", text: "Jemand macht dich für eine Karte zuständig" },
  { art: "faellig", name: "Fällig", symbol: "fa-calendar-day", farbe: "koralle", text: "Eine deiner Karten ist heute fällig oder überfällig" },
  { art: "erwaehnt", name: "Erwähnt", symbol: "fa-at", farbe: "violett", text: "Jemand erwähnt dich mit @ in Beschreibung, Notizen oder einem Kommentar" },
  { art: "termin", name: "Termin", symbol: "fa-calendar-days", farbe: "petrol", text: "Ein neuer Termin mit dir" },
  { art: "kommentar", name: "Kommentar", symbol: "fa-comment", farbe: "stahl", text: "Neuer Kommentar an einer Karte, für die du zuständig bist" },
  { art: "verschoben", name: "Verschoben", symbol: "fa-right-left", farbe: "tuerkis", text: "Jemand verschiebt eine Karte, für die du zuständig bist" },
];

export interface ModulBeschreibung {
  id: ModulKennung;
  name: string;
  symbol: string;
  art: "fach" | "anbindung";
  text: string;
  ansichten: string[];
  felder: string[];
}

/** Was jedes Modul in ein Board bringt; die Rechte erklärt es selbst (RECHTE in den Beispieldaten) */
export const MODULE: ModulBeschreibung[] = [
  { id: "zeiterfassung", name: "Zeiterfassung", symbol: "fa-stopwatch", art: "fach",
    text: "Timer und gebuchte Zeit an jeder Arbeitskarte; Ideen haben keine Zeiterfassung.",
    ansichten: ["Zeit an der Karte", "Stundenzettel unter Zeiten"], felder: ["Schätzung"] },
  { id: "arbeitszeit", name: "Arbeitszeit und Urlaub", symbol: "fa-calendar-check", art: "fach",
    text: "Zeigt Zeiten und Abwesenheiten der Mitglieder; das Zeitkonto bleibt bei jeder Person.",
    ansichten: ["Auslastung der Mitglieder", "Abwesenheiten im Kalender"], felder: [] },
  { id: "serien", name: "Serien und Termine", symbol: "fa-repeat", art: "fach",
    text: "Wiederkehrende Karten und Termine mit Teilnehmern, angelegt in ihrer Zielspalte.",
    ansichten: ["Serien und Termine", "Termine im Kalender"], felder: ["Serie"] },
  { id: "berichte", name: "Berichte", symbol: "fa-file-lines", art: "fach",
    text: "Auswertungen des Boards als PDF, Tabelle oder Text.",
    ansichten: ["Berichte"], felder: [] },
  { id: "transkripte", name: "Transkripte", symbol: "fa-closed-captioning", art: "anbindung",
    text: "Karte mit Aufnahme und Transkript verknüpfen, Sprung zur Fundstelle; Spracheingabe beim Erfassen.",
    ansichten: ["Transkripte im Kartendetail"], felder: ["Transkript-Marken"] },
  { id: "vorlesen", name: "Vorlesen", symbol: "fa-volume-high", art: "anbindung",
    text: "Beschreibung, Kommentare und den Tagesplan vorlesen lassen.",
    ansichten: ["Vorlesen an Beschreibung, Kommentaren und in Heute"], felder: [] },
  { id: "ki", name: "KI an der Karte", symbol: "fa-wand-magic-sparkles", art: "anbindung",
    text: "Zusammenfassen, Checkliste und Labels vorschlagen, aus Text Karten machen; übernommen wird nur, was du bestätigst.",
    ansichten: ["Vorschläge im Kartendetail", "Karten aus Text beim Anlegen"], felder: [] },
];

export const MODUL_NAME: Record<"kern" | ModulKennung, string> = {
  kern: "Board und Karten",
  ...Object.fromEntries(MODULE.map((m) => [m.id, m.name])) as Record<ModulKennung, string>,
};
