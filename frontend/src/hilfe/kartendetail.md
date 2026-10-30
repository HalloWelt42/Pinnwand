---
titel: Das Kartendetail
untertitel: Alles an einer Karte ansehen und ändern
bereich: Boards
symbol: fa-pen-to-square
---
Ein Klick auf eine Karte öffnet ihr Detail als Leiste rechts über dem Board. Dort siehst und änderst du alles an der Karte. Gespeichert wird von selbst: jedes Feld speichert für sich, und jede Änderung lässt sich in der Meldung rückgängig machen.

## Öffnen und schließen {#aufruf}
- Öffnen: ein Klick auf die Karte im Board, in der Liste, im Kalender oder in der Zeitachse, oder auf einen Treffer der Suche. Hat eine Karte im Board den Fokus, öffnet sie auch Enter.
- Die Adresse im Browser zeigt die Karte, etwa /board/prod/12; so lässt sie sich auch weitergeben.
- Schließen: das X oben rechts (**Schließen (Escape)**), Escape oder ein Klick daneben ins Board. Ein Klick auf eine andere Karte öffnet gleich diese.
- Steckt der Cursor in einem Feld, verwirft das erste Escape nur die Eingabe in diesem Feld; erst das zweite schließt das Detail.
- Der Knopf mit den Pfeilen nach außen (**Vollbild**) macht das Detail breit, derselbe Knopf (**Als Leiste**) wieder schmal.

## Der Kopf {#kopf}
Links stehen der Schlüssel (ein Klick kopiert ihn, siehe [Nummern einer Karte](hilfe:karten/kennung)), die Spalte, in der die Karte liegt, und der Umschalter **Arbeit** und **Idee** (siehe [Arbeit oder Idee](hilfe:karten/art)). Rechts die Knöpfe, jeweils nur mit dem passenden Modul oder Recht:

| Knopf | was er tut |
| - | - |
| Zauberstab | **Zusammenfassen**: Vorschlag aus Beschreibung, Notizen, Checkliste und Kommentaren; mit dem Modul KI an der Karte, siehe [KI an der Karte](hilfe:ki) |
| Lautsprecher | **Karte vorlesen**: Titel, Beschreibung und offene Punkte; mit dem Modul Vorlesen, siehe [Vorlesen](hilfe:vorlesen) |
| zwei Blätter | **Duplizieren**, siehe [Duplizieren](hilfe:karten/duplizieren) |
| zwei Pfeile | in ein anderes Board, siehe [Umziehen](hilfe:karten/umziehen) |
| Kette | **Verweis kopieren**, siehe [Verweis](hilfe:karten/verweis) |
| Pfeile nach außen | **Vollbild** oder **Als Leiste** |
| X | **Schließen (Escape)** |

Unten im Detail steht **In den Papierkorb** (mit dem Recht Karten löschen) und der Satz **Jedes Feld speichert für sich; jede Änderung lässt sich in der Meldung rückgängig machen.**

## Titel, Beschreibung und Notizen {#texte}
- **Titel**: das große Feld oben. Ändern, dann Enter oder das Feld verlassen speichert; Escape stellt den bisherigen Titel wieder her. Ein leerer Titel wird nicht übernommen.
- **Beschreibung**: ein Klick auf den Text oder auf den Stift (**Bearbeiten**) öffnet ein Eingabefeld an Ort und Stelle. **Fertig** oder Strg und Enter speichert, **Verwerfen** oder Escape stellt den Stand vom Öffnen wieder her. Daneben steht **Nicht gespeichert**, solange du etwas geändert hast, sonst **Unverändert**.
- **Notizen**: Platz für längere Texte; sie öffnen sich zum Bearbeiten immer im Vollbild.
- Der Knopf mit den Pfeilen nach außen am Abschnitt (**Im Vollbild bearbeiten, mit Vorschau**) zeigt links das Eingabefeld und rechts, wie der Text aussehen wird.

Geschrieben wird in Markdown, einer einfachen Schreibweise für Text: zwei Sternchen vor und nach einem Wort machen es fett, ein Sternchen kursiv, ein Bindestrich am Zeilenanfang einen Listenpunkt, eine Raute am Zeilenanfang eine Überschrift; Tabellen und Verweise gehen auch. Verweise im Text sind anklickbar. Schließt du das Detail oder wechselst die Karte, während ein Textfeld offen ist, wird dein Text gespeichert.

## Angaben {#angaben}
Unter den Texten stehen die Angaben der Karte:

