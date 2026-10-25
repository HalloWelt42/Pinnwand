// Beispieldaten der Entwürfe: erfundene Personen, Firmen und Aufgaben (das Repo ist öffentlich). "Heute" ist in allen
// Entwürfen Dienstag, der 27. Oktober 2026, 10:42 Uhr; angemeldet ist Max Paulsen. Eine Welt für alle Ansichten: was
// eine Ansicht zusätzlich braucht, steht in daten-<bereich>.ts daneben und fließt in denselben Zustand (stand.svelte.ts).
// Die Zeit einer Karte ist immer die Summe ihrer Zeiteinträge, der Timer gehört der Person.

import type {
  Abwesenheit, Board, Gruppe, Hinweis, Karte, Konto, Ordner, PersonEinstellungen, Recht, Rolle, Serie, Termin, Timer, Vorlage, Zeiteintrag,
  Zeitkonto,
} from "../modell";

export const HEUTE = "2026-10-27";
export const JETZT = "2026-10-27T10:42:00";
export const ICH = "k-max";

export const KONTEN: Konto[] = [
  { id: "k-max", name: "Max Paulsen", kuerzel: "MP", farbe: "himmel", kellerwolke: "max.paulsen" },
  { id: "k-anna", name: "Anna Berger", kuerzel: "AB", farbe: "minze", kellerwolke: "anna.berger" },
  { id: "k-jonas", name: "Jonas Keller", kuerzel: "JK", farbe: "honig", kellerwolke: "jonas.keller" },
  { id: "k-lea", name: "Lea Wolf", kuerzel: "LW", farbe: "rose", kellerwolke: "lea.wolf" },
  { id: "k-tim", name: "Tim Sander", kuerzel: "TS", farbe: "flieder", kellerwolke: "tim.sander" },
];

/** Ordner von Max (jede Person ordnet ihre Boards selbst) */
export const ORDNER: Ordner[] = [
  { id: "o-firma", name: "Firma", boards: ["b-prod", "b-ideen"] },
  { id: "o-privat", name: "Privat", boards: ["b-haus"] },
];

export const RECHTE: Recht[] = [
  { id: "board.verwalten", modul: "kern", name: "Board verwalten", erklaerung: "Name, Spalten, Labels, Felder, Module und Einstellungen ändern" },
  { id: "mitglieder.verwalten", modul: "kern", name: "Mitglieder und Rollen verwalten", erklaerung: "Personen einladen, Rollen vergeben und ihre Rechte einstellen" },
  { id: "karten.anlegen", modul: "kern", name: "Karten anlegen", erklaerung: "Neue Karten in jeder Spalte anlegen" },
  { id: "karten.bearbeiten", modul: "kern", name: "Karten bearbeiten", erklaerung: "Titel, Beschreibung, Felder, Checklisten und Labels ändern" },
  { id: "karten.verschieben", modul: "kern", name: "Karten verschieben", erklaerung: "Karten zwischen Spalten ziehen und erledigen" },
  { id: "karten.loeschen", modul: "kern", name: "Karten löschen", erklaerung: "Karten in den Papierkorb legen" },
  { id: "kommentieren", modul: "kern", name: "Kommentieren", erklaerung: "Kommentare schreiben und Personen erwähnen" },
  { id: "papierkorb.leeren", modul: "kern", name: "Papierkorb leeren", erklaerung: "Karten endgültig entfernen" },
  { id: "zeit.buchen", modul: "zeiterfassung", name: "Eigene Zeit buchen", erklaerung: "Timer starten und eigene Zeit nachtragen" },
  { id: "zeit.andere.sehen", modul: "zeiterfassung", name: "Zeiten anderer sehen", erklaerung: "Gebuchte Zeiten aller Mitglieder auf Karten dieses Boards sehen" },
  { id: "zeit.andere.bearbeiten", modul: "zeiterfassung", name: "Zeiten anderer bearbeiten", erklaerung: "Zeiteinträge anderer Mitglieder ändern oder löschen" },
  { id: "abwesenheit.sehen", modul: "arbeitszeit", name: "Abwesenheiten sehen", erklaerung: "Urlaub und Abwesenheit der Mitglieder in Kalender und Auslastung sehen" },
  { id: "serien.verwalten", modul: "serien", name: "Serien und Termine verwalten", erklaerung: "Wiederkehrende Karten und Termine anlegen, pausieren, ändern" },
  { id: "berichte.erstellen", modul: "berichte", name: "Berichte erstellen", erklaerung: "Auswertungen dieses Boards erstellen und herunterladen" },
];

