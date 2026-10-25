// Feste Angaben der Oberfläche, gleich denen des Servers (backend/app/regeln/board.py, anwendung/rahmen.py): Namen und
// Erklärungen der Rechte je Modul, das Konto der Pinnwand selbst.

import type { Konto, Recht } from "../modell";

/** Die Pinnwand selbst als Konto: so schreibt die tägliche Vorbuchung der Serien (Begleiter im Server) in den Verlauf
 *  und in Ereignisse. Es steht in keinem Board und nicht unter den Konten des Stands. */
export const PINNWAND_KONTO: Konto = { id: "pinnwand", name: "Pinnwand", kuerzel: "PW", farbe: "stahl", kellerwolke: "" };

export const RECHTE: Recht[] = [
  { id: "board.verwalten", modul: "kern", name: "Board verwalten", erklaerung: "Name, Spalten, Labels, Felder, Module und Einstellungen ändern" },
  { id: "mitglieder.verwalten", modul: "kern", name: "Mitglieder und Rollen verwalten", erklaerung: "Personen einladen, Rollen vergeben und ihre Rechte einstellen" },
  { id: "karten.anlegen", modul: "kern", name: "Karten anlegen", erklaerung: "Neue Karten in jeder Spalte anlegen" },
  { id: "karten.bearbeiten", modul: "kern", name: "Karten bearbeiten", erklaerung: "Titel, Beschreibung, Felder, Checklisten und Labels ändern" },
  { id: "karten.verschieben", modul: "kern", name: "Karten verschieben", erklaerung: "Karten zwischen Spalten ziehen und erledigen" },
  { id: "karten.loeschen", modul: "kern", name: "Karten löschen", erklaerung: "Karten in den Papierkorb legen" },
  { id: "kommentieren", modul: "kern", name: "Kommentieren", erklaerung: "Kommentare schreiben und Personen erwähnen" },
  { id: "papierkorb.leeren", modul: "kern", name: "Papierkorb leeren", erklaerung: "Karten endgültig entfernen" },
  { id: "zeit.buchen", modul: "zeiterfassung", name: "Eigene Zeit buchen", erklaerung: "Timer starten und eigene Zeit nachtragen" },
  { id: "zeit.andere.sehen", modul: "zeiterfassung", name: "Zeiten anderer sehen", erklaerung: "Gebuchte Zeiten aller Mitglieder auf Karten dieses Boards sehen" },
  { id: "zeit.andere.bearbeiten", modul: "zeiterfassung", name: "Zeiten anderer bearbeiten", erklaerung: "Zeiteinträge anderer Mitglieder ändern oder löschen" },
  { id: "abwesenheit.sehen", modul: "arbeitszeit", name: "Abwesenheiten sehen", erklaerung: "Urlaub und Abwesenheit der Mitglieder in Kalender und Auslastung sehen" },
  { id: "serien.verwalten", modul: "serien", name: "Serien und Termine verwalten", erklaerung: "Wiederkehrende Karten und Termine anlegen, pausieren, ändern" },
  { id: "berichte.erstellen", modul: "berichte", name: "Berichte erstellen", erklaerung: "Auswertungen dieses Boards erstellen und herunterladen" },
];
