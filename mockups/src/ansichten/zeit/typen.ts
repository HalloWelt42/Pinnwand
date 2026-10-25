// Typen der Zeit-Ansichten, die das gemeinsame Modell (src/modell.ts) noch nicht trägt. Was hier steht, gehört nach
// der Freigabe ins Modell (Bedarf im Bericht); die Ansichten kennen nur diese Typen und die des Modells.

import type { Kennung, Zeiteintrag } from "../../modell";

/** Zeiteintrag mit Notiz und den Spuren der Buchungsregeln (Zusammenfassen, Mitternacht, Deckel) */
export interface Eintrag extends Zeiteintrag {
  notiz?: string;
  /** Timer-Sitzungen, die je Karte und Tag zu diesem einen Eintrag zusammengefasst sind */
  sitzungen?: { von: string; bis: string }[];
  /** an Mitternacht zerlegt: der andere Teil derselben Sitzung liegt an diesem Tag */
  zerlegt?: string;
  /** der Timer lief länger als 12 Stunden (spanne, sekunden); gebucht wurden die ersten 12, die Rückfrage ist offen */
  gedeckelt?: { spanne: string; sekunden: number };
}

/** Zeit je Person und Tag aus Einträgen, die die Entwürfe nicht einzeln führen (in der App: Summe der Schnittstelle) */
export type Tagesrest = Record<Kennung, Record<string, number>>;

export type BerichtArt = "stundennachweis" | "board" | "erledigt";
export type BerichtFormat = "pdf" | "tabelle" | "markdown";

/** Ein erstellter Bericht, abgelegt in der Kellerwolke im Ordner der Pinnwand */
export interface Bericht {
  id: Kennung;
  art: BerichtArt;
  titel: string;
  zeitraum: string;
  format: BerichtFormat;
  datei: string;
  erstellt: string;
  groesse: string;
}

/** Inhalt eines Berichts unabhängig vom Format: Abschnitte mit Spalten, Zeilen und Summe (wie der Dienst der alten App) */
export interface BerichtInhalt {
  titel: string;
  zeitraum: string;
  abschnitte: { titel: string; spalten: string[]; zeilen: string[][]; summe?: string[]; fuss?: string }[];
}
