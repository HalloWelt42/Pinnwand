// Beispieldaten der Verwaltung (Board-Einstellungen, Board anlegen, persönliche Einstellungen): was das gemeinsame
// Modell noch nicht trägt. In der App kommen diese Werte aus der Schnittstelle; Personen und Kennungen sind erfunden.

import type { Farbe, HinweisArt, Kennung, ModulKennung, Zeitfenster } from "../../modell";

/** Palette für Board, Spalten und Labels, in der Reihenfolge der Wahl im Kartendetail; Wort und Farbe gehören zusammen */
export const FARBEN: Farbe[] = ["koralle", "rose", "violett", "flieder", "himmel", "petrol", "tuerkis", "minze", "honig", "sand", "stahl"];

export const FARBNAMEN: Record<Farbe, string> = {
  koralle: "Koralle", rose: "Rose", violett: "Violett", flieder: "Flieder", himmel: "Himmel", petrol: "Petrol",
  tuerkis: "Türkis", minze: "Minze", honig: "Honig", sand: "Sand", stahl: "Stahl",
};

export const ZEITFENSTER: Record<Zeitfenster, string> = {
  heute: "Heute", gestern: "Gestern", woche: "Diese Woche", monat: "Dieser Monat", jahr: "Dieses Jahr", alle: "Alle",
};

/** Einstellungen eines Boards (bisher global, BOARD_MECHANIK Abschnitt 3.1), jetzt je Board */
export interface BoardEinstellung {
  /** Sanduhr auf der Karte als Warnung ab so vielen Tagen im Status, 0: aus */
  alterungWarnung: number;
  /** als Gefahr ab so vielen Tagen, 0: aus; unabhängig von der Warnung */
  alterungGefahr: number;
  /** Karten je Ladeschritt einer Erledigt-Spalte */
  ladeschritt: number;
  /** fertige Karten mit älterem Abschluss nur im Archiv */
  archivTage: number;
}

export const GRENZEN = {
  alterung: [0, 365],
  ladeschritt: [1, 500],
  archivTage: [1, 100000],
} as const;

export const BOARD_EINSTELLUNGEN: Record<Kennung, BoardEinstellung> = {
  "b-prod": { alterungWarnung: 4, alterungGefahr: 8, ladeschritt: 50, archivTage: 365 },
  "b-ideen": { alterungWarnung: 14, alterungGefahr: 30, ladeschritt: 50, archivTage: 365 },
  "b-haus": { alterungWarnung: 4, alterungGefahr: 8, ladeschritt: 50, archivTage: 365 },
};

/** Seit wann eine Person Mitglied eines Boards ist */
export const MITGLIED_SEIT: Record<Kennung, Record<Kennung, string>> = {
  "b-prod": { "k-max": "2025-03-03", "k-anna": "2025-03-03", "k-jonas": "2025-04-14", "k-tim": "2026-02-02", "k-lea": "2026-09-21" },
  "b-ideen": { "k-max": "2025-06-10", "k-anna": "2025-06-12" },
  "b-haus": { "k-max": "2025-01-05" },
};

/** Kennung im Kellerwolke-Konto der Personen, die schon in der Pinnwand sind */
export const KENNUNGEN: Record<Kennung, string> = {
  "k-max": "max.paulsen", "k-anna": "anna.berger", "k-jonas": "jonas.keller", "k-lea": "lea.wolf", "k-tim": "tim.sander",
};

/** Eine Person aus den Konten der Kellerwolke, gefunden per Name */
export interface Vorschlag {
  kennung: string;
  name: string;
  /** Konto in der Pinnwand, wenn die Person schon in einem Board ist */
  konto?: Kennung;
}

/** Konten der Kellerwolke ohne Board in der Pinnwand: sie bekommen Kürzel und Farbe erst mit der ersten Einladung */
export const KELLERWOLKE_NEU: Vorschlag[] = [
  { kennung: "karla.senft", name: "Karla Senft" },
  { kennung: "kai.brenner", name: "Kai Brenner" },
  { kennung: "nina.hoff", name: "Nina Hoff" },
  { kennung: "paul.kranz", name: "Paul Kranz" },
  { kennung: "greta.lund", name: "Greta Lund" },
];

/** Kürzel von Boards anderer Personen: vergeben, auch wenn du sie nicht siehst (der Server prüft über alle Boards) */
export const KUERZEL_ANDERER = ["WERK", "LAGER", "EINK", "WH1"];