const ALLE = RECHTE.map((r) => r.id);

function rollen(): Rolle[] {
  return [
    { id: "besitzer", name: "Besitzer", vorgabe: true, rechte: ALLE },
    { id: "mitglied", name: "Mitglied", vorgabe: true, rechte: ["karten.anlegen", "karten.bearbeiten", "karten.verschieben", "karten.loeschen",
      "kommentieren", "zeit.buchen", "zeit.andere.sehen", "abwesenheit.sehen", "serien.verwalten", "berichte.erstellen"] },
    { id: "leser", name: "Leser", vorgabe: true, rechte: ["kommentieren"] },
  ];
}

/** Vorgaben eines neuen Boards (Mechanik 3.1) */
export const EINSTELLUNGEN_VORGABE = { alterungWarnung: 4, alterungGefahr: 8, ladeschritt: 50, archivTage: 365 };

export const BOARDS: Board[] = [
  {
    id: "b-prod", name: "Produktionsplanung", kuerzel: "PROD", farbe: "petrol", laufnummer: 148,
    spalten: [
      { id: "s-eingang", name: "Eingang", farbe: "stahl", erledigt: false },
      { id: "s-geplant", name: "Geplant", farbe: "himmel", erledigt: false },
      { id: "s-arbeit", name: "In Arbeit", farbe: "honig", erledigt: false, grenze: 4 },
      { id: "s-pruefung", name: "Prüfung", farbe: "flieder", erledigt: false, grenze: 3 },
      { id: "s-fertig", name: "Erledigt", farbe: "minze", erledigt: true, zeitfenster: "woche" },
    ],
    labels: [
      { id: "l-kunde", name: "Kunde", farbe: "petrol" },
      { id: "l-intern", name: "Intern", farbe: "stahl" },
      { id: "l-fehler", name: "Fehler", farbe: "koralle" },
      { id: "l-wartung", name: "Wartung", farbe: "sand" },
      { id: "l-angebot", name: "Angebot", farbe: "violett" },
    ],
    felder: [
      { id: "f-kunde", name: "Kunde", art: "text", aufKarte: true },
      { id: "f-auftrag", name: "Auftragsnummer", art: "text", aufKarte: false },
      { id: "f-stueck", name: "Stückzahl", art: "zahl", aufKarte: true },
      { id: "f-maschine", name: "Maschine", art: "auswahl", optionen: ["CNC 1", "CNC 2", "Laser", "Kantbank"], aufKarte: false },
    ],
    rollen: [...rollen(), { id: "r-werkstatt", name: "Werkstatt", rechte: ["karten.verschieben", "kommentieren", "zeit.buchen"] }],
    mitglieder: [
      { konto: "k-max", rolle: "besitzer", seit: "2025-03-03" },
      { konto: "k-anna", rolle: "mitglied", seit: "2025-03-03" },
      { konto: "k-jonas", rolle: "mitglied", seit: "2025-04-14" },
      { konto: "k-tim", rolle: "r-werkstatt", seit: "2026-02-02" },
      { konto: "k-lea", rolle: "leser", seit: "2026-09-21" },
    ],
    module: { zeiterfassung: true, arbeitszeit: true, serien: true, berichte: true, transkripte: true, vorlesen: true, ki: true },
    einstellungen: { ...EINSTELLUNGEN_VORGABE },
  },
  {
    id: "b-ideen", name: "Ideen", kuerzel: "IDEE", farbe: "flieder", laufnummer: 23,
    spalten: [
      { id: "s-gesammelt", name: "Gesammelt", farbe: "flieder", erledigt: false },
      { id: "s-bewerten", name: "Bewerten", farbe: "himmel", erledigt: false },
      { id: "s-umsetzen", name: "Umsetzen", farbe: "tuerkis", erledigt: false },
      { id: "s-umgesetzt", name: "Umgesetzt", farbe: "minze", erledigt: true, zeitfenster: "monat" },
    ],
    labels: [{ id: "l-produkt", name: "Produkt", farbe: "violett" }, { id: "l-ablauf", name: "Ablauf", farbe: "tuerkis" }],
    felder: [{ id: "f-nutzen", name: "Nutzen", art: "auswahl", optionen: ["klein", "mittel", "groß"], aufKarte: true }],
    rollen: rollen(),
    mitglieder: [{ konto: "k-max", rolle: "besitzer", seit: "2025-06-10" }, { konto: "k-anna", rolle: "mitglied", seit: "2025-06-12" }],
    module: { zeiterfassung: false, arbeitszeit: false, serien: false, berichte: false, transkripte: true, vorlesen: true, ki: true },
    einstellungen: { ...EINSTELLUNGEN_VORGABE, alterungWarnung: 14, alterungGefahr: 30 },
  },
  {
    id: "b-haus", name: "Haushalt", kuerzel: "HAUS", farbe: "minze", laufnummer: 61,
    spalten: [
      { id: "s-offen", name: "Offen", farbe: "stahl", erledigt: false },
      { id: "s-dran", name: "Dran", farbe: "honig", erledigt: false },
      { id: "s-erledigt", name: "Erledigt", farbe: "minze", erledigt: true, zeitfenster: "heute" },
    ],
    labels: [{ id: "l-einkauf", name: "Einkauf", farbe: "honig" }, { id: "l-garten", name: "Garten", farbe: "minze" }],
    felder: [],
    rollen: rollen(),
    mitglieder: [{ konto: "k-max", rolle: "besitzer", seit: "2025-01-05" }],
    module: { zeiterfassung: true, arbeitszeit: false, serien: true, berichte: false, transkripte: false, vorlesen: true, ki: false },
    einstellungen: { ...EINSTELLUNGEN_VORGABE },
  },
];

