---
titel: Heute
untertitel: deine Karten und Termine aus allen Boards auf einen Blick
bereich: Grundlagen
symbol: fa-calendar-day
---
**Heute** sammelt alles, was für dich ansteht, aus allen Boards, in denen du Mitglied bist: deine Karten nach
Fälligkeit, deinen Timer, deine Termine und die Karten deiner Serien. Hier hakst du ab, startest Timer und sagst Termine
zu, ohne jedes Board einzeln zu öffnen. Die Pinnwand startet mit dieser Seite.

## Aufbau der Seite {#aufbau}
Du öffnest **Heute** in der Seitenleiste ganz oben.

- Im Kopf stehen das Datum und woraus die Seite besteht, etwa "deine Karten, Termine und Serien aus 3 Boards".
- Hast du einen Timer, steht er groß unter dem Kopf (siehe [Dein Timer](hilfe:heute/timer)).
- Links stehen deine Karten in Abschnitten nach Fälligkeit (siehe [Die Abschnitte](hilfe:heute/abschnitte)).
- Rechts stehen **Termine heute** und **Serien heute**, wenn eines deiner Boards das Modul Serien und Termine an hat.
  Sonst nehmen die Karten die ganze Breite.

In **Heute** stehen nur Karten, für die du **zuständig** bist, also die dir zugewiesen sind, und nur offene: Karten in
einer Erledigt-Spalte stehen hier nicht. Jede Karte steht genau einmal. Innerhalb eines Abschnitts ordnet die
Pinnwand nach dem Fälligkeitstag, bei gleichem Tag nach der Priorität (Dringend zuerst). Was dir jemand zuweist,
erscheint sofort.

## Die Abschnitte {#abschnitte}
| Abschnitt | Was darin steht |
|---|---|
| **Überfällig** | Karten, deren Fälligkeitstag vor heute liegt; der Abschnitt ist rot, sobald er etwas enthält |
| **Heute** | Karten, die heute fällig sind (ohne Karten aus Serien) |
| **Diese Woche** | Karten, die in den nächsten sieben Tagen fällig sind |
| **Liegengeblieben** | Karten, die so lange in ihrer Spalte stehen, dass sie die Stufe **Gefahr ab** ihres Boards erreicht haben, und auf denen kein Timer läuft |
| **Blockiert** | Karten, die als blockiert markiert sind, mit Grund |
| **Ohne Datum** | Karten ohne Fälligkeitstag |

Dazu gelten diese Regeln:

- Ist keine Karte überfällig, heute oder diese Woche fällig und keine Serie heute dran, steht statt der ersten drei
  Abschnitte "Heute ist nichts fällig".
- **Liegengeblieben** und **Blockiert** erscheinen nur, wenn sie etwas enthalten. **Ohne Datum** steht immer da.
- Liegengeblieben, Blockiert und Ohne Datum nehmen nur Karten auf, die nicht schon wegen ihrer Fälligkeit oben stehen.
  Eine Karte, die liegt, steht nicht noch einmal unter Blockiert oder Ohne Datum.
- Eine Karte mit einem Fälligkeitstag, der mehr als sieben Tage entfernt ist, erscheint erst, wenn sie in die Woche
  rückt, es sei denn, sie ist liegengeblieben oder blockiert.
- Ab wann eine Karte liegt, stellt jedes Board selbst ein: in seinen Einstellungen, Reiter **Allgemein**, unter
  **Alterung der Karten** bei **Gefahr ab** (Tage seit dem letzten Spaltenwechsel). Steht dort 0, gilt keine Karte des
  Boards als liegengeblieben.

## Eine Karte in Heute {#zeile}
Jede Zeile zeigt links den Haken zum Abhaken, in der Mitte Schlüssel und Titel und darunter die Angaben:

- das Board mit seinem Farbpunkt,
- die Fälligkeit: "heute", "morgen", ein Datum oder "3 Tage über"; von heute bis übermorgen gelb, überfällig rot,
- **Blockiert**, wenn die Karte blockiert ist (der Grund steht im Hinweis beim Darüberzeigen),
- die Sanduhr "liegt ... Tage", sobald die Karte die Warnstufe der Alterung ihres Boards erreicht,
- den Stand der Checkliste, etwa 2/5,
- die Kürzel der anderen Personen, die auch zuständig sind.

Ein Klick auf den Titel öffnet die Karte in ihrem Board. Rechts steht der Knopf des Timers (siehe
[Dein Timer](hilfe:heute/timer)) oder, bei einer Idee, das Zeichen **Idee**.

## Abhaken {#abhaken}
Der Haken links in der Zeile erledigt die Karte: sie kommt in die Erledigt-Spalte ihres Boards. Zeigst du auf den
Haken, steht dort, wohin, etwa "Erledigt: nach Erledigt in Projekt".