| Angabe | Bedeutung |
| - | - |
| **Status** | die Spalte; umstellen verschiebt die Karte ans Ende dieser Spalte, wie Ziehen (Recht Karten verschieben) |
| **Priorität** | Keine, Niedrig, Mittel, Hoch oder Dringend |
| **Start** | ab wann an der Karte gearbeitet wird |
| **Fällig** | bis wann sie fertig sein soll |
| **Zuständig** | wer sich kümmert; mehrere Personen sind möglich |
| **Labels** | die farbigen Schlagworte des Boards |
| **Blockiert** | ein Grund, wenn die Karte wartet, etwa wartet auf Ersatzteil; leer heißt nicht blockiert |
| **Cover** | eine Farbe als Streifen oben auf der Karte, oder keine |

Darunter folgen die eigenen Felder des Boards (siehe [Felder](hilfe:boardeinstellungen/felder)).

### So gibst du sie ein
- **Start** und **Fällig** nehmen ein Datum in deutscher Schreibweise: 16.11.2026, 16.11. oder 16112026. Unter dem Feld steht, was verstanden wurde, oder **Datum nicht lesbar**. Enter oder Verlassen übernimmt, ein leeres Feld entfernt das Datum. Der Start darf nicht nach dem Fälligkeitstag liegen.
- **Zuständig**: das X an einer Person nimmt sie heraus. Im Feld **Mitglied des Boards zuweisen** ab zwei Buchstaben den Namen tippen und aus bis zu sechs Vorschlägen wählen; Enter nimmt den ersten. Zuständig sein kann nur, wer Mitglied des Boards ist. Wer neu zuständig wird, bekommt einen Hinweis.
- **Labels**: ein Klick auf ein Label setzt oder entfernt es. Mit dem Modul KI an der Karte schlägt der Zauberstab daneben passende Labels vor.
- **Blockiert** und die Textfelder der eigenen Felder speichern beim Verlassen oder mit Enter; Escape verwirft die Eingabe. Ein Zahlenfeld nimmt auch ein Komma.
- Auswahlfelder speichern sofort.

Darunter stehen drei Angaben zum Lesen: **Im Status** mit der Sanduhr (Tage seit dem letzten Wechsel der Spalte, gefärbt nach der Alterung des Boards), **Durchlaufzeit** (Tage vom Anlegen bis zum Abschluss, bei offenen Karten bis heute) und **Erstellt** mit Datum und dem Kürzel der Person, die die Karte angelegt hat.

## Checkliste {#checkliste}
- Das Kästchen vor einem Punkt hakt ihn ab oder öffnet ihn wieder.
- Ein Klick auf den Text benennt den Punkt um; Enter oder Verlassen speichert, Escape verwirft, ein leerer Text behält den alten Namen.
- Das X am Ende entfernt den Punkt, mit Rückgängig.
- Im Feld **Punkt hinzufügen, Enter** tippst du einen neuen Punkt; Enter hängt ihn an.

Oben zeigt der Zähler erledigt/gesamt und ein Balken den Fortschritt; ist alles abgehakt, wird der Zähler grün. Dieselbe Angabe steht auf der Karte im Board. Mit dem Modul KI an der Karte schlägt **Vorschlagen** neue Punkte vor; **Übernehmen** hängt nur die angehakten ans Ende. Eine Checkliste hat höchstens 200 Punkte.

## Kommentare und Erwähnungen {#kommentare}
Unten im Detail stehen die Reiter **Kommentare** und **Verlauf**, je mit ihrer Zahl.

- Im Feld **Kommentar schreiben, @ erwähnt eine Person** tippen. Enter sendet, Umschalt und Enter macht eine neue Zeile; **Senden** geht ebenso. Kommentare verstehen dieselbe Schreibweise wie die Beschreibung.
- Mit @ erwähnst du ein Mitglied des Boards: @ und dahinter sein Vorname, sein Kontoname der Kellerwolke oder sein Kürzel, etwa @Anna. Die Erwähnung wird hervorgehoben, der volle Name erscheint beim Überfahren.
- Wer in einem Kommentar erwähnt ist, bekommt einen Hinweis; die übrigen Zuständigen der Karte bekommen einen Hinweis, dass kommentiert wurde. Wer in Beschreibung oder Notizen neu erwähnt wird, bekommt ebenfalls einen Hinweis.

Kommentieren braucht das Recht Kommentieren. Mehr zu Hinweisen unter [Hinweise und Mitteilungen](hilfe:hinweise).

## Anhänge {#anhaenge}
Der Abschnitt **Anhänge** hängt Dateien an die Karte. Ändern braucht das Recht Karten bearbeiten.

