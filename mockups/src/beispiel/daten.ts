// Beispieldaten der Entwürfe: erfundene Personen, Firmen und Aufgaben (das Repo ist öffentlich). "Heute" ist in allen
// Entwürfen Dienstag, der 27. Oktober 2026, 10:42 Uhr; angemeldet ist Max Paulsen.

import type {
  Abwesenheit, Board, Gruppe, Hinweis, Karte, Konto, Ordner, Recht, Rolle, Serie, Termin, Vorlage, Zeiteintrag, Zeitkonto,
} from "../modell";

export const HEUTE = "2026-10-27";
export const JETZT = "2026-10-27T10:42:00";
export const ICH = "k-max";

export const KONTEN: Konto[] = [
  { id: "k-max", name: "Max Paulsen", kuerzel: "MP", farbe: "himmel" },
  { id: "k-anna", name: "Anna Berger", kuerzel: "AB", farbe: "minze" },
  { id: "k-jonas", name: "Jonas Keller", kuerzel: "JK", farbe: "honig" },
  { id: "k-lea", name: "Lea Wolf", kuerzel: "LW", farbe: "rose" },
  { id: "k-tim", name: "Tim Sander", kuerzel: "TS", farbe: "flieder" },
];

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

export const BOARDS: Board[] = [
  {
    id: "b-prod", name: "Produktionsplanung", kuerzel: "PROD", ordner: "o-firma", farbe: "petrol", laufnummer: 148,
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
    rollen: [...rollen(), { id: "r-kunde", name: "Werkstatt", rechte: ["karten.verschieben", "kommentieren", "zeit.buchen"] }],
    mitglieder: [
      { konto: "k-max", rolle: "besitzer" },
      { konto: "k-anna", rolle: "mitglied" },
      { konto: "k-jonas", rolle: "mitglied" },
      { konto: "k-tim", rolle: "r-kunde" },
      { konto: "k-lea", rolle: "leser" },
    ],
    module: { zeiterfassung: true, arbeitszeit: true, serien: true, berichte: true, transkripte: true, vorlesen: true, ki: true },
  },
  {
    id: "b-ideen", name: "Ideen", kuerzel: "IDEE", ordner: "o-firma", farbe: "flieder", laufnummer: 23,
    spalten: [
      { id: "s-gesammelt", name: "Gesammelt", farbe: "flieder", erledigt: false },
      { id: "s-bewerten", name: "Bewerten", farbe: "himmel", erledigt: false },
      { id: "s-umsetzen", name: "Umsetzen", farbe: "minze", erledigt: false },
      { id: "s-umgesetzt", name: "Umgesetzt", farbe: "minze", erledigt: true, zeitfenster: "monat" },
    ],
    labels: [{ id: "l-produkt", name: "Produkt", farbe: "violett" }, { id: "l-ablauf", name: "Ablauf", farbe: "tuerkis" }],
    felder: [{ id: "f-nutzen", name: "Nutzen", art: "auswahl", optionen: ["klein", "mittel", "groß"], aufKarte: true }],
    rollen: rollen(),
    mitglieder: [{ konto: "k-max", rolle: "besitzer" }, { konto: "k-anna", rolle: "mitglied" }],
    module: { zeiterfassung: false, arbeitszeit: false, serien: false, berichte: false, transkripte: true, vorlesen: true, ki: true },
  },
  {
    id: "b-haus", name: "Haushalt", kuerzel: "HAUS", ordner: "o-privat", farbe: "minze", laufnummer: 61,
    spalten: [
      { id: "s-offen", name: "Offen", farbe: "stahl", erledigt: false },
      { id: "s-dran", name: "Dran", farbe: "honig", erledigt: false },
      { id: "s-erledigt", name: "Erledigt", farbe: "minze", erledigt: true, zeitfenster: "heute" },
    ],
    labels: [{ id: "l-einkauf", name: "Einkauf", farbe: "honig" }, { id: "l-garten", name: "Garten", farbe: "minze" }],
    felder: [],
    rollen: rollen(),
    mitglieder: [{ konto: "k-max", rolle: "besitzer" }],
    module: { zeiterfassung: true, arbeitszeit: false, serien: true, berichte: false, transkripte: false, vorlesen: true, ki: false },
  },
];

