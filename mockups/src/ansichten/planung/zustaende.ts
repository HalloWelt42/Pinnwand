// Einträge dieses Bereichs in der Galerie der Entwürfe (siehe src/zustaende.ts).
import type { Zustand } from "../../zustaende";

export const ZUSTAENDE: Zustand[] = [
  { pfad: "/serien", stufe: 3, symbol: "fa-repeat", titel: "Serien und Termine",
    text: "Alle Serien und kommenden Termine deiner Boards: Rhythmus, Uhrzeit, Dauer, nächster Tag, Teilnehmer, Zielspalte; Termine mit Zusage je Person." },
  { pfad: "/serien", entwurf: "nachtrag", stufe: 3, symbol: "fa-clock-rotate-left", titel: "Nachtrag am Folgetag",
    text: "Vorgebuchte Zeiten von gestern bestätigen, anpassen oder verwerfen, als Bereich auf der Seite; nur deine, ohne Antwort zählt nichts." },
  { pfad: "/serien", entwurf: "neu", stufe: 3, symbol: "fa-calendar-plus", titel: "Neue Serie",
    text: "Links Karte, Rhythmus, Teilnehmer und Vorlauf, rechts sofort die Tage, die vorgebucht werden, mit Urlaub und Feiertagen der Teilnehmer." },
  { pfad: "/serien/se-runde", stufe: 3, symbol: "fa-pen-to-square", titel: "Serie bearbeiten",
    text: "Produktionsrunde werktags: rechts jeder Tag mit Stand (gezählt, wartet, vorgebucht, angefasst, gelöscht kommt nicht wieder), Abwesende je Tag." },
  { pfad: "/serien/se-runde", entwurf: "aendern", stufe: 3, symbol: "fa-arrows-rotate", titel: "Serie ändern",
    text: "Uhrzeit und Dauer geändert: Speichern passt nur unberührte Vorbuchungen an; angefasste, vergangene und gelöschte Tage bleiben." },
  { pfad: "/serien/se-runde", entwurf: "loeschen", stufe: 3, symbol: "fa-trash-can", titel: "Serie löschen",
    text: "Rückfrage in der Fläche: unberührte Vorbuchungen in den Papierkorb, Karten mit Zeit bleiben als Verlauf und werden gelöst." },
  { pfad: "/serien/se-reinigung", stufe: 3, symbol: "fa-circle-pause", titel: "Pausierte Serie",
    text: "Hallenreinigung pausiert: keine neuen Karten, unberührte Zukunftskarten entfernt; Fortsetzen bucht ab heute, gelöschte Tage bleiben." },
  { pfad: "/board/prod/kalender", stufe: 3, symbol: "fa-calendar-days", titel: "Kalender",
    text: "Monat mit Karten nach Fälligkeit, Terminen, Serientagen, Abwesenheiten und Feiertagen; Karte auf einen Tag ziehen setzt die Fälligkeit." },
  { pfad: "/board/prod/kalender", entwurf: "woche", stufe: 3, symbol: "fa-calendar-week", titel: "Kalender, Woche",
    text: "Woche mit Stundenraster: Termine und Serien zur Uhrzeit, Karten und Abwesenheiten ganztägig, Linie für jetzt; Leiste der Karten ohne Datum." },
  { pfad: "/board/prod/zeitachse", stufe: 3, symbol: "fa-bars-progress", titel: "Zeitachse",
    text: "Karten von Start bis Fällig als Balken je Spalte; ziehen verschiebt, am Rand ziehen ändert Start oder Ende; Wochenenden, Feiertage, heute." },
  { pfad: "/board/prod/zeitachse", entwurf: "personen", stufe: 3, symbol: "fa-people-group", titel: "Zeitachse nach Personen",
    text: "Je Person ihre Karten und Abwesenheiten; eine Karte im Urlaub ihrer Person ist markiert. Maßstab Woche oder Monat." },
];
