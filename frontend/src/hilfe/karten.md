---
titel: Karten anlegen und bewegen
untertitel: Anlegen, ziehen, verknüpfen, umziehen und wegwerfen
bereich: Boards
symbol: fa-note-sticky
---
Eine Karte ist eine Aufgabe oder eine Idee. Hier steht, wie du Karten anlegst, durch die Spalten bewegst, miteinander verknüpfst, in ein anderes Board bringst, kopierst und wieder loswirst.

## Karte anlegen {#anlegen}
1. Am Fuß einer offenen Spalte auf **Karte** klicken.
2. Den Titel tippen; Enter oder **Anlegen** legt die Karte an.
3. Das Feld bleibt offen für die nächste Karte. **Schließen** oder Escape schließt es; was noch im Feld steht, wird verworfen.

Die neue Karte kommt ans Ende der Spalte, und du bist für sie zuständig. Unter dem Feld steht, welchen Schlüssel sie bekommt und wo sie landet, etwa "PROD-132 in Offen". Nummern vergibt die Pinnwand fortlaufend je Board und nie zweimal, auch nicht nach dem Löschen. Lehnt die Pinnwand ab, steht dein Titel wieder im Feld, und die Meldung nennt den Grund. Liegt die Spalte danach über ihrer Grenze, sagt es die Meldung ebenfalls.

Karten anlegen darf, wer im Board das Recht Karten anlegen hat. Neue Karten entstehen in den offenen Spalten; am Fuß der Erledigt-Spalte stehen stattdessen der Weg ins Archiv und, wenn es weitere erledigte Karten gibt, **Mehr laden**.

## Arbeit oder Idee {#art}
Jede Karte ist entweder **Arbeit** oder **Idee**. Auf einer Arbeitskarte lässt sich Zeit erfassen, und sie lässt sich mit anderen Arbeitskarten verknüpfen. Eine Idee ist ein Gedanke ohne Zeiterfassung; sie trägt auf dem Board die Marke **Idee** mit Glühbirne.

- Hat das Board das Modul Zeiterfassung, wählst du beim Anlegen mit dem Umschalter **Arbeit** oder **Idee** unter dem Titelfeld.
- Sonst bekommt eine neue Karte die Art, die in den Einstellungen des Boards unter **Neue Karten sind** steht.
- Im Kartendetail schaltest du die Art jederzeit oben im Kopf um. Wird eine Arbeitskarte zur Idee, halten laufende Timer auf ihr an und buchen.

## Karten aus Text {#aus-text}
Hat das Board das Modul KI an der Karte und ist es eingerichtet, steht unter dem Titelfeld der Knopf **Aus Text**. Damit machst du aus einer Notiz, einer Nachricht oder einer Liste mehrere Karten auf einmal:

1. **Aus Text** klicken und den Text in das große Feld schreiben oder einfügen.
2. **Vorschlagen** klicken oder Strg und Enter drücken. Das Rechnen kann einen Moment dauern; **Abbrechen** hält an.
3. Der Vorschlag listet die Karten mit Titel und, falls vorhanden, Beschreibung und Zahl der Checklistenpunkte. Das Häkchen vor einer Karte nimmt sie heraus oder wieder hinein, ihren Titel kannst du direkt ändern.
4. **Anlegen** legt alle angehakten Karten am Ende dieser Spalte an, mit Beschreibung und Checkliste, höchstens 50 auf einmal. Ein einziges **Rückgängig** nimmt alle zurück.

**Verwerfen** schließt den Vorschlag. Ging etwas schief, nennt der Kasten den Grund, und **Noch einmal** fragt erneut. **Einzeln anlegen** führt zurück zum einfachen Titelfeld. Mehr dazu unter [KI an der Karte](hilfe:ki).

## Karten ziehen {#ziehen}
Zieh eine Karte mit der Maus an eine andere Stelle derselben Spalte oder in eine andere Spalte. Ein gestrichelter Platzhalter zeigt, wo sie landet. Kommt sie in eine andere Spalte:

- beginnt ihr Alter, die Sanduhr, neu;
- ziehen verknüpfte Karten desselben Boards mit und reihen sich am Ende der Zielspalte ein (siehe [Verknüpfen](hilfe:karten/verknuepfen));
- bekommen ihre Zuständigen einen Hinweis, dass sie verschoben wurde;
- vermerkt der Verlauf der Karte den Wechsel;
- nennt die Meldung, wenn die Zielspalte danach über ihrer Grenze liegt; aufgehalten wird nichts.

