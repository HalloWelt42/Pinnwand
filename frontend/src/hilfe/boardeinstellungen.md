---
titel: Einstellungen des Boards
untertitel: Aufbau, Module, Rollen und Mitglieder eines Boards
bereich: Boards
symbol: fa-sliders
---
Jedes Board hat eigene Einstellungen: Name und Farbe, Module, Spalten, Labels, eigene Felder, Rollen mit ihren Rechten und die Mitglieder. Sie gelten für alle Mitglieder des Boards.

## Einstellungen öffnen {#aufruf}
- Im Kopf des Boards der Knopf **Einstellungen**.
- In der Seitenleiste unter **Einstellungen**: dort steht oben je Board ein Knopf zu seinen Einstellungen.
- **Einladen** im Kopf des Boards führt direkt zum Reiter **Mitglieder**.

Oben stehen die Reiter **Allgemein**, **Module**, **Spalten**, **Labels**, **Felder**, **Rollen und Rechte** und **Mitglieder**, jeder mit eigener Adresse. **Zum Board** oben rechts führt zurück zum Board.

## Wer was ändern darf {#wer-darf}
Jede Änderung speichert von selbst, gilt sofort für alle Mitglieder und kommt mit **Rückgängig** in der Meldung.

- **Rollen und Rechte** und **Mitglieder** ändert, wer das Recht Mitglieder und Rollen verwalten hat.
- Alle anderen Reiter ändert, wer das Recht Board verwalten hat.

Fehlt dir das Recht für einen Reiter, siehst du ihn nur an; oben steht dann zum Beispiel **nur ansehen: dir fehlt das Recht Board verwalten**. Die Zeile im Kopf nennt außerdem den Ordner, für wie viele Mitglieder die Einstellungen gelten und welche Rolle du hast.

## Allgemein {#allgemein}
- **Name**: steht in der Seitenleiste und im Kopf. Umbenennen ändert das Kürzel nicht.
- **Kürzel**: fest seit dem Anlegen und über alle Boards eindeutig, damit Kartenschlüssel und Adressen nie brechen. Daneben steht die Nummer der nächsten Karte. Nummern werden nie wiederverwendet, auch nicht nach dem Löschen.
- **Farbe**: der Punkt in der Seitenleiste und im Kopf; er unterscheidet die Boards.
- **Neue Karten sind**: **Arbeit** oder **Idee**, die Vorgabe beim Anlegen. Bestehende Karten bleiben, wie sie sind; jede lässt sich im Kartendetail umschalten.

## Alterung und erledigte Karten {#alterung}
Unter **Alterung der Karten**:

- **Warnung ab** und **Gefahr ab**: nach so vielen Tagen seit dem letzten Wechsel der Spalte wird die Sanduhr auf der Karte bernsteinfarben (Warnung) oder rot (Gefahr). Erlaubt ist eine ganze Zahl von 0 bis 365; 0 schaltet die Stufe aus, die beiden Stufen sind unabhängig voneinander. Neue Boards beginnen mit 4 und 8 Tagen.
- **So sieht es aus** zeigt Beispiele der Sanduhr mit diesen Stufen. Kommt Gefahr vor der Warnung, sagt es ein Hinweis; die Karte zeigt dann gleich Gefahr.

Die Stufen gelten auch für **Im Status** im Kartendetail und für **Liegengeblieben** in [Heute](hilfe:heute). Mehr unter [Alterung](hilfe:board/alterung).

Unter **Erledigte Karten**:

- **Karten je Ladeschritt**: so viele Karten laden die Erledigt-Spalte und das Archiv auf einmal; 1 bis 500, neue Boards beginnen mit 50.
- **Archiv ab**: erledigte Karten mit älterem Abschluss stehen nur noch im Archiv; 1 bis 100.000 Tage, neue Boards beginnen mit 365. Das ist eine reine Ladegrenze: eine größere Zahl holt die Karten zurück ins Board.

Eine Zahl außerhalb der Grenzen wird nicht übernommen; unter dem Feld steht dann, welche Zahlen gehen.