const leer = { kommentare: [], checkliste: [], anhaenge: [], transkripte: [], verlauf: [], felder: {}, labels: [] };

export const KARTEN: Karte[] = [
  // Eingang
  { ...leer, id: "c-148", board: "b-prod", schluessel: "PROD-148", spalte: "s-eingang", titel: "Anfrage Gehäuseserie 400 Stück prüfen", art: "arbeit",
    zustaendig: [], prioritaet: "mittel", labels: ["l-kunde", "l-angebot"], erfasstSek: 0, bewegtAm: "2026-10-27T08:12:00", erstelltAm: "2026-10-27T08:12:00",
    felder: { "f-kunde": "Lindner Möbelbau", "f-stueck": "400" } },
  { ...leer, id: "c-146", board: "b-prod", schluessel: "PROD-146", spalte: "s-eingang", titel: "Kühlmittel CNC 2 tauschen", art: "arbeit",
    zustaendig: ["k-jonas"], prioritaet: "niedrig", labels: ["l-wartung"], faellig: "2026-10-30", erfasstSek: 0, bewegtAm: "2026-10-24T14:00:00", erstelltAm: "2026-10-24T14:00:00",
    serie: "se-kuehl", felder: { "f-maschine": "CNC 2" } },
  { ...leer, id: "c-141", board: "b-prod", schluessel: "PROD-141", spalte: "s-eingang", titel: "Zeichnungsstand Halterung B klären", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "keine", erfasstSek: 0, bewegtAm: "2026-10-19T09:30:00", erstelltAm: "2026-10-19T09:30:00",
    blockiert: "Wartet auf Rückmeldung der Konstruktion", felder: { "f-kunde": "Hoffmann Antriebe" } },
  // Geplant
  { ...leer, id: "c-139", board: "b-prod", schluessel: "PROD-139", spalte: "s-geplant", titel: "Musterteile Serie K7 fräsen", art: "arbeit",
    zustaendig: ["k-jonas", "k-max"], prioritaet: "hoch", labels: ["l-kunde"], start: "2026-10-28", faellig: "2026-10-29",
    schaetzungMin: 360, erfasstSek: 0, bewegtAm: "2026-10-23T11:05:00", erstelltAm: "2026-10-20T08:40:00", cover: "petrol",
    checkliste: [{ text: "Rohmaterial bereitstellen", erledigt: true }, { text: "Programm einfahren", erledigt: false }, { text: "Erstmuster messen", erledigt: false }],
    felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "12", "f-auftrag": "A-2026-0417", "f-maschine": "CNC 1" } },
  { ...leer, id: "c-137", board: "b-prod", schluessel: "PROD-137", spalte: "s-geplant", titel: "Prüfvorrichtung für Biegeteile bauen", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "mittel", labels: ["l-intern"], faellig: "2026-11-04", schaetzungMin: 480, erfasstSek: 3 * 3600 + 1200,
    bewegtAm: "2026-10-21T16:20:00", erstelltAm: "2026-10-14T10:00:00", gruppe: "g-pruef",
    checkliste: [{ text: "Skizze", erledigt: true }, { text: "Material bestellen", erledigt: true }, { text: "Grundplatte", erledigt: false }, { text: "Anschläge", erledigt: false }] },
  { ...leer, id: "c-136", board: "b-prod", schluessel: "PROD-136", spalte: "s-geplant", titel: "Messmittel für Prüfvorrichtung kalibrieren", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "niedrig", labels: ["l-intern"], erfasstSek: 2400, bewegtAm: "2026-10-21T16:20:00", erstelltAm: "2026-10-14T10:05:00",
    gruppe: "g-pruef" },
  // In Arbeit
  { ...leer, id: "c-131", board: "b-prod", schluessel: "PROD-131", spalte: "s-arbeit", titel: "Angebot Schaltschrankgehäuse kalkulieren", art: "arbeit",
    zustaendig: ["k-max"], prioritaet: "dringend", labels: ["l-kunde", "l-angebot"], faellig: "2026-10-27", schaetzungMin: 180,
    erfasstSek: 2 * 3600 + 35 * 60, laeuft: { seit: "2026-10-27T09:58:00", konto: "k-max" }, bewegtAm: "2026-10-26T08:15:00", erstelltAm: "2026-10-22T13:30:00",
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
  { ...leer, id: "c-128", board: "b-prod", schluessel: "PROD-128", spalte: "s-arbeit", titel: "Laser: Düse wechseln und Strahl justieren", art: "arbeit",
    zustaendig: ["k-jonas"], prioritaet: "hoch", labels: ["l-wartung", "l-fehler"], erfasstSek: 5400, laeuft: { seit: "2026-10-27T10:05:00", konto: "k-jonas" },
    bewegtAm: "2026-10-27T07:50:00", erstelltAm: "2026-10-26T17:10:00", felder: { "f-maschine": "Laser" } },
  { ...leer, id: "c-125", board: "b-prod", schluessel: "PROD-125", spalte: "s-arbeit", titel: "Serie K5 Abkanten, Los 2 von 3", art: "arbeit",
    zustaendig: ["k-tim"], prioritaet: "mittel", labels: ["l-kunde"], faellig: "2026-10-28", schaetzungMin: 600, erfasstSek: 7 * 3600 + 20 * 60,
    bewegtAm: "2026-10-20T07:30:00", erstelltAm: "2026-10-13T09:00:00", felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "250" } },
  { ...leer, id: "c-122", board: "b-prod", schluessel: "PROD-122", spalte: "s-arbeit", titel: "Arbeitsanweisung Kantbank überarbeiten", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "niedrig", labels: ["l-intern"], erfasstSek: 1800, bewegtAm: "2026-10-09T10:00:00", erstelltAm: "2026-10-02T10:00:00" },
  { ...leer, id: "c-118", board: "b-prod", schluessel: "PROD-118", spalte: "s-arbeit", titel: "Lagerplätze Rohmaterial neu beschriften", art: "arbeit",
    zustaendig: ["k-tim"], prioritaet: "keine", labels: ["l-intern"], erfasstSek: 900, bewegtAm: "2026-10-26T13:00:00", erstelltAm: "2026-10-01T08:00:00" },
  // Prüfung
  { ...leer, id: "c-115", board: "b-prod", schluessel: "PROD-115", spalte: "s-pruefung", titel: "Erstmuster Halter K5 vermessen", art: "arbeit",
    zustaendig: ["k-anna"], prioritaet: "hoch", labels: ["l-kunde"], faellig: "2026-10-26", erfasstSek: 3 * 3600, bewegtAm: "2026-10-25T16:00:00", erstelltAm: "2026-10-12T09:00:00",
    felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "3" } },
  // Erledigt (Fenster: diese Woche)
  { ...leer, id: "c-112", board: "b-prod", schluessel: "PROD-112", spalte: "s-fertig", titel: "Wochenwartung Kompressor", art: "arbeit", zustaendig: ["k-jonas"],
    prioritaet: "keine", labels: ["l-wartung"], erfasstSek: 2700, bewegtAm: "2026-10-26T15:00:00", erstelltAm: "2026-10-26T06:00:00", abgeschlossen: "2026-10-26", serie: "se-kompressor" },
  { ...leer, id: "c-110", board: "b-prod", schluessel: "PROD-110", spalte: "s-fertig", titel: "Lieferschein Serie K5 Los 1", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "mittel", labels: ["l-kunde"], erfasstSek: 1500, bewegtAm: "2026-10-26T11:20:00", erstelltAm: "2026-10-21T10:00:00", abgeschlossen: "2026-10-26" },
  { ...leer, id: "c-107", board: "b-prod", schluessel: "PROD-107", spalte: "s-fertig", titel: "Angebot Halterungen Brandt verschickt", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "hoch", labels: ["l-angebot"], erfasstSek: 4 * 3600 + 600, bewegtAm: "2026-10-26T09:00:00", erstelltAm: "2026-10-19T08:00:00", abgeschlossen: "2026-10-26" },
  // Ideen
  { ...leer, id: "c-i23", board: "b-ideen", schluessel: "IDEE-23", spalte: "s-gesammelt", titel: "Rüstzeiten am Laser mit Vorlagen verkürzen", art: "idee",
    zustaendig: ["k-max"], prioritaet: "keine", labels: ["l-ablauf"], erfasstSek: 0, bewegtAm: "2026-10-25T18:00:00", erstelltAm: "2026-10-25T18:00:00",
    felder: { "f-nutzen": "groß" } },
  { ...leer, id: "c-i21", board: "b-ideen", schluessel: "IDEE-21", spalte: "s-bewerten", titel: "Restblech als Zuschnittware anbieten", art: "idee",
    zustaendig: ["k-anna"], prioritaet: "keine", labels: ["l-produkt"], erfasstSek: 0, bewegtAm: "2026-10-20T10:00:00", erstelltAm: "2026-10-10T10:00:00",
    felder: { "f-nutzen": "mittel" } },
  // Haushalt
  { ...leer, id: "c-h61", board: "b-haus", schluessel: "HAUS-61", spalte: "s-offen", titel: "Englisch lernen", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "keine", erfasstSek: 0, faellig: "2026-10-27", bewegtAm: "2026-10-27T00:00:00", erstelltAm: "2026-10-27T00:00:00", serie: "se-englisch" },
  { ...leer, id: "c-h58", board: "b-haus", schluessel: "HAUS-58", spalte: "s-dran", titel: "Winterreifen aufziehen lassen", art: "arbeit", zustaendig: ["k-max"],
    prioritaet: "mittel", faellig: "2026-10-31", erfasstSek: 0, bewegtAm: "2026-10-24T19:00:00", erstelltAm: "2026-10-20T19:00:00" },
];

