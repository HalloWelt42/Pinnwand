---
titel: KI an der Karte
untertitel: Vorschläge für Zusammenfassung, Checkliste, Labels und neue Karten
bereich: Verbund
symbol: fa-wand-magic-sparkles
---
Mit dem Modul KI an der Karte liest eine KI (künstliche Intelligenz: ein Programm, das Texte versteht und schreibt) deine Karten und macht Vorschläge: eine Zusammenfassung, nächste Schritte für die Checkliste, passende Labels, Karten aus einem längeren Text und Notizen zu Transkript-Stellen. Die KI ändert nie selbst etwas. Übernommen wird nur, was du in der Vorschau bestätigst, und jede Übernahme lässt sich rückgängig machen.

## Was du brauchst {#voraussetzungen}
- Das Modul **KI an der Karte** ist im Board an (siehe [Module einschalten](hilfe:module/einschalten)).
- Die Leitstelle ist mit der Pinnwand verbunden. Die Leitstelle ist der Dienst, über den die Pinnwand eine KI fragt: Sie nimmt die Anfrage an und lässt ein Sprachmodell rechnen, das ist die eigentliche KI. Welches Modell rechnet, ist für die ganze Pinnwand eingestellt; ohne feste Wahl entscheidet die Leitstelle.
- Für die meisten Vorschläge brauchst du ein Recht im Board, siehe die Tabelle unten.

Fehlt die Leitstelle, erscheinen keine Zauberstab-Knöpfe. Warum, sagt der Reiter **Module** in den Einstellungen des Boards (siehe [Wenn eine Verbindung fehlt](hilfe:module/verbindung-fehlt)).

| Vorschlag | Wo du ihn findest | Wer ihn holen kann |
|---|---|---|
| Zusammenfassung | Zauberstab im Kopf des Kartendetails | jedes Mitglied; übernehmen nur mit **Karten bearbeiten** |
| Checkliste | Knopf **Vorschlagen** an der Checkliste | mit **Karten bearbeiten** |
| Labels | Zauberstab hinter den Labels im Kartendetail | mit **Karten bearbeiten** |
| Karten aus Text | Knopf **Aus Text** beim Anlegen in einer Spalte | mit **Karten anlegen** |
| Notiz zu einer Stelle | Zauberstab neben der Notiz einer Transkript-Stelle | mit **Karten bearbeiten**, dazu das Modul Transkripte |

## Der Vorschlagskasten {#vorschau}
Jeder Vorschlag erscheint in einem eigenen Kasten mit Zauberstab und Überschrift, etwa "Vorschlag: Zusammenfassung aus Beschreibung, Notizen und Kommentaren". Der Kasten zeigt immer einen von drei Zuständen:

- **Die KI rechnet:** "Die Leitstelle rechnet; das kann einen Moment dauern." Es gibt keine feste Wartezeit, beim ersten Mal kann es auch länger dauern. Mit **Abbrechen** hörst du auf zu warten.
- **Es ging nicht:** Der Kasten nennt den Grund. Mit **Noch einmal** fragst du erneut, mit **Schließen** schließt du den Kasten.
- **Der Vorschlag ist da:** Du siehst ihn als Vorschau und entscheidest. Der Knopf zum Übernehmen heißt je nach Vorschlag **In die Notizen übernehmen**, **Übernehmen**, **Setzen**, **Anlegen** oder **Als Notiz übernehmen**. **Verwerfen** schließt den Kasten, ohne etwas zu ändern.

Ein zweiter Klick auf denselben Zauberstab schließt den Kasten ebenfalls. Schließt du das Kartendetail, wartet die Pinnwand nicht weiter auf den Vorschlag.

Nach jeder Übernahme erscheint unten rechts die Meldung mit **Rückgängig**. So nimmst du eine Übernahme mit einem Klick zurück.

## Zusammenfassung {#zusammenfassung}
1. Öffne eine Karte. Im Kopf des Kartendetails steht der Zauberstab mit dem Hinweis "Zusammenfassen: Vorschlag aus Beschreibung, Notizen, Checkliste und Kommentaren".
2. Klicke darauf. Die KI schreibt zwei bis vier Sätze: worum es geht, was schon geschehen ist und was offen ist.
3. Mit **In die Notizen übernehmen** hängt die Pinnwand den Text an die Notizen der Karte an, fett eingeleitet mit **Zusammenfassung:**. Was schon in den Notizen stand, bleibt davor stehen.

Dafür liest die KI die Karte: Titel, Status, Fälligkeit, Blockiert, Beschreibung, Notizen, Checkliste und die jüngsten Kommentare. Sie soll nur schreiben, was in der Karte steht, und nichts erfinden.

## Checkliste vorschlagen {#checkliste}
1. Klicke in der Checkliste der Karte rechts auf **Vorschlagen** (Hinweis "Neue Punkte vorschlagen (über die Leitstelle)").
2. Die KI schlägt die nächsten Schritte vor, höchstens zehn. Jeder Punkt hat ein Häkchen, anfangs sind alle angehakt.
3. Nimm die Häkchen bei Punkten weg, die du nicht willst, und klicke auf **Übernehmen**. Die angehakten Punkte kommen offen ans Ende der Checkliste.

