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
    text: "Produktionsplanung mit fünf Spalten, Grenze im Kopf (rot darüber), Erledigt neueste zuerst; Karten mit Priorität, Gruppe, Auszug, Timer. Ziehen, Spalten ordnen, Kette und Papierkorb gehen echt." },
  { pfad: "/board/prod/131", stufe: 1, symbol: "fa-id-card", titel: "Kartendetail",
    text: "Leiste rechts über dem Board: alle Felder direkt bearbeitbar, Escape verwirft im Feld und schließt danach, ein Klick daneben schließt; Duplizieren und Verweis kopieren im Kopf." },
  { pfad: "/board/prod/131", entwurf: "bearbeiten", stufe: 1, symbol: "fa-pen", titel: "Beschreibung bearbeiten",
    text: "Ein Klick auf die Beschreibung bearbeitet den Markdown-Text an Ort und Stelle; Fertig speichert, Escape verwirft." },
  { pfad: "/board/prod/131", entwurf: "notizen", stufe: 1, symbol: "fa-note-sticky", titel: "Notizen im Vollbild",
    text: "Notizen bearbeiten im Vollbild: Markdown links, die Vorschau rechts; Fertig speichert, Escape verwirft." },
  { pfad: "/board/prod/131", entwurf: "verknuepfen", stufe: 1, symbol: "fa-link", titel: "Karte verknüpfen",
    text: "Suche in den offenen Arbeitskarten des Boards nach Titel oder Schlüssel, höchstens 8 Treffer; Pfeile wählen, Enter verknüpft." },
  { pfad: "/board/prod/131", entwurf: "kellerwolke", stufe: 1, symbol: "fa-cloud", titel: "Anhang aus der Kellerwolke",
    text: "Dateien aus der eigenen Kellerwolke suchen und verknüpfen; Hochladen und Ziehen legen sie im Ordner des Boards ab." },
  { pfad: "/board/prod/131", entwurf: "verlauf", stufe: 1, symbol: "fa-clock-rotate-left", titel: "Verlauf der Karte",
    text: "Alles, was an der Karte geschah, neueste zuerst: Verschieben, Zuständig, Fällig, Kommentare, Zeit, Anhänge." },
  { pfad: "/board/prod/137", stufe: 1, symbol: "fa-link", titel: "Verknüpfte Aufgaben",
    text: "Zwei verknüpfte Karten mit geteilter Zeit; im Detail die Gruppe, der Schalter Zeit teilen und Lösen." },
  { pfad: "/board/prod", entwurf: "ziehen", stufe: 1, symbol: "fa-up-down-left-right", titel: "Ziehen in Aktion",
    text: "PROD-137 wird nach In Arbeit gezogen; die verknüpfte PROD-136 zieht mit, die Zielspalte zeigt den Platz." },
  { pfad: "/board/prod", entwurf: "schnell", stufe: 1, symbol: "fa-bolt", titel: "Schnelleingabe",
    text: "Karte am Fuß der Spalte anlegen: Enter legt an, das Feld bleibt offen, Person vorbelegt, Arbeit oder Idee." },
  { pfad: "/board/prod", entwurf: "suche", stufe: 1, symbol: "fa-magnifying-glass", titel: "Suche",
    text: "Suche aktiv: Verschieben pausiert, Erledigte werden ohne Zeitfenster durchsucht; Zahl und Grenze im Kopf zählen alle Karten." },
  { pfad: "/board/prod", entwurf: "filter", stufe: 1, symbol: "fa-filter", titel: "Filtertafel",
    text: "Priorität und Label in der Tafel unter der Werkzeugleiste: die Spalten zeigen die Treffer, Verschieben pausiert; gilt auch in Liste, Kalender und Zeitachse." },
  { pfad: "/board/prod", entwurf: "personen", stufe: 1, symbol: "fa-user", titel: "Personen und Sortierung",
    text: "Nur Karten von Anna Berger, offene Spalten nach Fälligkeit; ein Klick auf Verschieben pausiert setzt alles zurück." },
  { pfad: "/board/prod", entwurf: "spaltenmenue", stufe: 1, symbol: "fa-ellipsis", titel: "Spaltenmenü",
    text: "Geplant steht genau an seiner Grenze (Bernstein), In Arbeit darüber (rot); im Menü Name, Farbe, Grenze, einklappen, verschieben, löschen." },
  { pfad: "/board/prod", entwurf: "spalte-loeschen", stufe: 1, symbol: "fa-trash-can", titel: "Spalte löschen",
    text: "Rückfrage im Menü von Geplant: die Karten verschieben oder mit der Spalte in den Papierkorb." },
  { pfad: "/board/prod", entwurf: "neue-spalte", stufe: 1, symbol: "fa-plus", titel: "Neue Spalte",
    text: "Am Ende des Streifens: Name und Farbe, Enter legt an, Escape bricht ab; die Spalte kommt ans Ende." },
  { pfad: "/board/prod", entwurf: "eingeklappt", stufe: 1, symbol: "fa-angles-left", titel: "Eingeklappte Spalten",
    text: "Eingang und Prüfung eingeklappt: ein Strich je Karte, Karten lassen sich hineinziehen; gemerkt je Board an diesem Gerät." },
  { pfad: "/board/prod", entwurf: "kette", stufe: 1, symbol: "fa-link", titel: "Kette ziehen",
    text: "Die Kette von PROD-148 liegt über PROD-139: Loslassen verknüpft beide, daneben bricht ab." },
  { pfad: "/board/prod", entwurf: "mehr", stufe: 1, symbol: "fa-angles-down", titel: "Erledigt seitenweise",
    text: "Ladeschritt 3, Zeitfenster Alle: Erledigt zeigt 3 von 10, Mehr laden oder Rollen ans Ende holt die nächsten." },
  { pfad: "/board/prod", entwurf: "getrennt", stufe: 1, symbol: "fa-plug-circle-xmark", titel: "Ablage abgewiesen",
    text: "Verbindung getrennt: PROD-139 nach In Arbeit gezogen, die Ablage wird abgewiesen und die Karte steht wieder in Geplant; die Meldung nennt den Grund." },
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
