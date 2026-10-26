---
titel: Serien und Termine
untertitel: Wiederkehrende Karten, Termine und der Nachtrag
bereich: Zeit
symbol: fa-repeat
---
Eine Serie legt an festen Tagen von selbst eine Karte in eine Spalte, etwa für die tägliche Abstimmung oder den Monatsabschluss, und bucht den Teilnehmern die geplante Zeit vor. Ein Termin ist ein einmaliges Treffen mit Teilnehmern, ohne Karte. Vorgebuchte Zeit zählt erst, wenn du sie am Folgetag im Nachtrag bestätigst.

## Serien und Termine im Überblick {#uebersicht}
Den Eintrag **Serien und Termine** in der Seitenleiste gibt es, sobald eines deiner Boards das Modul **Serien und Termine** eingeschaltet hat (siehe [Module](hilfe:module)). Die Seite zeigt Serien und kommende Termine aller Boards, in denen du Mitglied bist und das Modul an ist.
- Oben filterst du mit **Alle Boards** oder einem einzelnen Board und mit **Nur meine** (nur Serien und Termine, an denen du teilnimmst).
- Die Tabelle **Serien** zeigt je Serie Rhythmus, Uhrzeit (oder **ganztägig**), Dauer je Tag und Teilnehmer, den nächsten Tag, die Teilnehmer, Board und Zielspalte und den Zustand **aktiv** oder **pausiert**. Fehlen am nächsten Tag Teilnehmer, steht **ohne** und ihre Zahl dabei. Ein heutiger Tag zählt als nächster, solange seine Uhrzeit noch kommt.
- Darunter stehen die **Kommenden Termine** (siehe [Termine](#termine)).
- Wartet vorgebuchte Zeit auf dich, steht ganz oben ein Hinweis mit **Jetzt bestätigen** (siehe [Nachtrag](#nachtrag)).

Serien und Termine anlegen, ändern, pausieren und löschen darf, wer im Board das Recht **Serien und Termine verwalten** hat. In den Start-Rollen sind das **Besitzer** und **Mitglied**. Alle anderen Mitglieder sehen Serien nur an; zusagen und ihre eigene Zeit bestätigen können sie trotzdem.

## Serie anlegen {#anlegen}
Der Knopf **Neue Serie** oben auf der Seite öffnet das Formular. Links stellst du ein, rechts zeigt **So bucht die Serie vor** die Tage mit ihrem Stand. Der Vorschlag: das erste Board, in dem du Serien anlegen darfst, du als Teilnehmer, die erste offene Spalte, wöchentlich am heutigen Wochentag, 30 Minuten.

Im Bereich **Karte**:
- **Titel**: der Titel jeder Karte; die Uhrzeit steht davor.
- **Board**: nur Boards, in denen du das Recht hast. Nach dem Anlegen steht das Board fest. Wechselst du es vorher, springt die Zielspalte auf die erste offene Spalte, die Labels leeren sich, und es bleiben nur Teilnehmer, die dort Mitglied sind.
- **Zielspalte**: eine offene Spalte des Boards; hier legt die Serie ihre Karten an.
- **Labels** und eine Beschreibung jeder Karte (mit Markdown).

Dazu kommen [Rhythmus und Zeitraum](#rhythmus), [Teilnehmer](#teilnehmer) und das [Vorbuchen](#vorbuchen). **Anlegen und vorbuchen** legt die Serie an und sofort die Karten im Vorlauf; der Knopf bleibt grau, solange Titel, Teilnehmer oder Zielspalte fehlen oder die Uhrzeit nicht stimmt. **Abbrechen** verwirft alles.

## Rhythmus und Zeitraum {#rhythmus}
Im Bereich **Rhythmus**:
- **Wie oft**:
  - **Täglich**, mit dem Schalter **Wochenende**: Samstag und Sonntag auslassen.
  - **Werktags**: Montag bis Freitag.
  - **Wöchentlich**: unter **An Tagen** mindestens ein Wochentag.
  - **Monatlich**: unter **Im Monat** entweder **am Tag** mit einer Zahl (hat ein Monat weniger Tage, gilt sein letzter), **erster Werktag** oder **letzter Werktag**. Ein Werktag ist Montag bis Freitag, an dem für keinen Teilnehmer ein Feiertag ist.
- **Uhrzeit**: etwa 07:30. Sie steht vor dem Titel jeder Karte; leer heißt ganztägig.
- **Dauer**: als Stunden:Minuten, von einer Minute bis 24 Stunden. Sie wird die Schätzung jeder Karte und die vorgebuchte Zeit je Teilnehmer.
- **Zeitraum**: der erste mögliche Tag und der letzte mögliche Tag; ein leeres Ende heißt ohne Ende.

## Teilnehmer {#teilnehmer}
Im Bereich **Teilnehmer** fügst du Mitglieder des Boards über die Personensuche hinzu; das X am Namen entfernt sie wieder. Mindestens eine Person nimmt teil. Die Teilnehmer werden die Zuständigen jeder Karte.

Erfasst das Board Zeit, kann nur teilnehmen, wer dort **Eigene Zeit buchen** darf; andere stehen darunter als **ohne Recht, Zeit zu buchen, nicht wählbar**. Jeder Teilnehmer bekommt die Zeit vorgebucht und bestätigt sie am Folgetag selbst.

Wer an einem Tag fehlt, bekommt dort nichts vorgebucht und steht nicht auf der Karte:
- bei einer ganztägigen Abwesenheit (Urlaub, Krank, Frei, Fortbildung; halbe Tage zählen nicht als Fehlen),
- bei einem Feiertag im Bundesland seines Zeitkontos, wenn **Feiertage auslassen** an ist.

Fehlen alle Teilnehmer, entfällt der Tag. Trägt jemand später eine ganztägige Abwesenheit ein, nimmt ihn die Pinnwand ab heute aus den unberührten Karten dieser Tage; bleibt niemand, fällt die Karte weg (siehe [Abwesenheiten](hilfe:arbeitszeit/abwesenheiten)). Wird jemand aus dem Board entfernt, verlässt er auch dessen Serien.

## Wie die Karten entstehen {#vorbuchen}
Jeden Tag legt die Pinnwand für jede aktive Serie die Karten von heute bis zum Ende des Vorlaufs an, je Tag eine. Beim Anlegen, Ändern und Fortsetzen einer Serie geschieht das sofort. Im Verlauf jeder Karte steht **aus der Serie ... angelegt**; bei der täglichen Vorbuchung ist die Pinnwand selbst als Urheber eingetragen.

Im Bereich **Vorbuchen**:
- **Vorlauf**: so viele Tage im Voraus liegen die Karten in der Zielspalte, 0 bis 60 Tage; 0 heißt nur heute.
- **Feiertage auslassen**: nach dem Bundesland jedes Teilnehmers aus seinem Zeitkonto.

Jede Karte eines Serientags bekommt den Titel mit der Uhrzeit davor, Beschreibung und Labels der Serie, die anwesenden Teilnehmer als Zuständige, den Tag als Fälligkeit und die Dauer als Schätzung. Auf der Karte im Board steht das Wiederholungszeichen (**Aus einer Serie**). Serienkarten lösen keinen Hinweis "fällig" aus; in [Heute](hilfe:heute) stehen sie unter **Serien heute**. Kommt eine Serienkarte in die Erledigt-Spalte, ist ihr Abschlussdatum immer ihr Tag, nicht der Tag des Ablegens.

Eine Karte gilt als unberührt, solange sie in der Zielspalte liegt, nicht erledigt ist, keine Zeit hat und ihr Verlauf nur ihr Anlegen zeigt. Sonst ist sie angefasst: Ändern, Pause und Urlaub lassen sie stehen.

Rechts im Formular steht jeder Tag mit seinem Stand:

| Stand | Bedeutung |
|---|---|
| **gezählt** | Vorbei; alle Teilnehmer haben ihre Zeit bestätigt |
| **wartet** | Vorbei; mindestens eine vorgebuchte Zeit wartet auf Bestätigung im Nachtrag |
| **fand nicht statt** | Im Nachtrag verworfen; es zählt keine Zeit |
| **heute** | Die Karte liegt in der Zielspalte; morgen fragt der Nachtrag nach der Zeit |
| **vorgebucht** | Die Karte liegt unberührt in der Zielspalte; Ändern und Pause passen sie an oder nehmen sie zurück |
| **angefasst, bleibt** | Jemand hat die Karte angefasst; Ändern, Pause und Urlaub lassen sie stehen |
| **noch nicht vorgebucht** | Jenseits des Vorlaufs; die Karte entsteht, sobald der Tag in den Vorlauf rückt |
| **gelöscht, kommt nicht wieder** | Der Tag wurde bewusst gelöscht; er bleibt gemerkt und wird nie wieder angelegt |
| **entfällt** | Alle Teilnehmer fehlen an dem Tag (Abwesenheit oder Feiertag) |
| **pausiert** | Die Serie ist pausiert; an diesem Tag entsteht keine Karte |

## Serie ändern, pausieren und löschen {#bearbeiten}
Ein Klick auf den Namen einer Serie in der Tabelle öffnet sie im selben Formular.
- **Ändern**: Sobald du etwas änderst, steht oben **Nicht gespeichert** mit der Liste der Änderungen, dazu **Verwerfen** und **Speichern**. Rechts zeigen betroffene Tage **wird angepasst**. Speichern passt die unberührten Karten ab morgen an (Titel, Beschreibung, Labels, Teilnehmer, Dauer, Zielspalte), nimmt Tage zurück, die nach dem neuen Rhythmus entfallen, und legt neue Tage im Vorlauf an. Angefasste, vergangene und gelöschte Tage bleiben, wie sie sind.
- **Einen Tag auslassen**: der Knopf mit dem durchgestrichenen Kalender an einem künftigen Tag. Der Tag wird gemerkt und kommt nicht wieder; eine unberührte Karte dieses Tags geht in den Papierkorb. Dasselbe geschieht, wenn du eine Serienkarte in den Papierkorb legst oder in ein anderes Board ziehst. Holst du sie aus dem Papierkorb zurück, ist der Tag wieder da.
- **Pausieren**: Es entstehen keine neuen Karten; unberührte Karten ab morgen werden zurückgenommen, angefasste bleiben. Oben steht dann **pausiert seit** und das Datum.
- **Fortsetzen**: Ab heute wird wieder vorgebucht. Die Tage der Pause bleiben ohne Karte, gelöschte Tage bleiben gelöscht.
- **Löschen**: Die Rückfrage in der Fläche nennt, was passiert; **Behalten** bricht ab. Unberührte Karten ab morgen gehen in den Papierkorb. Karten mit erfasster Zeit, angefasste und erledigte bleiben als Verlauf und werden von der Serie gelöst; bestätigte Zeiten zählen weiter. Solange die Meldung steht, holt Rückgängig die Serie zurück.

Wird die Zielspalte gelöscht, legt die Serie ihre Karten danach in die Spalte, in die die Karten der gelöschten Spalte gewandert sind, sonst in die erste offene Spalte. Ohne das Recht **Serien und Termine verwalten** siehst du das Formular nur an.

## Termine {#termine}
Ein Termin hat einen Tag, eine Zeit von bis, Teilnehmer und wahlweise einen Ort, aber keine Karte.

So legst du einen an:
1. Klicke über der Tabelle **Kommende Termine** auf **Termin anlegen** (nur mit dem Recht **Serien und Termine verwalten**).
2. Fülle **Titel**, **Board**, **Wann** (Tag sowie Beginn und Ende als Uhrzeit, etwa 09:00 bis 10:00), **Ort** (frei lassen, wenn egal) und **Teilnehmer** aus.
3. Klicke **Anlegen**. Fehlt etwas, nennt die Zeile daneben den Grund, etwa **Das Ende liegt vor dem Beginn**.

Nimmst du selbst teil, bist du gleich zugesagt. Die anderen Teilnehmer bekommen einen [Hinweis](hilfe:hinweise) und sagen selbst zu.

In der Tabelle **Kommende Termine** steht bei jedem Teilnehmer sein Stand: vorher **zugesagt** oder **offen**, nach dem Tag **bestätigt** oder **wartet**. Hat das Board das Modul Arbeitszeit an und du dort das Recht **Abwesenheiten sehen**, steht dort auch, wer abwesend ist. In der Spalte **Du** sagst du mit **Zusagen** zu; **Absagen** nimmt die Zusage zurück. In [Heute](hilfe:heute) stehen deine Termine unter **Termine heute** und **Nächste sieben Tage**, ebenfalls mit **Zusagen**.

Erfasst das Board Zeit, zählt die Zeit eines Termins erst, wenn du sie ab dem Folgetag im [Nachtrag](#nachtrag) bestätigst, und zwar von Beginn bis Ende. Sie steht dann in deinem Stundenzettel als eigene Zeile.

## Nachtrag {#nachtrag}
Der Nachtrag sammelt deine vorgebuchten Zeiten vergangener Tage, die auf deine Bestätigung warten. Ohne Antwort zählen sie nicht in deinem Zeitkonto. Du öffnest ihn auf der Seite **Serien und Termine** mit **Jetzt bestätigen** im Hinweis oben.

Im Nachtrag stehen:
- Serientage, an denen du auf der Karte stehst und für diesen Tag noch keine Zeit auf ihr gebucht hast,
- Termine, an denen du teilnimmst, an dem Tag nicht ganztägig abwesend warst und deine Zeit noch nicht bestätigt hast,
- jeweils höchstens 31 Tage zurück und nur in Boards mit Zeiterfassung, in denen du **Eigene Zeit buchen** darfst. Ältere Serientage gelten als gezählt.

Jede Zeile zeigt Uhrzeit, Titel, Board, Schlüssel der Karte, ob Serie oder Termin, die geplante Dauer und wer schon bestätigt hat.
- Bei einer Serie ist die Dauer mit der geplanten Zeit vorbelegt; war es länger oder kürzer, ändere sie. Bei einem Termin zählt die geplante Zeit fest.
- **Bestätigen** bucht: bei einer Serie einen Eintrag mit Herkunft Serie auf die Karte des Tags, die dann in die Erledigt-Spalte kommt; bei einem Termin einen Eintrag von Beginn bis Ende.
- **Verwerfen** heißt: fand für dich nicht statt. Bei einer Serie fällst du aus der Karte, wenn andere eingeplant waren; warst du allein, geht die Karte in den Papierkorb und der Tag zählt als verworfen. Bei einem Termin bist du danach kein Teilnehmer mehr. Es zählt keine Zeit.
- **Alle offenen bestätigen** bestätigt alles auf einmal mit den eingetragenen Dauern, mit einem gemeinsamen Rückgängig.
- **Später** klappt den Nachtrag zu; er fragt wieder, solange etwas offen ist.

Hast du am Serientag schon Zeit auf seiner Karte gebucht, etwa mit dem Timer, gilt der Tag für dich als bestätigt. Löschst du die bestätigte Zeit eines Termins wieder, wartet er erneut im Nachtrag. In Boards ohne Zeiterfassung wartet nichts; dort gilt jeder vergangene Serientag als gezählt.

## Im Kalender und in Heute {#kalender}
Im Kalender eines Boards (siehe [Liste, Kalender und Zeitachse](hilfe:ansichten)) blendest du oben rechts **Termine** und **Serien** ein und aus.
- Ein Serientag mit Karte erscheint als Karte. Ein Tag, für den es noch keine Karte gibt, erscheint als kurze Marke mit dem Wiederholungszeichen; ihr Hinweis nennt Uhrzeit und Stand, ein Klick öffnet die Serie.
- Termine stehen mit Zeit und Titel; der Hinweis nennt Ort und Teilnehmer.
- In der Wochenansicht stehen Termine und Serientage ohne Karte, die eine Uhrzeit haben, als Blöcke in ihrer Zeit.
- Gelöschte, entfallene, verworfene und pausierte Tage erscheinen nicht.

In Heute stehen rechts **Termine heute**, darunter **Nächste sieben Tage**, und **Serien heute** mit der Uhrzeit jeder Serienkarte.
