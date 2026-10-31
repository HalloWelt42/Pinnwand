---
titel: Liste, Kalender und Zeitachse
untertitel: Dieselben Karten als Tabelle, nach Tagen und als Balken
bereich: Boards
symbol: fa-table-list
---
Neben den Spalten zeigt jedes Board seine Karten auf drei weitere Arten. Du wechselst oben im Kopf des Boards über die Reiter **Board**, **Liste**, **Kalender** und **Zeitachse**. Suche und Filter der Werkzeugleiste gelten in allen vier Ansichten gleich (siehe [Suchen und Filtern](hilfe:filter)).

## Wozu welche Ansicht {#wozu}
| Ansicht | taugt für |
| - | - |
| **Board** | den Ablauf: Karten durch die Spalten ziehen |
| **Liste** | den Überblick als Tabelle, sortieren und viele Karten auf einmal ändern |
| **Kalender** | Fälligkeiten, Termine und Abwesenheiten nach Tagen |
| **Zeitachse** | Karten mit Start und Fällig als Balken über Wochen und Monate planen |

In jeder Ansicht öffnet ein Klick auf eine Karte ihr [Kartendetail](hilfe:kartendetail); schließt du es, bist du wieder in derselben Ansicht.

## Liste {#liste}
Die Liste zeigt dieselben Karten wie die Spalten als Tabelle: alle offenen Karten und die erledigten im Zeitfenster der Erledigt-Spalte, das für alle eingestellt ist (ohne Einstellung Heute). Bei einer Suche oder einem Filter zeigt sie alle passenden erledigten Karten außerhalb des Archivs. Oben steht, wie viele Karten es sind, davon offen und erledigt.

Die Spalten der Tabelle: **Schlüssel**, **Titel**, **Status** (die Spalte im Board), **Zuständig**, **Priorität**, **Fällig**, **Labels**, die eigenen Felder des Boards und, mit Zeiterfassung, **Zeit** als gebucht und geschätzt. Vor dem Titel trägt eine Idee eine Glühbirne und eine blockierte Karte ein Sperrzeichen; erledigte Karten zeigen statt der Fälligkeit ihr Abschlussdatum.

### Sortieren
Ein Klick auf eine Spaltenüberschrift sortiert danach, ein zweiter Klick dreht die Richtung. Zu Beginn sortiert die Liste nach **Status**, also in der Reihenfolge der Spalten des Boards und darin so, wie die Spalte sortiert (siehe [Sortierung einer Spalte](hilfe:board/sortierung)). Die Liste zeigt zuerst so viele Zeilen wie **Karten je Ladeschritt**; Rollen ans Ende oder **mehr laden** holt die nächsten. Sortieren, Suche und Filter gehen dabei über alle Karten. Zahlenfelder sortieren der Größe nach; Karten ohne Wert stehen aufsteigend am Ende. Die Kopfzeile und die ersten Spalten bleiben beim Rollen stehen. Ein Klick auf eine Zeile öffnet die Karte.

## Sammelaktionen in der Liste {#sammelaktionen}
Mit den Kästchen links wählst du Karten aus; das Kästchen in der Kopfzeile wählt alle. Sobald eine gewählt ist, erscheint oben die Sammelleiste mit der Zahl der gewählten Karten:

- **Verschieben nach ...**: alle in eine Spalte, wie beim Ziehen. Das Alter beginnt neu, verknüpfte Karten ziehen mit, in der Erledigt-Spalte gilt der Abschluss.
- **Zuweisen: Name tippen**: ab zwei Buchstaben eine Person aus den Vorschlägen wählen; sie wird an allen gewählten Karten zusätzlich zuständig.
- **Label ...**: setzt ein Label an allen.
- **Priorität ...**: setzt die Priorität aller.
- **In den Papierkorb**: mit Zeiten, Kommentaren, Anhängen und Verknüpfungen; im Papierkorb wiederherstellbar.
- **Auswahl aufheben**.

Jede Sammelaktion ist eine einzige Änderung mit **Rückgängig** in der Meldung. Es gelten deine Rechte im Board: Verschieben braucht das Recht Karten verschieben, Zuweisen, Label und Priorität das Recht Karten bearbeiten, der Papierkorb das Recht Karten löschen. Fehlt dir eines, nennt die Meldung den Grund.

## Kalender {#kalender}
Der Kalender zeigt die Karten an ihrem Fälligkeitstag. Hat das Board das Modul Serien und Termine, stehen dort auch Termine und Serientage; mit dem Modul Arbeitszeit und dem Recht Abwesenheiten sehen auch die Abwesenheiten der Mitglieder. Feiertage erscheinen nach den Bundesländern der Mitglieder.

- Oben blättern die Pfeile vor und zurück, **Heute** springt zurück zu heute.
- **Monat** und **Woche** wechseln den Zeitraum.
- Rechts blenden Schalter einzelne Arten aus und wieder ein: **Karten**, **Termine**, **Serien** und **Abwesenheiten**, soweit das Board sie hat.
- Im Monat steht links die Kalenderwoche. Je Tag stehen bis zu vier Zeilen; passen nicht alle hinein, öffnet der Knopf mit der Zahl der übrigen, etwa **+2 weitere**, die Woche dieses Tages.
- Die Woche zeigt oben in der Zeile **ganztägig** fällige Karten, Abwesenheiten und Serien ohne Uhrzeit, darunter ein Stundenraster mit Terminen und Serientagen zu ihrer Uhrzeit. Was sich überschneidet, steht nebeneinander; eine Linie zeigt die jetzige Uhrzeit.
- Erledigte Karten stehen mit Haken und durchgestrichen da, überfällige mit einem Warnzeichen.
- Ein Klick auf eine Karte öffnet sie, ein Klick auf einen Serientag öffnet die Serie (siehe [Serien und Termine](hilfe:serien)).