export const GRUPPEN: Gruppe[] = [{ id: "g-pruef", zeitTeilen: true }];

export const ZEITEINTRAEGE: Zeiteintrag[] = [
  { id: "z1", karte: "c-131", konto: "k-max", datum: "2026-10-26", von: "08:15", bis: "10:10", sekunden: 6900, herkunft: "timer" },
  { id: "z2", karte: "c-131", konto: "k-max", datum: "2026-10-26", sekunden: 1800, herkunft: "hand" },
  { id: "z3", karte: "c-131", konto: "k-max", datum: "2026-10-27", von: "08:30", bis: "08:40", sekunden: 600, herkunft: "timer" },
  { id: "z4", karte: "c-110", konto: "k-max", datum: "2026-10-26", von: "11:00", bis: "11:25", sekunden: 1500, herkunft: "timer" },
  { id: "z5", karte: "c-107", konto: "k-max", datum: "2026-10-23", sekunden: 4 * 3600 + 600, herkunft: "hand" },
  { id: "z6", karte: "c-125", konto: "k-tim", datum: "2026-10-26", sekunden: 4 * 3600, herkunft: "timer" },
  { id: "z7", karte: "c-125", konto: "k-tim", datum: "2026-10-27", sekunden: 3 * 3600 + 1200, herkunft: "timer" },
];

