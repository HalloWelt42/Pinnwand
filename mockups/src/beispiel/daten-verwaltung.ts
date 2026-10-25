// Beispieldaten für die Verwaltung und die Kellerwolke, zusätzlich zu daten.ts: was der Server über Boards und Konten
// weiß, die Max nicht sieht (Kürzel fremder Boards, Personen ohne Board in der Pinnwand), und Dateien seiner Kellerwolke.

import type { KellerwolkeDatei, KellerwolkePerson } from "../modell";

/** Konten der Kellerwolke ohne Board in der Pinnwand: sie bekommen Kürzel und Farbe erst mit der ersten Einladung */
export const KELLERWOLKE_NEU: KellerwolkePerson[] = [
  { kennung: "karla.senft", name: "Karla Senft" },
  { kennung: "kai.brenner", name: "Kai Brenner" },
  { kennung: "nina.hoff", name: "Nina Hoff" },
  { kennung: "paul.kranz", name: "Paul Kranz" },
  { kennung: "greta.lund", name: "Greta Lund" },
];

/** Kürzel von Boards anderer Personen: vergeben, auch wenn du sie nicht siehst (der Server prüft über alle Boards) */
export const KUERZEL_ANDERER = ["WERK", "LAGER", "EINK", "WH1"];

/** Dateien in der Kellerwolke von Max: eine kleine Auswahl erfundener Dateien zum Verknüpfen an Karten */
export const KELLERWOLKE_DATEIEN: KellerwolkeDatei[] = [
  { pfad: "Dokumente/Angebote", name: "Kalkulation 2026.ods", groesse: "88 KB", art: "tabelle" },
  { pfad: "Dokumente/Angebote", name: "Angebotsvorlage Gehäuse.odt", groesse: "46 KB", art: "text" },
  { pfad: "Dokumente/Lieferanten", name: "Preisliste Pulverbeschichtung.pdf", groesse: "204 KB", art: "pdf" },
  { pfad: "Dokumente/Prüfung", name: "Prüfplan Biegeteile.pdf", groesse: "1,1 MB", art: "pdf" },
  { pfad: "Bilder/Werkstatt", name: "Musterteil K5 Oberfläche.jpg", groesse: "2,3 MB", art: "bild" },
  { pfad: "Bilder/Werkstatt", name: "Laser Düsenwechsel.png", groesse: "940 KB", art: "bild" },
  { pfad: "Aufnahmen", name: "Telefonat Kunde Brandt.m4a", groesse: "6,1 MB", art: "ton" },
];
