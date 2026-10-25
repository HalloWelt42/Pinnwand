// Namen und Zeichen für Menschen, eine Quelle für alle Ansichten: Farben, Zeitfenster, Prioritäten, Herkunft von Zeiten,
// Hinweise und Module. Schlüssel werden nie gedruckt, immer ihr Name von hier.

import type { Farbe, Herkunft, HinweisArt, HinweisWeg, ModulKennung, Prioritaet, Zeitfenster } from "./modell";

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

export const PRIORITAETEN: [Prioritaet, string][] = [["keine", "Keine"], ["niedrig", "Niedrig"], ["mittel", "Mittel"], ["hoch", "Hoch"],
  ["dringend", "Dringend"]];

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
  { art: "termin", name: "Termin", symbol: "fa-calendar-days", farbe: "petrol", text: "Ein Termin mit dir steht an oder ändert sich" },
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
    text: "Timer und gebuchte Zeit an jeder Karte; ohne das Modul sind alle Karten Ideen.",
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
    ansichten: ["Vorschläge im Kartendetail"], felder: [] },
];

export const MODUL_NAME: Record<"kern" | ModulKennung, string> = {
  kern: "Board und Karten",
  ...Object.fromEntries(MODULE.map((m) => [m.id, m.name])) as Record<ModulKennung, string>,
};
