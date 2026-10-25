// Typen des Moduls Serien und Termine, die das gemeinsame Modell (modell.ts) noch nicht trägt. Sie gehören nach der
// Freigabe zu Serie und Termin ins Modell; bis dahin hängen sie hier über die Kennung der Serie daran.

import type { Kennung } from "../../modell";

/** Welcher Tag im Monat bei monatlichem Rhythmus */
export type Monatsregel = "tag" | "erster-werktag" | "letzter-werktag";

/** Regeln einer Serie: wann sie vorbucht, was sie überspringt und was nicht wiederkommt */
export interface SerienRegel {
  serie: Kennung;
  beschreibung?: string;
  labels: Kennung[];
  /** Anker des Rhythmus: erster möglicher Tag */
  ab: string;
  /** letzter möglicher Tag, leer: ohne Ende */
  bis?: string;
  monatsregel?: Monatsregel;
  /** Tag im Monat bei Monatsregel "tag" (größer als der Monat: dessen letzter Tag) */
  monatstag?: number;
  /** so viele Tage im Voraus legt die Serie ihre Karten an (0: nur heute) */
  vorlaufTage: number;
  /** nur bei täglichem Rhythmus: Samstag und Sonntag auslassen */
  wochenendenUeberspringen: boolean;
  /** Feiertage im Bundesland eines Teilnehmers: er fehlt an dem Tag, fehlen alle, entfällt der Tag */
  feiertageUeberspringen: boolean;
  /** pausiert ab diesem Tag: keine neuen Vorbuchungen, unberührte Zukunftskarten sind entfernt */
  pausiertSeit?: string;
  /** fortgesetzt an diesem Tag: die Tage der Pause davor bleiben ohne Karte, vorgebucht wird ab hier */
  fortgesetzt?: string;
  /** bewusst gelöschte Tage (Auslass): kommen nie wieder, auch nicht nach Ändern oder Fortsetzen */
  auslass: { tag: string; von: Kennung; am: string }[];
  /** Vorbuchungen, die jemand angefasst hat (Zeit, Spalte, Inhalt): Ändern, Pause und Urlaub lassen sie stehen */
  beruehrt: { tag: string; grund: string }[];
  /** vergangene Tage, die im Nachtrag verworfen wurden (fand nicht statt) */
  verworfen: string[];
}

export interface Feiertag {
  tag: string;
  name: string;
  /** leer: bundesweit */
  laender: string[];
}

/** Stand eines Tages einer Serie, aus Regel, Abwesenheiten und Bestätigungen berechnet */
export type VorkommenStand =
  | "gezaehlt"     // vorbei, alle Anwesenden haben ihre Zeit bestätigt
  | "wartet"       // vorbei, mindestens eine Zeit wartet auf Bestätigung
  | "verworfen"    // vorbei, fand nicht statt
  | "heute"
  | "vorgebucht"   // Karte liegt in der Zielspalte, unberührt
  | "beruehrt"     // Karte liegt da und wurde angefasst: bleibt beim Ändern
  | "geplant"      // jenseits des Vorlaufs: noch keine Karte
  | "geloescht"    // bewusst gelöscht: kommt nicht wieder
  | "ausgelassen"  // alle Teilnehmer fehlen (Urlaub, Feiertag)
  | "pausiert";

export interface Vorkommen {
  serie: Kennung;
  tag: string;
  stand: VorkommenStand;
  /** Teilnehmer, die an diesem Tag fehlen, mit Grund */
  ohne: { konto: Kennung; grund: string }[];
  /** wer seine Zeit noch nicht bestätigt hat (nur vorbei) */
  offen: Kennung[];
  notiz?: string;
}

/** Eine vorgebuchte Zeit eines vergangenen Tages, die auf deine Bestätigung wartet (Nachtrag am Folgetag) */
export interface Nachtragposten {
  art: "serie" | "termin";
  /** Kennung der Serie oder des Termins */
  bezug: Kennung;
  board: Kennung;
  titel: string;
  tag: string;
  von?: string;
  geplantMin: number;
  /** wer sonst schon bestätigt hat */
  bestaetigt: Kennung[];
}
