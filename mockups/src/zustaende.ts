// Galerie der Entwürfe: je Zustand ein echter Pfad der App, dazu ?entwurf=<name> für vorgeführte Zustände derselben
// Ansicht und ?geraet=telefon für die Telefonansicht. Jeder Bereich trägt seine Einträge in
// ansichten/<bereich>/zustaende.ts ein.

import { ZUSTAENDE as PLANUNG } from "./ansichten/planung/zustaende";
import { ZUSTAENDE as TELEFON } from "./ansichten/telefon/zustaende";
import { ZUSTAENDE as UEBERSICHT } from "./ansichten/uebersicht/zustaende";
import { ZUSTAENDE as VERWALTUNG } from "./ansichten/verwaltung/zustaende";
import { ZUSTAENDE as ZEIT } from "./ansichten/zeit/zustaende";

export interface Zustand {
  pfad: string;
  entwurf?: string;
  geraet?: "rechner" | "telefon";
  stufe: 1 | 2 | 3 | 4;
  titel: string;
  text: string;
  symbol: string;
}

export const STUFEN = {
  1: "Stufe 1: Board",
  2: "Stufe 2: Zeit",
  3: "Stufe 3: Planung",
  4: "Stufe 4: Verbund",
} as const;

/** Adresse eines Zustands (Pfad mit Zusätzen) */
export function adresse(z: Zustand): string {
  const zusatz = new URLSearchParams();
  if (z.entwurf) zusatz.set("entwurf", z.entwurf);
  if (z.geraet === "telefon") zusatz.set("geraet", "telefon");
  const s = zusatz.toString();
  return z.pfad + (s ? `?${s}` : "");
}

const BOARD: Zustand[] = [
  { pfad: "/board/prod", stufe: 1, symbol: "fa-table-columns", titel: "Board",
    text: "Produktionsplanung mit fünf Spalten, Grenzen, Erledigt mit Zeitfenster; Karten mit Labels, Feldern, Timer, Alter, Gruppe. Ziehen geht echt." },
  { pfad: "/board/prod/131", stufe: 1, symbol: "fa-id-card", titel: "Kartendetail",
    text: "Leiste rechts über dem Board: alle Felder direkt bearbeitbar, eigene Felder, Zeiterfassung, Checkliste, Anhänge, Transkripte, Kommentare." },
  { pfad: "/board/prod/131", entwurf: "bearbeiten", stufe: 1, symbol: "fa-pen", titel: "Beschreibung bearbeiten",
    text: "Ein Klick auf die Beschreibung bearbeitet an Ort und Stelle; Fertig speichert, Escape verwirft." },
  { pfad: "/board/prod/137", stufe: 1, symbol: "fa-link", titel: "Verknüpfte Aufgaben",
    text: "Zwei verknüpfte Karten mit geteilter Zeit; im Detail die Gruppe, der Schalter Zeit teilen und Lösen." },
  { pfad: "/board/prod", entwurf: "ziehen", stufe: 1, symbol: "fa-up-down-left-right", titel: "Ziehen in Aktion",
    text: "PROD-137 wird nach In Arbeit gezogen; die verknüpfte PROD-136 zieht mit, die Zielspalte zeigt den Platz." },
  { pfad: "/board/prod", entwurf: "schnell", stufe: 1, symbol: "fa-bolt", titel: "Schnelleingabe",
    text: "Karte am Fuß der Spalte anlegen: Enter legt an, das Feld bleibt offen, Person vorbelegt, Arbeit oder Idee." },
  { pfad: "/board/prod", entwurf: "suche", stufe: 1, symbol: "fa-filter", titel: "Suche und Filter",
    text: "Suche aktiv: Verschieben pausiert, Erledigte werden ohne Zeitfenster durchsucht." },
  { pfad: "/board/prod", entwurf: "live", stufe: 1, symbol: "fa-tower-broadcast", titel: "Änderung durch andere",
    text: "Anna ändert gerade PROD-115: die Karte zeigt es sofort, mit Meldung unten rechts." },
  { pfad: "/board/prod/115", entwurf: "konflikt", stufe: 1, symbol: "fa-code-merge", titel: "Gleichzeitig geändert",
    text: "Speichern auf veralteter Fassung: nichts wird still überschrieben, beide Fassungen stehen zur Wahl." },
  { pfad: "/board/prod", entwurf: "erledigt", stufe: 1, symbol: "fa-circle-check", titel: "Erledigt mit Timer",
    text: "PROD-131 nach Erledigt gezogen: der Timer hält an und bucht, Rückgängig unten rechts." },
  { pfad: "/board/idee", stufe: 1, symbol: "fa-lightbulb", titel: "Board ohne Zeiterfassung",
    text: "Ideen: Modul Zeiterfassung aus, Karten sind Ideen; zwei Mitglieder." },
  { pfad: "/board/haus", stufe: 1, symbol: "fa-house", titel: "Privates Board",
    text: "Haushalt im Ordner Privat: nur du bist Mitglied, Serienkarte Englisch lernen." },
];

export const ZUSTAENDE: Zustand[] = [...BOARD, ...UEBERSICHT, ...VERWALTUNG, ...ZEIT, ...PLANUNG, ...TELEFON];