export const SERIEN: Serie[] = [
  { id: "se-kompressor", board: "b-prod", titel: "Wochenwartung Kompressor", rhythmus: "woechentlich", tage: [1], uhrzeit: "06:00", dauerMin: 45,
    zielspalte: "s-eingang", teilnehmer: ["k-jonas"], naechste: "2026-11-02" },
  { id: "se-kuehl", board: "b-prod", titel: "Kühlmittel CNC prüfen", rhythmus: "monatlich", dauerMin: 60, zielspalte: "s-eingang", teilnehmer: ["k-jonas"], naechste: "2026-11-30" },
  { id: "se-runde", board: "b-prod", titel: "Produktionsrunde", rhythmus: "werktags", uhrzeit: "07:30", dauerMin: 15, zielspalte: "s-geplant",
    teilnehmer: ["k-max", "k-anna", "k-jonas", "k-tim"], naechste: "2026-10-28" },
  { id: "se-englisch", board: "b-haus", titel: "Englisch lernen", rhythmus: "taeglich", uhrzeit: "12:00", dauerMin: 30, zielspalte: "s-offen", teilnehmer: ["k-max"], naechste: "2026-10-28" },
];

export const TERMINE: Termin[] = [
  { id: "t1", board: "b-prod", titel: "Abnahme Erstmuster mit Krause", datum: "2026-10-29", von: "10:00", bis: "11:30", teilnehmer: ["k-max", "k-anna"], ort: "Prüfraum", bestaetigt: ["k-anna"] },
  { id: "t2", board: "b-prod", titel: "Lieferantengespräch Pulverbeschichtung", datum: "2026-10-28", von: "14:00", bis: "14:45", teilnehmer: ["k-max"], bestaetigt: ["k-max"] },
];

