// Beispieldaten der Planung (Serien und Termine, Kalender, Zeitachse), zusätzlich zu beispiel/daten.ts: Karten mit
// Start und Fällig für die Zeitachse, weitere Serien und Termine, die Regeln jeder Serie und die Feiertage der
// Bundesländer der Mitglieder. Heute ist Dienstag, der 27. Oktober 2026; angemeldet ist Max Paulsen.

import type { Karte, Kennung, Serie, Termin } from "../../modell";
import type { Feiertag, SerienRegel } from "./typen";

type Pflicht = Pick<Karte, "id" | "schluessel" | "spalte" | "titel" | "zustaendig" | "prioritaet" | "erstelltAm">;

function karte(k: Pflicht & Partial<Karte>): Karte {
  return { board: "b-prod", art: "arbeit", labels: [], checkliste: [], kommentare: [], anhaenge: [], transkripte: [], verlauf: [],
           felder: {}, erfasstSek: 0, bewegtAm: k.erstelltAm, ...k };
}

/** Karten der Produktionsplanung mit Start und Fällig (Zeitachse) und weiteren Fälligkeiten (Kalender) */
export const PLAN_KARTEN: Karte[] = [
  karte({ id: "c-147", schluessel: "PROD-147", spalte: "s-eingang", titel: "Lieferplan 2027 mit Krause abstimmen", zustaendig: ["k-max"],
          prioritaet: "mittel", labels: ["l-kunde"], start: "2026-11-09", faellig: "2026-11-20", erstelltAm: "2026-10-26T14:10:00",
          felder: { "f-kunde": "Krause Gerätebau" } }),
  karte({ id: "c-145", schluessel: "PROD-145", spalte: "s-geplant", titel: "Wartungsplan Laser 2027 erstellen", zustaendig: ["k-jonas"],
          prioritaet: "niedrig", labels: ["l-wartung"], start: "2026-11-16", faellig: "2026-11-27", erstelltAm: "2026-10-23T08:30:00" }),
  karte({ id: "c-144", schluessel: "PROD-144", spalte: "s-geplant", titel: "Serie K5 Abkanten, Los 3 von 3", zustaendig: ["k-tim"],
          prioritaet: "mittel", labels: ["l-kunde"], start: "2026-11-02", faellig: "2026-11-06", schaetzungMin: 600, erstelltAm: "2026-10-13T09:05:00",
          felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "250" } }),
  karte({ id: "c-143", schluessel: "PROD-143", spalte: "s-geplant", titel: "Erstlos 40 Gehäuse für Elektro Brandt fertigen", zustaendig: ["k-jonas", "k-max"],
          prioritaet: "hoch", labels: ["l-kunde"], start: "2026-11-09", faellig: "2026-11-25", erstelltAm: "2026-10-22T13:40:00", cover: "petrol",
          felder: { "f-kunde": "Elektro Brandt", "f-stueck": "40" } }),
  karte({ id: "c-142", schluessel: "PROD-142", spalte: "s-eingang", titel: "Muster Pulverbeschichtung prüfen und freigeben", zustaendig: ["k-anna"],
          prioritaet: "mittel", labels: ["l-kunde"], start: "2026-11-02", faellig: "2026-11-04", erstelltAm: "2026-10-22T15:00:00",
          felder: { "f-kunde": "Elektro Brandt" } }),
  karte({ id: "c-140", schluessel: "PROD-140", spalte: "s-eingang", titel: "Inventur Rohmaterial zum Jahresende", zustaendig: ["k-tim", "k-anna"],
          prioritaet: "niedrig", labels: ["l-intern"], start: "2026-12-14", faellig: "2026-12-22", erstelltAm: "2026-10-21T10:00:00" }),
  karte({ id: "c-138", schluessel: "PROD-138", spalte: "s-geplant", titel: "Einweisung neue Abkantpresse", zustaendig: ["k-anna"],
          prioritaet: "mittel", labels: ["l-intern"], start: "2026-11-11", faellig: "2026-11-12", erstelltAm: "2026-10-20T11:00:00" }),
  karte({ id: "c-135", schluessel: "PROD-135", spalte: "s-geplant", titel: "Absaugung am Laser reinigen", zustaendig: ["k-jonas"],
          prioritaet: "mittel", labels: ["l-wartung"], start: "2026-11-03", faellig: "2026-11-05", erstelltAm: "2026-10-19T07:45:00",
          felder: { "f-maschine": "Laser" } }),
  karte({ id: "c-134", schluessel: "PROD-134", spalte: "s-pruefung", titel: "Prüfprotokolle Halter K5 ablegen", zustaendig: ["k-anna"],
          prioritaet: "niedrig", labels: ["l-intern"], start: "2026-10-26", faellig: "2026-10-28", erstelltAm: "2026-10-19T08:00:00",
          bewegtAm: "2026-10-26T09:00:00" }),
  karte({ id: "c-133", schluessel: "PROD-133", spalte: "s-fertig", titel: "Serie K5 Abkanten, Los 1 von 3", zustaendig: ["k-tim"],
          prioritaet: "mittel", labels: ["l-kunde"], start: "2026-10-12", faellig: "2026-10-16", abgeschlossen: "2026-10-16", erfasstSek: 9 * 3600,
          erstelltAm: "2026-10-12T07:00:00", bewegtAm: "2026-10-16T15:30:00" }),
  karte({ id: "c-132", schluessel: "PROD-132", spalte: "s-fertig", titel: "Halter K5 Erstmuster fräsen", zustaendig: ["k-jonas"],
          prioritaet: "hoch", labels: ["l-kunde"], start: "2026-10-19", faellig: "2026-10-22", abgeschlossen: "2026-10-21", erfasstSek: 6 * 3600,
          erstelltAm: "2026-10-16T10:00:00", bewegtAm: "2026-10-21T16:00:00" }),
  karte({ id: "c-130", schluessel: "PROD-130", spalte: "s-eingang", titel: "Angebot Lochblechverkleidung Lindner", zustaendig: ["k-max"],
          prioritaet: "mittel", labels: ["l-angebot"], faellig: "2026-11-03", erstelltAm: "2026-10-21T09:30:00",
          felder: { "f-kunde": "Lindner Möbelbau" } }),
  karte({ id: "c-129", schluessel: "PROD-129", spalte: "s-geplant", titel: "Kundenbesuch Hoffmann vorbereiten", zustaendig: ["k-max"],
          prioritaet: "niedrig", labels: ["l-kunde"], start: "2026-10-29", faellig: "2026-10-30", erstelltAm: "2026-10-20T16:00:00",
          felder: { "f-kunde": "Hoffmann Antriebe" } }),
];

