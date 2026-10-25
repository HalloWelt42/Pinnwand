// Einträge dieses Bereichs in der Galerie der Entwürfe (siehe src/zustaende.ts).
import type { Zustand } from "../../zustaende";

export const ZUSTAENDE: Zustand[] = [
  { pfad: "/heute", stufe: 1, symbol: "fa-sun", titel: "Heute",
    text: "Alles für dich aus allen Boards: überfällig, heute, diese Woche, ohne Datum; Termine, Serien, oben der laufende Timer. Abhaken und Timer gehen echt." },
  { pfad: "/heute", entwurf: "leer", stufe: 1, symbol: "fa-mug-hot", titel: "Heute: nichts fällig",
    text: "Nichts überfällig, nichts für heute oder diese Woche, kein Termin: ein ruhiger, freundlicher leerer Zustand." },
  { pfad: "/heute", entwurf: "getrennt", stufe: 1, symbol: "fa-plug-circle-xmark", titel: "Heute: Verbindung getrennt",
    text: "Band oben mit Stand, nicht gespeichertem Haken und nächstem Versuch; der letzte Stand bleibt sichtbar, alles Schreibende ist gesperrt." },
  { pfad: "/hinweise", stufe: 1, symbol: "fa-bell", titel: "Hinweise",
    text: "Zugewiesen, fällig, erwähnt, Termin: ungelesene hervorgehoben, Filter nach Art, Sprung zur Karte, alle gelesen, Verweis auf die Einstellungen." },
  { pfad: "/board/prod/liste", stufe: 1, symbol: "fa-table-list", titel: "Liste",
    text: "Karten des Boards als Tabelle mit Status, Zuständig, Priorität, Fällig, Labels, eigenen Feldern und Zeit; sortierbar, Kopf und Titel bleiben stehen." },
  { pfad: "/board/prod/liste", entwurf: "auswahl", stufe: 1, symbol: "fa-list-check", titel: "Liste mit Auswahl",
    text: "Drei Karten gewählt: Sammelleiste mit Verschieben, Zuweisen, Label, Priorität und In den Papierkorb." },
  { pfad: "/board/prod/archiv", stufe: 1, symbol: "fa-box-archive", titel: "Archiv",
    text: "Erledigte Karten älter als die Archivgrenze: neueste zuerst, seitenweise, durchsuchbar; ein Klick öffnet die Karte im Board." },
  { pfad: "/board/prod/papierkorb", stufe: 1, symbol: "fa-trash-can", titel: "Papierkorb",
    text: "Gelöschte Karten und eine Spalte mit allem, was dranhängt, wer wann gelöscht hat; Wiederherstellen an die alte Stelle." },
  { pfad: "/board/prod/papierkorb", entwurf: "rueckfrage", stufe: 1, symbol: "fa-triangle-exclamation", titel: "Endgültig entfernen",
    text: "Rückfrage in der Fläche: nennt, was verloren geht (Zeit aus den Zeitkonten, Kommentare, Anhang, Verknüpfung); nur mit dem Recht Papierkorb leeren." },
];
