# Transkript-Verknüpfung mit Tickets

Verbindet Tickets (Karten) mit Stellen in Transkripten, sodass von einer Karte aus
gezielt an eine Sprechposition gesprungen werden kann und ein Abschnitt mit einer
eigenen Zusammenfassung versehen wird.

## Modell: die Transkript-Marke

Eine Marke (Tabelle `transkript_marke`) ist die Brücke zwischen einer Karte und einer
Stelle in einem Transkript. Sie hält: Karte, Transkript (Id und Name denormalisiert),
Position (Segment-Startzeit in Sekunden, optional), den Segment-Text und Sprecher
(denormalisiert, damit die Marke ohne Nachladen lesbar bleibt), ein Label, eine
editierbare Zusammenfassung und eine Reihenfolge. Eine Karte kann beliebig viele
Marken tragen. Beim Löschen einer Karte, Spalte oder eines Boards werden ihre Marken
mitentfernt.

Die Position ist ein Punkt (eine Segment-Startzeit); die Zusammenfassung beschreibt
den Abschnitt ab dieser Stelle. Die bestehende einfache Einzel-Verknüpfung der Karte
(`transkript_id`) bleibt unverändert daneben bestehen.

## Vom Ticket aus

Im Karten-Detail listet der Abschnitt "Transkript-Verweise" alle Marken der Karte. Je
Marke gibt es: Name und Position, den Segment-Text, ein Textfeld für die Zusammenfassung
(Auto-Speichern), einen Knopf "Öffnen" (Sprung ins Transkript an die Position) und das
Entfernen. Neue Verweise entstehen über die Transkript-Suche im selben Abschnitt.

KI-Vorschlag: Ein Knopf erzeugt aus dem Abschnitt einen Zusammenfassungs-Vorschlag (LM
Studio, erstes geladenes Nicht-Embedding-Modell). Der Vorschlag erscheint zuerst als
Vorschau und wird erst auf "Übernehmen" gespeichert. Ist kein Chat-Modell geladen,
meldet die Oberfläche das und bleibt nutzbar (rein manuelle Zusammenfassung).

## Vom Transkript aus

Die Transkript-Ansicht listet alle vorhandenen Transkripte (Suche filtert) und zeigt im
Detail die Segmente mit Zeit, Sprecher und Text. Jedes Segment hat einen Anheft-Knopf:
darüber wird ein Ticket gewählt (Board, dann Karte), und es entsteht eine Marke an
genau dieser Segment-Position, mit übernommenem Text und Sprecher.

Bereits verknüpfte Segmente sind markiert. Im Kopf des Transkripts zeigt eine Leiste
"Verknüpfte Tickets" alle Marken; ein Klick springt zurück zur jeweiligen Karte.

## Sprung an die Position

"Öffnen" an einer Marke wechselt in die Transkript-Ansicht, öffnet das Transkript,
setzt das Audio auf die Position und hebt das passende Segment hervor (über den
Navigations-Store, der Id und Position trägt). So entsteht ein durchgehender Weg vom
Ticket zur konkreten Inhaltsstelle und zurück.