export const LEER = { kommentare: [], checkliste: [], anhaenge: [], transkripte: [], verlauf: [], felder: {}, labels: [] };

/** Die Karten der Boards im Zeitfenster; weitere (Vorwoche, Planung, Archiv) stehen in den daten-<bereich>.ts */
export const KARTEN: Karte[] = [
  // Eingang
  { ...LEER, id: "c-148", board: "b-prod", schluessel: "PROD-148", spalte: "s-eingang", titel: "Anfrage Gehäuseserie 400 Stück prüfen", art: "arbeit",
    zustaendig: ["k-max"], prioritaet: "mittel", labels: ["l-kunde", "l-angebot"], bewegtAm: "2026-10-27T08:12:00", erstelltAm: "2026-10-27T08:12:00",
    felder: { "f-kunde": "Lindner Möbelbau", "f-stueck": "400" } },
  { ...LEER, id: "c-146", board: "b-prod", schluessel: "PROD-146", spalte: "s-eingang", titel: "Kühlmittel CNC 2 tauschen", art: "arbeit",
    zustaendig: ["k-jonas"], prioritaet: "niedrig", labels: ["l-wartung"], faellig: "2026-10-30", bewegtAm: "2026-10-24T14:00:00", erstelltAm: "2026-10-24T14:00:00",
    serie: "se-kuehl", felder: { "f-maschine": "CNC 2" } },
  { ...LEER, id: "c-141", board: "b-prod", schluessel: "PROD-141", spalte: "s-eingang", titel: "Zeichnungsstand Halterung B klären", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "keine", bewegtAm: "2026-10-19T09:30:00", erstelltAm: "2026-10-19T09:30:00",
    blockiert: "Wartet auf Rückmeldung der Konstruktion", felder: { "f-kunde": "Hoffmann Antriebe" } },
  // Geplant
  { ...LEER, id: "c-139", board: "b-prod", schluessel: "PROD-139", spalte: "s-geplant", titel: "Musterteile Serie K7 fräsen", art: "arbeit",
    zustaendig: ["k-jonas", "k-max"], prioritaet: "hoch", labels: ["l-kunde"], start: "2026-10-28", faellig: "2026-10-29",
    schaetzungMin: 360, bewegtAm: "2026-10-23T11:05:00", erstelltAm: "2026-10-20T08:40:00", cover: "petrol",
    checkliste: [{ text: "Rohmaterial bereitstellen", erledigt: true }, { text: "Programm einfahren", erledigt: false }, { text: "Erstmuster messen", erledigt: false }],
    felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "12", "f-auftrag": "A-2026-0417", "f-maschine": "CNC 1" } },
  { ...LEER, id: "c-137", board: "b-prod", schluessel: "PROD-137", spalte: "s-geplant", titel: "Prüfvorrichtung für Biegeteile bauen", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "mittel", labels: ["l-intern"], faellig: "2026-11-04", schaetzungMin: 480,
    bewegtAm: "2026-10-21T16:20:00", erstelltAm: "2026-10-14T10:00:00", gruppe: "g-pruef",
    checkliste: [{ text: "Skizze", erledigt: true }, { text: "Material bestellen", erledigt: true }, { text: "Grundplatte", erledigt: false }, { text: "Anschläge", erledigt: false }] },
  { ...LEER, id: "c-136", board: "b-prod", schluessel: "PROD-136", spalte: "s-geplant", titel: "Messmittel für Prüfvorrichtung kalibrieren", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "niedrig", labels: ["l-intern"], bewegtAm: "2026-10-21T16:20:00", erstelltAm: "2026-10-14T10:05:00",
    gruppe: "g-pruef" },
  // In Arbeit
  { ...LEER, id: "c-131", board: "b-prod", schluessel: "PROD-131", spalte: "s-arbeit", titel: "Angebot Schaltschrankgehäuse kalkulieren", art: "arbeit",
    zustaendig: ["k-max"], prioritaet: "dringend", labels: ["l-kunde", "l-angebot"], faellig: "2026-10-27", schaetzungMin: 180,
    start: "2026-10-26", bewegtAm: "2026-10-26T08:15:00", erstelltAm: "2026-10-22T13:30:00",
    beschreibung: "<p>Kunde möchte <strong>120 Gehäuse</strong> in RAL 7035, Lieferung bis KW 50.</p><ul><li>Blechstärke 1,5 mm</li><li>Montageplatte verzinkt</li><li>Türanschlag rechts</li></ul><p>Preise der Lieferanten liegen im Anhang.</p>",
    notizen: "<p>Telefonat 26.10.: Kunde akzeptiert Teillieferung, wenn die ersten 40 Stück bis KW 48 kommen.</p>",
    checkliste: [{ text: "Materialpreise einholen", erledigt: true }, { text: "Laserzeit schätzen", erledigt: true }, { text: "Pulverbeschichtung anfragen", erledigt: false }, { text: "Angebot schreiben", erledigt: false }],
    kommentare: [
      { von: "k-anna", zeit: "2026-10-26T15:40:00", text: "Pulverbeschichtung bei Fa. Rother angefragt, Antwort morgen früh." },
      { von: "k-max", zeit: "2026-10-27T08:20:00", text: "@Anna danke, ich rechne erst mal mit dem alten Preis." },
    ],
    anhaenge: [{ name: "Lieferantenpreise.pdf", groesse: "312 KB", art: "pdf" }, { name: "Skizze Gehäuse.png", groesse: "1,4 MB", art: "bild" },
      { name: "Kalkulation 2026.ods", groesse: "88 KB", art: "tabelle", verknuepft: true }],
    transkripte: [{ aufnahme: "Telefonat Kunde 26.10.", stelle: "04:12", text: "die ersten vierzig Stück bis Kalenderwoche achtundvierzig" }],
    verlauf: [
      { zeit: "2026-10-22T13:30:00", von: "k-max", text: "hat die Karte angelegt" },
      { zeit: "2026-10-26T08:15:00", von: "k-max", text: "hat sie nach In Arbeit verschoben" },
      { zeit: "2026-10-27T09:58:00", von: "k-max", text: "hat den Timer gestartet" },
    ],
    felder: { "f-kunde": "Elektro Brandt", "f-stueck": "120", "f-auftrag": "A-2026-0431", "f-maschine": "Laser" } },
  { ...LEER, id: "c-128", board: "b-prod", schluessel: "PROD-128", spalte: "s-arbeit", titel: "Laser: Düse wechseln und Strahl justieren", art: "arbeit",
    zustaendig: ["k-jonas"], prioritaet: "hoch", labels: ["l-wartung", "l-fehler"], start: "2026-10-27",
    bewegtAm: "2026-10-27T07:50:00", erstelltAm: "2026-10-26T17:10:00", felder: { "f-maschine": "Laser" } },
  { ...LEER, id: "c-125", board: "b-prod", schluessel: "PROD-125", spalte: "s-arbeit", titel: "Serie K5 Abkanten, Los 2 von 3", art: "arbeit",
    zustaendig: ["k-tim"], prioritaet: "mittel", labels: ["l-kunde"], start: "2026-10-19", faellig: "2026-10-28", schaetzungMin: 600,
    bewegtAm: "2026-10-20T07:30:00", erstelltAm: "2026-10-13T09:00:00", felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "250" } },
  { ...LEER, id: "c-122", board: "b-prod", schluessel: "PROD-122", spalte: "s-arbeit", titel: "Arbeitsanweisung Kantbank überarbeiten", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "niedrig", labels: ["l-intern"], bewegtAm: "2026-10-09T10:00:00", erstelltAm: "2026-10-02T10:00:00" },
  { ...LEER, id: "c-118", board: "b-prod", schluessel: "PROD-118", spalte: "s-arbeit", titel: "Lagerplätze Rohmaterial neu beschriften", art: "arbeit",
    zustaendig: ["k-tim"], prioritaet: "keine", labels: ["l-intern"], bewegtAm: "2026-10-26T13:00:00", erstelltAm: "2026-10-01T08:00:00" },
  // Prüfung
  { ...LEER, id: "c-115", board: "b-prod", schluessel: "PROD-115", spalte: "s-pruefung", titel: "Erstmuster Halter K5 vermessen", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "hoch", labels: ["l-kunde"], faellig: "2026-10-26", bewegtAm: "2026-10-25T16:00:00", erstelltAm: "2026-10-12T09:00:00",
    felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "3" } },
  // Erledigt (Zeitfenster: diese Woche)
  { ...LEER, id: "c-112", board: "b-prod", schluessel: "PROD-112", spalte: "s-fertig", titel: "Wochenwartung Kompressor", art: "arbeit", zustaendig: ["k-jonas"],
    prioritaet: "keine", labels: ["l-wartung"], faellig: "2026-10-26", schaetzungMin: 45, bewegtAm: "2026-10-26T15:00:00", erstelltAm: "2026-10-12T06:00:00",
    abgeschlossen: "2026-10-26", serie: "se-kompressor" },
  { ...LEER, id: "c-110", board: "b-prod", schluessel: "PROD-110", spalte: "s-fertig", titel: "Lieferschein Serie K5 Los 1", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "mittel", labels: ["l-kunde"], bewegtAm: "2026-10-26T11:20:00", erstelltAm: "2026-10-21T10:00:00", abgeschlossen: "2026-10-26" },
  { ...LEER, id: "c-107", board: "b-prod", schluessel: "PROD-107", spalte: "s-fertig", titel: "Angebot Halterungen Brandt verschickt", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "hoch", labels: ["l-angebot"], bewegtAm: "2026-10-26T09:00:00", erstelltAm: "2026-10-19T08:00:00", abgeschlossen: "2026-10-26" },
  // Ideen
  { ...LEER, id: "c-i23", board: "b-ideen", schluessel: "IDEE-23", spalte: "s-gesammelt", titel: "Rüstzeiten am Laser mit Vorlagen verkürzen", art: "idee",
    zustaendig: ["k-max"], prioritaet: "keine", labels: ["l-ablauf"], bewegtAm: "2026-10-25T18:00:00", erstelltAm: "2026-10-25T18:00:00",
    felder: { "f-nutzen": "groß" } },
  { ...LEER, id: "c-i21", board: "b-ideen", schluessel: "IDEE-21", spalte: "s-bewerten", titel: "Restblech als Zuschnittware anbieten", art: "idee",
    zustaendig: ["k-anna"], prioritaet: "keine", labels: ["l-produkt"], bewegtAm: "2026-10-20T10:00:00", erstelltAm: "2026-10-10T10:00:00",
    felder: { "f-nutzen": "mittel" } },
  // Haushalt
  { ...LEER, id: "c-h61", board: "b-haus", schluessel: "HAUS-61", spalte: "s-offen", titel: "Englisch lernen", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "keine", faellig: "2026-10-27", schaetzungMin: 30, bewegtAm: "2026-10-27T00:00:00", erstelltAm: "2026-10-20T00:00:00", serie: "se-englisch" },
  { ...LEER, id: "c-h58", board: "b-haus", schluessel: "HAUS-58", spalte: "s-dran", titel: "Winterreifen aufziehen lassen", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "mittel", faellig: "2026-10-26", bewegtAm: "2026-10-24T19:00:00", erstelltAm: "2026-10-20T19:00:00" },
];