Punkte, die die Checkliste schon hat, auch mit anderen Worten, lässt die Pinnwand weg. Gibt es nichts Neues, steht dort "Keine neuen Punkte; die Checkliste deckt die Karte schon ab."

## Labels vorschlagen {#labels}
1. Im Kartendetail stehen unter **Angaben** bei **Labels** alle Labels des Boards. Dahinter steht der Zauberstab "Labels vorschlagen (über die Leitstelle)". Er erscheint nur, wenn die Karte noch nicht alle Labels des Boards trägt.
2. Die KI wählt aus den Labels des Boards, die die Karte noch nicht hat. Neue Labels erfindet sie nicht, und sie wählt lieber keins als ein falsches.
3. Die vorgeschlagenen Labels sind anfangs alle gewählt. Ein Klick auf ein Label nimmt es heraus ("Nicht setzen") oder wieder hinein ("Doch setzen").
4. **Setzen** gibt der Karte die gewählten Labels.

Passt nichts, steht dort "Kein weiteres Label passt klar zu dieser Karte."

## Karten aus Text {#aus-text}
Aus einer Notiz, einer Nachricht, einem Protokoll oder einer Liste macht die KI mehrere Karten auf einmal.

1. Klicke am Fuß einer Spalte auf **Karte**. Es öffnet sich die Schnelleingabe.
2. Klicke dort auf **Aus Text** (Hinweis "Aus einem Text mehrere Karten machen (Vorschlag über die Leitstelle)").
3. Füge den Text in das große Feld ein und klicke auf **Vorschlagen** oder drücke Strg und Enter.
4. Die KI schlägt bis zu zwanzig Karten vor. Jede hat ein Häkchen und ihren Titel in einem Feld, den du gleich hier ändern kannst. Darunter steht kurz, welche Beschreibung sie bekommt und wie viele Punkte ihre Checkliste hat.
5. Nimm die Häkchen bei Karten weg, die du nicht willst, und klicke auf **Anlegen**.

Die angehakten Karten entstehen in einem Schritt oben in der Spalte, mit Titel, Beschreibung und Checkliste; zuständig bist du. Hat das Board Zeiterfassung, gilt dabei die Wahl **Arbeit** oder **Idee** aus der Schnelleingabe, sonst die Kartenart des Boards. Die Meldung nennt alle neuen Karten, etwa "3 Karten in Offen angelegt (HAUS-12 bis HAUS-14)", und ein einziges **Rückgängig** nimmt sie alle zurück.

Der Text darf bis zu 20.000 Zeichen lang sein. **Einzeln anlegen** oder Escape führt zurück zur Eingabe einzelner Titel; Text und Vorschlag gehen dabei verloren. Steht im Text nichts, woraus eine Karte würde, sagt der Kasten das.

## Notiz zu einer Transkript-Stelle {#notiz}
Ist auch das Modul [Transkripte](hilfe:transkripte) an, hilft die KI bei den Notizen zu verknüpften Stellen.

1. Im Kartendetail im Abschnitt **Transkripte** steht neben dem Feld **Notiz zur Stelle** der Zauberstab "Notiz vorschlagen (über die Leitstelle)".
2. Die KI liest das Gespräch um die Stelle herum, von einer halben Minute davor bis anderthalb Minuten danach. Ist das ganze Transkript verknüpft, liest sie die ersten zehn Minuten.
3. Sie schlägt ein bis zwei Sätze vor: was an der Stelle gesagt oder entschieden wird.
4. **Als Notiz übernehmen** setzt den Vorschlag als Notiz der Stelle; eine bisherige Notiz wird dabei ersetzt.

## Wenn es nicht geht {#fehler}
Der Vorschlagskasten nennt immer den Grund. Die Karte bleibt dabei unverändert.

| Meldung | Was sie heißt |
|---|---|
| "Die Leitstelle kann gerade nicht: ..." | Die Leitstelle meldet ein Problem, etwa weil der Rechner mit dem Modell gerade nicht bereit ist. Später **Noch einmal**. |
| "Die Antwort des Modells war nicht lesbar; noch einmal versuchen" | Das Modell hat in einer falschen Form geantwortet. **Noch einmal** hilft meist. |
| "Die Antwort des Modells brach ab, bevor sie fertig war; ..." | Die Antwort wurde zu lang. Noch einmal versuchen oder den Text kürzen. |
| "Der Auftrag wurde in der Leitstelle abgebrochen" | Jemand hat die Anfrage in der Leitstelle beendet. |
| "Dir fehlt im Board ... das Recht ..." | Dir fehlt das Recht aus der Tabelle oben. |
| "KI an der Karte ist im Board ... aus" | Jemand hat das Modul inzwischen ausgeschaltet. |