## Fälligkeit im Kalender ändern {#kalender-ziehen}
- Zieh eine Karte auf einen anderen Tag: sie ist dann an diesem Tag fällig. Liegt ihr Start danach, rückt er auf denselben Tag.
- Rechts steht die Leiste **Ohne Fälligkeit** mit allen offenen Karten ohne Fälligkeitstag. Von dort auf einen Tag ziehen setzt die Fälligkeit.
- Eine Karte aus dem Kalender auf diese Leiste ziehen entfernt ihre Fälligkeit.
- Der Doppelpfeil klappt die Leiste ein und aus; in schmalen Fenstern beginnt sie eingeklappt.

Ziehen geht mit dem Recht Karten bearbeiten, und nicht, solange eine Suche oder ein Filter gilt. Jede Änderung kommt mit **Rückgängig** in der Meldung.

## Zeitachse {#zeitachse}
Die Zeitachse zeigt jede Karte mit Start oder Fälligkeit als Balken über die Tage, vom Start bis zum Fälligkeitstag. Hat eine Karte nur einen Fälligkeitstag, ist ihr Balken einen Tag lang und als reine Fälligkeit gekennzeichnet. Wochenenden und Feiertage sind hinterlegt, eine Linie zeigt heute; die Legende oben rechts erklärt die Muster.

- **Nach Spalte** gruppiert die Karten nach den Spalten des Boards, **Nach Person** nach den Zuständigen; Karten ohne Zuständige stehen dann unter **Ohne Zuständige**, eine Karte mit mehreren Zuständigen bei jeder dieser Personen. Nach Person stehen mit dem Recht Abwesenheiten sehen auch die Abwesenheiten in der Zeile jeder Person.
- **Woche** zeigt einen Tag je Spalte über zehn Wochen, beginnend mit der Vorwoche; die Pfeile springen vier Wochen. **Monat** zeigt vier Monate im Überblick; die Pfeile springen einen Monat. **Heute** springt zurück.
- Erledigte Karten tragen einen Haken, überfällige ein Warnzeichen. Fällt ein Balken in die Abwesenheit einer zuständigen Person, trägt er einen Sonnenschirm, und der Hinweis beim Überfahren nennt die Abwesenheit.
- Liegt eine Karte außerhalb des gezeigten Zeitraums, zeigt ein Pfeil am Rand, in welcher Richtung sie liegt.
- Ein Klick auf den Namen links oder auf den Balken öffnet die Karte.
- Die Zahl neben einer Spalte zählt alle ihre Karten, auch die ohne Datum; beim Überfahren steht, wie viele davon hier zu sehen sind.

### Arbeit auf der Zeitachse {#zeitachse-arbeit}
Neben den geplanten Tagen zeigt die Zeitachse, wann tatsächlich an einer Karte gearbeitet wurde: an jedem Tag mit gebuchter Zeit steht in einer eigenen schmalen Spur unten in der Zeile, unter dem Balken, ein kleines Säulchen, so hoch wie die Zeit (ein voller Arbeitstag von acht Stunden füllt die Spur). Haben mehrere Personen an dem Tag gebucht, ist es in ihren Farben geteilt, etwa du und der Helfer. Beim Überfahren steht je Person, wie lange an welchem Tag, etwa "Helfer: 1:20 h am Fr 30.10.". Die Legende oben rechts nennt die Säulchen **Gebuchte Arbeit**. Eine Karte ohne Start und Fälligkeit, an der im gezeigten Zeitraum gearbeitet wurde, steht mit ihren Säulchen in ihrer Spalte, ohne Balken. **Nach Person** zeigt bei jeder Person nur ihre eigene Arbeit, auch an Karten, für die sie nicht zuständig ist. Gezählt wird, was du von der Zeit siehst: deine eigene und, mit dem Recht Zeiten anderer sehen, die der anderen.

## Planen auf der Zeitachse {#zeitachse-ziehen}
- Den Balken ziehen verschiebt Start und Fälligkeit gemeinsam.
- Am linken Rand ziehen ändert den Start, am rechten Rand den Fälligkeitstag. Hat eine Karte nur einen Fälligkeitstag, setzt der linke Rand einen Start.
- Mit der Tastatur: den Balken mit der Tabulatortaste wählen, dann verschiebt Pfeil links oder rechts um einen Tag; mit Umschalt ändert er nur den Fälligkeitstag, mit Alt nur den Start. Enter öffnet die Karte.
- Rechts steht die Leiste **Ohne Datum** mit allen offenen Karten ohne Start und Fälligkeit. Auf einen Tag ziehen setzt Start und Fällig auf diesen Tag.

Der Start liegt dabei nie nach dem Fälligkeitstag. Ziehen geht mit dem Recht Karten bearbeiten, und nicht, solange eine Suche oder ein Filter gilt.
