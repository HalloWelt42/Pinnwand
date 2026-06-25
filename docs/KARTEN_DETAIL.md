# Karten-Detail: Felder, Idee, verknüpfte Aufgaben

Das Karten-Detail (CardDrawer) zeigt die Felder kompakt und direkt bearbeitbar. Es kennt
zwei Karten-Arten und verknüpfte Aufgaben mit geteilter Zeit. Ein globaler Lese-/
Bearbeiten-Umschalter wurde bewusst wieder entfernt - er war mehr Aufwand statt weniger;
stattdessen ist jedes Feld an Ort und Stelle bearbeitbar.

## Felder: lesen und bearbeiten

- **Beschreibung**: sauber gerendertes Markdown. Ein Klick darauf (oder der Knopf
  "Bearbeiten") öffnet einen Editor mit Live-Vorschau direkt an der Stelle; "Vollbild"
  blendet ihn groß und ruhig ein, "Fertig" speichert und kehrt zur gerenderten Ansicht
  zurück. Bei vorhandenem Text gibt es zusätzlich "Vorlesen".
- **Notizen**: gerendertes Markdown und **read-only**. Ein Klick (oder "Vollbild")
  öffnet die Notizen direkt im Vollbild-Editor mit Live-Vorschau; "Fertig" speichert und
  schließt. So liegt der Fokus auf den gerenderten Notizen, bearbeitet wird nur bewusst.
- **Meta-Felder** (Status, Priorität, Start, Fällig, Zuständig, Cover) sind direkt als
  Auswahl-/Datumsfelder bearbeitbar - kein Moduswechsel nötig.
- Ebenso direkt bearbeitbar: Checklisten-Haken UND -Texte, die Zeit-Tageszeilen
  (Datum + Dauer), Labels und das Kommentarfeld.

## Checkliste

Punkte lassen sich nach dem Erstellen umbenennen: ein Klick auf den Text macht ihn zur
Eingabe (Enter speichert, Escape bricht ab). Haken setzen, umbenennen, hinzufügen und
entfernen gehen in beiden Modi.

## Ideenticket (Arbeit vs. Idee)

Jede Karte ist entweder **Arbeit** (mit Zeiterfassung) oder **Idee** (Notiz, ohne
Zeiten, ohne Play). Der Typ ist im Kopf jederzeit umschaltbar; beim Anlegen lässt sich
direkt ein Ideenticket erstellen. Bei einer Idee sind Zeiterfassung und verknüpfte
Aufgaben ausgeblendet und der Timer ist gesperrt (das Backend weist einen Start ab).
Schon erfasste Zeiten bleiben gespeichert und erscheinen wieder, sobald die Karte
zurück auf Arbeit gestellt wird. So unterscheiden wir sauber zwischen Arbeit und Idee.

## Verknüpfte Aufgaben (geteilte Zeit)

Mehrere Aufgaben, die man parallel abarbeitet, lassen sich verknüpfen. Sie bilden eine
Gruppe und zeigen die **kombinierte Zeit** der Gruppe an. Wichtig: die Zeit zählt nur
**einmal** - getrackt wird wie immer auf je einer Karte, die kombinierte Anzeige ist
nur eine Sicht. Auswertungen (Arbeitszeit je Tag, Personenstunden, Berichte) zählen
deshalb unverändert jede Sekunde genau einmal. Details siehe ZEITMODELL.md, Abschnitt
"Geteilte Zeitgruppe".

Im Abschnitt "Verknüpfte Aufgaben": die Mitglieder werden gelistet (Klick öffnet die
jeweilige Karte), eine weitere Karte lässt sich per Suche verknüpfen, und diese Karte
kann sich wieder lösen. Der Schalter **"Zeit teilen"** ist der einstellbare Spezialfall:
ausgeschaltet zeigt jede Karte wieder nur ihre eigene Zeit.

### Eine Zeitgruppe bilden

Es gibt drei Wege, damit jeder den findet, der zu ihm passt - per Symbol, Klick und
Drag-and-Drop:

- **Drag-and-Drop** direkt auf dem Board: das Ketten-Symbol einer Karte auf eine andere
  Karte ziehen und fallen lassen verknüpft beide zu einer Gruppe.
- **Symbol/Knopf auf der Karte**: das Ketten-Symbol greift die Karte zum Verknüpfen;
  bereits verknüpfte Karten tragen ein gefülltes Ketten-Symbol (Wire) als Erkennung.
- **Im Karten-Detail**: das Suchfeld unter "Verknüpfte Aufgaben" findet eine Karte und
  hängt sie an die Gruppe.

## Bausteine (Modularisierung)

Das Karten-Detail ist in fokussierte Unterkomponenten aufgeteilt, statt alles in einer
großen Datei zu halten. Jede trägt genau eine Verantwortung, ist getypt und kapselt
ihren eigenen Zustand und ihr eigenes CSS:

- `MarkdownFeld.svelte` - das gerenderte Markdown-Feld (lesen, bearbeiten, Vollbild,
  optional Vorlesen). Wird für Beschreibung und Notizen wiederverwendet (`nurVollbild`
  schaltet auf das read-only-mit-Klick-ins-Vollbild-Verhalten der Notizen um).
- `Zeiterfassung.svelte` - Start/Pause/Stopp, Schätzung, Fortschritt, geteilte
  Gruppen-Zeit, Tag nachbuchen und die Tages-Aufschlüsselung.
- `VerknuepfteAufgaben.svelte` - Gruppen-Mitglieder, Verknüpfen/Lösen, Schalter
  "Zeit teilen".
- `Checkliste.svelte` - abhaken, umbenennen, hinzufügen, entfernen.
- `TranskriptVerweise.svelte` - mehrere Transkript-Marken je Karte.

`CardDrawer.svelte` orchestriert nur noch diese Bausteine und die Kopf-/Meta-Felder.
