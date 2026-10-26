---
titel: Arbeitszeit
untertitel: Zeitkonto, Urlaub, Feiertage und Team
bereich: Zeit
symbol: fa-calendar-check
---
Das Zeitkonto rechnet aus, wie viel du arbeiten sollst (das Soll), wie viel du gebucht hast (das Ist) und was daraus an Überstunden und Resturlaub folgt. Es gehört dir als Person, nicht einem Board: Gebuchte Zeit aus allen Boards fließt hinein, Urlaub und andere Abwesenheiten trägst du hier ein.

## Arbeitszeit öffnen {#aufruf}
Den Eintrag **Arbeitszeit** in der Seitenleiste gibt es, sobald eines deiner Boards das Modul **Arbeitszeit und Urlaub** eingeschaltet hat (siehe [Module](hilfe:module)). Oben stehen vier Reiter, jeder mit eigener Adresse:

| Reiter | Wofür |
|---|---|
| **Zeitkonto** | Soll und Ist, Überstunden, Resturlaub, Einstellungen |
| **Kalender** | Jahreskalender mit Feiertagen und Abwesenheiten; Tage anklicken oder ziehen |
| **Urlaub** | Urlaub und Abwesenheit eintragen, Wirkung auf das Soll, Brückentage |
| **Team** | Anwesenheit und Auslastung der Mitglieder eines Boards |

Kalender und Urlaub brauchen ein Zeitkonto, weil Bundesland und Arbeitstage darüber bestimmen. Ohne Zeitkonto steht dort **Noch kein Zeitkonto.** mit dem Knopf **Zum Zeitkonto**. Du änderst immer nur dein eigenes Zeitkonto und deine eigenen Abwesenheiten.

## Zeitkonto einstellen {#einstellen}
Im Reiter **Zeitkonto** steht der Bereich **Zeitkonto einstellen**:
- **Wochenstunden**: das Soll der Woche, gleich verteilt auf die Arbeitstage (0 bis 80, Komma erlaubt).
- **Arbeitstage**: die Knöpfe Montag bis Sonntag. Daneben steht, wie viel Soll das je Tag ergibt; andere Tage sind frei.
- **Bundesland**: bestimmt die Feiertage. Ohne Bundesland lässt sich nicht speichern.
- **Urlaubsanspruch**: Urlaubstage im Jahr.
- **Resturlaub** des Vorjahrs: der Übertrag aus dem letzten Jahr.
- **Halbe Tage**: Tage, die jedes Jahr nur ein halber Arbeitstag sind, etwa der 24.12. Trage Tag und Monat als TT.MM. und einen Namen ein und klicke **Tag**; das X entfernt einen halben Tag wieder. An diesen Tagen ist das Soll halb, und ein Urlaubstag zählt dort halb.

Unten wählst du bei **Gilt ab**, ab welchem Tag die Einstellung gilt, und klickst **Speichern**. Jede Speicherung ist eine neue Fassung: Sie gilt ab ihrem Tag bis zur nächsten. Frühere Tage behalten ihr Soll, deine Überstunden ändern sich also nicht rückwirkend. Speicherst du eine Fassung mit demselben Tag wie eine vorhandene, ersetzt sie diese.

Die Liste **Fassungen** zeigt alle Fassungen mit Stunden und Arbeitstagen; die heute gültige trägt **gilt heute**. Als Tag schlägt die Pinnwand den Montag der nächsten Woche vor, bei der ersten Fassung den 1. Januar des laufenden Jahres. Vor der ersten Fassung gibt es kein Soll.

