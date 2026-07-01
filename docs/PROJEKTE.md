# Projekte (Mappe = Projekt)

Eine **Mappe ist ein Projekt**, ein **Board ist eine Phase** darin. Der Aufwand eines
Projekts ist die Summe über alle Boards und Karten der Mappe. Es gibt bewusst keine
zusätzliche Projekt-Zuordnung an der Karte: die Hierarchie Mappe -> Board -> Karte ->
Zeiteintrag reicht, und `zeiteintrag` trägt `board_id` und `mappe_id` bereits
denormalisiert.

## Kennzahlen: Ist, Soll und Budget bleiben getrennt

- **Ist** = tatsächlich erfasste Zeit, Summe der `zeiteintrag.sekunden` je Mappe.
  `zeiteintrag` ist die einzige Wahrheit für erfasste Zeit (keine Doppelzählung).
- **Soll** = Summe der Karten-Schätzungen (`karte.schaetzung_min`) über die Boards der
  Mappe.
- **Budget** = optionale Planungsobergrenze je Projekt (`mappe.budget_min`, in Minuten).

Die drei Werte werden nie vermischt. **Rest** und der Fortschrittsbalken messen gegen
das Budget, falls eines gesetzt ist, sonst gegen das Soll.

## Projektfelder an der Mappe

Additiv, mit sanfter Migration:

- `owner` - verantwortliche Person (Kürzel),
- `budget_min` - Budget in Minuten (optional),
- `status` - `aktiv`, `pausiert` oder `abgeschlossen` (steuert nur die Darstellung,
  nicht die Sichtbarkeit - die hängt an der Mitgliedschaft, siehe ROLLEN.md).

Ein defensiver Backfill ordnet alte Zeiteinträge ohne `mappe_id` über ihr Board zu,
damit die Ist-Summe je Projekt vollständig ist.

## API

- `GET /api/kanban/projekte` - Aufwand je Projekt (nach Mitgliedschaft gescoped:
  Mitarbeiter sehen nur ihre Projekte, geteilte Mappen bleiben sichtbar, Admin alle).
- `GET /api/kanban/projekte/{mappe_id}` - Detail mit Aufschlüsselung je Phase (Board)
  und je Person (403 für Nicht-Mitglieder).
- `PATCH /api/kanban/mappen/{mappe_id}` - setzt neben dem Titel auch `owner`,
  `budget_min` und `status`.

Die Aggregation liegt bewusst im Modul `kanban_kern`, das Mappe, Board, Karte und
Zeiteintrag ohnehin besitzt (kohäsiver als eine modulübergreifende Auswertung).

## Ansicht

Die globale Ansicht **Projekte** zeigt je Projekt Ist/Soll/Budget/Rest mit
Fortschrittsbalken, Status und Verantwortlichem. Owner, Budget und Status sind inline
editierbar; ein Aufklappen bricht den Aufwand auf Phasen (Boards) und Personen herunter.
