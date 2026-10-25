// Beispieldaten für die Verwaltung, zusätzlich zu daten.ts: was der Server über Boards und Konten weiß, die Max nicht
// sieht (Kürzel fremder Boards, Personen der Kellerwolke ohne Board in der Pinnwand).

import type { KellerwolkePerson } from "../modell";

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