Auch eingeklappte Spalten nehmen Karten an. Ziehen geht mit dem Recht Karten verschieben, und nicht, solange eine Suche, ein Filter oder eine Sortierung außer Manuell gilt (siehe [Verschieben pausiert](hilfe:filter/pausiert)).

Ohne Ziehen geht es auch: im Kartendetail stellt **Status** die Spalte um, in der Liste **Verschieben nach ...**. Die Karte kommt dann ans Ende der Spalte; sonst gilt dasselbe wie beim Ziehen.

## Nach Erledigt legen {#erledigen}
Ziehst du eine Karte in die Erledigt-Spalte oder stellst ihren Status darauf:

- bekommt sie das Abschlussdatum von heute, eine Karte aus einer Serie ihren Termintag;
- halten laufende Timer auf ihr an und buchen; stoppt dabei dein eigener Timer, nennt die Meldung die gebuchte Zeit;
- steht sie oben in der Erledigt-Spalte, die nach Abschluss geordnet ist und sich nicht von Hand umsortieren lässt;
- werden verknüpfte Karten mit erledigt;
- wandert sie nach der Archivgrenze des Boards von selbst ins Archiv.

Holst du sie zurück in eine offene Spalte, ist sie wieder offen, und das Abschlussdatum entfällt.

## Verknüpfen: Karten ziehen zusammen {#verknuepfen}
Arbeitskarten desselben Boards lassen sich zu einer Gruppe verknüpfen, etwa die Teilaufgaben eines Auftrags. Verknüpfte Karten ziehen zusammen: bewegst du eine in eine andere Spalte, folgen die anderen. Eine Kette mit Zahl auf jeder Karte der Gruppe zeigt, wie viele dazugehören.

So verknüpfst du im Board:

1. Mit der Maus über eine Arbeitskarte fahren; oben rechts erscheint die Kette (**Auf eine andere Arbeitskarte ziehen: beide werden verknüpft, ziehen zusammen und teilen ihre Zeit; daneben loslassen bricht ab**).
2. Die Kette greifen und auf eine andere Arbeitskarte desselben Boards ziehen. Eine Marke folgt dem Zeiger: **Auf eine Arbeitskarte ziehen**, über einer passenden Karte **Hier verknüpfen** mit deren Schlüssel.
3. Loslassen verknüpft beide. Daneben loslassen oder Escape bricht ab.

Karten in eingeklappten Spalten sind kein Ziel. Hat eine der beiden Karten schon eine Gruppe, tritt die andere bei; haben beide eine, gehen die Gruppen in einer auf. Eine neue Gruppe teilt ihre Zeit: jede Karte zeigt die Zeit der ganzen Gruppe, und jede Sekunde zählt einmal. Gebucht wird weiter je Karte. Im Kartendetail verknüpfst und löst du unter **Verknüpfte Aufgaben**, dort schaltet auch **Zeit teilen** (siehe [Verknüpfte Aufgaben](hilfe:kartendetail/verknuepft)). Verknüpfen braucht das Recht Karten bearbeiten.

## In den Papierkorb und zurück {#papierkorb}
Eine Karte legst du an drei Stellen in den Papierkorb:

- im Board über den Papierkorb oben rechts auf der Karte, der beim Überfahren erscheint;
- im Kartendetail unten mit **In den Papierkorb**;
- in der Liste als Sammelaktion.

Die Karte verschwindet aus dem Board und liegt mit Zeiten, Kommentaren, Anhängen und Verknüpfung im Papierkorb des Boards. Die Meldung unten bietet sofort **Rückgängig**. Laufende Timer auf ihr halten an und buchen. Ist sie die Karte eines Serientags, legt die Serie diesen Tag nicht noch einmal an; stellst du die Karte wieder her, gehört der Tag wieder zur Serie.

Später holst du sie über den Knopf **Papierkorb** in der Werkzeugleiste des Boards mit **Wiederherstellen** zurück, an ihre alte Stelle und mit demselben Schlüssel (siehe [Papierkorb des Boards](hilfe:board/papierkorb)). Hineinlegen und Wiederherstellen braucht das Recht Karten löschen.

### Endgültig löschen

