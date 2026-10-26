---
titel: Zeiterfassung
untertitel: Timer, Schätzung und nachgetragene Zeit
bereich: Zeit
symbol: fa-stopwatch
---
Mit der Zeiterfassung hältst du fest, wie lange du an einer Karte arbeitest: mit einem Timer, der mitläuft, oder indem du Zeit nachträgst. Die Zeit einer Karte ist immer die Summe ihrer Zeiteinträge. Daraus rechnen der Stundenzettel, dein Zeitkonto und die Berichte.

## Voraussetzungen und Rechte {#rechte}
- Das Board hat das Modul **Zeiterfassung** eingeschaltet (siehe [Module](hilfe:module)). Sobald eines deiner Boards Zeit erfasst, stehen der Eintrag **Zeiten** in der Seitenleiste und deine Stunden im Kopf.
- Zeit gibt es nur auf Karten der Art **Arbeit**. Eine **Idee** hat keine Zeiterfassung. Den Umschalter **Arbeit** und **Idee** findest du oben im Kartendetail; schaltest du eine Karte auf Idee, halten ihre laufenden Timer an und buchen.
- Wer was darf, legt die Rolle im Board fest:

| Recht | Was es erlaubt |
|---|---|
| **Eigene Zeit buchen** | Timer starten und eigene Zeit nachtragen; dazu eigene Einträge ändern und löschen, Zellen und Ticketzeit setzen, Termine und Serientage bestätigen |
| **Zeiten anderer sehen** | Gebuchte Zeiten und laufende Timer aller Mitglieder auf Karten dieses Boards sehen |
| **Zeiten anderer bearbeiten** | Zeiteinträge anderer Mitglieder ändern oder löschen |

Die Start-Rollen jedes Boards: **Besitzer** haben alle drei Rechte, **Mitglied** die ersten beiden, **Leser** keines. Die Rechte gelten nur, solange die Zeiterfassung im Board an ist. Rollen stellst du in den [Einstellungen des Boards](hilfe:boardeinstellungen) ein.

Deine eigenen Zeiten siehst du immer. Andere sehen sie nur in Boards, in denen sie das Recht **Zeiten anderer sehen** haben.

## Timer starten, anhalten und stoppen {#timer}
Jede Person hat genau einen Timer, über alle Boards hinweg. Er läuft immer auf einer Karte. Eine Sitzung ist die Zeit von Start oder Fortsetzen bis Anhalten oder Stoppen.

Starten kannst du ihn hier:
- Auf der Karte im Board: der Zeitknopf mit dem Abspielzeichen in der unteren Zeile der Karte. Du musst die Karte dafür nicht öffnen.
- Im Kartendetail im Abschnitt **Zeiterfassung**: Knopf **Start**.
- In [Heute](hilfe:heute) rechts an jeder Karte.
- Unter **Zeiten** am Anfang jeder Kartenzeile im Stundenzettel.
- [Am Telefon](hilfe:telefon) auf der Seite für die Zeit.

Läuft dein Timer schon auf einer anderen Karte oder ist er dort angehalten, endet er beim Start und bucht; die Meldung nennt die gebuchte Zeit. Timer anderer Personen laufen weiter. Der erste Start setzt den Starttag der Karte, wenn sie noch keinen hat.

- **Anhalten** bucht die laufende Sitzung. Der Timer bleibt auf der Karte und lässt sich mit **Fortsetzen** weiterführen.
- **Stoppen** bucht ebenso und beendet den Timer.

Die Knöpfe je nach Ort:
- Im Kopf jeder Seite steht dein Timer mit Schlüssel, Titel und Zeit der Karte, dazu Anhalten oder Fortsetzen und das Stoppzeichen (**Stoppen und buchen**).
- Im Kartendetail: läuft er, **Anhalten** und **Stopp und buchen**; ist er angehalten, **Fortsetzen** und **Beenden**.
- In Heute oben: **Anhalten** oder **Fortsetzen** und **Stoppen**, mit der Startzeit und dem Anteil an der Schätzung.
- Auf der Karte im Board hält derselbe Zeitknopf an (Pausezeichen) oder setzt fort (Abspielzeichen).