export const HINWEISE: Hinweis[] = [
  { id: "h1", art: "erwaehnt", zeit: "2026-10-27T08:20:00", von: "k-anna", board: "b-prod", karte: "c-131", text: "Anna Berger hat dich in PROD-131 erwähnt", gelesen: false },
  { id: "h2", art: "zugewiesen", zeit: "2026-10-27T07:55:00", von: "k-jonas", board: "b-prod", karte: "c-139", text: "Jonas Keller hat dir PROD-139 zugewiesen", gelesen: false },
  { id: "h3", art: "faellig", zeit: "2026-10-27T06:00:00", board: "b-prod", karte: "c-131", text: "PROD-131 ist heute fällig", gelesen: false },
  { id: "h4", art: "termin", zeit: "2026-10-26T17:00:00", von: "k-anna", board: "b-prod", text: "Termin morgen 14:00: Lieferantengespräch Pulverbeschichtung", gelesen: true },
  { id: "h5", art: "verschoben", zeit: "2026-10-26T16:00:00", von: "k-anna", board: "b-prod", karte: "c-115", text: "Anna Berger hat PROD-115 nach Prüfung verschoben", gelesen: true },
];

export const VORLAGEN: Vorlage[] = [
  { id: "v-aufgaben", name: "Aufgaben", beschreibung: "Offen, Dran, Erledigt; mit Zeiterfassung und Serien", symbol: "fa-list-check",
    spalten: ["Offen", "Dran", "Erledigt"], module: ["zeiterfassung", "serien", "vorlesen"] },
  { id: "v-projekt", name: "Projekt", beschreibung: "Eingang bis Erledigt mit Prüfung, Zeiterfassung, Arbeitszeit und Berichten", symbol: "fa-diagram-project",
    spalten: ["Eingang", "Geplant", "In Arbeit", "Prüfung", "Erledigt"], module: ["zeiterfassung", "arbeitszeit", "serien", "berichte", "transkripte", "vorlesen", "ki"] },
  { id: "v-ideen", name: "Ideen", beschreibung: "Gesammelt, Bewerten, Umsetzen; Karten sind Ideen ohne Zeiten", symbol: "fa-lightbulb",
    spalten: ["Gesammelt", "Bewerten", "Umsetzen", "Umgesetzt"], module: ["transkripte", "vorlesen", "ki"] },
  { id: "v-werkstatt", name: "Werkstattplanung", beschreibung: "Eigene Vorlage aus Produktionsplanung, mit Feldern Kunde, Stückzahl und Maschine",
    symbol: "fa-industry", spalten: ["Eingang", "Geplant", "In Arbeit", "Prüfung", "Erledigt"], module: ["zeiterfassung", "arbeitszeit", "serien", "berichte"], eigen: true },
];

export const ZEITKONTEN: Zeitkonto[] = [
  { konto: "k-max", wochenstunden: 40, tage: [1, 2, 3, 4, 5], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 30, resturlaubVorjahr: 4, genommen: 21, geplant: 5 },
  { konto: "k-anna", wochenstunden: 32, tage: [1, 2, 3, 4], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 28, resturlaubVorjahr: 0, genommen: 18, geplant: 6 },
  { konto: "k-jonas", wochenstunden: 40, tage: [1, 2, 3, 4, 5], bundesland: "Niedersachsen", urlaubsanspruch: 30, resturlaubVorjahr: 2, genommen: 24, geplant: 3 },
  { konto: "k-tim", wochenstunden: 20, tage: [1, 3, 5], bundesland: "Nordrhein-Westfalen", urlaubsanspruch: 15, resturlaubVorjahr: 0, genommen: 9, geplant: 2 },
];

export const ABWESENHEITEN: Abwesenheit[] = [
  { konto: "k-anna", von: "2026-10-30", bis: "2026-10-30", art: "frei" },
  { konto: "k-jonas", von: "2026-11-02", bis: "2026-11-06", art: "urlaub" },
  { konto: "k-max", von: "2026-11-02", bis: "2026-11-02", art: "fortbildung", notiz: "Messe" },
  { konto: "k-max", von: "2026-12-23", bis: "2026-12-31", art: "urlaub" },
  { konto: "k-tim", von: "2026-10-26", bis: "2026-10-26", art: "krank" },
];