export const GRUPPEN: Gruppe[] = [{ id: "g-pruef", zeitTeilen: true }];

/** Laufende Timer: einer je Person; Max auf PROD-131, Jonas auf PROD-128 */
export const TIMER: Timer[] = [
  { konto: "k-max", karte: "c-131", seit: "2026-10-27T09:58:00" },
  { konto: "k-jonas", karte: "c-128", seit: "2026-10-27T10:05:00" },
];

export const ZEITEINTRAEGE: Zeiteintrag[] = [
  { id: "z1", karte: "c-131", konto: "k-max", datum: "2026-10-26", von: "08:15", bis: "10:10", sekunden: 6900, herkunft: "timer" },
  { id: "z2", karte: "c-131", konto: "k-max", datum: "2026-10-26", sekunden: 1800, herkunft: "hand", notiz: "Preise am Abend verglichen" },
  { id: "z3", karte: "c-131", konto: "k-max", datum: "2026-10-27", von: "08:30", bis: "08:40", sekunden: 600, herkunft: "timer" },
  { id: "z4", karte: "c-110", konto: "k-max", datum: "2026-10-26", von: "11:00", bis: "11:25", sekunden: 1500, herkunft: "timer" },
  { id: "z5", karte: "c-107", konto: "k-max", datum: "2026-10-23", sekunden: 4 * 3600 + 600, herkunft: "hand" },
  { id: "z6", karte: "c-125", konto: "k-tim", datum: "2026-10-23", sekunden: 4 * 3600, herkunft: "timer" },
  { id: "z7", karte: "c-125", konto: "k-tim", datum: "2026-10-19", sekunden: 3 * 3600 + 1200, herkunft: "timer" },
  { id: "z8", karte: "c-118", konto: "k-tim", datum: "2026-10-16", sekunden: 900, herkunft: "hand" },
];

