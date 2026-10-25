// Datenmodell der Oberfläche der neuen Pinnwand. In den Entwürfen kommen die Werte aus den Beispieldaten, in der App
// aus der Schnittstelle; die Ansichten kennen nur diese Typen. Was sich aus anderen Werten ergibt (gebuchte Zeit einer
// Karte, Urlaubstage, nächster Tag einer Serie), steht hier nicht, sondern wird gerechnet (daten/abfragen.ts).

export type Kennung = string;

/** Farben der Palette des Appkerns (Marken), für Spalten, Labels, Cover und Personen. */
export type Farbe = "tuerkis" | "minze" | "honig" | "petrol" | "rose" | "koralle" | "sand" | "himmel" | "flieder" | "violett" | "stahl";

/** Eine Person mit ihrem Kellerwolke-Konto; die Pinnwand legt Konten nicht selbst an */
export interface Konto {
  id: Kennung;
  name: string;
  kuerzel: string;
  farbe: Farbe;
  /** Kennung im Kellerwolke-Konto (Anmeldung, Einladen per Name) */
  kellerwolke: string;
}

/** Eine Person aus den Konten der Kellerwolke, gefunden per Name beim Einladen */
export interface KellerwolkePerson {
  kennung: string;
  name: string;
  /** Konto in der Pinnwand, wenn die Person schon in einem Board ist */
  konto?: Kennung;
}

/** Ein Eintrag deiner Kellerwolke, wie die Dateiwahl ihn zeigt (zum Verknüpfen an einer Karte): Ordner zum Hineingehen,
 *  Dateien zum Wählen */
export interface KellerwolkeDatei {
  /** Kennung in der Kellerwolke */
  id: string;
  typ: "ordner" | "datei";
  name: string;
  /** Ordner, in dem er liegt (null: Meine Dateien), und dessen Weg vom Konto aus ("Dokumente/Angebote") */
  ordner: string | null;
  pfad: string;
  groesse: string;
  art: Anhang["art"];
}

/** Ein Ordner deiner Kellerwolke in der Dateiwahl (id null: Meine Dateien) */
export interface KellerwolkeOrdner {
  id: string | null;
  /** Weg vom Konto bis hier: Meine Dateien, dann die Ordner */
  kette: { id: string | null; name: string }[];
  eintraege: KellerwolkeDatei[];
}

/** Persönlicher Ordner in der Seitenleiste: ordnet nur, trägt keine Rechte; jede Person ordnet ihre Boards selbst */
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
  /** Vorgabe des Zeitfensters einer Erledigt-Spalte */
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
  /** Konto der Pinnwand; leer, bis die eingeladene Person sich das erste Mal anmeldet */
  konto: Kennung;
  /** Kontoname der Kellerwolke, unter dem eingeladen wurde */
  kellerwolke: string;
  rolle: Kennung;
  /** Tag des Beitritts */
  seit: string;
}

/** Einstellungen eines Boards (in der alten App global, jetzt je Board) */
export interface BoardEinstellungen {
  /** Sanduhr auf der Karte als Warnung ab so vielen Tagen im Status, 0: aus */
  alterungWarnung: number;
  /** als Gefahr ab so vielen Tagen, 0: aus; unabhängig von der Warnung */
  alterungGefahr: number;
  /** Karten je Ladeschritt einer Erledigt-Spalte */
  ladeschritt: number;
  /** erledigte Karten mit älterem Abschluss stehen nur im Archiv */
  archivTage: number;
}

