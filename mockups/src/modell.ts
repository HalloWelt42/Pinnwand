// Datenmodell der Oberfläche der neuen Pinnwand. In den Entwürfen kommen die Werte aus den Beispieldaten, in der App
// aus der Schnittstelle; die Ansichten kennen nur diese Typen.

export type Kennung = string;

/** Farben der Palette des Appkerns (Marken), für Spalten, Labels, Cover und Personen. */
export type Farbe = "tuerkis" | "minze" | "honig" | "petrol" | "rose" | "koralle" | "sand" | "himmel" | "flieder" | "violett" | "stahl";

export interface Konto {
  id: Kennung;
  name: string;
  kuerzel: string;
  farbe: Farbe;
}

export interface Ordner {
  id: Kennung;
  name: string;
  boards: Kennung[];
}

export interface Label {
  id: Kennung;
  name: string;
  farbe: Farbe;
}

export type Zeitfenster = "heute" | "gestern" | "woche" | "monat" | "jahr" | "alle";

export interface Spalte {
  id: Kennung;
  name: string;
  farbe: Farbe;
  /** Erledigt-Spalten laden gefenstert nach Abschlussdatum, mit Zeitfilter und Archiv */
  erledigt: boolean;
  /** Grenze offener Karten (Warnung beim Überschreiten), leer: keine */
  grenze?: number;
  eingeklappt?: boolean;
  zeitfenster?: Zeitfenster;
}

export type FeldArt = "text" | "zahl" | "datum" | "auswahl" | "verweis";

/** Eigenes Feld eines Boards */
export interface Feld {
  id: Kennung;
  name: string;
  art: FeldArt;
  optionen?: string[];
  /** auf der Karte im Board sichtbar, nicht nur im Detail */
  aufKarte: boolean;
}

export type ModulKennung = "zeiterfassung" | "arbeitszeit" | "serien" | "berichte" | "transkripte" | "vorlesen" | "ki";

/** Ein Recht, erklärt von einem Modul (Kern oder Fachmodul) */
export interface Recht {
  id: Kennung;
  modul: "kern" | ModulKennung;
  name: string;
  erklaerung: string;
}

export interface Rolle {
  id: Kennung;
  name: string;
  rechte: Kennung[];
  /** Start-Rolle jedes Boards (Besitzer, Mitglied, Leser); umbenennbar, nicht löschbar */
  vorgabe?: boolean;
}

export interface Mitglied {
  konto: Kennung;
  rolle: Kennung;
}

export interface Board {
  id: Kennung;
  name: string;
  /** Kürzel der Kartenschlüssel, bleibt beim Umbenennen fest */
  kuerzel: string;
  ordner: Kennung;
  farbe: Farbe;
  laufnummer: number;
  spalten: Spalte[];
  labels: Label[];
  felder: Feld[];
  rollen: Rolle[];
  mitglieder: Mitglied[];
  module: Record<ModulKennung, boolean>;
}

export type Prioritaet = "keine" | "niedrig" | "mittel" | "hoch" | "dringend";

export interface Punkt {
  text: string;
  erledigt: boolean;
}

export interface Kommentar {
  von: Kennung;
  zeit: string;
  text: string;
}

export interface Anhang {
  name: string;
  groesse: string;
  art: "pdf" | "bild" | "tabelle" | "text" | "ton";
  /** aus der eigenen Kellerwolke verknüpft statt hochgeladen */
  verknuepft?: boolean;
}

export interface TranskriptMarke {
  aufnahme: string;
  stelle: string;
  text: string;
}

export interface Ereignis {
  zeit: string;
  von: Kennung;
  text: string;
}

export interface Karte {
  id: Kennung;
  board: Kennung;
  schluessel: string;
  spalte: Kennung;
  titel: string;
  art: "arbeit" | "idee";
  beschreibung?: string;
  notizen?: string;
  zustaendig: Kennung[];
  prioritaet: Prioritaet;
  start?: string;
  faellig?: string;
  labels: Kennung[];
  checkliste: Punkt[];
  kommentare: Kommentar[];
  cover?: Farbe;
  blockiert?: string;
  schaetzungMin?: number;
  /** Summe der Zeiteinträge in Sekunden */
  erfasstSek: number;
  /** läuft der Timer einer Person auf dieser Karte: seit wann (ISO) und wer */
  laeuft?: { seit: string; konto: Kennung };
  /** letzter Spaltenwechsel (Alter im Status) */
  bewegtAm: string;
  erstelltAm: string;
  /** Abschlussdatum bei Karten in Erledigt-Spalten */
  abgeschlossen?: string;
  /** Verknüpfte Aufgaben mit geteilter Zeit */
  gruppe?: Kennung;
  serie?: Kennung;
  felder: Record<Kennung, string>;
  anhaenge: Anhang[];
  transkripte: TranskriptMarke[];
  verlauf: Ereignis[];
}

export interface Gruppe {
  id: Kennung;
  zeitTeilen: boolean;
}

export interface Zeiteintrag {
  id: Kennung;
  karte: Kennung;
  konto: Kennung;
  datum: string;
  von?: string;
  bis?: string;
  sekunden: number;
  herkunft: "timer" | "hand" | "korrektur" | "serie";
}

export type Rhythmus = "taeglich" | "werktags" | "woechentlich" | "monatlich";

export interface Serie {
  id: Kennung;
  board: Kennung;
  titel: string;
  rhythmus: Rhythmus;
  tage?: number[];
  uhrzeit?: string;
  dauerMin: number;
  zielspalte: Kennung;
  teilnehmer: Kennung[];
  pausiert?: boolean;
  naechste: string;
}

export interface Termin {
  id: Kennung;
  board: Kennung;
  titel: string;
  datum: string;
  von: string;
  bis: string;
  teilnehmer: Kennung[];
  ort?: string;
  bestaetigt: Kennung[];
}

export type HinweisArt = "zugewiesen" | "faellig" | "erwaehnt" | "termin" | "kommentar" | "verschoben";

export interface Hinweis {
  id: Kennung;
  art: HinweisArt;
  zeit: string;
  von?: Kennung;
  board: Kennung;
  karte?: Kennung;
  text: string;
  gelesen: boolean;
}

export interface Vorlage {
  id: Kennung;
  name: string;
  beschreibung: string;
  symbol: string;
  spalten: string[];
  module: ModulKennung[];
  eigen?: boolean;
}

/** Zeitkonto einer Person (Arbeitszeit und Urlaub, je Person) */
export interface Zeitkonto {
  konto: Kennung;
  wochenstunden: number;
  tage: number[];
  bundesland: string;
  urlaubsanspruch: number;
  resturlaubVorjahr: number;
  genommen: number;
  geplant: number;
}

export type AbwesenheitArt = "urlaub" | "krank" | "frei" | "halbtag" | "feiertag" | "fortbildung";

export interface Abwesenheit {
  konto: Kennung;
  von: string;
  bis: string;
  art: AbwesenheitArt;
  notiz?: string;
}
