---
titel: Board und Spalten
untertitel: Spalten, Grenzen, Erledigt und was eine Karte zeigt
bereich: Boards
symbol: fa-table-columns
---
Ein Board ist eine Tafel für ein Vorhaben: Karten stehen in Spalten und wandern von links nach rechts, bis sie in der Erledigt-Spalte ankommen. Hier liest du, wie ein Board aufgebaut ist, wie du mit seinen Spalten arbeitest und was dir eine Karte auf einen Blick sagt.

## Ein Board öffnen {#aufruf}
Deine Boards stehen in der Seitenleiste unter **Boards**, sortiert nach deinen Ordnern; Boards ohne Ordner stehen zuletzt unter **Ohne Ordner**. Jedes Board trägt einen Farbpunkt und sein Kürzel. Ein Klick öffnet das Board mit seinen Spalten.

Das Kürzel (etwa PROD) ist der feste Kurzname des Boards. Es steht vor jeder Kartennummer: PROD-12 ist die zwölfte Karte des Boards PROD. Die Adresse einer Karte, etwa /board/prod/12, führt immer zu genau dieser Karte, auch wenn sie längst im Archiv liegt.

## Ein Board anlegen {#anlegen}
**Board anlegen** unter der Liste der Boards in der Seitenleiste öffnet eine Seite mit vier Schritten, rechts daneben siehst du die Vorschau des Boards:

1. **Vorlage**: deine eigenen Vorlagen zuerst, dann die mitgelieferten, zuletzt **Leer anfangen**. Jede Vorlage nennt ihre Spalten.
2. **Name und Kürzel**: das Kürzel schlägt die Pinnwand aus dem Namen vor, du kannst es überschreiben. Es hat 2 bis 6 Zeichen, vorne einen Buchstaben, nur Großbuchstaben und Ziffern; Umlaute werden ausgeschrieben (aus Übergabe wird UEBE). Es ist über alle Boards eindeutig. Ist es schon vergeben, stehen freie Kürzel zum Anklicken daneben.
3. **Ordner**: in welchem deiner Ordner das Board in deiner Seitenleiste steht.
4. **Mitglieder einladen**, freiwillig, mit dem Kontonamen der Kellerwolke.

**Board anlegen** unten legt es an, **Abbrechen** verwirft alles. Wer ein Board anlegt, ist sein Besitzer.

## Der Kopf des Boards {#kopf}
Oben steht der Name des Boards mit seiner Farbe. Daneben die Reiter **Board**, **Liste**, **Kalender** und **Zeitachse** (siehe [Liste, Kalender und Zeitachse](hilfe:ansichten)). Rechts siehst du die Mitglieder als Kürzel im Kreis (der volle Name erscheint beim Überfahren), den Knopf **Einladen** (nur mit dem Recht Mitglieder und Rollen verwalten) und den Knopf **Einstellungen**, der zu den [Einstellungen des Boards](hilfe:boardeinstellungen) führt. Die Zeile darunter nennt Ordner, Kürzel, die Zahl der Mitglieder und deine Rolle.

Darunter liegt die Werkzeugleiste: links Suche, **Filter** und Personen (siehe [Suchen und Filtern](hilfe:filter)), rechts die Knöpfe **Archiv** und **Papierkorb**. Wie die Karten einer Spalte geordnet sind, stellt jede Spalte selbst ein (siehe [Sortierung einer Spalte](hilfe:board/sortierung)).

## Spalten {#spalten}
Jede Spalte ist ein Schritt im Ablauf, etwa Offen, In Arbeit, Erledigt. Im Kopf einer Spalte stehen Farbe, Name, die Zahl ihrer Karten und das kleine Symbol ihrer Sortierung. Am Fuß einer offenen Spalte legt **Karte** eine neue Karte an (siehe [Karten anlegen und bewegen](hilfe:karten)).

Mit dem Recht Board verwalten hat jede Spalte links im Kopf einen Griff (**Ziehen zum Umsortieren**): daran ziehen ordnet die Spalten um, für alle Mitglieder.

## Sortierung einer Spalte {#sortierung}
Oben in einer Spalte steht immer das Neueste; nach unten geht es in die Vergangenheit. Wonach eine Spalte ordnet, zeigt das kleine Symbol im Kopf der Spalte; beim Überfahren erklärt es sich. Ein Klick darauf öffnet die Auswahl:

| Sortierung | Symbol | Oben steht |
| - | - | - |
| **Priorität** | Fahne | Dringend, dann Hoch, Mittel, Niedrig, ohne; bei gleicher Priorität die zuletzt angelegte |
| **Fälligkeit** | Kalenderblatt | die früheste Fälligkeit; Karten ohne Datum stehen unten |
| **Arbeitsbeginn** | Spielen | die Karte, die zuletzt in die Spalte kam, in einer Spalte wie Dran also die zuletzt begonnene |
| **Erledigung** | Uhr mit Pfeil | die zuletzt erledigte, am selben Tag die zuletzt abgelegte |
| **Anlage** | Plus | die zuletzt angelegte |
| **Von Hand** | Hand | die Reihenfolge, in die ihr die Karten gezogen habt |