- **Hochladen** wählt Dateien von deinem Gerät; du kannst sie auch direkt auf den Abschnitt ziehen (**Loslassen hängt die Dateien an**). Je Datei bis 25 MB, höchstens 20 auf einmal; leere Dateien bleiben draußen, die Meldung sagt es. Hochgeladenes liegt in der Kellerwolke im Ordner des Boards, und jedes Mitglied kann es öffnen.
- **Aus der Kellerwolke** öffnet deine Kellerwolke in einer Fläche im Detail: einen Ordner anklicken geht hinein, der Weg oben führt zurück, das Suchfeld sucht im gezeigten Ordner. Dateien ankreuzen, auch aus verschiedenen Ordnern und bis zu 20, dann **Verknüpfen**. Die Dateien bleiben, wo sie sind; an der Karte sehen alle Mitglieder Name und Größe, öffnen kann sie, wer sie verknüpft hat. Schon angehängte Dateien sind als solche gekennzeichnet. **Abbrechen** oder Escape schließt die Fläche.
- Ein Klick auf den Namen oder auf den Pfeil öffnet einen Anhang in einem neuen Reiter.
- Das X nimmt einen Anhang von der Karte (bei verknüpften heißt es **Verknüpfung lösen**), mit Rückgängig; die Datei in der Kellerwolke bleibt.

## Verknüpfte Aufgaben {#verknuepft}
Diesen Abschnitt haben nur Arbeitskarten. Er zeigt die anderen Karten der Gruppe mit Schlüssel und Titel; ein Klick öffnet eine davon, **Lösen** nimmt sie aus der Gruppe. Bleibt nur eine Karte übrig, endet die Gruppe.

- Im Feld **Karte suchen und verknüpfen (zieht mit, Zeit geteilt)** nach Titel oder Schlüssel suchen. Es erscheinen bis zu acht offene Arbeitskarten dieses Boards; die Pfeiltasten wählen, Enter oder ein Klick verknüpft. Ist der Treffer schon in einer Gruppe, tritt diese Karte ihr bei.
- **Zeit teilen** (Schalter rechts): an, zeigen die Karten der Gruppe ihre gemeinsame Zeit, und jede Sekunde zählt einmal; aus, zeigt jede Karte nur ihre eigene. Gebucht wird immer je Karte.

Verknüpfte Karten ziehen zusammen in andere Spalten (siehe [Verknüpfen](hilfe:karten/verknuepfen)). Ändern braucht das Recht Karten bearbeiten.

## Abschnitte der Module {#module}
Je nach den Modulen des Boards hat das Detail weitere Abschnitte:

- **Zeiterfassung** bei Arbeitskarten: Timer, gebuchte Zeit, Schätzung und Nachtragen (siehe [Zeiterfassung](hilfe:zeiterfassung)).
- **Transkripte**: Stellen aus Aufnahmen an der Karte (siehe [Transkripte](hilfe:transkripte)).
- Vorschläge der KI an Kopf, Labels und Checkliste (siehe [KI an der Karte](hilfe:ki)). Übernommen wird nur, was du im Vorschlag bestätigst.

## Verlauf {#verlauf}
Der Reiter **Verlauf** listet, was mit der Karte geschah, neueste zuerst, mit Zeit und dem Kürzel der Person: Anlegen, Verschieben (auch als mitgezogene verknüpfte Karte), Erledigen, Zuständige, Start, Fällig, Priorität, Blockade, Arbeit oder Idee, Kommentare, Verknüpfungen, Zeitbuchungen und Anhänge. Änderungen an Titel, Beschreibung, Notizen und Checkliste stehen bewusst nicht darin.

## Speichern und Rückgängig {#speichern}
Jedes Feld ist sofort bearbeitbar und speichert von selbst: beim Verlassen, mit Enter oder, bei Auswahlfeldern, gleich bei der Wahl. Nach jeder Änderung erscheint unten rechts eine Meldung, was geschah, mit dem Knopf **Rückgängig**. Sie verschwindet nach sechs Sekunden, aber nicht, solange der Mauszeiger auf ihr ruht; das X schließt sie gleich.

- Lehnt die Pinnwand eine Änderung ab, nennt die Meldung den Grund, und der alte Wert steht wieder da.
- Ohne Verbindung sind Änderungen gesperrt, bis die Verbindung wieder steht; die Meldung sagt es.
- Ohne das Recht Karten bearbeiten sind die Felder nur zum Lesen da.

## Gleichzeitig bearbeiten {#konflikt}
Mehrere Personen können dieselbe Karte zugleich offen haben. Änderungen der anderen erscheinen sofort bei dir. Im Board zeigt eine Karte, die gerade jemand anders geändert hat, fünf Sekunden lang dessen Kürzel, und die Meldung sagt, wer was getan hat.

Hat jemand dasselbe Feld geändert, während du es bearbeitet hast, schreibt die Pinnwand deine Änderung nicht still darüber. Stattdessen erscheint oben im Detail ein Hinweis wie **PROD-12 wurde inzwischen geändert.** Er nennt deine Änderung, oben steht der jetzige Stand, und du entscheidest:

- **Jetzige behalten**: deine Änderung wird verworfen.
- **Meine übernehmen**: deine Änderung ersetzt den jetzigen Stand.

Änderungen an verschiedenen Feldern stören sich nicht.