/** weitere Serien neben denen aus beispiel/daten.ts */
export const PLAN_SERIEN: Serie[] = [
  { id: "se-reinigung", board: "b-prod", titel: "Hallenreinigung", rhythmus: "woechentlich", tage: [5], uhrzeit: "14:00", dauerMin: 60,
    zielspalte: "s-eingang", teilnehmer: ["k-tim"], pausiert: true, naechste: "2026-10-30" },
  { id: "se-altpapier", board: "b-haus", titel: "Altpapier rausstellen", rhythmus: "woechentlich", tage: [3], uhrzeit: "20:00", dauerMin: 10,
    zielspalte: "s-offen", teilnehmer: ["k-max"], naechste: "2026-10-28" },
];

/** Regeln je Serie (Kennung der Serie) */
export const REGELN: Record<Kennung, SerienRegel> = {
  "se-kompressor": { serie: "se-kompressor", beschreibung: "Kondensat ablassen, Filter prüfen, Druck ins Protokoll eintragen.", labels: ["l-wartung"],
                     ab: "2026-01-05", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
                     auslass: [], beruehrt: [], verworfen: [] },
  "se-kuehl": { serie: "se-kuehl", beschreibung: "Konzentration messen, bei Bedarf tauschen, Ölabscheider leeren.", labels: ["l-wartung"],
                ab: "2026-03-30", monatsregel: "tag", monatstag: 30, vorlaufTage: 14, wochenendenUeberspringen: false,
                feiertageUeberspringen: true, auslass: [], beruehrt: [], verworfen: [] },
  "se-runde": { serie: "se-runde", beschreibung: "Stand der Aufträge, Engpässe an den Maschinen, wer heute was macht.", labels: ["l-intern"],
                ab: "2026-09-01", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true,
                auslass: [{ tag: "2026-11-04", von: "k-max", am: "2026-10-23T09:12:00" }],
                beruehrt: [{ tag: "2026-10-29", grund: "Anna hat die Tagesordnung ergänzt" }],
                verworfen: ["2026-10-21"] },
  "se-englisch": { serie: "se-englisch", labels: [], ab: "2026-09-14", vorlaufTage: 7, wochenendenUeberspringen: false,
                   feiertageUeberspringen: false, auslass: [], beruehrt: [], verworfen: [] },
  "se-reinigung": { serie: "se-reinigung", beschreibung: "Späne an den Maschinen, Gänge kehren, Abfall trennen.", labels: ["l-intern"],
                    ab: "2026-06-05", vorlaufTage: 14, wochenendenUeberspringen: false, feiertageUeberspringen: true, pausiertSeit: "2026-10-20",
                    auslass: [], beruehrt: [], verworfen: [] },
  "se-altpapier": { serie: "se-altpapier", labels: ["l-einkauf"], ab: "2026-01-07", vorlaufTage: 7, wochenendenUeberspringen: false,
                    feiertageUeberspringen: false, auslass: [], beruehrt: [], verworfen: [] },
};