Kein Timer läuft auf einer Idee, auf einer Karte in der Erledigt-Spalte und in einem Board ohne Zeiterfassung. Ohne das Recht **Eigene Zeit buchen** kannst du keinen Timer starten oder fortsetzen. Deinen eigenen Timer kannst du aber immer anhalten und stoppen, auch wenn dir das Recht inzwischen fehlt.

Den Timer einer anderen Person siehst du nur mit dem Recht **Zeiten anderer sehen**: auf der Karte als Zeichen ohne Knopf, im Kartendetail als Zeile **Timer von ... läuft**.

## Wann ein Timer von selbst endet {#timer-ende}
In diesen Fällen hält die Pinnwand Timer an, bucht die Sitzung und beendet den Timer. Keine Sekunde geht dabei verloren.

| Was passiert | Welche Timer enden |
|---|---|
| Eine Karte kommt in die Erledigt-Spalte, auch als mitgezogene verknüpfte Karte | alle Timer auf diesen Karten |
| Eine Karte wird zur Idee | alle Timer auf der Karte |
| Eine Karte, eine Spalte oder ein ganzes Board geht in den Papierkorb | alle Timer auf den betroffenen Karten |
| Eine Karte zieht in ein anderes Board | alle Timer auf der Karte; ihre gebuchte Zeit zieht mit |
| Das Modul Zeiterfassung wird im Board ausgeschaltet | alle Timer im Board; die Zeiten bleiben erhalten |
| Ein Mitglied wird aus dem Board entfernt | die Timer dieser Person in diesem Board |
| Du startest deinen Timer auf einer anderen Karte | dein bisheriger Timer |

Betrifft es deinen eigenen Timer, sagt es die Meldung mit **dein Timer ist gestoppt** und der gebuchten Zeit. Jede Buchung steht außerdem im Verlauf der Karte.

## Wie gebucht wird {#buchung}
Jede Buchung ist ein Zeiteintrag mit Tag, Person, Dauer und Herkunft. Die Herkunft zeigt, woher er stammt:

| Herkunft | Bedeutung |
|---|---|
| **Timer** | Aus Start und Stopp; je Karte und Tag ein Eintrag |
| **nachgetragen** | Von Hand auf diesen Tag gebucht |
| **Korrektur** | Differenz aus dem Setzen der Zeit (Zelle oder Ticketzeit) |
| **Serie** | Aus einer Serie nachgetragen, mit der geplanten Dauer als Vorschlag |
| **Termin** | Bestätigte Zeit eines Termins, von Beginn bis Ende |