## Soll und Ist {#soll}
Das Soll eines Tags entsteht aus der Fassung, die an diesem Tag gilt, in dieser Reihenfolge:
1. Ist der Tag kein Arbeitstag in deinem Zeitkonto (Wochenende oder arbeitsfrei), ist das Soll null.
2. Ist der Tag ein Feiertag in deinem Bundesland, ist das Soll null.
3. Ist der Tag einer deiner halben Tage, ist das Soll halb so groß.
4. Hast du eine Abwesenheit, wirkt sie nach ihrer Art auf das Soll (siehe [Abwesenheiten](#abwesenheiten)).

An einem gewöhnlichen Arbeitstag ist das Soll die Wochenstunden geteilt durch die Zahl der Arbeitstage.

Das Ist eines Tags ist alles, was du an diesem Tag gebucht hast, aus allen Boards: Timer, nachgetragene Zeit, bestätigte Serien und Termine, dazu ein gerade laufender Timer. Wie du Zeit buchst, steht unter [Zeiterfassung](hilfe:zeiterfassung).

**Überstunden** sind Ist minus Soll vom 1. Januar bis gestern. Der laufende Tag zählt erst am nächsten Tag mit, darum steht dabei **Stand** und das Datum von gestern.

## Zeitkonto ansehen {#zeitkonto}
Oben im Reiter **Zeitkonto** stehen die Kennzahlen:
- **Heute**, **Woche**, der laufende Monat und das Jahr: jeweils gebucht und darunter **von** dem Soll. Läuft dein Timer, steht bei Heute **Timer läuft**.
- **Überstunden**: grün ab null, rot darunter.
- **Resturlaub**: Anspruch und Übertrag aus dem Vorjahr minus der Urlaub, den du bis heute genommen hast. Darunter **davon** geplanter Urlaub nach heute und was dann noch **frei** zu verplanen ist. Ein Klick führt zum Reiter Urlaub.

Die Tabelle **Monate** zeigt je Monat **Soll**, **Ist**, **Differenz** und **Überstunden** als laufenden Stand seit Jahresbeginn. Der laufende Monat zählt bis gestern, spätere Monate tragen **geplant** und nur ihr Soll.

Ohne Zeitkonto steht statt der Zahlen ein Hinweis, und die Einstellungen darunter legen die erste Fassung an.

## Abwesenheiten {#abwesenheiten}
Jede Abwesenheit hat einen Zeitraum, eine Art und eine Notiz. Die Art bestimmt ihre Wirkung:

| Art | Wirkung |
|---|---|
| **Urlaub** | Soll entfällt, zählt als Urlaubstag |
| **Krank** | Soll entfällt, kein Urlaubstag |
| **Frei (Ausgleich)** | Soll bleibt, baut Überstunden ab |
| **Fortbildung** | Soll entfällt, kein Urlaubstag |

Regeln dazu:
- Der Schalter **Halbe Tage** lässt jeden Tag des Zeitraums halb zählen, für Soll und Urlaub. Bei Frei (Ausgleich) gibt es ihn nicht.
- Wochenenden, freie Tage und Feiertage zählen nie als Urlaubstag. An einem deiner halben Tage zählt ein Urlaubstag halb.
- Überschneidet sich eine neue Abwesenheit mit vorhandenen, ersetzt sie diese ganz, auch mit ihren Tagen außerhalb des neuen Zeitraums. Die Wirkung nennt sie vorher unter **Ersetzt**; trage übrige Tage danach neu ein.
- **Eintragen** bleibt grau, wenn im Zeitraum kein Arbeitstag liegt.
- Eine ganztägige Abwesenheit nimmt dich ab heute aus noch unberührten Karten von Serien an diesen Tagen; bleibt niemand übrig, fällt die Karte weg. Die Meldung sagt, wie viele es waren. Mehr dazu unter [Teilnehmer einer Serie](hilfe:serien/teilnehmer).
- Jede Änderung meldet sich unten mit Rückgängig.

## Urlaub eintragen {#urlaub}
Im Reiter **Urlaub** trägst du links unter **Eintragen** ein: **Von**, **Bis**, die Art, wenn nötig **Halbe Tage**, eine Notiz, dann **Eintragen**. Liegt Bis vor Von, steht **Bis liegt vor Von.**

Rechts steht schon beim Tippen die **Wirkung**:
- **Arbeitstage** im Zeitraum und wie viel **Soll** entfällt (oder **bleibt**).
- Bei Urlaub die **Urlaubstage** und **Frei verplanbar** vorher und nachher; rot, wenn der Urlaub nicht reicht.
- Ein Hinweis **Ersetzt**, wenn eine vorhandene Abwesenheit wegfällt.
- Darunter jeder Tag einzeln, etwa Soll 8:00 auf 0:00, Wochenende oder Feiertag.

**Brückentage** schlägt die Pinnwand von heute bis Ende nächsten Jahres vor: ein Arbeitstag, dessen beide Nachbartage frei sind (Feiertag oder kein Arbeitstag) und neben dem ein Feiertag liegt. Jeder Vorschlag nennt den Feiertag und wie viele freie Tage am Stück er bringt. **Übernehmen** füllt das Formular mit diesem Tag, Art Urlaub und der Notiz Brückentag; eingetragen ist er erst mit **Eintragen**.

Die Liste **Abwesenheiten** des Jahres zeigt Zeitraum, Art, Arbeitstage, Urlaub, Wirkung auf das Soll und Notiz. Künftige tragen **geplant** und lassen sich mit dem X entfernen, mit Rückgängig. Vergangene und laufende entfernst du im [Jahreskalender](#kalender).

## Jahreskalender {#kalender}
Der Reiter **Kalender** zeigt zwölf Monate mit Kalenderwochen. Mit den Pfeilen wechselst du das Jahr; daneben steht, für welches Bundesland die Feiertage gelten. Farben zeigen Feiertage, halbe Tage, Wochenenden und jede Art von Abwesenheit, die Legende rechts erklärt sie. Unter jedem Monat stehen seine Einträge in Worten. Fährst du über einen Tag, nennt der Hinweis, was er ist und welches Soll er hat.

So trägst du ein:
1. Klicke einen Tag an oder ziehe mit gedrückter Maustaste über mehrere Tage, auch über Monatsgrenzen.
2. Rechts erscheint die **Auswahl** mit Zahl der Arbeitstage und Kalendertage. Wähle die Art, wenn nötig **Halbe Tage** und eine Notiz.
3. Die Wirkung zeigt, wie viel Soll entfällt, bei Urlaub die Urlaubstage und **Frei verplanbar danach**.
4. **Eintragen** trägt ein, **Aufheben** verwirft die Auswahl. Liegen schon Abwesenheiten in der Auswahl, entfernt **Leeren** sie, jeweils ganz und mit Rückgängig.

Der Kasten mit dem Jahr zählt die Tage: Urlaub genommen und geplant, frei verplanbar, Krank, Fortbildung, Frei (Ausgleich) und Feiertage an Arbeitstagen.

## Feiertage {#feiertage}
Die Feiertage richten sich nach dem Bundesland in deinem Zeitkonto. Bundesweit gelten Neujahr, Karfreitag, Ostermontag, Tag der Arbeit, Christi Himmelfahrt, Pfingstmontag, Tag der Deutschen Einheit sowie der 1. und 2. Weihnachtstag. Dazu kommen:

| Feiertag | Bundesländer |
|---|---|
| Heilige Drei Könige (6. Januar) | Baden-Württemberg, Bayern, Sachsen-Anhalt |
| Frauentag (8. März) | Berlin, Mecklenburg-Vorpommern |
| Ostersonntag, Pfingstsonntag | Brandenburg |
| Fronleichnam | Baden-Württemberg, Bayern, Hessen, Nordrhein-Westfalen, Rheinland-Pfalz, Saarland |
| Mariä Himmelfahrt (15. August) | Saarland |
| Weltkindertag (20. September) | Thüringen |
| Reformationstag (31. Oktober) | Brandenburg, Bremen, Hamburg, Mecklenburg-Vorpommern, Niedersachsen, Sachsen, Sachsen-Anhalt, Schleswig-Holstein, Thüringen |
| Allerheiligen (1. November) | Baden-Württemberg, Bayern, Nordrhein-Westfalen, Rheinland-Pfalz, Saarland |
| Buß- und Bettag (Mittwoch vor dem 23. November) | Sachsen |

Ein Feiertag an einem Arbeitstag setzt das Soll auf null und zählt nicht als Urlaubstag. Feiertage stehen außerdem im Stundenzettel, im Kalender eines Boards (je nach Bundesland jedes Mitglieds) und bei den [Serien](hilfe:serien/teilnehmer), die Feiertage ihrer Teilnehmer auslassen können.

## Team {#team}
Der Reiter **Team** zeigt die Mitglieder eines Boards als Tafel: je Person eine Zeile, je Tag eine Spalte, vier Wochen lang.
- Oben wählst du das Board; angeboten werden Boards mit dem Modul Arbeitszeit. Die Pfeile springen **Vier Wochen früher** oder **Vier Wochen später**, **Heute** zurück in die laufende Zeit.
- Unter **Ebenen** schaltest du ein, was die Tafel zeigt: **Anwesenheit** (wer da ist und wer fehlt, mit Art der Abwesenheit), **Feiertage** (im Bundesland jeder Person), **Stunden** (gebuchte Stunden je Tag aus allen Boards) oder **Auslastung** (gebuchte Stunden im Verhältnis zum Soll des Tags). Stunden und Auslastung schließen sich aus.
- Die Kürzel in den Zellen erklärt die Legende darunter. Bei der Auslastung heißt die Farbe unter 90 Prozent, im Soll oder über 105 Prozent des Solls.
- Neben jedem Namen steht, wie viel die Person bis heute im Zeitraum gebucht hat, gegen das Soll bis heute, und wie viele Tage sie abwesend ist.
- Die Tafel zeigt nur Tagessummen, keine einzelnen Einträge. Wer kein Zeitkonto hat, steht darunter als **Ohne Zeitkonto und darum nicht in der Matrix**.

Ohne das Recht **Abwesenheiten sehen** im gewählten Board siehst du nur deine eigene Zeile. Dann steht oben **Nur deine Zeile.** mit deiner Rolle und dem Knopf **Rollen ansehen**.

## Wer was sieht {#sichtbarkeit}
Dein Zeitkonto und deine Abwesenheiten siehst du selbst. Andere sehen sie nur, wenn sie mit dir in einem Board sind, das das Modul Arbeitszeit an hat, und dort das Recht **Abwesenheiten sehen** haben: Urlaub und Abwesenheit der Mitglieder in Kalender und Auslastung sehen.

Mit diesem Recht siehst du in einem Board:
- im Reiter **Team** alle Mitglieder statt nur dich,
- im Kalender des Boards die Abwesenheiten der Mitglieder (siehe [Liste, Kalender und Zeitachse](hilfe:ansichten)),
- bei Terminen, wer an dem Tag abwesend ist,
- im Stundennachweis unter [Berichte](hilfe:berichte/personen) diese Personen, sofern sie ein Zeitkonto haben.

In den Start-Rollen haben **Besitzer** und **Mitglied** das Recht, **Leser** nicht. Rollen stellst du in den [Einstellungen des Boards](hilfe:boardeinstellungen) ein.
