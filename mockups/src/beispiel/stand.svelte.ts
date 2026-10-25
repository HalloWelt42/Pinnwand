// Der eine veränderliche Zustand der Entwürfe: alle Beispieldaten in einem Ort, Änderungen wirken in jeder Ansicht bis
// zum Neuladen der Seite. Ändern nur über die Anwendungsfälle in beispiel/anwendung/, lesen über die Hilfen hier und in
// beispiel/abfragen.ts. In der App tritt an diese Stelle der Zustand aus der Schnittstelle und dem Ereignisstrom; die
// Ansichten merken davon nichts.

import type {
  Abwesenheit, Board, Entfernt, Geloescht, Gruppe, Hinweis, Karte, Konto, Ordner, PersonEinstellungen, Serie, Termin, Timer,
  Verbindung, Zeiteintrag, Zeitkonto,
} from "../modell";
import {
  ABWESENHEITEN, BOARDS, EINSTELLUNGEN_PERSON, GRUPPEN, HINWEISE, KARTEN, KONTEN, ORDNER, SERIEN, TERMINE, TIMER, ZEITEINTRAEGE,
  ZEITKONTEN,
} from "./daten";
import { KARTEN_PLANUNG, ZEITEINTRAEGE_PLANUNG } from "./daten-planung";
import { KARTEN_ARCHIV, PAPIERKORB, ZEITEINTRAEGE_UEBERSICHT } from "./daten-uebersicht";
import { ABWESENHEITEN_ZEIT, KARTEN_ZEIT, ZEITEINTRAEGE_ZEIT } from "./daten-zeit";

/** Meldung unten: was eben geschah, mit Rückgängig, solange sie steht */
export interface Meldung {
  text: string;
  rueckgaengig?: () => void;
}

/** Alle Teile des Zustands (Daten, Verbindung, Meldung) */
export interface Ausgangsstand {
  konten: Konto[];
  boards: Board[];
  karten: Karte[];
  gruppen: Gruppe[];
  reihen: Record<string, string[]>;
  ordner: Ordner[];
  timer: Timer[];
  zeiteintraege: Zeiteintrag[];
  zeitkonten: Zeitkonto[];
  abwesenheiten: Abwesenheit[];
  serien: Serie[];
  termine: Termin[];
  hinweise: Hinweis[];
  einstellungen: PersonEinstellungen;
  papierkorb: Geloescht[];
  entfernt: Entfernt[];
  verbindung: Verbindung;
  meldung: Meldung | null;
}

const ALLE_KARTEN: Karte[] = [...KARTEN, ...KARTEN_ZEIT, ...KARTEN_PLANUNG, ...KARTEN_ARCHIV];

function anfangsreihen(): Record<string, string[]> {
  const r: Record<string, string[]> = {};
  for (const k of ALLE_KARTEN) (r[k.spalte] ??= []).push(k.id);
  return r;
}

/** Der Ausgangsstand aus den Beispieldaten, frisch kopiert */
function ausgangsstand(): Ausgangsstand {
  return {
    /** Personen mit Konto in der Pinnwand (aus der Kellerwolke; neue kommen mit der ersten Einladung dazu) */
    konten: structuredClone(KONTEN) as Konto[],
    boards: structuredClone(BOARDS) as Board[],
    karten: structuredClone(ALLE_KARTEN) as Karte[],
    gruppen: structuredClone(GRUPPEN) as Gruppe[],
    /** Reihenfolge der Karten je Spalte (alle Karten der Spalte; Erledigt-Spalten zeigen davon ihr Zeitfenster) */
    reihen: anfangsreihen(),
    ordner: structuredClone(ORDNER) as Ordner[],
    timer: structuredClone(TIMER) as Timer[],
    zeiteintraege: structuredClone([...ZEITEINTRAEGE, ...ZEITEINTRAEGE_ZEIT, ...ZEITEINTRAEGE_PLANUNG, ...ZEITEINTRAEGE_UEBERSICHT]) as Zeiteintrag[],
    zeitkonten: structuredClone(ZEITKONTEN) as Zeitkonto[],
    abwesenheiten: structuredClone([...ABWESENHEITEN, ...ABWESENHEITEN_ZEIT]) as Abwesenheit[],
    serien: structuredClone(SERIEN) as Serie[],
    termine: structuredClone(TERMINE) as Termin[],
    hinweise: structuredClone(HINWEISE) as Hinweis[],
    einstellungen: structuredClone(EINSTELLUNGEN_PERSON) as PersonEinstellungen,
    papierkorb: structuredClone(PAPIERKORB) as Geloescht[],
    /** endgültig entfernte Karten: ihr Name für die Zeiteinträge, die weiter gebucht sind */
    entfernt: [] as Entfernt[],
    /** Verbindung zum Ereignisstrom; getrennt: letzter Stand sichtbar, Schreibendes gesperrt */
    verbindung: "verbunden" as Verbindung,
    meldung: null as Meldung | null,
  };
}

