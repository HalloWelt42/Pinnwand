// Beispieldaten der Zeit-Ansichten, die in src/beispiel/daten.ts noch fehlen (erfundene Personen und Aufgaben).
// Zusammen mit ZEITKONTEN, ABWESENHEITEN und ZEITEINTRAEGE ergeben sie zwei volle Wochen von Max Paulsen (KW 43 und
// KW 44 bis heute 10:42) und die Tageszeiten des Teams; die Summen passen zum Kopf (heute 3:05 gebucht plus der
// laufende Timer, Woche 11:47). Nach der Freigabe gehört alles in die gemeinsamen Beispieldaten.

import type { Abwesenheit, Karte } from "../../modell";
import type { Halbtagsregel } from "./regeln";
import { dauerLesen } from "./regeln";
import type { Bericht, Eintrag, Tagesrest } from "./typen";

const h = (text: string): number => dauerLesen(text) ?? 0;

const leer = { kommentare: [], checkliste: [], anhaenge: [], transkripte: [], verlauf: [], felder: {}, labels: [] };

/** Karten der Vorwoche, die in Erledigt außerhalb des Zeitfensters (diese Woche) liegen und darum im Board fehlen */
export const ZUSATZKARTEN: Karte[] = [
  { ...leer, id: "c-129", board: "b-prod", schluessel: "PROD-129", spalte: "s-fertig", titel: "Angebot Typenschilder mit Lasergravur", art: "arbeit",
    zustaendig: ["k-max"], prioritaet: "hoch", labels: ["l-kunde", "l-angebot"], schaetzungMin: 1200, erfasstSek: h("20:50"),
    bewegtAm: "2026-10-23T09:00:00", erstelltAm: "2026-10-16T10:00:00", abgeschlossen: "2026-10-23", felder: { "f-kunde": "Hoffmann Antriebe" } },
  { ...leer, id: "c-133", board: "b-prod", schluessel: "PROD-133", spalte: "s-fertig", titel: "Wochenplan KW 44 aufstellen", art: "arbeit",
    zustaendig: ["k-max"], prioritaet: "mittel", labels: ["l-intern"], erfasstSek: h("3:40"),
    bewegtAm: "2026-10-22T09:10:00", erstelltAm: "2026-10-21T08:00:00", abgeschlossen: "2026-10-22" },
  { ...leer, id: "c-134", board: "b-prod", schluessel: "PROD-134", spalte: "s-fertig", titel: "Reklamation Krause: Gratbildung an K5 prüfen", art: "arbeit",
    zustaendig: ["k-max", "k-anna"], prioritaet: "hoch", labels: ["l-kunde", "l-fehler"], erfasstSek: h("9:20"),
    bewegtAm: "2026-10-23T11:00:00", erstelltAm: "2026-10-19T08:30:00", abgeschlossen: "2026-10-23", felder: { "f-kunde": "Krause Gerätebau" } },
  { ...leer, id: "c-138", board: "b-prod", schluessel: "PROD-138", spalte: "s-fertig", titel: "07:30 Produktionsrunde", art: "arbeit",
    zustaendig: ["k-max", "k-anna", "k-jonas", "k-tim"], prioritaet: "keine", faellig: "2026-10-23", schaetzungMin: 15, erfasstSek: h("0:15"),
    bewegtAm: "2026-10-26T07:20:00", erstelltAm: "2026-10-09T06:00:00", abgeschlossen: "2026-10-23", serie: "se-runde" },
];

