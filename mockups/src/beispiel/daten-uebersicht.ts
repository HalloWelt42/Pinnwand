// Beispieldaten für Archiv und Papierkorb, zusätzlich zu daten.ts. Archivierte Karten sind gewöhnliche erledigte Karten
// mit einem Abschluss vor der Archivgrenze des Boards; das Board zeigt sie nie, ein direkter Pfad öffnet sie einzeln.
// Was im Papierkorb liegt, steht nur dort; die gebuchte Zeit der gelöschten Karten bleibt in den Zeiteinträgen.

import type { Geloescht, Karte, Kennung, Prioritaet, Zeiteintrag } from "../modell";
import { LEER } from "./daten";

const ARCHIVZEITEN: Zeiteintrag[] = [];

/** Eine erledigte Karte, deren Abschluss älter als die Archivgrenze ist; ihre Zeit als ein Eintrag am Abschlusstag */
function archiviert(nr: number, titel: string, abgeschlossen: string, zustaendig: Kennung[], labels: Kennung[], sekunden: number,
                    prioritaet: Prioritaet = "keine", felder: Record<Kennung, string> = {}, serie?: Kennung): Karte {
  const id = `c-${nr}`;
  ARCHIVZEITEN.push({ id: `za-${nr}`, karte: id, konto: zustaendig[0], datum: abgeschlossen, sekunden, herkunft: "timer" });
  return { ...LEER, id, board: "b-prod", schluessel: `PROD-${nr}`, spalte: "s-fertig", titel, art: "arbeit", zustaendig,
           prioritaet, labels, bewegtAm: `${abgeschlossen}T15:30:00`, erstelltAm: `${abgeschlossen}T08:00:00`, abgeschlossen,
           felder, serie };
}

/** Erste Seite des Archivs von Produktionsplanung, neueste zuerst (wie die Schnittstelle sie liefert) */
export const KARTEN_ARCHIV: Karte[] = [
  archiviert(58, "Lieferschein Gehäuse G2, Los 4", "2025-10-20", ["k-max"], ["l-kunde"], 1200, "mittel", { "f-kunde": "Elektro Brandt", "f-stueck": "60" }),
  archiviert(57, "Wochenwartung Kompressor", "2025-10-20", ["k-jonas"], ["l-wartung"], 2700, "keine", {}, "se-kompressor"),
  archiviert(55, "Biegewerkzeug 88 Grad nachschleifen lassen", "2025-10-14", ["k-jonas"], ["l-wartung"], 1800, "niedrig", { "f-maschine": "Kantbank" }),
  archiviert(54, "Angebot Konsolen Hoffmann", "2025-10-09", ["k-max"], ["l-angebot"], 3 * 3600, "hoch", { "f-kunde": "Hoffmann Antriebe" }),
  archiviert(52, "Erstmuster Deckel D4 vermessen", "2025-09-30", ["k-anna"], ["l-kunde"], 2 * 3600 + 1200, "hoch",
             { "f-kunde": "Krause Gerätebau", "f-stueck": "5" }),
  archiviert(51, "Zuschnittliste Blechlager aktualisieren", "2025-09-24", ["k-anna"], ["l-intern"], 2400),
  archiviert(49, "Laser: Schutzglas tauschen", "2025-09-15", ["k-jonas"], ["l-wartung", "l-fehler"], 900, "hoch", { "f-maschine": "Laser" }),
  archiviert(47, "Serie K3 Abkanten, Los 3 von 3", "2025-09-05", ["k-jonas"], ["l-kunde"], 6 * 3600, "mittel",
             { "f-kunde": "Krause Gerätebau", "f-stueck": "180", "f-maschine": "Kantbank" }),
  archiviert(45, "Prüfplan Schweißnähte erstellen", "2025-08-22", ["k-anna"], ["l-intern"], 4 * 3600, "mittel"),
  archiviert(44, "Angebot Schaltkästen Lindner", "2025-08-14", ["k-max"], ["l-angebot", "l-kunde"], 2 * 3600 + 1800, "hoch",
             { "f-kunde": "Lindner Möbelbau" }),
  archiviert(41, "Absaugung am Schweißplatz reinigen", "2025-07-31", ["k-jonas"], ["l-wartung"], 3600),
  archiviert(38, "Musterteile Halter H1 fräsen", "2025-07-18", ["k-jonas", "k-max"], ["l-kunde"], 5 * 3600, "hoch",
             { "f-kunde": "Hoffmann Antriebe", "f-stueck": "10", "f-maschine": "CNC 1" }),
  archiviert(36, "Arbeitsanweisung Laser neu fassen", "2025-06-27", ["k-anna"], ["l-intern"], 3 * 3600, "niedrig"),
  archiviert(33, "Reklamation Gehäuse G1: Kratzer an der Tür", "2025-06-12", ["k-max"], ["l-kunde", "l-fehler"], 1800, "dringend",
             { "f-kunde": "Elektro Brandt" }),
  archiviert(29, "Inventur Rohmaterial zum Halbjahr", "2025-05-28", ["k-anna"], ["l-intern"], 5 * 3600 + 1800, "mittel"),
  archiviert(26, "CNC 1: Spindellager prüfen lassen", "2025-05-12", ["k-jonas"], ["l-wartung"], 2 * 3600, "hoch", { "f-maschine": "CNC 1" }),
];