## Als Vorlage speichern {#vorlage}
**Als Vorlage speichern** speichert den Aufbau des Boards ohne Karten und Mitglieder: Spalten, Felder, Labels, die Art neuer Karten und die Module. Die Erklärung daneben nennt, wie viele es sind. Nach einem Klick gibst du einen Namen ein (vorgeschlagen ist der Name des Boards), dann legt **Vorlage speichern** oder Enter sie an; **Abbrechen** verwirft. Die Vorlage steht danach beim [Anlegen eines Boards](hilfe:board/anlegen) unter deinen eigenen Vorlagen, nur für dich.

## Board entfernen {#entfernen}
**In den Papierkorb** unter **Board entfernen** legt das ganze Board mit allen Karten, Kommentaren und Anhängen in den Papierkorb der App. Erst kommt eine Rückfrage, die nennt, was dabei geschieht:

- Alle Karten gehen mit, samt Kommentaren und Anhängen.
- Die anderen Mitglieder sehen das Board nicht mehr.
- Laufende Timer halten an und buchen.
- Serien des Boards ruhen.

Nach dem Bestätigen landest du in Heute. Wiederherstellen geht in den [persönlichen Einstellungen](hilfe:einstellungen) im Reiter **Papierkorb**; bis dahin bleibt das Kürzel vergeben. Das braucht das Recht Board verwalten.

**Endgültig löschen** darunter nimmt das Board sofort und ohne Rückweg weg, ohne Papierkorb: mit allen Karten, Kommentaren, Anhängen, Serien und Terminen, auch für alle anderen Mitglieder. Gebuchte Zeiten bleiben unter dem Namen ihrer Karte stehen, das Kürzel wird frei. War das Board nur ein Versuch, löschst du deine Zeit danach unter **Zeiten** (siehe [Zeit gelöschter Karten und Boards](hilfe:zeiterfassung/entfernt)). Zur Sicherheit tippst du das Kürzel des Boards ein; erst dann wirkt der Knopf. Das braucht die Rechte Board verwalten und Papierkorb leeren.

In welchem Ordner ein Board in deiner Seitenleiste steht, entscheidest du dort selbst, per Ziehen (siehe [Ordner und Boards in der Seitenleiste](hilfe:uebersicht/ordner)).

## Module {#module}
Der Reiter **Module** schaltet Zusatzteile des Boards ein und aus, etwa Zeiterfassung, Serien und Termine oder KI an der Karte. Für jedes Modul zeigt eine Kachel, was es bringt (Ansichten, Felder, Rechte), und einen Schalter. Abschalten blendet ein Modul in Board, Karten und Rollen aus; seine Daten bleiben und sind beim Einschalten wieder da. Mehr unter [Module und Verbindungen](hilfe:module).

## Spalten {#spalten}
Der Reiter **Spalten** zeigt alle Spalten untereinander, in der Reihenfolge des Boards:

- Am Griff links ziehen ordnet sie um, wie im Board.
- Name, **Farbe** und die Zahl ihrer Karten.
- **Anfangs eingeklappt**: wie die Spalte im Board zuerst steht; jede Person klappt sie danach für sich um.
- Bei offenen Spalten die **Grenze** (1 bis 999 offene Karten, leer heißt keine; sie warnt nur) und **Zur Erledigt-Spalte machen**.
- Bei der Erledigt-Spalte ihr **Zeitfenster**, also welche erledigten Karten das Board zuerst zeigt, und die Marke **Erledigt-Spalte**.
- Der Papierkorb rechts löscht eine Spalte, mit derselben Rückfrage wie im Board: Karten verschieben oder mit der Spalte in den Papierkorb. Hier nennt sie zusätzlich, welche verknüpften Karten aus anderen Spalten mitziehen, ob die Zielspalte danach über ihrer Grenze liegt, wie viel gebuchte Zeit mit in den Papierkorb geht und in welche Spalte eine Serie künftig ihre Karten legt. Die Erledigt-Spalte und die letzte Spalte bleiben.

Unter **Neue Spalte** legt **Spalte anlegen** (oder Enter) eine Spalte mit Name und Farbe am Ende an, ohne Grenze und offen. Wie Spalten im Board wirken, steht unter [Board und Spalten](hilfe:board/spalten).

## Labels {#labels}
Labels sind farbige Schlagworte für Karten, etwa Dringend oder Kunde Meier.