/** Einträge, die zu den gemeinsamen ZEITEINTRAEGE dazukommen (z1 bis z7 bleiben dort) */
export const ZUSATZEINTRAEGE: Eintrag[] = [
  // Max, KW 43
  { id: "m1", karte: "c-129", konto: "k-max", datum: "2026-10-19", von: "08:05", bis: "11:50", sekunden: h("3:45"), herkunft: "timer" },
  { id: "m2", karte: "c-134", konto: "k-max", datum: "2026-10-19", von: "12:30", bis: "14:40", sekunden: h("2:10"), herkunft: "timer" },
  { id: "m3", karte: "c-137", konto: "k-max", datum: "2026-10-19", von: "14:45", bis: "15:30", sekunden: h("0:45"), herkunft: "timer" },
  { id: "m4", karte: "c-129", konto: "k-max", datum: "2026-10-19", sekunden: h("1:25"), herkunft: "hand", notiz: "Lieferantenpreise abends eingeholt" },
  { id: "m5", karte: "c-129", konto: "k-max", datum: "2026-10-20", von: "07:15", bis: "16:20", sekunden: h("5:25"), herkunft: "timer",
    sitzungen: [{ von: "07:15", bis: "09:30" }, { von: "13:10", bis: "16:20" }] },
  { id: "m6", karte: "c-134", konto: "k-max", datum: "2026-10-20", von: "10:00", bis: "12:20", sekunden: h("2:20"), herkunft: "timer" },
  { id: "m7", karte: "c-129", konto: "k-max", datum: "2026-10-21", von: "07:30", bis: "12:10", sekunden: h("4:40"), herkunft: "timer" },
  { id: "m8", karte: "c-134", konto: "k-max", datum: "2026-10-21", von: "13:00", bis: "14:30", sekunden: h("1:30"), herkunft: "timer" },
  { id: "m9", karte: "c-133", konto: "k-max", datum: "2026-10-21", von: "14:40", bis: "15:40", sekunden: h("1:00"), herkunft: "timer" },
  { id: "m10", karte: "c-133", konto: "k-max", datum: "2026-10-21", sekunden: h("1:10"), herkunft: "hand", notiz: "Schichtplan mit Jonas abgestimmt" },
  { id: "m11", karte: "c-133", konto: "k-max", datum: "2026-10-22", von: "07:40", bis: "09:10", sekunden: h("1:30"), herkunft: "timer" },
  { id: "m12", karte: "c-134", konto: "k-max", datum: "2026-10-22", von: "09:20", bis: "12:40", sekunden: h("3:20"), herkunft: "timer" },
  { id: "m13", karte: "c-129", konto: "k-max", datum: "2026-10-22", von: "19:10", bis: "24:00", sekunden: h("4:50"), herkunft: "timer", zerlegt: "2026-10-23" },
  { id: "m14", karte: "c-129", konto: "k-max", datum: "2026-10-23", von: "00:00", bis: "00:25", sekunden: h("0:25"), herkunft: "timer", zerlegt: "2026-10-22" },
  { id: "m15", karte: "c-138", konto: "k-max", datum: "2026-10-23", von: "07:30", bis: "07:45", sekunden: h("0:15"), herkunft: "serie",
    notiz: "Aus der Serie nachgetragen" },
  { id: "m16", karte: "c-129", konto: "k-max", datum: "2026-10-23", sekunden: h("0:20"), herkunft: "korrektur", notiz: "Rüstzeit der Gravur ergänzt" },
  // Max, KW 44 (dazu z1 bis z4 aus den gemeinsamen Daten)
  { id: "n1", karte: "c-115", konto: "k-max", datum: "2026-10-26", von: "13:00", bis: "14:57", sekunden: h("1:57"), herkunft: "timer" },
  { id: "n2", karte: "c-137", konto: "k-max", datum: "2026-10-26", von: "14:57", bis: "16:58", sekunden: h("2:01"), herkunft: "timer" },
  { id: "n3", karte: "c-122", konto: "k-max", datum: "2026-10-26", sekunden: h("0:30"), herkunft: "hand", notiz: "Abschnitt Biegeradien geschrieben" },
  { id: "n4", karte: "c-136", konto: "k-max", datum: "2026-10-26", sekunden: h("0:40"), herkunft: "hand", notiz: "Prüfmittel beim Kalibrierdienst abgeholt" },
  { id: "n5", karte: "c-115", konto: "k-max", datum: "2026-10-27", von: "06:40", bis: "07:43", sekunden: h("1:03"), herkunft: "timer" },
  { id: "n6", karte: "c-148", konto: "k-max", datum: "2026-10-27", von: "08:13", bis: "09:52", sekunden: h("1:29"), herkunft: "timer",
    sitzungen: [{ von: "08:13", bis: "08:30" }, { von: "08:40", bis: "09:52" }] },
  { id: "n7", karte: "c-137", konto: "k-max", datum: "2026-10-27", sekunden: h("0:23"), herkunft: "korrektur", notiz: "Ticketzeit im Kartendetail gesetzt" },
  // Jonas, KW 44
  { id: "j1", karte: "c-112", konto: "k-jonas", datum: "2026-10-26", von: "06:00", bis: "06:45", sekunden: h("0:45"), herkunft: "timer" },
  { id: "j2", karte: "c-128", konto: "k-jonas", datum: "2026-10-27", von: "07:50", bis: "09:20", sekunden: h("1:30"), herkunft: "timer" },
];