/** Serien mit ihren Regeln; der nächste Tag und die Vorbuchungen ergeben sich daraus (regeln/serien.ts) */
export const SERIEN: Serie[] = [
  { id: "se-kompressor", board: "b-prod", titel: "Wochenwartung Kompressor", rhythmus: "woechentlich", tage: [1], uhrzeit: "06:00", dauerMin: 45,
    zielspalte: "s-eingang", teilnehmer: ["k-jonas"], beschreibung: "Kondensat ablassen, Filter prüfen, Druck ins Protokoll eintragen.",
    labels: ["l-wartung"], ab: "2026-01-05", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
    auslass: [], beruehrt: [], verworfen: [] },
  { id: "se-kuehl", board: "b-prod", titel: "Kühlmittel CNC prüfen", rhythmus: "monatlich", monatsregel: "tag", monatstag: 30, dauerMin: 60,
    zielspalte: "s-eingang", teilnehmer: ["k-jonas"], beschreibung: "Konzentration messen, bei Bedarf tauschen, Ölabscheider leeren.",
    labels: ["l-wartung"], ab: "2026-03-30", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
    auslass: [], beruehrt: [], verworfen: [] },
  { id: "se-runde", board: "b-prod", titel: "Produktionsrunde", rhythmus: "werktags", uhrzeit: "07:30", dauerMin: 15, zielspalte: "s-geplant",
    teilnehmer: ["k-max", "k-anna", "k-jonas", "k-tim"], beschreibung: "Stand der Aufträge, Engpässe an den Maschinen, wer heute was macht.",
    labels: ["l-intern"], ab: "2026-09-01", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
    auslass: [{ tag: "2026-11-04", von: "k-max", am: "2026-10-23T09:12:00" }],
    beruehrt: [{ tag: "2026-10-29", grund: "Anna hat die Tagesordnung ergänzt" }], verworfen: ["2026-10-21"] },
  { id: "se-englisch", board: "b-haus", titel: "Englisch lernen", rhythmus: "taeglich", uhrzeit: "12:00", dauerMin: 30, zielspalte: "s-offen",
    teilnehmer: ["k-max"], labels: [], ab: "2026-09-14", vorlaufTage: 7, wochenendenUeberspringen: false, feiertageUeberspringen: false,
    auslass: [], beruehrt: [], verworfen: [] },
  { id: "se-reinigung", board: "b-prod", titel: "Hallenreinigung", rhythmus: "woechentlich", tage: [5], uhrzeit: "14:00", dauerMin: 60,
    zielspalte: "s-eingang", teilnehmer: ["k-tim"], beschreibung: "Späne an den Maschinen, Gänge kehren, Abfall trennen.", labels: ["l-intern"],
    ab: "2026-06-05", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true, pausiertSeit: "2026-10-20",
    auslass: [], beruehrt: [], verworfen: [] },
  { id: "se-altpapier", board: "b-haus", titel: "Altpapier rausstellen", rhythmus: "woechentlich", tage: [3], uhrzeit: "20:00", dauerMin: 10,
    zielspalte: "s-offen", teilnehmer: ["k-max"], labels: ["l-einkauf"], ab: "2026-01-07", vorlaufTage: 7, wochenendenUeberspringen: false,
    feiertageUeberspringen: false, auslass: [], beruehrt: [], verworfen: [] },
];