Im Kartendetail unten steht neben **In den Papierkorb** auch **Endgültig löschen**. Die Karte geht dann sofort und ohne Rückweg, ohne Papierkorb, mit Checkliste, Kommentaren, Anhängen und Verlauf; ein laufender Timer bucht vorher. Gebuchte Zeiten bleiben unter ihrem Namen stehen; war es nur ein Versuch, löschst du deine danach unter Zeiten ([Zeit gelöschter Karten](hilfe:zeiterfassung/entfernt)). Zur Sicherheit tippst du den Schlüssel der Karte ein, etwa HAUS-4; erst dann wirkt der Knopf. Das braucht die Rechte Karten löschen und Papierkorb leeren.

## Archiv {#archiv}
Erledigte Karten wandern von selbst ins Archiv des Boards, sobald ihr Abschluss länger zurückliegt als **Archiv ab** in den Einstellungen des Boards. Dort bleiben sie mit allem erhalten, und ihr Verweis führt weiter zu ihnen. Um eine archivierte Karte wieder ins Board zu holen, öffnest du sie im Archiv und stellst im Kartendetail ihren **Status** auf eine offene Spalte. Mehr unter [Archiv](hilfe:board/archiv).

## In ein anderes Board umziehen {#umziehen}
Eine Karte zieht in ein anderes Board, etwa vom Ideenboard aufs Arbeitsboard:

1. Im Kopf des Kartendetails den Knopf mit den zwei Pfeilen klicken (**In ein anderes Board, etwa vom Ideenboard aufs Arbeitsboard**).
2. Das Ziel-Board wählen; angeboten werden nur Boards, in denen du Karten anlegen darfst.
3. Eine Spalte des Ziel-Boards anklicken. Die Karte zieht sofort um, und das Detail folgt ihr.

Dabei gilt:

- Sie bekommt im neuen Board die nächste Nummer und dessen Art neuer Karten (Arbeit oder Idee). Ihr alter Schlüssel führt weiter zu ihr.
- Labels und eigene Felder bleiben, wenn das Ziel welche mit gleichem Namen hat, bei Feldern von gleicher Art und bei einer Auswahl mit derselben Option. Die übrigen entfallen; die Meldung nennt, wie viele.
- Zuständige bleiben, wenn sie im neuen Board Mitglied sind.
- Inhalt, Checkliste, Kommentare, Anhänge, Verlauf und gebuchte Zeit ziehen mit. Laufende Timer halten an und buchen.
- Eine Verknüpfung endet; eine Karte aus einer Serie zieht als einfache Karte um, und die Serie legt diesen Tag nicht wieder an.

Umziehen braucht im alten Board das Recht Karten löschen und im neuen das Recht Karten anlegen. Den Knopf siehst du nur, wenn es ein solches Ziel gibt.

## Duplizieren {#duplizieren}
Der Knopf mit den zwei Blättern im Kopf des Kartendetails (**Duplizieren: Kopie in derselben Spalte, ohne Zeiten, Kommentare und Anhänge**) legt eine Kopie am Ende derselben Spalte an und öffnet sie. Die Kopie heißt wie das Original mit "(Kopie)" dahinter, bekommt die nächste Nummer und übernimmt Inhalt und Angaben; alle Punkte der Checkliste sind wieder offen. Ohne Kopie bleiben Zeiten, Kommentare, Anhänge, Blockade, Transkripte, Verknüpfung und Serie. Duplizieren braucht das Recht Karten anlegen.

## Schlüssel kopieren {#kennung}
Ein Klick auf den Schlüssel einer Karte, etwa HAUS-12, legt ihn in die Zwischenablage: auf der Karte im Board, im Kopf
des Kartendetails und am Telefon oben im Kopf der Karte. Die Karte öffnet sich dabei nicht; die Meldung sagt
"HAUS-12 kopiert". So zeigst du jemandem schnell, welche Karte du meinst.

## Verweis kopieren {#verweis}
Der Knopf mit der Kette im Kopf des Kartendetails (**Verweis kopieren**) legt die Adresse der Karte in die Zwischenablage, etwa zum Einfügen in eine Nachricht. Wer sie öffnet und Mitglied des Boards ist, landet direkt bei der Karte, auch wenn sie inzwischen im Archiv liegt. Die Meldung zeigt die kopierte Adresse; klappt das Kopieren nicht, steht die Adresse dort zum Abschreiben.