/** Gesamtzahl archivierter Karten je Board (die Schnittstelle liefert sie mit der ersten Seite) */
export const ARCHIV_GESAMT: Record<Kennung, number> = { "b-prod": 41 };

/** Papierkorb der Boards, neueste zuerst */
export const PAPIERKORB: Geloescht[] = [
  {
    id: "p-123", board: "b-prod", art: "karte", stelle: { spalte: "s-geplant", platz: 1 }, von: "k-anna", am: "2026-10-26T16:05:00",
    karten: [{
      ...LEER, id: "c-123", board: "b-prod", schluessel: "PROD-123", spalte: "s-geplant", titel: "Prüfprotokoll für Biegeteile entwerfen",
      art: "arbeit", zustaendig: ["k-anna"], prioritaet: "mittel", labels: ["l-intern"], faellig: "2026-11-06", schaetzungMin: 240,
      bewegtAm: "2026-10-21T16:20:00", erstelltAm: "2026-10-14T10:10:00", gruppe: "g-pruef",
      checkliste: [{ text: "Merkmale festlegen", erledigt: true }, { text: "Toleranzen aus der Zeichnung", erledigt: true },
        { text: "Vordruck anlegen", erledigt: false }, { text: "Mit Prüfvorrichtung abgleichen", erledigt: false }, { text: "Freigabe", erledigt: false }],
      kommentare: [
        { von: "k-anna", zeit: "2026-10-22T09:15:00", text: "Erster Entwurf liegt im Anhang." },
        { von: "k-max", zeit: "2026-10-22T11:40:00", text: "Bitte noch die Biegewinkel mit aufnehmen." },
      ],
      anhaenge: [{ name: "Prüfprotokoll Entwurf.pdf", groesse: "148 KB", art: "pdf" }],
    }],
  },
  {
    id: "p-nacharbeit", board: "b-prod", art: "spalte", stelle: { platz: 3 }, von: "k-max", am: "2026-10-23T11:10:00",
    spalte: { id: "s-nacharbeit", name: "Nacharbeit", farbe: "koralle", erledigt: false, grenze: 2 },
    karten: [
      { ...LEER, id: "c-120", board: "b-prod", schluessel: "PROD-120", spalte: "s-nacharbeit", titel: "Gratbildung Serie K5, Los 1 nacharbeiten",
        art: "arbeit", zustaendig: ["k-tim"], prioritaet: "hoch", labels: ["l-kunde", "l-fehler"],
        bewegtAm: "2026-10-20T13:00:00", erstelltAm: "2026-10-20T13:00:00", felder: { "f-kunde": "Krause Gerätebau", "f-stueck": "40" } },
      { ...LEER, id: "c-121", board: "b-prod", schluessel: "PROD-121", spalte: "s-nacharbeit", titel: "Lackschäden Gehäuse G2 ausbessern",
        art: "arbeit", zustaendig: ["k-anna"], prioritaet: "mittel", labels: ["l-fehler"],
        bewegtAm: "2026-10-21T10:00:00", erstelltAm: "2026-10-21T10:00:00", felder: { "f-kunde": "Elektro Brandt" },
        kommentare: [{ von: "k-anna", zeit: "2026-10-21T10:05:00", text: "Zwei Türen betroffen, Foto anbei." }],
        anhaenge: [{ name: "Lackschaden Tür.jpg", groesse: "2,1 MB", art: "bild" }] },
    ],
  },
  {
    id: "p-119", board: "b-prod", art: "karte", stelle: { spalte: "s-geplant", platz: 0 }, von: "k-jonas", am: "2026-10-21T07:05:00",
    karten: [{
      ...LEER, id: "c-119", board: "b-prod", schluessel: "PROD-119", spalte: "s-geplant", titel: "07:30 Produktionsrunde", art: "arbeit",
      zustaendig: ["k-max", "k-anna", "k-jonas", "k-tim"], prioritaet: "keine", faellig: "2026-10-21", schaetzungMin: 15,
      bewegtAm: "2026-10-07T06:00:00", erstelltAm: "2026-10-07T06:00:00", serie: "se-runde",
      kommentare: [{ von: "k-jonas", zeit: "2026-10-21T07:04:00", text: "Fällt aus, Betriebsversammlung um 8 Uhr." }],
    }],
  },
];

/** Gebuchte Zeit der archivierten und der gelöschten Karten (sie bleibt gebucht, auch im Papierkorb) */
export const ZEITEINTRAEGE_UEBERSICHT: Zeiteintrag[] = [
  ...ARCHIVZEITEN,
  { id: "zp1", karte: "c-123", konto: "k-anna", datum: "2026-10-22", von: "08:30", bis: "09:45", sekunden: 4500, herkunft: "timer" },
  { id: "zp2", karte: "c-123", konto: "k-max", datum: "2026-10-22", sekunden: 1800, herkunft: "hand" },
  { id: "zp3", karte: "c-120", konto: "k-tim", datum: "2026-10-23", von: "07:00", bis: "08:30", sekunden: 5400, herkunft: "timer" },
  { id: "zp4", karte: "c-121", konto: "k-anna", datum: "2026-10-21", sekunden: 1200, herkunft: "hand" },
];