/** Bestätigte Zeiten von Serientagen: bis zu diesem Tag sind in den Beispielen alle bestätigt, danach gilt die Liste */
export const BESTAETIGT_BIS = "2026-10-25";
export const BESTAETIGT: { serie: Kennung; tag: string; konten: Kennung[] }[] = [
  { serie: "se-runde", tag: "2026-10-26", konten: ["k-anna", "k-jonas"] },
  { serie: "se-kompressor", tag: "2026-10-26", konten: ["k-jonas"] },
];

/** weitere Termine (ohne Karte, mit Teilnehmern; bestätigt: vorher zugesagt, danach Zeit bestätigt) */
export const PLAN_TERMINE: Termin[] = [
  { id: "t3", board: "b-prod", titel: "Abstimmung Lieferplan K5", datum: "2026-10-26", von: "13:00", bis: "14:00", teilnehmer: ["k-max", "k-anna"],
    ort: "Büro", bestaetigt: ["k-anna"] },
  { id: "t4", board: "b-prod", titel: "Sicherheitsunterweisung Werkstatt", datum: "2026-11-04", von: "09:00", bis: "10:00",
    teilnehmer: ["k-max", "k-anna", "k-jonas", "k-tim"], ort: "Werkstatt", bestaetigt: ["k-max", "k-tim"] },
  { id: "t5", board: "b-prod", titel: "Quartalsgespräch Krause Gerätebau", datum: "2026-11-12", von: "14:00", bis: "15:30",
    teilnehmer: ["k-max", "k-anna"], ort: "Besprechungsraum", bestaetigt: [] },
  { id: "t6", board: "b-prod", titel: "Wartung Laser durch den Hersteller", datum: "2026-10-30", von: "07:00", bis: "12:00",
    teilnehmer: ["k-jonas"], ort: "Halle 2", bestaetigt: ["k-jonas"] },
  { id: "t7", board: "b-haus", titel: "Kontrolle beim Zahnarzt", datum: "2026-10-30", von: "08:30", bis: "09:15", teilnehmer: ["k-max"],
    bestaetigt: ["k-max"] },
];

/** Feiertage Oktober 2026 bis Januar 2027 (Bundesländer ausgeschrieben, leer: bundesweit) */
export const FEIERTAGE: Feiertag[] = [
  { tag: "2026-10-03", name: "Tag der Deutschen Einheit", laender: [] },
  { tag: "2026-10-31", name: "Reformationstag", laender: ["Brandenburg", "Bremen", "Hamburg", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"] },
  { tag: "2026-11-01", name: "Allerheiligen", laender: ["Baden-Württemberg", "Bayern", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland"] },
  { tag: "2026-11-18", name: "Buß- und Bettag", laender: ["Sachsen"] },
  { tag: "2026-12-25", name: "Erster Weihnachtstag", laender: [] },
  { tag: "2026-12-26", name: "Zweiter Weihnachtstag", laender: [] },
  { tag: "2027-01-01", name: "Neujahr", laender: [] },
  { tag: "2027-01-06", name: "Heilige Drei Könige", laender: ["Baden-Württemberg", "Bayern", "Sachsen-Anhalt"] },
];