/** Abwesenheiten, die zu den gemeinsamen ABWESENHEITEN dazukommen; Max kommt damit auf 21 genommene Urlaubstage */
export const ZUSATZABWESENHEITEN: Abwesenheit[] = [
  { konto: "k-max", von: "2026-01-02", bis: "2026-01-09", art: "urlaub", notiz: "Winterurlaub" },
  { konto: "k-max", von: "2026-02-16", bis: "2026-02-18", art: "krank" },
  { konto: "k-max", von: "2026-03-04", bis: "2026-03-04", art: "fortbildung", notiz: "Seminar Arbeitssicherheit" },
  { konto: "k-max", von: "2026-03-13", bis: "2026-03-13", art: "halbtag" },
  { konto: "k-max", von: "2026-04-02", bis: "2026-04-10", art: "urlaub", notiz: "Ostern" },
  { konto: "k-max", von: "2026-05-15", bis: "2026-05-15", art: "urlaub", notiz: "Brückentag" },
  { konto: "k-max", von: "2026-06-05", bis: "2026-06-05", art: "urlaub", notiz: "Brückentag" },
  { konto: "k-max", von: "2026-07-27", bis: "2026-08-04", art: "urlaub", notiz: "Sommer" },
  { konto: "k-max", von: "2026-10-12", bis: "2026-10-12", art: "frei", notiz: "Überstunden abgebaut" },
  { konto: "k-max", von: "2026-10-23", bis: "2026-10-23", art: "halbtag", notiz: "Termin am Nachmittag" },
  { konto: "k-anna", von: "2026-10-14", bis: "2026-10-15", art: "urlaub" },
  { konto: "k-anna", von: "2026-11-16", bis: "2026-11-19", art: "urlaub" },
  { konto: "k-jonas", von: "2026-10-20", bis: "2026-10-20", art: "krank" },
  { konto: "k-tim", von: "2026-10-21", bis: "2026-10-21", art: "urlaub" },
  { konto: "k-tim", von: "2026-11-11", bis: "2026-11-11", art: "fortbildung", notiz: "Schulung Kantbank" },
];

/** Halbe Arbeitstage je Zeitkonto (Vorgabe Heiligabend und Silvester, wie in der alten App) */
const VORGABE_HALBTAGE: Halbtagsregel[] = [{ monat: 12, tag: 24, name: "Heiligabend" }, { monat: 12, tag: 31, name: "Silvester" }];
export const HALBTAGSREGELN: Record<string, Halbtagsregel[]> = {
  "k-max": VORGABE_HALBTAGE, "k-anna": VORGABE_HALBTAGE, "k-jonas": VORGABE_HALBTAGE, "k-tim": VORGABE_HALBTAGE,
};