Was du dort wählst, gilt nur für dich an diesem Gerät, wie das Zeitfenster. Was für alle zuerst gilt, legt **Sortierung für alle** im Menü der Spalte oder in den Einstellungen des Boards fest; in der Auswahl steht daran "für alle". Ohne eigene Einstellung ordnet die Erledigt-Spalte nach Erledigung und jede andere nach Priorität. Ein neues Board bringt die Sortierung aus seiner Vorlage mit: offene Spalten nach Priorität, Spalten wie Dran oder In Arbeit nach Arbeitsbeginn, Erledigt nach Erledigung. Eine eigene Vorlage übernimmt die Sortierung ihres Boards.

Neue Karten kommen oben in die Spalte, ebenso Kopien und Karten, die über **Status**, die Liste oder das Telefon in die Spalte wechseln. In einer sortierten Spalte steht eine hineingezogene Karte dort, wo die Sortierung sie hinstellt; innerhalb der Spalte umsortieren geht nur mit **Von Hand**.

Eine lange Spalte zeigt zuerst so viele Karten, wie **Karten je Ladeschritt** in den Einstellungen des Boards angibt, anfangs 50. Rollst du ans Ende, kommen die nächsten; **Mehr laden** am Fuß der Spalte tut dasselbe, und oben steht, wie viele geladen sind, etwa 50 von 120 geladen. Suche und Filter gehen immer über alle Karten, nicht nur über die geladenen; Zahl und Grenze im Kopf zählen ebenfalls alle.

### Neue Spalte
Mit demselben Recht steht am Ende des Spaltenstreifens der Knopf **Spalte** (**Neue Spalte am Ende anlegen**). Er öffnet ein Feld für den Namen und eine Farbwahl; vorgewählt ist eine Farbe, die noch keine Spalte trägt. Enter oder **Anlegen** legt die Spalte an, Escape oder **Abbrechen** bricht ab. Die neue Spalte kommt ans Ende, ohne Grenze und offen.

## Grenze {#grenze}
Eine offene Spalte kann eine Grenze haben: höchstens so viele Karten sollen gleichzeitig darin liegen, etwa höchstens 4 in Arbeit. Die Zahl im Kopf heißt dann zum Beispiel 3/4, und ein Balken darunter zeigt, wie voll die Spalte ist.

- Genau an der Grenze wird die Zahl bernsteinfarben.
- Darüber wird sie rot.
- Die Grenze warnt nur: Karten lassen sich trotzdem hineinziehen. Die Meldung nach dem Ablegen nennt es, etwa "In Arbeit über der Grenze (5/4)".

Gezählt werden immer alle Karten der Spalte, auch wenn eine Suche oder ein Filter gerade einige ausblendet. Die Grenze stellst du im Menü der Spalte oder in den Einstellungen des Boards ein: eine ganze Zahl von 1 bis 999, leer heißt keine Grenze. Die Erledigt-Spalte hat keine Grenze.

## Spalten einklappen {#einklappen}
Der Knopf mit dem Doppelpfeil im Kopf einer Spalte (**Einklappen: nur für dich an diesem Gerät**) klappt sie zu einem schmalen Streifen zusammen. Eingeklappt zeigt sie die Zahl ihrer Karten, ihren Namen senkrecht und je Karte einen Strich; beim Überfahren eines Strichs erscheinen Schlüssel und Titel der Karte. Ein Klick auf den Streifen klappt die Spalte wieder auf.

Eingeklappt nimmt die Spalte weiter Karten an: zieh eine Karte einfach auf den Streifen. Das Einklappen gilt nur für dich und nur auf diesem Gerät. Ob eine Spalte für alle anfangs eingeklappt steht, legt **Anfangs eingeklappt** in den Einstellungen des Boards fest; jede Person klappt danach für sich um.

## Das Menü einer Spalte {#spaltenmenue}
Mit dem Recht Board verwalten steht im Kopf jeder aufgeklappten Spalte der Knopf mit den drei Punkten (**Spalte bearbeiten: Name, Farbe, Grenze, Reihenfolge, löschen**). Er öffnet ein Menü direkt an der Spalte:

- **Name** und **Farbe**. Ein neuer Name gilt beim Verlassen des Felds oder mit Enter; Escape im Feld stellt den alten Namen wieder her.
- **Sortierung für alle** (siehe [Sortierung einer Spalte](hilfe:board/sortierung)).
- **Grenze** bei offenen Spalten, **Zeitfenster für alle** bei der Erledigt-Spalte (siehe [Zeitfenster](hilfe:board/zeitfenster)).
- **Einklappen**, **Nach links** und **Nach rechts**.
- **Zur Erledigt-Spalte machen** (siehe [Die Erledigt-Spalte](hilfe:board/erledigt)).
- **Löschen**, außer bei der Erledigt-Spalte und bei der letzten Spalte des Boards.

Escape oder ein Klick daneben schließt das Menü, ebenso jeder Befehl darin.

### Spalte löschen
**Löschen** fragt erst nach. Ist die Spalte leer, reicht **Spalte löschen**. Hat sie Karten, wählst du, wohin damit:

- **Verschieben nach** einer anderen Spalte: wie beim Ziehen beginnt das Alter neu, und verknüpfte Karten ziehen mit. Ist das Ziel die Erledigt-Spalte, gelten die Karten als erledigt, und laufende Timer buchen. Liegt das Ziel danach über seiner Grenze, sagt es ein Hinweis.
- **Mit in den Papierkorb**: die Spalte liegt mit ihren Karten im Papierkorb des Boards; **Wiederherstellen** bringt sie mit allem an ihre alte Stelle zurück.

Serien, die ihre Karten bisher in dieser Spalte angelegt haben, legen sie danach in der Spalte an, in die die Karten gewandert sind, sonst in der ersten offenen Spalte.

## Die Erledigt-Spalte {#erledigt}
Jedes Board hat genau eine Erledigt-Spalte, meist ganz rechts. Was dort hineinkommt, gilt als erledigt:

- Die Karte bekommt das Abschlussdatum von heute; eine Karte aus einer Serie bekommt ihren Termintag.
- Laufende Timer auf der Karte halten an und buchen.
- Statt der Sanduhr zeigt die Karte ihr Abschlussdatum mit Haken; eine Fälligkeit zeigt sie nicht mehr.

Die Erledigt-Spalte ordnet sich anfangs nach Erledigung: die zuletzt erledigte oben, am selben Tag die zuletzt abgelegte. Eine neu hineingezogene Karte landet oben (siehe [Sortierung einer Spalte](hilfe:board/sortierung)). Holst du eine Karte zurück in eine offene Spalte, ist sie wieder offen und verliert ihr Abschlussdatum.

**Zur Erledigt-Spalte machen** (im Menü einer Spalte oder in den Einstellungen) macht eine andere Spalte zur Erledigt-Spalte. Ihre Karten gelten dann als erledigt mit Abschluss heute, und ihre Grenze entfällt. Die bisherige Erledigt-Spalte wird eine offene Spalte; ihre Karten sind wieder offen, und ihr Alter beginnt neu.

## Zeitfenster der Erledigt-Spalte {#zeitfenster}
Damit die Erledigt-Spalte nicht endlos wächst, zeigt sie nur die Karten eines Zeitfensters. Oben in der Spalte wählst du es aus: **Heute**, **Gestern**, **Diese Woche** (ab Montag), **Dieser Monat**, **Dieses Jahr** oder **Alle**. Diese Wahl gilt nur für dich an diesem Gerät. Was für alle zuerst gilt, legt **Zeitfenster für alle** im Menü der Spalte fest; ohne Einstellung ist es Heute.

Daneben steht, wie viele Karten geladen sind, etwa 50 von 120. Die Spalte lädt seitenweise wie jede Spalte: **Mehr laden** oder Rollen ans Ende holt die nächsten.

Solange eine Suche oder ein Filter gilt, steht dort **Ohne Zeitfenster**: die Spalte zeigt dann alle passenden erledigten Karten außerhalb des Archivs.

## Alterung: die Sanduhr {#alterung}
Jede offene Karte zeigt unten eine Sanduhr mit einer Zahl: so viele Tage liegt sie schon in ihrer Spalte. Das Alter beginnt bei jedem Wechsel der Spalte neu, nicht beim Bearbeiten. So siehst du, welche Karten liegen bleiben.

| Stufe | Aussehen | ab |
| - | - | - |
| Normal | schlicht | sofort |
| Warnung | bernsteinfarben | **Warnung ab**, anfangs 4 Tage |
| Gefahr | rot | **Gefahr ab**, anfangs 8 Tage |

Beide Schwellen stellst du in den Einstellungen des Boards unter **Alterung der Karten** ein; 0 schaltet eine Stufe aus. Dieselbe Stufe zeigt **Im Status** im Kartendetail. Deine offenen Karten ab der Gefahrschwelle, die weder überfällig noch in den nächsten sieben Tagen fällig sind und auf denen kein Timer läuft, erscheinen in [Heute](hilfe:heute) unter **Liegengeblieben**.