/** Termine: vorher zugesagt, nach dem Termin bestätigt jeder seine Zeit */
export const TERMINE: Termin[] = [
  { id: "t1", board: "b-prod", titel: "Abnahme Erstmuster mit Krause", datum: "2026-10-29", von: "10:00", bis: "11:30", teilnehmer: ["k-max", "k-anna"],
    ort: "Prüfraum", zugesagt: ["k-anna"], bestaetigt: [] },
  { id: "t2", board: "b-prod", titel: "Lieferantengespräch Pulverbeschichtung", datum: "2026-10-27", von: "14:00", bis: "14:45", teilnehmer: ["k-max"],
    zugesagt: ["k-max"], bestaetigt: [] },
  { id: "t3", board: "b-prod", titel: "Abstimmung Lieferplan K5", datum: "2026-10-26", von: "13:00", bis: "14:00", teilnehmer: ["k-max", "k-anna"],
    ort: "Büro", zugesagt: ["k-max", "k-anna"], bestaetigt: ["k-anna"] },
  { id: "t4", board: "b-prod", titel: "Sicherheitsunterweisung Werkstatt", datum: "2026-11-04", von: "09:00", bis: "10:00",
    teilnehmer: ["k-max", "k-anna", "k-jonas", "k-tim"], ort: "Werkstatt", zugesagt: ["k-max", "k-tim"], bestaetigt: [] },
  { id: "t5", board: "b-prod", titel: "Quartalsgespräch Krause Gerätebau", datum: "2026-11-12", von: "14:00", bis: "15:30",
    teilnehmer: ["k-max", "k-anna"], ort: "Besprechungsraum", zugesagt: [], bestaetigt: [] },
  { id: "t6", board: "b-prod", titel: "Wartung Laser durch den Hersteller", datum: "2026-10-30", von: "07:00", bis: "12:00",
    teilnehmer: ["k-jonas"], ort: "Halle 2", zugesagt: ["k-jonas"], bestaetigt: [] },
  { id: "t7", board: "b-haus", titel: "Kontrolle beim Zahnarzt", datum: "2026-10-30", von: "08:30", bis: "09:15", teilnehmer: ["k-max"],
    zugesagt: ["k-max"], bestaetigt: [] },
];

