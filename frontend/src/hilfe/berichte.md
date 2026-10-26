---
titel: Berichte
untertitel: Auswertungen als PDF, Tabelle oder Markdown
bereich: Zeit
symbol: fa-file-lines
---
Berichte fassen gebuchte Zeit und erledigte Karten für einen Zeitraum zusammen, etwa als Stundennachweis für dich oder als Übersicht eines Projekts. Du stellst sie in wenigen Schritten zusammen, siehst vorher genau, was in der Datei steht, und legst sie in der Kellerwolke ab.

## Berichte öffnen {#aufruf}
Den Eintrag **Berichte** in der Seitenleiste gibt es, sobald eines deiner Boards das Modul **Berichte** eingeschaltet hat (siehe [Module](hilfe:module)). Links stehen die Schritte **Art**, **Zeitraum**, **Boards**, **Personen** und **Format**, rechts die Liste deiner erstellten Berichte oder die Vorschau. Die Leiste oben zeigt die Schritte bis zur **Vorschau**.

Für jeden Bericht brauchst du in mindestens einem Board das Recht **Berichte erstellen**: Auswertungen dieses Boards erstellen und herunterladen. In den Start-Rollen haben es **Besitzer** und **Mitglied**.

## Art {#art}
Im ersten Schritt **Art** wählst du, was der Bericht zeigt:

| Art | Inhalt |
|---|---|
| **Stundennachweis je Person** | Soll, Ist und Differenz je Tag aus dem Zeitkonto, mit Karten und Abwesenheiten |
| **Zeiten je Board und Karte** | Gebuchte Zeit je Karte eines Boards, mit Personen und Schätzung |
| **Erledigte Karten** | Karten, die im Zeitraum erledigt wurden, mit Zuständigen und Zeit |

Was in den Abschnitten steht:
- **Stundennachweis je Person**: je Person ein Abschnitt mit den Spalten Tag, Soll, Ist, Differenz, Karten und Hinweis, darunter die Summe. Das Ist ist die gebuchte Zeit aus allen Boards, das Soll kommt aus dem [Zeitkonto](hilfe:arbeitszeit/soll) mit Feiertagen und Abwesenheiten. Unter Hinweis steht der Feiertag, die Abwesenheit oder der halbe Tag. Tage ohne Soll, ohne Zeit, ohne Feiertag und ohne Abwesenheit fehlen.
- **Zeiten je Board und Karte**: je Board ein Abschnitt mit Schlüssel, Karte, den Kürzeln der Personen, Zeit und Schätzung; die Karte mit der meisten Zeit zuerst. Bestätigte Termine stehen als eigene Zeile. Unten die Summe.
- **Erledigte Karten**: je Board die Karten, deren Abschluss im Zeitraum liegt, auch archivierte, mit Schlüssel, Karte, Tag des Abschlusses, Zuständigen und Zeit. Unten die Zahl der Karten und ihre Zeit.

## Zeitraum {#zeitraum}
Im Schritt **Zeitraum** stehen die Knöpfe **Diese Woche**, **Letzte Woche** (die Vorgabe), **Dieser Monat**, **Letzter Monat**, **Dieses Jahr** und **Eigener**. Bei **Eigener** wählst du **Von** und **Bis** selbst. Neben der Überschrift steht der gewählte Zeitraum in Worten. Ein Bericht umfasst höchstens 400 Tage.

## Boards und Personen {#personen}
Schritt **Boards**:
- Der Stundennachweis braucht keine Boardwahl: Er kommt aus dem Zeitkonto und umfasst alle Boards.
- Für die beiden anderen Arten wählst du mindestens ein Board. Angeboten werden Boards mit dem Modul Berichte, in denen du Berichte erstellen darfst.

Schritt **Personen**: Du stehst schon da. Weitere fügst du über **Person hinzufügen** hinzu; die Vorschläge erscheinen darunter, das X am Namen entfernt eine Person.
- Im Stundennachweis gehen du und andere Personen mit Zeitkonto, deren Abwesenheiten du in einem gemeinsamen Board sehen darfst. Jede Person braucht ein Zeitkonto, mindestens eine muss gewählt sein.
- In den Board-Berichten kommen die Mitglieder der gewählten Boards in Frage. Entfernst du alle Personen, auch dich, gilt **alle**. Mit Personen zählt bei **Zeiten je Board und Karte** nur deren Zeit, und bei **Erledigte Karten** stehen nur Karten, für die eine von ihnen zuständig ist.

## Format {#format}
Im Schritt **Format** wählst du, wie die Datei aussieht:
- **PDF**: ein Blatt im Hochformat mit Titel, Zeitraum, Tabellen, Summen und den Erklärungen unter jedem Abschnitt; im Fuß steht, wann der Bericht erstellt wurde, und die Seitenzahl.
- **Tabelle**: eine Datei mit Werten, die durch Semikolon getrennt sind, wie Tabellenprogramme sie hierzulande direkt öffnen.
- **Markdown**: eine Textdatei mit Überschriften und Tabellen, gut zum Weiterbearbeiten und zum Vorlesen.

Der Dateiname nennt die Art, die Person (bei mehreren Team) oder die Kürzel der Boards und den Zeitraum.

## Vorschau {#vorschau}
**Vorschau** zeigt rechts genau das, was die Datei enthalten wird, mit ihrem Namen. Änderst du links etwas, folgt die Vorschau nach einem kurzen Moment. Bei Markdown siehst du den Text der Datei, sonst die Tabellen wie im Blatt.

Ist [Vorlesen](hilfe:vorlesen) eingerichtet, liest **Vorlesen** die Vorschau Zeile für Zeile vor; ein zweiter Klick auf **Stopp** hält an. **Erstellte Berichte** führt zurück zur Liste.

Vorschau und Erstellen bleiben grau, solange etwas fehlt: im Stundennachweis eine Person, sonst ein Board, oder wenn Bis vor Von liegt.

## Erstellen und ablegen {#ablegen}
**Erstellen und ablegen** erstellt die Datei und legt sie in der Kellerwolke im Ordner **Berichte** der Pinnwand ab. Die Meldung nennt den Ort. Eine erstellte Datei lässt sich nicht zurücknehmen, darum gibt es hier kein Rückgängig.

Die Liste **Erstellte Berichte** rechts zeigt deine Berichte mit Titel, Zeitraum, wann sie erstellt wurden, und Größe; ein eben erstellter ist hervorgehoben. Das Symbol zum Herunterladen am Ende der Zeile lädt die Datei. Berichte im Format Markdown lassen sich hier auch vorlesen. Jede Person sieht und lädt nur ihre eigenen Berichte.

## Was ein Bericht zeigt {#rechte}
Ein Bericht zeigt nie mehr, als du in der Pinnwand selbst sehen darfst:
- Deine eigene Zeit steht immer darin.
- Die Zeit anderer zählt in einem Board nur, wenn du dort das Recht **Zeiten anderer sehen** hast (siehe [Zeiterfassung](hilfe:zeiterfassung/rechte)). Ohne das Recht zählt im Board nur deine eigene Zeit, auch in der Spalte Zeit der erledigten Karten.
- Im Stundennachweis stehen andere Personen nur, wenn du ihre Abwesenheiten sehen darfst (siehe [Wer was sieht](hilfe:arbeitszeit/sichtbarkeit)). Ihr Ist zählt ihre ganze gebuchte Zeit aus allen Boards; welche Karten es waren, nennt die Spalte Karten nur dort, wo du ihre Zeit siehst.
- Board-Berichte gehen nur für Boards mit dem Modul Berichte, in denen du **Berichte erstellen** darfst.
