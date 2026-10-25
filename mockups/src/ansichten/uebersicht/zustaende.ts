// Einträge dieses Bereichs in der Galerie der Entwürfe (siehe src/zustaende.ts).
import type { Zustand } from "../../zustaende";

export const ZUSTAENDE: Zustand[] = [
  { pfad: "/heute", stufe: 1, symbol: "fa-sun", titel: "Heute",
    text: "Alles für dich aus allen Boards: überfällig, heute, die nächsten sieben Tage, ohne Datum; Termine, Serien, oben dein Timer. Abhaken, Timer und Zusagen gehen echt, mit Rückgängig." },
  { pfad: "/heute", entwurf: "leer", stufe: 1, symbol: "fa-mug-hot", titel: "Heute: nichts fällig",
    text: "Deine fälligen Karten sind erledigt, der Timer ist gestoppt: ein ruhiger Zustand statt leerer Abschnitte; Termine und Karten ohne Datum bleiben." },
  { pfad: "/heute", entwurf: "getrennt", stufe: 1, symbol: "fa-plug-circle-xmark", titel: "Heute: Verbindung getrennt",
    text: "Band oben, Fuß getrennt: der letzte Stand bleibt sichtbar, Schreibendes ist gesperrt; ein Haken an HAUS-58 wird sichtbar abgewiesen." },
  { pfad: "/hinweise", stufe: 1, symbol: "fa-bell", titel: "Hinweise",
    text: "Zugewiesen, fällig, erwähnt, Termin: ungelesene hervorgehoben, Filter nach Art, Sprung zur Karte, alle gelesen, Verweis auf die Einstellungen." },
  { pfad: "/board/prod/liste", stufe: 1, symbol: "fa-table-list", titel: "Liste",
    text: "Karten des Boards als Tabelle mit Status, Zuständig, Priorität, Fällig, Labels, eigenen Feldern und Zeit; sortierbar, Kopf und Titel bleiben stehen." },
  { pfad: "/board/prod/liste", entwurf: "auswahl", stufe: 1, symbol: "fa-list-check", titel: "Liste mit Auswahl",
    text: "Drei Karten gewählt: Sammelleiste mit Verschieben, Zuweisen, Label, Priorität und In den Papierkorb." },
  { pfad: "/board/prod/archiv", stufe: 1, symbol: "fa-box-archive", titel: "Archiv",
    text: "Erledigte Karten älter als die Archivgrenze des Boards: neueste zuerst, seitenweise, durchsuchbar; ein Klick öffnet die Karte im Board." },
  { pfad: "/board/prod/papierkorb", stufe: 1, symbol: "fa-trash-can", titel: "Papierkorb",
    text: "Gelöschte Karten und eine Spalte mit allem, was dranhängt, wer wann gelöscht hat; Wiederherstellen an die alte Stelle, mit Rückgängig." },
  { pfad: "/board/prod/papierkorb", entwurf: "rueckfrage", stufe: 1, symbol: "fa-triangle-exclamation", titel: "Endgültig entfernen",
    text: "Rückfrage in der Fläche: nennt, was verloren geht (Kommentare, Anhang, Verknüpfung); die gebuchte Zeit bleibt. Nur mit dem Recht Papierkorb leeren." },
];