Beim Anhalten und Stoppen gelten diese Regeln:
- Mehrere Sitzungen auf derselben Karte am selben Tag landen in einem Timer-Eintrag. Er zeigt **Sitzungen zusammengefasst** mit ihrer Zahl.
- Läuft eine Sitzung über Mitternacht, bucht jeder Tag seinen Teil als eigenen Eintrag. Der Eintrag zeigt **über Mitternacht, Teil am** und den anderen Tag.
- Eine Sitzung bucht höchstens 12 Stunden am Stück, siehe [Deckel nach 12 Stunden](#deckel).

Solange dein Timer läuft, zählt seine Zeit schon überall mit: im Kopf, im Stundenzettel, in Heute und an der Karte. Ändern lässt sich diese Zeit erst, wenn du anhältst.

## Deckel nach 12 Stunden {#deckel}
Vergisst du den Timer, bucht eine Sitzung nur die ersten 12 Stunden ab ihrem Beginn, an Mitternacht zerlegt. Diese Einträge tragen den Vermerk **nach 12 Stunden gedeckelt**, und der Verlauf der Karte sagt es auch.

Die Rückfrage dazu findest du unter **Zeiten**: Klick im Stundenzettel auf einen der Tage, über die die Sitzung lief. Oben in der Leiste steht **Timer lief ... Stunden** mit Beginn, Stopp und den gebuchten Teilen und die Frage **Wann hast du aufgehört?**
1. Trage bei **Ende** die Uhrzeit ein, zu der du wirklich aufgehört hast, etwa 18:30. Sie gilt als die erste solche Uhrzeit nach dem Beginn, am Starttag oder am Tag danach.
2. **Übernehmen** bucht die Sitzung neu von ihrem Beginn bis zu diesem Ende, ohne Deckel und an Mitternacht zerlegt. Das Ende darf auch nach den 12 Stunden liegen, wenn du wirklich so lange gearbeitet hast, aber nicht nach dem Stopp des Timers. Dann bleibt der Knopf grau und nennt den Grund.
3. Stimmen die 12 Stunden, nimmt **12 Stunden lassen** nur den Vermerk weg.

Beide Antworten melden sich mit Rückgängig; Rückgängig bringt die Rückfrage zurück.

## Ticketzeit und Schätzung {#schaetzung}
Im Kartendetail zeigt der Abschnitt **Zeiterfassung** groß die Ticketzeit: die Summe aller Einträge der Karte, die du siehst, samt laufender Timer. Ohne das Recht **Zeiten anderer sehen** ist das nur deine eigene Zeit, und der Hinweis am Feld sagt **Deine Zeit auf dieser Karte**.

Die Ticketzeit lässt sich direkt überschreiben. Die Differenz wird heute bei dir gebucht:
- Mehr legt die Differenz als Eintrag auf heute, als **Korrektur**, wenn du heute schon Zeit auf der Karte hast, sonst als **nachgetragen**.
- Weniger nimmt Zeit von deinen heutigen Einträgen auf dieser Karte. Weiter als bis null kommst du so nicht; fremde Einträge und frühere Tage bleiben, wie sie sind. Ältere Tage änderst du in der [Liste der Einträge](#eintraege).
- Das Feld ist gesperrt, solange dein Timer auf dieser Karte läuft, und ohne das Recht **Eigene Zeit buchen**.

Daneben steht die **Schätzung**: wie lange die Karte voraussichtlich dauert, etwa 3:00 oder 2,5. Ein leeres Feld entfernt sie. Ändern braucht das Recht **Karten bearbeiten**. Mit Schätzung zeigt ein Balken unter der Zeit, wie viel davon schon verbraucht ist; der Hinweis am Balken nennt die Prozent. Über der Schätzung wird der Balken zur Warnfarbe, der Zeitknopf auf der Karte wird rot, und Heute schreibt **überschritten**.

## Zeit nachtragen {#nachtragen}
Für Zeit ohne Timer, etwa ein Telefonat von gestern, trägst du einen Eintrag von Hand nach. Er bekommt die Herkunft **nachgetragen** und gehört dir. Jeder Eintrag ist länger als null und höchstens 24 Stunden lang. Auf eine erledigte Karte kannst du weiter nachtragen, nur auf eine Idee nicht.

### Im Kartendetail
Unter der Ticketzeit stehen ein Datumsfeld (Vorgabe heute), ein Feld für die Dauer und der Knopf **Tag buchen**. Enter im Tag oder in der Dauer bucht ebenfalls. Die Dauer leert sich, sobald gebucht ist. Die Zeile erscheint nur mit dem Recht **Eigene Zeit buchen**.

### Unter Zeiten
Der Knopf **Zeit nachtragen** oben im Stundenzettel oder **Auf diesen Tag nachtragen** unten in der Leiste eines Tags öffnet rechts die Leiste **Nachtragen**:
1. **Karte**: Schlüssel oder Titel eintippen, gesucht wird in allen Boards; jedes Wort muss vorkommen. Es erscheinen bis zu acht Karten, offene vor erledigten. Ideen fehlen, ebenso Boards ohne Zeiterfassung und Boards, in denen du keine Zeit buchen darfst. Das X neben der gewählten Karte wählt eine andere.
2. **Tag**: im Datumsfeld oder mit den Knöpfen **Heute** und **Gestern**.
3. **Dauer** und eine **Notiz**. Neben der Dauer steht, wie die Pinnwand sie gelesen hat. Die Notiz steht im Stundennachweis neben der Karte.

Unten steht vorher die Wirkung: die Zeit der Karte an diesem Tag vorher und nachher und der ganze Tag gegen dein Soll. Im Stundenzettel links erscheint die Buchung schon als Vorschau. **Buchen** (oder Enter in der Dauer) bucht; die Leiste bleibt für die nächste Buchung offen. **Fertig** schließt sie.

### Dauer eingeben
Alle Felder für eine Dauer verstehen dieselben Schreibweisen:
- 1:30 heißt eine Stunde und 30 Minuten, 1:30:15 dazu 15 Sekunden.
- 1,5 oder 1.5 sind anderthalb Stunden; eine Zahl ohne Einheit sind immer Stunden.
- 90m oder 90min sind Minuten, 2h oder 2std Stunden.

Enter oder das Verlassen des Felds übernimmt, Escape verwirft. Was die Pinnwand nicht lesen kann, bleibt rot markiert stehen, statt still zu verschwinden.

## Einträge ändern und löschen {#eintraege}
Im Kartendetail stehen unter der Zeiterfassung alle Einträge der Karte, die du siehst, der neueste Tag zuerst: Tag mit Uhrzeiten, Person, Herkunft und Dauer.
- **Tag ändern**: Ein Klick auf den Tag öffnet ein Datumsfeld; Enter übernimmt, Escape verwirft. Der Eintrag zieht mit Dauer, Uhrzeiten und Herkunft auf den neuen Tag. War er ein Teil einer Sitzung über Mitternacht, verlieren beide Teile ihren Bezug aufeinander.
- **Dauer ändern**: direkt im Feld überschreiben, länger als null und höchstens 24 Stunden. Bei einem Timer-Eintrag rückt das Ende mit.
- **Löschen**: das X am Ende der Zeile. Rückgängig bringt den Eintrag genau so zurück, mit Person, Zeiten und Herkunft.
- Einträge anderer zeigen ein Schloss (**Eintrag einer anderen Person**). Ändern und löschen kannst du sie nur mit dem Recht **Zeiten anderer bearbeiten**.

Jede Änderung meldet sich unten mit Rückgängig und steht im Verlauf der Karte. Nur die Notiz eines Eintrags (in der Leiste eines Tags unter **Zeiten**) speichert still, ohne Meldung.

Löschst du die bestätigte Zeit eines Termins, ist auch die Bestätigung zurückgenommen: Der Termin wartet wieder im [Nachtrag](hilfe:serien/nachtrag).

## Stundenzettel {#stundenzettel}
Der Eintrag **Zeiten** in der Seitenleiste öffnet deinen Stundenzettel: deine gebuchte Zeit einer Woche aus allen Boards.
- Oben wählst du die Woche mit den Pfeilen **Vorige Woche** und **Nächste Woche**; **Diese Woche** springt zurück.
- Die Kennzahlen: **Woche** (gebucht von Soll), **Bis heute** (Differenz bis heute, in anderen Wochen **Differenz**), **Überstunden** mit Stand von gestern (nur mit Zeitkonto; mit dem Modul Arbeitszeit führt ein Klick zum Zeitkonto) und dein Timer mit **Läuft seit** oder **Angehalten**.
- Die Tabelle hat je Karte eine Zeile und die Spalten Montag bis Sonntag und **Woche**. Die Karten stehen nach Board und Nummer, darunter bestätigte Termine als eigene Zeilen, zuletzt Karten, die nicht mehr im Board stehen (im Papierkorb, entfernt oder archiviert).
- Jede Zelle ist deine Zeit auf der Karte an diesem Tag und direkt änderbar. Mehr bucht die Differenz auf genau diesen Tag. Weniger kürzt deine Einträge dieses Tags in dieser Reihenfolge: erst Korrekturen, dann nachgetragene, dann Einträge aus Serien, zuletzt Timer-Einträge, jeweils der jüngste zuerst. Eine leere Zelle oder 0:00 nimmt deine ganze Zeit des Tags von der Karte. Einträge anderer bleiben immer.
- Läuft dein Timer an dem Tag auf der Karte, zeigt die Zelle einen Punkt und lässt sich erst nach dem Anhalten ändern.
- Am Anfang jeder Zeile sitzt der Timer-Knopf. Ein leerer Platz dort heißt **Kein Timer: erledigt, Idee oder nicht mehr im Board; nachtragen geht**.
- In Termin-Zeilen lässt sich die Zeit nicht in der Zelle ändern; löschen geht in den Einträgen des Tags.
- Unten stehen **Summe**, **Soll** aus deinem [Zeitkonto](hilfe:arbeitszeit/zeitkonto) und **Differenz**. Für heute zeigt die Differenz **noch** und die fehlende Zeit, solange das Soll nicht erreicht ist. Im Kopf einer Tagesspalte steht, was das Soll ändert: ein Feiertag, eine Abwesenheit, ein halber Tag oder ein freier Tag.

Im Kopf jeder Seite siehst du außerdem **Heute** und **Woche**, jeweils gebucht gegen Soll. Ein Klick darauf öffnet den Stundenzettel.

## Einträge eines Tags {#tagesleiste}
Ein Klick auf einen Tag im Kopf des Stundenzettels öffnet rechts die Leiste **Einträge** mit deinen Einträgen dieses Tags. Mit den Pfeilen gehst du zum Vortag oder Folgetag, das X schließt die Leiste.
- Oben stehen **Ist**, **Soll** und **Differenz** (heute **Bisher**), darunter der Grund für das Soll, etwa ein Feiertag, eine Abwesenheit, ein halber Arbeitstag, **Wochenende**, **Kein Arbeitstag in deinem Zeitkonto** oder **Ohne Zeitkonto**.
- Jeder Eintrag zeigt Karte oder Termin, die Uhrzeiten (oder **ohne Uhrzeit**), die Herkunft, die Dauer zum Ändern und ein Feld für eine **Notiz**. Das X löscht ihn mit Rückgängig. Die Dauer eines Termins ist fest.
- Spuren der Buchungsregeln stehen am Eintrag: **Sitzungen zusammengefasst** (der Hinweis nennt die einzelnen Sitzungen), **über Mitternacht, Teil am** (ein Klick springt zum anderen Teil) und **nach 12 Stunden gedeckelt** mit der [Rückfrage](#deckel) oben in der Leiste.
- Läuft dein Timer an diesem Tag, steht er als eigene Zeile **läuft** mit einem Knopf zum Anhalten. Beim Anhalten kommt seine Zeit in den Timer-Eintrag der Karte für diesen Tag.
- Unten führt **Auf diesen Tag nachtragen** zur Leiste [Nachtragen](#nachtragen) mit diesem Tag.

## Geteilte Zeit verknüpfter Karten {#geteilte-zeit}
Verknüpfte Arbeitskarten bilden eine Gruppe (siehe [Das Kartendetail](hilfe:kartendetail)). Im Abschnitt **Verknüpfte Aufgaben** des Kartendetails steht dann der Schalter **Zeit teilen**: Die Gruppe zeigt ihre gemeinsame Zeit; gebucht wird je Karte. Eine neue Gruppe teilt ihre Zeit von Anfang an.
- Ist der Schalter an, zeigt der Zeitknopf jeder Karte der Gruppe im Board die Zeit der ganzen Gruppe; sein Hinweis sagt **Zeit der Gruppe**. Auch die rote Markierung über der Schätzung richtet sich dort nach dieser Zeit.
- Im Kartendetail steht unter der Ticketzeit **Zusammen mit der Gruppe** und die gemeinsame Zeit; jede Sekunde zählt einmal.
- Gebucht wird weiter auf die Karte, auf der der Timer läuft oder auf die du nachträgst.
- Ist der Schalter aus, zeigt jede Karte nur ihre eigene Zeit.

Den Schalter umlegen kann, wer im Board **Karten bearbeiten** darf. Verknüpfst du zwei Karten, die schon in verschiedenen Gruppen sind, gilt die Einstellung der Gruppe der Karte, von der aus du verknüpfst; waren beide verschieden eingestellt, sagt es die Meldung.