- Name und Farbe jedes Labels änderst du direkt in seiner Zeile. Das gilt sofort auf allen Karten und im Filter, denn die Karten tragen das Label selbst.
- Daneben steht, an wie vielen Karten es hängt.
- Der Papierkorb löscht ein Label nach einer Rückfrage, die die betroffenen Karten nennt; dort fällt es weg, sonst ändert sich an den Karten nichts.
- Unter **Neues Label** Namen tippen, Farbe wählen, **Label anlegen**. Jeden Namen gibt es nur einmal; Groß- und Kleinschreibung zählt dabei nicht.

## Felder {#felder}
Eigene Felder ergänzen die Grundfelder jeder Karte um Angaben, die dein Board braucht, etwa Kunde, Stückzahl oder Maschine. Sie stehen im Kartendetail unter den Angaben.

| Art | wofür |
| - | - |
| **Text** | eine Zeile Text, etwa ein Kunde oder eine Auftragsnummer |
| **Zahl** | eine Zahl, etwa eine Stückzahl; die Liste sortiert sie der Größe nach |
| **Datum** | ein Tag im deutschen Format, etwa ein Liefertermin |
| **Auswahl** | eine aus festen Optionen, etwa eine Maschine; im Filter wählbar |
| **Verweis** | ein Verweis auf eine andere Karte, etwa ihr Schlüssel |

- Unter **Neues Feld** Namen tippen, Art wählen, **Feld anlegen**.
- Die **Art** lässt sich ändern, solange keine Karte einen Wert trägt; danach ist sie fest, ein Schloss zeigt es.
- **Auf der Karte**: das Feld steht dann auch auf der Karte im Board, nicht nur im Kartendetail.
- Bei einer Auswahl die **Optionen**: im Feld **Option, Enter** hinzufügen, mit dem X entfernen. Karten mit einer entfernten Option verlieren diesen Wert.
- Am Griff ziehen ordnet die Felder; in dieser Reihenfolge stehen sie im Kartendetail und auf der Karte.
- Der Papierkorb löscht ein Feld nach einer Rückfrage; die Werte an den Karten fallen mit weg.

Darunter stehen die **Felder der Module**, die mit ihrem Modul kommen und gehen, und die **Grundfelder jeder Karte**, die immer da sind.

## Rollen {#rollen}
Jede Person im Board hat genau eine Rolle, und die Rolle bestimmt ihre Rechte. Jedes Board hat drei Start-Rollen; sie lassen sich umbenennen, aber nicht löschen:

| Rolle | Rechte zu Beginn |
| - | - |
| **Besitzer** | alle |
| **Mitglied** | Karten anlegen, bearbeiten, verschieben und löschen, Kommentieren, Eigene Zeit buchen, Zeiten anderer sehen, Abwesenheiten sehen, Serien und Termine verwalten, Berichte erstellen |
| **Leser** | Kommentieren |

- Eine neue Rolle legst du unten an: Namen tippen, unter **mit den Rechten von** eine bestehende Rolle als Muster wählen, **Rolle anlegen**.
- Eigene Rollen lassen sich löschen. Wer eine solche Rolle hat, bekommt eine Ersatzrolle, die du in der Rückfrage wählst; Besitzer geht als Ersatz nicht.
- In der Tabelle **Rechte** steht je Recht eine Zeile und je Rolle eine Spalte. Ein Häkchen wirkt sofort für alle mit dieser Rolle, auch auf Seiten, die gerade offen sind.
- Die Rechte sind nach Modulen gruppiert. Ist ein Modul aus, ruhen seine Rechte, ausgegraut mit **Modul aus**, und gelten wieder, sobald es an ist.
- Besitzer behalten immer Board verwalten und Mitglieder und Rollen verwalten (mit Schloss), damit immer jemand das Board führen kann.

Die Pinnwand prüft jedes Recht bei jeder Änderung, am Rechner wie am Telefon; was dir fehlt, blendet die Oberfläche aus oder sperrt es.

