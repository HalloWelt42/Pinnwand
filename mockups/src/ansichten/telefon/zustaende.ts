// Einträge der Telefonansicht in der Galerie der Entwürfe (siehe src/zustaende.ts).
import type { Zustand } from "../../zustaende";

export const ZUSTAENDE: Zustand[] = [
  { pfad: "/heute", geraet: "telefon", stufe: 1, symbol: "fa-sun", titel: "Heute am Telefon",
    text: "Deine Karten aus allen Boards: heute fällig, Termine, diese Woche; Serienkarten mit Uhrzeit. Den Ring halten erledigt, ein Tippen öffnet die Karte, rechts der Timer." },
  { pfad: "/heute", entwurf: "halten", geraet: "telefon", stufe: 1, symbol: "fa-hand-pointer", titel: "Erledigen per Halten",
    text: "Der Ring an HAUS-61 füllt sich gerade zur Hälfte: erst voll gilt es, Loslassen vorher bricht ab, kurzes Tippen erklärt nur. Danach Rückgängig in der Meldung." },
  { pfad: "/boards", geraet: "telefon", stufe: 1, symbol: "fa-layer-group", titel: "Boards am Telefon",
    text: "Deine Boards nach Ordnern, je Board offene und eigene Karten; ein Tippen öffnet das Board spaltenweise." },
  { pfad: "/board/prod", geraet: "telefon", stufe: 1, symbol: "fa-table-columns", titel: "Board spaltenweise",
    text: "Spalten als Reiter mit Zahl und Grenze, Wischen wechselt die Spalte; darunter die Karten der Spalte groß. In Arbeit liegt über der Grenze." },
  { pfad: "/board/prod/131", geraet: "telefon", stufe: 1, symbol: "fa-id-card", titel: "Karte am Telefon",
    text: "Status mit großem Knopf Verschieben nach, Fällig, Zuständige, Timer mit Anhalten und Stopp, Checkliste zum Abhaken, Beschreibung, Kommentare lesen und schreiben." },
  { pfad: "/board/prod/131", entwurf: "verschieben", geraet: "telefon", stufe: 1, symbol: "fa-arrow-right-arrow-left", titel: "Verschieben nach",
    text: "Zielspalte als Leiste von unten: Tippen verschiebt, eine volle Spalte warnt vorher; Erledigt nur per Halten, der Timer hält dabei an und bucht." },
  { pfad: "/erfassen", geraet: "telefon", stufe: 1, symbol: "fa-circle-plus", titel: "Schnell erfassen",
    text: "Board vorbelegt mit dem zuletzt genutzten, Titel, Arbeit oder Idee, Fällig per Chip; Anlegen lässt das Formular für die nächste offen. Sprechen nimmt auf." },
  { pfad: "/zeiten", geraet: "telefon", stufe: 2, symbol: "fa-stopwatch", titel: "Timer und Zeit",
    text: "Dein Timer groß mit Anhalten und Stopp, zuletzt genutzte Karten zum Starten, Zeit nachbuchen mit Karte, Tag und Dauer, Stand von heute und der Woche gegen das Soll." },
  { pfad: "/erfassen", entwurf: "sprache", geraet: "telefon", stufe: 4, symbol: "fa-microphone", titel: "Erfassen per Sprache",
    text: "Aufnahme über die App Transkription: Pegel, der Text erscheint live, die letzten Wörter noch vorläufig. Stopp übernimmt den ersten Satz als Titel, alles als Beschreibung." },
  { pfad: "/hinweise", geraet: "telefon", stufe: 4, symbol: "fa-bell", titel: "Hinweise am Telefon",
    text: "Erwähnt, zugewiesen, fällig, Termin, verschoben: kurz und neueste zuerst; ein Tippen springt zur Karte und gilt als gelesen." },
];
