// Beispieldaten für Serien, Kalender und Zeitachse, zusätzlich zu daten.ts: Karten mit Start und Fällig, die Karte der
// Produktionsrunde vom 26.10. und die Zeiten dazu. Eine bestätigte Zeit eines Serientags ist ein Zeiteintrag auf der
// Karte dieses Tags (Herkunft Serie oder Timer); es gibt keine zweite Liste der Bestätigungen.

import type { Karte, Zeiteintrag } from "../modell";
import { LEER } from "./daten";

type Pflicht = Pick<Karte, "id" | "schluessel" | "spalte" | "titel" | "zustaendig" | "prioritaet" | "erstelltAm">;

function karte(k: Pflicht & Partial<Karte>): Karte {
  return { ...LEER, board: "b-prod", art: "arbeit", bewegtAm: k.erstelltAm, ...k };
}

/** Karten der Produktionsplanung mit Start und Fällig (Zeitachse) und weiteren Fälligkeiten (Kalender) */
export const KARTEN_PLANUNG: Karte[] = [
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
  karte({ id: "c-127", schluessel: "PROD-127", spalte: "s-geplant", titel: "Einweisung neue Abkantpresse", zustaendig: ["k-anna"],
          prioritaet: "mittel", labels: ["l-intern"], start: "2026-11-11", faellig: "2026-11-12", erstelltAm: "2026-10-20T11:00:00" }),
  karte({ id: "c-135", schluessel: "PROD-135", spalte: "s-geplant", titel: "Absaugung am Laser reinigen", zustaendig: ["k-jonas"],
          prioritaet: "mittel", labels: ["l-wartung"], start: "2026-11-03", faellig: "2026-11-05", erstelltAm: "2026-10-19T07:45:00",
          felder: { "f-maschine": "Laser" } }),
  karte({ id: "c-126", schluessel: "PROD-126", spalte: "s-pruefung", titel: "Prüfprotokolle Halter K5 ablegen", zustaendig: ["k-anna"],
          prioritaet: "niedrig", labels: ["l-intern"], start: "2026-10-26", faellig: "2026-10-28", erstelltAm: "2026-10-19T08:00:00",
          bewegtAm: "2026-10-26T09:00:00" }),
  karte({ id: "c-116", schluessel: "PROD-116", spalte: "s-fertig", titel: "Serie K5 Abkanten, Los 1 von 3", zustaendig: ["k-tim"],
          prioritaet: "mittel", labels: ["l-kunde"], start: "2026-10-12", faellig: "2026-10-16", abgeschlossen: "2026-10-16",
          erstelltAm: "2026-10-12T07:00:00", bewegtAm: "2026-10-16T15:30:00" }),
  karte({ id: "c-132", schluessel: "PROD-132", spalte: "s-fertig", titel: "Halter K5 Erstmuster fräsen", zustaendig: ["k-jonas"],
          prioritaet: "hoch", labels: ["l-kunde"], start: "2026-10-19", faellig: "2026-10-22", abgeschlossen: "2026-10-21",
          erstelltAm: "2026-10-16T10:00:00", bewegtAm: "2026-10-21T16:00:00" }),
  karte({ id: "c-130", schluessel: "PROD-130", spalte: "s-eingang", titel: "Angebot Lochblechverkleidung Lindner", zustaendig: ["k-max"],
          prioritaet: "mittel", labels: ["l-angebot"], faellig: "2026-11-03", erstelltAm: "2026-10-21T09:30:00",
          felder: { "f-kunde": "Lindner Möbelbau" } }),
  karte({ id: "c-124", schluessel: "PROD-124", spalte: "s-geplant", titel: "Kundenbesuch Hoffmann vorbereiten", zustaendig: ["k-max"],
          prioritaet: "niedrig", labels: ["l-kunde"], start: "2026-10-29", faellig: "2026-10-30", erstelltAm: "2026-10-20T16:00:00",
          felder: { "f-kunde": "Hoffmann Antriebe" } }),
  // Englisch lernen vom 26.10. (Haushalt): liegt noch offen, Max hat seine Zeit nicht bestätigt (Nachtrag)
  karte({ id: "c-h60", board: "b-haus", schluessel: "HAUS-60", spalte: "s-offen", titel: "12:00 Englisch lernen", zustaendig: ["k-max"],
          prioritaet: "keine", faellig: "2026-10-26", schaetzungMin: 30, serie: "se-englisch", erstelltAm: "2026-10-19T00:00:00" }),
  // Produktionsrunde vom 26.10.: hat stattgefunden, Anna und Jonas haben ihre Zeit bestätigt, Max fehlt noch (Nachtrag)
  karte({ id: "c-117", schluessel: "PROD-117", spalte: "s-fertig", titel: "07:30 Produktionsrunde", zustaendig: ["k-max", "k-anna", "k-jonas", "k-tim"],
          prioritaet: "keine", faellig: "2026-10-26", schaetzungMin: 15, abgeschlossen: "2026-10-26", serie: "se-runde",
          erstelltAm: "2026-10-12T06:00:00", bewegtAm: "2026-10-26T07:50:00" }),
];

export const ZEITEINTRAEGE_PLANUNG: Zeiteintrag[] = [
  { id: "p1", karte: "c-116", konto: "k-tim", datum: "2026-10-12", sekunden: 3 * 3600, herkunft: "timer" },
  { id: "p2", karte: "c-116", konto: "k-tim", datum: "2026-10-14", sekunden: 3 * 3600, herkunft: "timer" },
  { id: "p3", karte: "c-116", konto: "k-tim", datum: "2026-10-16", sekunden: 3 * 3600, herkunft: "timer" },
  { id: "p4", karte: "c-132", konto: "k-jonas", datum: "2026-10-19", sekunden: 3 * 3600, herkunft: "timer" },
  { id: "p5", karte: "c-132", konto: "k-jonas", datum: "2026-10-21", sekunden: 3 * 3600, herkunft: "timer" },
  { id: "p6", karte: "c-117", konto: "k-anna", datum: "2026-10-26", von: "07:30", bis: "07:45", sekunden: 900, herkunft: "serie" },
  { id: "p7", karte: "c-117", konto: "k-jonas", datum: "2026-10-26", von: "07:30", bis: "07:45", sekunden: 900, herkunft: "serie" },
];

/** Serientage bis zu diesem Tag gelten als bestätigt: die Entwürfe führen ihre Karten und Einträge nicht einzeln (in der
 *  App kommt der Stand jedes Tags aus der Schnittstelle) */
export const BESTAETIGT_BIS = "2026-10-25";