export const HINWEISE: Hinweis[] = [
  { id: "h1", art: "erwaehnt", zeit: "2026-10-27T08:20:00", von: "k-anna", board: "b-prod", karte: "c-131", text: "Anna Berger hat dich in PROD-131 erwähnt", gelesen: false },
  { id: "h2", art: "zugewiesen", zeit: "2026-10-27T07:55:00", von: "k-jonas", board: "b-prod", karte: "c-139", text: "Jonas Keller hat dir PROD-139 zugewiesen", gelesen: false },
  { id: "h3", art: "faellig", zeit: "2026-10-27T06:00:00", board: "b-prod", karte: "c-131", text: "PROD-131 ist heute fällig", gelesen: false },
  { id: "h4", art: "termin", zeit: "2026-10-26T17:00:00", von: "k-anna", board: "b-prod", text: "Termin morgen 14:00: Lieferantengespräch Pulverbeschichtung", gelesen: true },
  { id: "h5", art: "verschoben", zeit: "2026-10-26T16:00:00", von: "k-anna", board: "b-prod", karte: "c-115", text: "Anna Berger hat PROD-115 nach Prüfung verschoben", gelesen: true },
];

/** Hinweise je Art und Weg (persönliche Einstellung von Max) */
export const EINSTELLUNGEN_PERSON: PersonEinstellungen = {
  hinweise: {
    zugewiesen: { pinnwand: true, push: true, assistent: false },
    faellig: { pinnwand: true, push: true, assistent: true },
    erwaehnt: { pinnwand: true, push: true, assistent: false },
    termin: { pinnwand: true, push: true, assistent: true },
    kommentar: { pinnwand: true, push: false, assistent: false },
    verschoben: { pinnwand: true, push: false, assistent: false },
  },
};

const ERLEDIGT = (name = "Erledigt") => ({ name, farbe: "minze" as const, erledigt: true });

