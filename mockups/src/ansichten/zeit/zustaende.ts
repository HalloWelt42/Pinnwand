// Einträge dieses Bereichs in der Galerie der Entwürfe (siehe src/zustaende.ts).
import type { Zustand } from "../../zustaende";

export const ZUSTAENDE: Zustand[] = [
  { pfad: "/zeiten", stufe: 2, symbol: "fa-clock", titel: "Stundenzettel",
    text: "Deine Woche aus allen Boards: Karten mal Tage, Zellen direkt änderbar, Summe, Soll aus dem Zeitkonto, Differenz; der laufende Timer zählt mit." },
  { pfad: "/zeiten", entwurf: "tag", stufe: 2, symbol: "fa-list-ul", titel: "Einträge eines Tags",
    text: "Fr 23.10., halber Urlaubstag: Timer, nachgetragen, Korrektur, Serie, ein Teil über Mitternacht; Dauer und Notiz änderbar, Löschen mit Rückgängig." },
  { pfad: "/zeiten", entwurf: "nachtragen", stufe: 2, symbol: "fa-clock-rotate-left", titel: "Zeit nachtragen",
    text: "Karte in allen Boards suchen, Tag und Dauer (1,5 heißt 1:30); der Stundenzettel zeigt schon beim Tippen, wo die Zeit landet." },
  { pfad: "/zeiten", entwurf: "deckel", stufe: 2, symbol: "fa-hourglass-end", titel: "Vergessener Timer",
    text: "Eine Sitzung lief 12:30 Std.: gebucht sind die ersten 12, an Mitternacht zerlegt, mit Rückfrage nach dem echten Ende." },
  { pfad: "/arbeitszeit", stufe: 2, symbol: "fa-scale-balanced", titel: "Zeitkonto",
    text: "Soll und Ist heute, Woche, Monat und Jahr, Überstunden, Resturlaub; Monate mit Saldo; Wochenstunden, Arbeitstage, Bundesland, Urlaub, halbe Tage." },
  { pfad: "/arbeitszeit/kalender", stufe: 2, symbol: "fa-calendar-days", titel: "Jahreskalender",
    text: "Zwölf Monate mit Feiertagen in Nordrhein-Westfalen, Urlaub, halben Tagen, krank, frei, Fortbildung; Tage anklicken oder ziehen." },
  { pfad: "/arbeitszeit/kalender", entwurf: "auswahl", stufe: 2, symbol: "fa-hand-pointer", titel: "Tage im Kalender eintragen",
    text: "16. bis 20.11. gezogen: rechts Art, halbe Tage und Notiz, dazu die Wirkung auf Soll und Resturlaub vor dem Eintragen." },
  { pfad: "/arbeitszeit/urlaub", stufe: 2, symbol: "fa-umbrella-beach", titel: "Urlaub und Abwesenheit",
    text: "Von, bis, Art, halbe Tage, Notiz; rechts die Wirkung Tag für Tag und Brückentage als Vorschlag; die Liste des Jahres mit Wirkung auf das Soll." },
  { pfad: "/arbeitszeit/team", stufe: 2, symbol: "fa-users", titel: "Team",
    text: "Mitglieder von Produktionsplanung mal vier Wochen, Ebenen Anwesenheit, Feiertage je Bundesland, Stunden und Auslastung; nur mit dem Recht Abwesenheiten sehen." },
  { pfad: "/arbeitszeit/team", entwurf: "ohne-recht", stufe: 2, symbol: "fa-user-lock", titel: "Team ohne Recht",
    text: "Mit einer Rolle ohne das Recht Abwesenheiten sehen bleibt nur die eigene Zeile, mit Hinweis, wo das Recht vergeben wird." },
  { pfad: "/berichte", stufe: 4, symbol: "fa-file-lines", titel: "Berichte",
    text: "Bericht in Schritten wählen: Art, Zeitraum, Boards, Personen, Format; rechts die erstellten Berichte in der Kellerwolke mit Herunterladen und Vorlesen." },
  { pfad: "/berichte", entwurf: "vorschau", stufe: 4, symbol: "fa-eye", titel: "Berichtsvorschau",
    text: "Stundennachweis der letzten Woche für Max und Jonas als PDF-Blatt: Soll, Ist und Differenz je Tag mit Karten und Abwesenheiten." },
];