## Die Rechte im Einzelnen {#rechte}
| Recht | erlaubt |
| - | - |
| **Board verwalten** | Name, Spalten, Labels, Felder, Module und Einstellungen ändern; Spalten im Board ordnen, anlegen und löschen; gelöschte Spalten wiederherstellen; das Board als Vorlage speichern, in den Papierkorb legen und wiederherstellen |
| **Mitglieder und Rollen verwalten** | Personen einladen und entfernen, Rollen vergeben, Rollen anlegen und ihre Rechte einstellen |
| **Karten anlegen** | neue Karten in jeder Spalte anlegen, auch über Aus Text, und Karten duplizieren; Ziel sein, wenn eine Karte aus einem anderen Board umzieht |
| **Karten bearbeiten** | Titel, Beschreibung, Notizen, Felder, Checklisten und Labels ändern, dazu Zuständige, Priorität, Start und Fällig, Blockade, Cover, Arbeit oder Idee, Anhänge und Verknüpfungen |
| **Karten verschieben** | Karten zwischen Spalten ziehen und erledigen, auch über den Status und in der Liste |
| **Karten löschen** | Karten in den Papierkorb legen und von dort wiederherstellen; Karten in ein anderes Board umziehen |
| **Kommentieren** | Kommentare schreiben und Personen erwähnen |
| **Papierkorb leeren** | Karten und Spalten aus dem Papierkorb endgültig entfernen |
| **Eigene Zeit buchen** | Timer starten und eigene Zeit nachtragen (Modul Zeiterfassung) |
| **Zeiten anderer sehen** | gebuchte Zeiten aller Mitglieder auf Karten dieses Boards sehen (Modul Zeiterfassung) |
| **Zeiten anderer bearbeiten** | Zeiteinträge anderer Mitglieder ändern oder löschen (Modul Zeiterfassung) |
| **Abwesenheiten sehen** | Urlaub und Abwesenheit der Mitglieder in Kalender und Auslastung sehen (Modul Arbeitszeit und Urlaub) |
| **Serien und Termine verwalten** | wiederkehrende Karten und Termine anlegen, pausieren und ändern (Modul Serien und Termine) |
| **Berichte erstellen** | Auswertungen dieses Boards erstellen und herunterladen (Modul Berichte) |

## Mitglieder {#mitglieder}
### Einladen
1. Im Feld **Kontoname in der Kellerwolke** den Kontonamen tippen. Bekannte Personen erscheinen ab zwei Buchstaben als Vorschlag; jeder andere gültige Kontoname geht auch.
2. Hinter **als** die Rolle wählen.
3. **Einladen** klicken.

Wer schon einmal in der Pinnwand angemeldet war, sieht das Board sofort in seiner Seitenleiste. Wer noch nie da war, steht mit dem Vermerk **wartet auf die erste Anmeldung** im Board und sieht es, sobald er sich mit diesem Kellerwolke-Konto zum ersten Mal anmeldet. Ein Kontoname besteht nur aus Buchstaben, Ziffern, Punkt, Bindestrich, Unterstrich und @, ohne Leerzeichen.

### Rolle und Entfernen
- In der Tabelle **Mitglieder** wählst du je Person ihre **Rolle**; daneben steht, seit wann sie dabei ist.
- **Entfernen** nimmt eine Person nach einer Rückfrage aus dem Board. Das Board verschwindet aus ihrer Seitenleiste, an offenen Karten fällt ihre Zuständigkeit weg, ihr laufender Timer in diesem Board hält an und bucht, und aus den Serien des Boards fällt sie heraus. Gebuchte Zeiten bleiben an den Karten und im Zeitkonto.
- Bei einer wartenden Einladung heißt der Knopf **Einladung zurücknehmen**.

### Besitz übertragen
Ein Board hat immer mindestens einen Besitzer. Weitere Besitzer bekommst du, indem du Personen die Rolle Besitzer gibst. Der einzige Besitzer kann seine Rolle nicht ändern und nicht entfernt werden; er gibt den Besitz so ab:

1. In seiner Zeile **Besitz übertragen** klicken.
2. Den neuen Besitzer wählen; das kann nur jemand sein, der sich schon einmal angemeldet hat.
3. Hinter **du wirst** die eigene neue Rolle wählen.
4. **Übertragen** klicken.

Den Besitz überträgt nur der Besitzer selbst. Ab dann verwaltet der neue Besitzer Board, Rollen und Mitglieder.
