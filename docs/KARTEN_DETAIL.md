# Karten-Detail: Lesen, Bearbeiten, Idee, verknüpfte Aufgaben

Das Karten-Detail (CardDrawer) trennt klar zwischen Lesen und Bearbeiten und fasst die
Felder kompakt zusammen. Es kennt zwei Karten-Arten und verknüpfte Aufgaben mit
geteilter Zeit.

## Lese- und Bearbeitungsmodus

- Das Detail öffnet im **Lesemodus**: Titel als Überschrift, Beschreibung und Notizen
  als sauber gerendertes Markdown, die Meta-Felder (Status, Priorität, Start, Fällig,
  Zuständig, Cover) als ruhige Label->Wert-Zeilen.
- Ein Knopf im Kopf schaltet auf **Bearbeiten**; dann werden die großen Textfelder zu
  Eingaben und die Meta-Felder zu Auswahlfeldern. Ein Klick auf einen Text wechselt
  ebenfalls in den Bearbeitungsmodus.
- **Vollbild** ist immer der Bearbeitungsmodus des ganzen Tickets - breit und ruhig,
  mit zweispaltiger Markdown-Vorschau. "Vollbild schließen" speichert und kehrt in den
  Lesemodus zurück.
- **Immer direkt bearbeitbar**, in beiden Modi: Checklisten-Haken UND -Texte, die
  Zeit-Tageszeilen (Datum + Dauer), Labels und das Kommentarfeld. Nur die großen
  Textfelder sind dem Bearbeitungsmodus vorbehalten. Die frühere doppelte Vollbild-
  Lösung je Textfeld entfällt zugunsten des einen Ticket-Vollbilds.

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