/** Spalten beim leeren Anfang (BOARD_MECHANIK 3.2), die letzte ist die Erledigt-Spalte */
export const LEER_SPALTEN = ["Offen", "In Arbeit", "Erledigt"];

/** Eigene Felder einer Vorlage (das Modell der Vorlage trägt bisher nur Spalten und Module) */
export const VORLAGE_FELDER: Record<Kennung, string[]> = {
  "v-werkstatt": ["Kunde", "Auftragsnummer", "Stückzahl", "Maschine"],
};

export interface ModulBeschreibung {
  id: ModulKennung;
  name: string;
  symbol: string;
  art: "fach" | "anbindung";
  text: string;
  ansichten: string[];
  felder: string[];
}

/** Was jedes Modul in ein Board bringt; die Rechte erklärt es selbst (RECHTE in den gemeinsamen Beispieldaten) */
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

/** Grundfelder jeder Karte (fest, nicht abschaltbar) */
export const GRUNDFELDER = ["Titel", "Beschreibung", "Notizen", "Arbeit oder Idee", "Zuständige", "Priorität", "Start", "Fällig",
  "Labels", "Checkliste", "Kommentare", "Cover", "Blockiert"];

export type HinweisWeg = "pinnwand" | "push" | "assistent";

export const HINWEIS_WEGE: { id: HinweisWeg; name: string; symbol: string; text: string }[] = [
  { id: "pinnwand", name: "In der Pinnwand", symbol: "fa-bell", text: "Glocke und Seite Hinweise; gelesen gilt auf allen Geräten" },
  { id: "push", name: "Push aufs Telefon", symbol: "fa-mobile-screen", text: "Mitteilung auf dem Telefon über die Web-App" },
  { id: "assistent", name: "Über den Assistenten", symbol: "fa-comment-dots", text: "Der Assistent nennt es in seinen Hinweisen" },
];

export const HINWEIS_ARTEN: { art: HinweisArt; name: string; symbol: string; text: string }[] = [
  { art: "zugewiesen", name: "Zugewiesen", symbol: "fa-user-plus", text: "Jemand macht dich für eine Karte zuständig" },
  { art: "faellig", name: "Fällig", symbol: "fa-calendar-day", text: "Eine deiner Karten ist heute fällig oder überfällig" },
  { art: "erwaehnt", name: "Erwähnt", symbol: "fa-at", text: "Jemand erwähnt dich mit @ in einem Kommentar" },
  { art: "termin", name: "Termin", symbol: "fa-calendar-days", text: "Ein Termin mit dir steht an oder ändert sich" },
  { art: "kommentar", name: "Kommentar", symbol: "fa-comment", text: "Neuer Kommentar an einer Karte, für die du zuständig bist" },
  { art: "verschoben", name: "Verschoben", symbol: "fa-right-left", text: "Jemand verschiebt eine Karte, für die du zuständig bist" },
];

export const HINWEIS_VORGABE: Record<HinweisArt, Record<HinweisWeg, boolean>> = {
  zugewiesen: { pinnwand: true, push: true, assistent: false },
  faellig: { pinnwand: true, push: true, assistent: true },
  erwaehnt: { pinnwand: true, push: true, assistent: false },
  termin: { pinnwand: true, push: true, assistent: true },
  kommentar: { pinnwand: true, push: false, assistent: false },
  verschoben: { pinnwand: true, push: false, assistent: false },
};

/** Reiter der Board-Einstellungen, je mit eigener Adresse /board/<kürzel>/einstellungen/<reiter> */
export const BOARD_REITER = [
  { id: "allgemein", name: "Allgemein", symbol: "fa-sliders" },
  { id: "spalten", name: "Spalten", symbol: "fa-grip-vertical" },
  { id: "labels", name: "Labels", symbol: "fa-tags" },
  { id: "felder", name: "Felder", symbol: "fa-rectangle-list" },
  { id: "rollen", name: "Rollen und Rechte", symbol: "fa-user-shield" },
  { id: "mitglieder", name: "Mitglieder", symbol: "fa-users" },
  { id: "module", name: "Module", symbol: "fa-puzzle-piece" },
] as const;

/** Reiter der persönlichen Einstellungen, je mit eigener Adresse /einstellungen/<reiter> */
export const PERSON_REITER = [
  { id: "darstellung", name: "Darstellung", symbol: "fa-circle-half-stroke" },
  { id: "hinweise", name: "Hinweise", symbol: "fa-bell" },
  { id: "konto", name: "Konto", symbol: "fa-circle-user" },
  { id: "gestaltung", name: "Gestaltung", symbol: "fa-palette" },
] as const;