- Die Karte verschwindet aus **Heute**; die Meldung unten bietet **Rückgängig** an.
- Läuft auf der Karte ein Timer, endet er dabei, und die Zeit wird gebucht.
- Mit der Karte verknüpfte Karten desselben Boards ziehen mit.
- Du brauchst im Board das Recht **Karten verschieben**. Fehlt es, meldet die Pinnwand "Verschieben abgelehnt: dir
  fehlt in diesem Board das Recht Karten verschieben".

## Dein Timer {#timer}
Diesen Teil gibt es, wenn eines deiner Boards die Zeiterfassung an hat. Jede Person hat genau einen Timer, der läuft
oder angehalten ist.

Hast du einen Timer, steht er oben über den Abschnitten: "Läuft seit 09:12" oder "Angehalten, die Sitzungen sind
gebucht", dazu Karte, Board und die gebuchte Zeit der Karte. Hat die Karte eine Schätzung, zeigt ein Balken, wie viel
davon verbraucht ist, etwa "40 % von 2:30", und "überschritten", wenn es mehr ist.

- **Anhalten** bucht die laufende Sitzung; der Timer bleibt auf der Karte.
- **Fortsetzen** lässt ihn auf derselben Karte weiterlaufen.
- **Stoppen** bucht die Sitzung und beendet den Timer.

Rechts in jeder Zeile steht der Knopf des Timers dieser Karte:

| Lage | Was dort steht | Ein Klick |
|---|---|---|
| Dein Timer läuft auf der Karte | Pause mit der laufenden Zeit | hält an und bucht |
| Dein Timer ist auf der Karte angehalten | Dreieck mit der Zeit | setzt ihn fort |
| Der Timer einer anderen Person läuft | Kreis mit der Zeit, ohne Knopf | nichts |
| Kein Timer, aber einer ist erlaubt | **Start** oder, wenn schon Zeit gebucht ist, Dreieck mit der Zeit | startet deinen Timer; dein Timer auf einer anderen Karte endet dabei und bucht |

Starten lässt sich ein Timer nur auf einer Karte, die Arbeit ist, nicht erledigt ist, in einem Board mit
Zeiterfassung liegt und für die du dort das Recht **Eigene Zeit buchen** hast. Mehr unter
[Zeiterfassung](hilfe:zeiterfassung).

## Termine {#termine}
Mit dem Modul Serien und Termine steht rechts **Termine heute**: deine Termine von heute, also die, bei denen du
Teilnehmer bist. Darunter folgen unter **Nächste sieben Tage** die Termine der kommenden Woche mit ihrem Tag.

Jeder Termin zeigt Beginn und Ende, Titel, Board, Ort und die Teilnehmer. Mit **Zusagen** sagst du zu; danach steht
dort **zugesagt**. Wer einen Termin anlegt und selbst teilnimmt, hat schon zugesagt. Ein Klick auf den Titel führt zu
**Serien und Termine** (siehe [Serien und Termine](hilfe:serien)).

## Serien heute {#serien}
Unter **Serien heute** stehen die Karten aus Serien, die heute fällig sind und für die du zuständig bist. Statt der
Fälligkeit zeigt jede Zeile die Uhrzeit der Serie. Abhaken und Timer funktionieren wie bei jeder anderen Karte. Die
Karten der Serientage legt die Pinnwand jeden Tag selbst an; wie Serien entstehen, steht unter
[Serien und Termine](hilfe:serien).

## Tagesplan vorlesen {#vorlesen}
Hat eines deiner Boards das Modul Vorlesen an und ist die Vertonung angebunden, steht im Kopf der Knopf
**Vorlesen**. Er liest deinen Tagesplan vor:

1. den Tag mit Wochentag und Datum,
2. was überfällig ist, je mit "fällig seit" und dem Tag,
3. was heute fällig ist,
4. die Karten aus Serien von heute mit ihrer Uhrzeit,
5. deine Termine von heute mit Beginn, Ende und Ort.

Steht nichts davon an, hörst du "Heute ist nichts fällig und nichts überfällig." Während des Lesens heißt der Knopf
**Stopp**; ein zweiter Klick hält an. Was sonst vorgelesen werden kann, steht unter [Vorlesen](hilfe:vorlesen).

## Ohne Verbindung {#ohne-verbindung}
Reißt die Verbindung zum Server ab, steht oben der Kasten "Keine Verbindung zum Server." Du siehst weiter den letzten
Stand, aber Haken, Timer und **Zusagen** sind gesperrt, damit nichts nur scheinbar gespeichert wird. Die Pinnwand
verbindet sich von selbst neu; danach geht alles wieder.

Am Telefon hat **Heute** eine eigene, schmale Form (siehe [Am Telefon](hilfe:telefon/heute)).