export const stand = $state(ausgangsstand());

/** Zurück zum Ausgangsstand: jeder vorgeführte Zustand (?entwurf=...) beginnt hier und richtet sich danach über die
 *  Anwendungsfälle ein, damit nichts aus einem anderen Entwurf hineinwirkt und die ganze Seite zusammenpasst. Zeigt ein
 *  Entwurf einen Stand, den kein Anwendungsfall herstellt (etwa einen Timer, den der Server nach 12 Stunden gedeckelt
 *  hat), gibt er eine Abwandlung der Beispieldaten mit (daten-<bereich>.ts), nie eine eigene Kopie. */
export function zuruecksetzen(abwandlung?: (d: Ausgangsstand) => void): void {
  const d = ausgangsstand();
  abwandlung?.(d);
  Object.assign(stand, d);
}

/** Die Teile des Zustands, die Rückgängig wiederherstellt (alles außer Meldung und Verbindung) */
export const DATEN = ["konten", "boards", "karten", "gruppen", "reihen", "ordner", "timer", "zeiteintraege", "zeitkonten", "abwesenheiten",
  "serien", "termine", "hinweise", "einstellungen", "papierkorb", "entfernt"] as const;

export function board(id: string): Board {
  return stand.boards.find((b) => b.id === id) ?? stand.boards[0];
}

/** Board aus dem Kürzel im Pfad (klein oder groß geschrieben) */
export function boardAusKuerzel(kuerzel: string): Board | undefined {
  return stand.boards.find((b) => b.kuerzel.toLowerCase() === kuerzel.toLowerCase());
}

export function karte(id: string): Karte | undefined {
  return stand.karten.find((k) => k.id === id);
}

/** Karte aus ihrem Schlüssel im Pfad (/board/prod/131) */
export function karteAusNummer(b: Board, nr: string): Karte | undefined {
  return stand.karten.find((k) => k.board === b.id && k.schluessel === `${b.kuerzel}-${nr}`);
}

/** Alle Karten einer Spalte in ihrer Reihenfolge (ohne Zeitfenster) */
export function kartenDerSpalte(spalte: string): Karte[] {
  return (stand.reihen[spalte] ?? []).map((id) => karte(id)).filter((k): k is Karte => k !== undefined);
}

/** Konto einer Person; eine unbekannte Kennung ergibt einen Platzhalter statt einer fremden Person */
export function konto(id: string): Konto {
  return stand.konten.find((k) => k.id === id) ?? { id, name: "Unbekannte Person", kuerzel: "?", farbe: "stahl", kellerwolke: "" };
}

/** Verknüpfte Karten (ohne sie selbst) */
export function gruppenmitglieder(k: Karte): Karte[] {
  return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id) : [];
}

/** Der persönliche Ordner, in dem ein Board liegt */
export function ordnerVon(boardId: string): Ordner | undefined {
  return stand.ordner.find((o) => o.boards.includes(boardId));
}