## Was eine Karte zeigt {#karte}
Eine Karte im Board zeigt alles, was du ohne Öffnen wissen musst. Von oben nach unten:

- ein farbiger Streifen, wenn die Karte ein **Cover** hat;
- ihre **Labels**;
- **Blockiert** mit dem Grund, wenn die Karte wartet;
- der **Titel** und ein Auszug der Beschreibung;
- eigene Felder, die auf der Karte stehen sollen;
- ein Balken für den Fortschritt der Checkliste.

In der unteren Zeile:

- bei Arbeitskarten mit Zeiterfassung der Timer-Knopf oder die gebuchte Zeit, rot über der Schätzung (siehe [Zeiterfassung](hilfe:zeiterfassung));
- **Idee** mit Glühbirne bei Ideen;
- eine Kette mit Zahl bei verknüpften Karten: so viele Karten gehören zur Gruppe;
- der Schlüssel, etwa PROD-12;
- die Fälligkeit als heute, morgen, Datum oder "2 Tage über": rot, wenn überfällig, bernsteinfarben von heute bis in zwei Tagen;
- die Sanduhr mit dem Alter, in der Erledigt-Spalte stattdessen das Abschlussdatum mit Haken;
- die Checkliste als erledigt/gesamt (grün, wenn alles abgehakt ist), die Zahl der Kommentare und der Anhänge, ein Wiederholungszeichen bei Karten aus einer Serie;
- rechts ein Zeichen für die Priorität und bis zu drei Zuständige.

Beim Überfahren erscheinen oben rechts zwei Knöpfe, je nach deinen Rechten: die Kette zum Verknüpfen (nur bei Arbeitskarten) und der Papierkorb. Ändert gerade eine andere Person die Karte, zeigt sie fünf Sekunden lang deren Kürzel am Rand. Ein Klick auf die Karte, oder Enter, wenn sie den Fokus hat, öffnet das [Kartendetail](hilfe:kartendetail).

## Archiv {#archiv}
Erledigte Karten, deren Abschluss länger zurückliegt als **Archiv ab** in den Einstellungen des Boards (anfangs 365 Tage), stehen nicht mehr im Board, sondern im Archiv. Am Fuß der Erledigt-Spalte steht dazu "Älter als 365 Tage im Archiv" mit dem Verweis **Archiv**; der Knopf **Archiv** rechts in der Werkzeugleiste führt ebenso dorthin.

- Das Archiv zeigt die Karten als Tabelle, neueste zuerst, mit Abschlussdatum, Zuständigen, Labels und, mit Zeiterfassung, der gebuchten Zeit.
- Es lädt seitenweise: **Mehr laden** oder Rollen ans Ende holt die nächsten.
- Das Feld **Im Archiv suchen** durchsucht die geladenen Karten nach Titel, Schlüssel, Labels, Feldern und Kommentaren.
- Ein Klick auf eine Zeile öffnet die Karte. Zurück ins Board holst du sie, indem du im Kartendetail ihren **Status** auf eine offene Spalte stellst.
- **Zurück zum Board** führt zum Board.

Die Archivgrenze ist eine reine Ladegrenze: eine größere Zahl holt Karten zurück ins Board, sie gehen dabei nicht verloren.

## Papierkorb des Boards {#papierkorb}
Gelöschte Karten und Spalten landen im Papierkorb ihres Boards: der Knopf **Papierkorb** rechts in der Werkzeugleiste, die Zahl daneben nennt die Einträge. Jeder Eintrag zeigt, wer ihn wann gelöscht hat, wo er lag und was daran hängt: Labels, Zuständige, gebuchte Zeit, Kommentare, Anhänge und Verknüpfungen.

- **Wiederherstellen** bringt eine Karte mit demselben Schlüssel an ihre alte Stelle zurück, mit Kommentaren, Anhängen und Verknüpfung. Gibt es ihre Spalte nicht mehr, kommt sie in die erste Spalte. Eine Spalte kommt mit allen Karten an ihren alten Platz. Labels, Felder und Zuständige, die es im Board inzwischen nicht mehr gibt, fallen dabei weg.
- **Endgültig entfernen** an einem Eintrag und **Papierkorb leeren** oben fragen vorher nach und nennen, was verloren geht. Das lässt sich nicht rückgängig machen; die gebuchte Zeit bleibt in den Zeitkonten.

Karten wiederherstellen darf, wer das Recht Karten löschen hat, Spalten, wer das Recht Board verwalten hat. Endgültig entfernen darf nur, wer das Recht Papierkorb leeren hat; was deine Rolle nicht darf, steht oben über der Liste. Ein ganzes gelöschtes Board liegt im Papierkorb deiner [persönlichen Einstellungen](hilfe:einstellungen).