export interface Board {
  id: Kennung;
  name: string;
  /** Kürzel der Kartenschlüssel, bleibt beim Umbenennen fest */
  kuerzel: string;
  farbe: Farbe;
  /** Art neuer Karten, wenn beim Anlegen keine gewählt ist */
  kartenart: "arbeit" | "idee";
  spalten: Spalte[];
  labels: Label[];
  felder: Feld[];
  rollen: Rolle[];
  mitglieder: Mitglied[];
  module: Record<ModulKennung, boolean>;
  einstellungen: BoardEinstellungen;
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

/** Eine Datei an einer Karte: hochgeladen in den Ordner des Boards in der Ablage der Pinnwand, oder aus der eigenen
 *  Kellerwolke verknüpft (die Datei bleibt, wo sie ist). Der Name ist an der Karte eindeutig */
export interface Anhang {
  name: string;
  groesse: string;
  art: "pdf" | "bild" | "tabelle" | "text" | "ton";
  /** aus der eigenen Kellerwolke verknüpft statt hochgeladen */
  verknuepft?: boolean;
  /** Kennung der Datei in der Kellerwolke */
  datei?: string;
  /** Weg der Datei in der Kellerwolke vom Konto aus, mit Namen ("Apps/Pinnwand/Haushalt/Skizze.png") */
  pfad?: string;
  /** wer sie angehängt hat; bei einer verknüpften: in wessen Kellerwolke sie liegt */
  von?: Kennung;
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
  /** letzter Spaltenwechsel (Alter im Status) */
  bewegtAm: string;
  erstelltAm: string;
  /** Abschlussdatum bei Karten in Erledigt-Spalten */
  abgeschlossen?: string;
  /** Verknüpfte Aufgaben: ziehen zusammen, Zeit geteilt */
  gruppe?: Kennung;
  serie?: Kennung;
  felder: Record<Kennung, string>;
  anhaenge: Anhang[];
  transkripte: TranskriptMarke[];
  verlauf: Ereignis[];
  /** Platz in der Spalte (Gleitkomma mit Raum dazwischen); offene Spalten ordnen danach */
  reihe: number;
}

/** Verknüpfte Karten eines Boards: ziehen zusammen und teilen auf Wunsch ihre Zeit */
export interface Gruppe {
  id: Kennung;
  board: Kennung;
  zeitTeilen: boolean;
}

/** Zuletzt vergebene Kartennummer eines Boards (Kennung: die des Boards); Nummern werden nie wiederverwendet */
export interface Laufnummer {
  id: Kennung;
  board: Kennung;
  zahl: number;
}

export type Herkunft = "timer" | "hand" | "korrektur" | "serie";

/** Vermerk an den Einträgen einer Timer-Sitzung, die länger als 12 Stunden lief: die echte Sitzung als Zeitpunkte
 *  (Ortszeit wie die Uhr) und ihre ganze Dauer; gebucht sind die ersten 12 Stunden, bis die Person das echte Ende nennt
 *  oder die 12 bestätigt. Die Spanne für Menschen rechnet die Ansicht aus seit und bis. */
export interface Deckel {
  seit: string;
  bis: string;
  sekunden: number;
}

/** Gebuchte Zeit einer Person auf einer Karte an einem Tag; die Zeit einer Karte ist die Summe ihrer Einträge */
export interface Zeiteintrag {
  id: Kennung;
  karte: Kennung;
  /** Board der Karte; danach richtet sich, wer den Eintrag sieht */
  board: Kennung;
  konto: Kennung;
  datum: string;
  von?: string;
  bis?: string;
  sekunden: number;
  herkunft: Herkunft;
  notiz?: string;
  /** Timer-Sitzungen, die je Karte und Tag zu diesem einen Eintrag zusammengefasst sind */
  sitzungen?: { von: string; bis: string }[];
  /** an Mitternacht zerlegt: der andere Teil derselben Sitzung liegt an diesem Tag */
  zerlegt?: string;
  /** der Timer lief länger als 12 Stunden; gebucht sind die ersten 12, die Rückfrage ist offen */
  gedeckelt?: Deckel;
}

/** Der eine Timer einer Person: läuft (seit) oder ist angehalten und lässt sich fortsetzen */
export interface Timer {
  /** gleich dem Konto: je Person einer */
  id: Kennung;
  konto: Kennung;
  karte: Kennung;
  /** Board der Karte; danach richtet sich, wer den Timer sieht */
  board: Kennung;
  /** läuft seit (ISO); leer: angehalten, die bisherigen Sitzungen sind gebucht */
  seit?: string;
}

export type Rhythmus = "taeglich" | "werktags" | "woechentlich" | "monatlich";

/** Welcher Tag im Monat bei monatlichem Rhythmus */
export type Monatsregel = "tag" | "erster-werktag" | "letzter-werktag";

/** Wiederkehrende Karte: legt im Vorlauf Karten in die Zielspalte, fällig am Termintag, Schätzung ist die Dauer */
export interface Serie {
  id: Kennung;
  board: Kennung;
  titel: string;
  beschreibung?: string;
  labels: Kennung[];
  rhythmus: Rhythmus;
  /** Wochentage bei wöchentlichem Rhythmus (0 Sonntag bis 6 Samstag) */
  tage?: number[];
  monatsregel?: Monatsregel;
  /** Tag im Monat bei Monatsregel "tag" (größer als der Monat: dessen letzter Tag) */
  monatstag?: number;
  uhrzeit?: string;
  dauerMin: number;
  zielspalte: Kennung;
  teilnehmer: Kennung[];
  /** Anker des Rhythmus: erster möglicher Tag */
  ab: string;
  /** letzter möglicher Tag, leer: ohne Ende */
  bis?: string;
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

/** Einmaliger Termin ohne Karte: vorher sagen Teilnehmer zu, danach bestätigt jeder seine Zeit (zählt erst dann) */
export interface Termin {
  id: Kennung;
  board: Kennung;
  titel: string;
  datum: string;
  von: string;
  bis: string;
  teilnehmer: Kennung[];
  ort?: string;
  /** vorab zugesagt */
  zugesagt: Kennung[];
  /** nach dem Termin die Zeit bestätigt */
  bestaetigt: Kennung[];
}

export type HinweisArt = "zugewiesen" | "faellig" | "erwaehnt" | "termin" | "kommentar" | "verschoben";
export type HinweisWeg = "pinnwand" | "push" | "assistent";

/** Ein Hinweis an die angemeldete Person; gelesen gilt am Konto, auf allen Geräten */
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

/** Persönliche Einstellungen am Konto: auf welchem Weg welche Hinweise kommen */
export interface PersonEinstellungen {
  hinweise: Record<HinweisArt, Record<HinweisWeg, boolean>>;
}

export interface VorlageSpalte {
  name: string;
  farbe: Farbe;
  erledigt: boolean;
  grenze?: number;
}

/** Vorlage eines neuen Boards: Spalten, eigene Felder, Labels und Module; eigene Vorlagen entstehen aus einem Board */
export interface Vorlage {
  id: Kennung;
  name: string;
  beschreibung: string;
  symbol: string;
  spalten: VorlageSpalte[];
  kartenart: "arbeit" | "idee";
  felder: Omit<Feld, "id">[];
  labels: Omit<Label, "id">[];
  module: ModulKennung[];
  eigen?: boolean;
}

/** Halber Arbeitstag an einem festen Tag im Jahr (etwa Heiligabend) */
export interface Halbtagsregel {
  monat: number;
  tag: number;
  name: string;
}

/** Zeitkonto einer Person (Arbeitszeit und Urlaub, je Person); eine neue Fassung gilt ab einem Tag, frühere Tage
 *  behalten ihr Soll. Genommene und geplante Urlaubstage ergeben sich aus den Abwesenheiten. */
export interface Zeitkonto {
  id: Kennung;
  konto: Kennung;
  /** gilt ab diesem Tag (bis zur nächsten Fassung) */
  ab: string;
  wochenstunden: number;
  /** Arbeitstage (0 Sonntag bis 6 Samstag); das Soll eines Arbeitstags ist Wochenstunden durch ihre Zahl */
  tage: number[];
  bundesland: string;
  urlaubsanspruch: number;
  resturlaubVorjahr: number;
  halbtage: Halbtagsregel[];
}

export type AbwesenheitArt = "urlaub" | "krank" | "frei" | "feiertag" | "fortbildung";

export interface Abwesenheit {
  id: Kennung;
  konto: Kennung;
  von: string;
  bis: string;
  art: AbwesenheitArt;
  /** halber Tag: 0,5; leer: ganze Tage */
  anteil?: number;
  notiz?: string;
}

/** Was eine Löschung im Papierkorb festhält, damit Wiederherstellen alles an seine alte Stelle bringt. Karten und Spalten
 *  liegen im Papierkorb ihres Boards, ganze Boards im Papierkorb der App (Einstellungen). */
export interface Geloescht {
  id: Kennung;
  board: Kennung;
  art: "karte" | "spalte" | "board";
  /** die gelöschte Spalte (nur bei art "spalte") */
  spalte?: Spalte;
  /** die Karten des Eintrags: eine bei einer Karte, alle der Spalte bei einer Spalte; ihre Zeiteinträge bleiben gebucht */
  karten: Karte[];
  /** alte Stelle (ab 0): bei einer Karte Spalte und Platz darin, bei einer Spalte ihr Platz in der Spaltenfolge */
  stelle: { spalte?: Kennung; platz: number };
  /** bei einem Board: alles, was daran hängt (ohne die Karten, die stehen in karten): seine Gruppen und die Ordner, in
   *  denen es lag */
  inhalt?: { board: Board; gruppen: Gruppe[]; ordner: Kennung[] };
  von: Kennung;
  am: string;
}

/** Name einer Karte, auf die sichtbare Zeiteinträge zeigen, die selbst nicht im Stand ist (archiviert, Board verlassen) */
export interface Kartenname {
  karte: Kennung;
  board: Kennung;
  schluessel: string;
  titel: string;
}

/** Eine endgültig entfernte Karte: ihr Name bleibt für die Zeiteinträge, die weiter gebucht sind */
export interface Entfernt {
  karte: Kennung;
  board: Kennung;
  schluessel: string;
  titel: string;
  am: string;
}

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

export type Verbindung = "verbunden" | "getrennt";