export const VORLAGEN: Vorlage[] = [
  { id: "v-aufgaben", name: "Aufgaben", beschreibung: "Offen, Dran, Erledigt; mit Zeiterfassung und Serien", symbol: "fa-list-check",
    spalten: [{ name: "Offen", farbe: "stahl", erledigt: false }, { name: "Dran", farbe: "honig", erledigt: false }, ERLEDIGT()],
    felder: [], labels: [], module: ["zeiterfassung", "serien", "vorlesen"] },
  { id: "v-projekt", name: "Projekt", beschreibung: "Eingang bis Erledigt mit Prüfung, Zeiterfassung, Arbeitszeit und Berichten", symbol: "fa-diagram-project",
    spalten: [{ name: "Eingang", farbe: "stahl", erledigt: false }, { name: "Geplant", farbe: "himmel", erledigt: false },
      { name: "In Arbeit", farbe: "honig", erledigt: false, grenze: 4 }, { name: "Prüfung", farbe: "flieder", erledigt: false, grenze: 3 }, ERLEDIGT()],
    felder: [], labels: [], module: ["zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki"] },
  { id: "v-ideen", name: "Ideen", beschreibung: "Gesammelt, Bewerten, Umsetzen; Karten sind Ideen ohne Zeiten", symbol: "fa-lightbulb",
    spalten: [{ name: "Gesammelt", farbe: "flieder", erledigt: false }, { name: "Bewerten", farbe: "himmel", erledigt: false },
      { name: "Umsetzen", farbe: "tuerkis", erledigt: false }, ERLEDIGT("Umgesetzt")],
    felder: [], labels: [], module: ["transkripte", "vorlesen", "ki"] },
  { id: "v-werkstatt", name: "Werkstattplanung", beschreibung: "Eigene Vorlage aus Produktionsplanung, mit Feldern Kunde, Stückzahl und Maschine",
    symbol: "fa-industry",
    spalten: [{ name: "Eingang", farbe: "stahl", erledigt: false }, { name: "Geplant", farbe: "himmel", erledigt: false },
      { name: "In Arbeit", farbe: "honig", erledigt: false, grenze: 4 }, { name: "Prüfung", farbe: "flieder", erledigt: false, grenze: 3 }, ERLEDIGT()],
    felder: [{ name: "Kunde", art: "text", aufKarte: true }, { name: "Auftragsnummer", art: "text", aufKarte: false },
      { name: "Stückzahl", art: "zahl", aufKarte: true }, { name: "Maschine", art: "auswahl", optionen: ["CNC 1", "CNC 2", "Laser", "Kantbank"], aufKarte: false }],
    labels: [{ name: "Kunde", farbe: "petrol" }, { name: "Intern", farbe: "stahl" }, { name: "Wartung", farbe: "sand" }],
    module: ["zeiterfassung", "arbeitszeit", "serien", "berichte"], eigen: true },
];

/** Halbe Arbeitstage (Vorgabe Heiligabend und Silvester, wie in der alten App) */
const HALBTAGE = [{ monat: 12, tag: 24, name: "Heiligabend" }, { monat: 12, tag: 31, name: "Silvester" }];

export const ZEITKONTEN: Zeitkonto[] = [
  { konto: "k-max", ab: "2025-01-01", wochenstunden: 40, tage: [1, 2, 3, 4, 5], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 30, resturlaubVorjahr: 4, halbtage: HALBTAGE },
  { konto: "k-anna", ab: "2025-01-01", wochenstunden: 32, tage: [1, 2, 3, 4], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 28, resturlaubVorjahr: 0, halbtage: HALBTAGE },
  { konto: "k-jonas", ab: "2025-01-01", wochenstunden: 40, tage: [1, 2, 3, 4, 5], bundesland: "Niedersachsen", urlaubsanspruch: 30, resturlaubVorjahr: 2, halbtage: HALBTAGE },
  { konto: "k-tim", ab: "2026-02-01", wochenstunden: 20, tage: [1, 3, 5], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 15, resturlaubVorjahr: 0, halbtage: HALBTAGE },
  { konto: "k-lea", ab: "2026-09-01", wochenstunden: 30, tage: [1, 2, 3, 4, 5], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 27, resturlaubVorjahr: 0, halbtage: HALBTAGE },
];

export const ABWESENHEITEN: Abwesenheit[] = [
  { id: "a1", konto: "k-anna", von: "2026-11-05", bis: "2026-11-05", art: "frei", notiz: "Überstunden abbauen" },
  { id: "a2", konto: "k-jonas", von: "2026-11-02", bis: "2026-11-06", art: "urlaub" },
  { id: "a3", konto: "k-max", von: "2026-11-02", bis: "2026-11-02", art: "fortbildung", notiz: "Messe" },
  { id: "a4", konto: "k-max", von: "2026-12-23", bis: "2026-12-31", art: "urlaub" },
  { id: "a5", konto: "k-tim", von: "2026-10-26", bis: "2026-10-26", art: "krank" },
];