/** Ist je Monat vor Oktober (Summe der Schnittstelle; einzelne Einträge führen die Entwürfe erst ab KW 43) */
export const MONATSIST: Record<string, Record<string, number>> = {
  "k-max": {
    "2026-01": h("122:10"), "2026-02": h("137:35"), "2026-03": h("167:20"), "2026-04": h("120:45"), "2026-05": h("140:05"),
    "2026-06": h("162:50"), "2026-07": h("145:15"), "2026-08": h("155:40"), "2026-09": h("180:39"),
  },
};

function tage(werte: [string, string][]): Record<string, number> {
  return Object.fromEntries(werte.map(([t, d]) => [t, h(d)]));
}

/** Tageszeiten aus nicht einzeln geführten Einträgen (Oktober), damit Zeitkonto und Auslastung volle Tage zeigen */
export const TAGESREST: Tagesrest = {
  "k-max": tage([["2026-10-01", "8:10"], ["2026-10-02", "7:45"], ["2026-10-05", "8:20"], ["2026-10-06", "8:05"], ["2026-10-07", "7:50"],
    ["2026-10-08", "8:40"], ["2026-10-09", "6:30"], ["2026-10-13", "8:15"], ["2026-10-14", "8:35"], ["2026-10-15", "8:00"], ["2026-10-16", "7:20"]]),
  "k-anna": tage([["2026-10-12", "7:50"], ["2026-10-13", "8:25"], ["2026-10-19", "8:05"], ["2026-10-20", "7:40"], ["2026-10-21", "8:30"],
    ["2026-10-22", "8:10"], ["2026-10-26", "7:45"], ["2026-10-27", "2:20"]]),
  "k-jonas": tage([["2026-10-12", "8:20"], ["2026-10-13", "8:05"], ["2026-10-14", "9:10"], ["2026-10-15", "8:00"], ["2026-10-16", "6:45"],
    ["2026-10-19", "8:30"], ["2026-10-21", "8:15"], ["2026-10-22", "8:40"], ["2026-10-23", "7:30"], ["2026-10-26", "7:15"], ["2026-10-27", "1:15"]]),
  "k-tim": tage([["2026-10-12", "6:50"], ["2026-10-14", "6:30"], ["2026-10-16", "7:05"], ["2026-10-19", "6:40"], ["2026-10-23", "6:15"]]),
};

/** Ordner der Pinnwand in der Kellerwolke, in dem erstellte Berichte liegen */
export const BERICHTSORDNER = "Pinnwand/Berichte";

export const BERICHTE: Bericht[] = [
  { id: "r5", art: "erledigt", titel: "Erledigte Karten: Produktionsplanung", zeitraum: "01.10. bis 25.10.2026", format: "markdown",
    datei: "Erledigt_PROD_2026-10-25.md", erstellt: "2026-10-26T07:42:00", groesse: "6 KB" },
  { id: "r4", art: "board", titel: "Zeiten je Karte: Produktionsplanung", zeitraum: "KW 43, 19.10. bis 25.10.2026", format: "tabelle",
    datei: "Zeiten_PROD_2026-KW43.csv", erstellt: "2026-10-26T07:40:00", groesse: "12 KB" },
  { id: "r3", art: "stundennachweis", titel: "Stundennachweis Anna Berger, Jonas Keller, Tim Sander", zeitraum: "September 2026", format: "pdf",
    datei: "Stundennachweis_Team_2026-09.pdf", erstellt: "2026-10-01T08:10:00", groesse: "214 KB" },
  { id: "r2", art: "stundennachweis", titel: "Stundennachweis Max Paulsen", zeitraum: "September 2026", format: "pdf",
    datei: "Stundennachweis_Max_Paulsen_2026-09.pdf", erstellt: "2026-10-01T08:05:00", groesse: "86 KB" },
  { id: "r1", art: "stundennachweis", titel: "Stundennachweis Max Paulsen", zeitraum: "August 2026", format: "pdf",
    datei: "Stundennachweis_Max_Paulsen_2026-08.pdf", erstellt: "2026-09-01T07:55:00", groesse: "81 KB" },
];
