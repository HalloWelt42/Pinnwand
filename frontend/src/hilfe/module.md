---
titel: Module und Verbindungen
untertitel: Zusatzteile je Board einschalten und an andere Apps anbinden
bereich: Verbund
symbol: fa-puzzle-piece
---
Jedes Board bringt von Haus aus Karten, Spalten, Labels, Checklisten und Kommentare mit. Alles Weitere kommt über Module dazu: Zeiterfassung, Arbeitszeit, Serien, Berichte und die Anbindungen an andere Apps. Du schaltest sie je Board ein, damit jedes Board nur zeigt, was es wirklich braucht.

## Was ein Modul ist {#was}
Ein Modul ist ein Zusatzteil, das du in einem Board ein- oder ausschaltest. Ist es an, zeigt die Pinnwand seine Teile: neue Einträge in der Seitenleiste, Knöpfe auf den Karten, Abschnitte im Kartendetail, eigene Felder und eigene Rechte. Ist es aus, verschwinden diese Teile wieder.

Es gibt zwei Arten:

- **Fachmodule** arbeiten ganz in der Pinnwand: Zeiterfassung, Arbeitszeit und Urlaub, Serien und Termine, Berichte.
- **Anbindungen an andere Apps** holen sich ihre Arbeit von einem anderen Dienst: Transkripte, Vorlesen und KI an der Karte. Sie wirken erst, wenn die Verbindung zu diesem Dienst steht (siehe [Verbindungen](hilfe:module/verbindungen)).

Ein Modul gilt immer für ein ganzes Board und damit für alle seine Mitglieder.

## Die Fachmodule {#fachmodule}
| Modul | Was es zeigt | Feld | Rechte |
|---|---|---|---|
| **Zeiterfassung** | In der Seitenleiste **Zeiten** (dein Stundenzettel der Woche), im Kopf deine Stunden von heute und der Woche und dein laufender Timer, auf jeder Arbeitskarte der Timer, im Kartendetail der Abschnitt **Zeiterfassung**, beim Anlegen die Wahl **Arbeit** oder **Idee**, am Telefon der Reiter **Zeit** | Schätzung | Eigene Zeit buchen, Zeiten anderer sehen, Zeiten anderer bearbeiten |
| **Arbeitszeit und Urlaub** | In der Seitenleiste **Arbeitszeit** (Zeitkonto, Kalender, Urlaub, Team mit der Auslastung der Mitglieder), im Kalender des Boards die Abwesenheiten | keins | Abwesenheiten sehen |
| **Serien und Termine** | In der Seitenleiste **Serien und Termine**, im Kalender des Boards Termine und Serien, in Heute die Termine und Serien des Tages | Serie | Serien und Termine verwalten |
| **Berichte** | In der Seitenleiste **Berichte** mit Auswertungen als PDF, Tabelle oder Text | keins | Berichte erstellen |

Mehr dazu in [Zeiterfassung](hilfe:zeiterfassung), [Arbeitszeit und Urlaub](hilfe:arbeitszeit), [Serien und Termine](hilfe:serien) und [Berichte](hilfe:berichte).

Die Einträge in der Seitenleiste erscheinen, sobald mindestens eines deiner Boards das Modul eingeschaltet hat. Hat keines deiner Boards es an, ist der Eintrag weg.

## Die Anbindungen {#anbindungen}
| Modul | Was es zeigt | Braucht | Feld |
|---|---|---|---|
| **Transkripte** | Im Kartendetail den Abschnitt **Transkripte**, am Telefon unter **Erfassen** den Knopf **Sprechen** | die Transkription | Transkript-Marken |
| **Vorlesen** | Lautsprecher-Knöpfe an Beschreibung, Karte und Kommentaren, den Knopf **Vorlesen** in Heute und bei den Berichten | die App Vorlesen | keins |
| **KI an der Karte** | Zauberstab-Knöpfe im Kartendetail, **Vorschlagen** an der Checkliste, **Aus Text** beim Anlegen in einer Spalte | die Leitstelle | keins |

Die Anbindungen haben keine eigenen Rechte. Sie richten sich nach den Rechten des Boards, etwa **Karten bearbeiten** oder **Karten anlegen**. Mehr dazu in [Transkripte](hilfe:transkripte), [Vorlesen](hilfe:vorlesen) und [KI an der Karte](hilfe:ki).

## Module einschalten {#einschalten}
1. Öffne das Board und klicke im Kopf des Boards auf **Einstellungen**. Alternativ findest du unter **Einstellungen** in der Seitenleiste oben je Board einen Knopf zu seinen Einstellungen.
2. Wähle den Reiter **Module** (der zweite Reiter).
3. Jedes Modul steht dort als eigene Kachel mit Symbol, Namen, dem Zustand **an** oder **aus** und einem Schalter. Darunter steht kurz, was es bringt: seine **Ansichten**, seine **Felder** und seine **Rechte**. Fährst du mit der Maus über ein Recht, erklärt es sich.
4. Klicke auf den Schalter. Das Modul ist sofort für alle Mitglieder an oder aus.

Die Meldung unten rechts bestätigt es, etwa "Zeiterfassung in Haus eingeschaltet", und bietet **Rückgängig** an. Einen Speichern-Knopf gibt es nicht.

Schalten darf, wer im Board das Recht **Board verwalten** hat. Fehlt es dir, siehst du den Reiter nur: oben steht "nur ansehen: dir fehlt das Recht Board verwalten", und die Schalter sind ausgegraut.

## Was beim Abschalten passiert {#abschalten}
Abschalten blendet ein Modul in Board, Karten und Rollen aus. Seine Daten bleiben und sind beim Einschalten wieder da. Auf der Kachel steht dann "Ausgeblendet; die Daten bleiben."

Im Einzelnen:

- Ansichten, Knöpfe und Abschnitte des Moduls verschwinden aus dem Board und den Karten.
- Die Felder des Moduls verschwinden. Im Reiter **Felder** stehen sie unter **Felder der Module**: Ein Modul bringt sie mit und nimmt sie beim Abschalten wieder mit.
- Die Rechte des Moduls ruhen. Im Reiter **Rollen und Rechte** steht bei ihnen **Modul aus** mit dem Satz "Diese Rechte ruhen und gelten wieder, sobald das Modul an ist." Die Häkchen bleiben, wie sie sind.
- Gebuchte Zeiten, Serien, Termine und verknüpfte Transkript-Stellen bleiben gespeichert.
- **Zeiterfassung aus:** Alle laufenden Timer in diesem Board halten an und werden gebucht, von allen Mitgliedern. Lief dein eigener Timer, nennt die Meldung die gebuchte Zeit, etwa "dein Timer ist gestoppt, 0:25 gebucht".
- **Serien und Termine aus:** Die Pinnwand legt in diesem Board keine neuen Karten aus Serien mehr an, bis du das Modul wieder einschaltest.

## Module aus Vorlagen {#vorlagen}
Wenn du ein Board anlegst, bringt die gewählte Vorlage ihre Module gleich mit. Die Vorschau beim Anlegen zeigt, welche es sind.

| Vorlage | Module |
|---|---|
| **Leer anfangen** | keine |
| **Aufgaben** | Zeiterfassung, Serien und Termine, Vorlesen |
| **Projekt** | alle sieben |
| **Ideen** | Transkripte, Vorlesen, KI an der Karte |

Speicherst du ein Board als eigene Vorlage (Reiter **Allgemein**, **Als Vorlage speichern**), nimmt die Vorlage die Module mit, die in diesem Board gerade an sind. Danach kannst du die Module jedes Boards jederzeit im Reiter **Module** ändern.

## Verbindungen zu anderen Apps {#verbindungen}
Die Anbindungen sprechen mit eigenen Diensten. Eine Verbindung besteht aus der Adresse des Dienstes und, wo nötig, einem Schlüssel.

| Dienst | Wofür | Was eingetragen wird |
|---|---|---|
| **Leitstelle** | KI an der Karte | Adresse und Schlüssel der Leitstelle, dazu wahlweise das Modell (ohne Wahl entscheidet die Leitstelle) |
| **Transkription** | Transkripte und Spracheingabe | Adresse |
| **Vorlesen** | Vorlesen | Adresse (Stimme und Tempo wählt man in der App Vorlesen) |
| **Kellerwolke** | Anmeldung, Anhänge, Berichte | Adresse und App-Schlüssel |

Diese Verbindungen gelten für die ganze Pinnwand, nicht je Board. Du trägst sie unter **Einstellungen**, Reiter
**App und Verbindungen** ein: Gruppe **Verbindungen** für die Adressen und Schlüssel, Gruppe **KI an der Karte** für das
Modell. Geänderte Werte tragen einen Punkt, bis du sie in der Leiste unten
mit **Speichern** übernimmst; **Verwerfen** lässt alles, wie es war (siehe
[App und Verbindungen](hilfe:einstellungen/app)).

Die Kellerwolke trägt man bei der ersten Einrichtung ein: Solange sie fehlt, zeigt die Pinnwand statt der Anmeldung die Seite **erste Einrichtung** mit **Adresse der Kellerwolke**, **App-Schlüssel** und dem Knopf **Prüfen und einrichten**. Ob die Verbindung steht, zeigt der Punkt **Kellerwolke** in der Fußleiste; fährst du mit der Maus darüber, steht dort die Adresse oder der Grund, warum es nicht geht.

## Wenn eine Verbindung fehlt {#verbindung-fehlt}
Ein Modul kann an sein, ohne dass sein Dienst verbunden ist. Dann zeigt die Pinnwand seine Knöpfe gar nicht erst. Den Grund nennt der Reiter **Module**: Unter der Kachel steht mit einem Stecker-Symbol, was fehlt.

| Modul | Hinweis auf der Kachel |
|---|---|
| **KI an der Karte** | "Die Leitstelle ist in den Einstellungen der App noch nicht eingerichtet; bis dahin erscheinen keine Vorschläge." |
| **Transkripte** | "Die Adresse der Transkription fehlt in den Einstellungen der App; bis dahin gibt es keine Transkripte." |
| **Vorlesen** | "Die Adresse der App Vorlesen fehlt in den Einstellungen der App; bis dahin wird nichts vorgelesen." |

Ist die Verbindung eingetragen, aber der Dienst gerade nicht erreichbar oder lässt er dein Konto nicht zu, merkst du es erst beim Benutzen: Dann nennt die Pinnwand den Grund an der Stelle, an der du geklickt hast, etwa "Die Transkription ist gerade nicht erreichbar" oder "Die Leitstelle kann gerade nicht". Alles andere in der Pinnwand läuft dabei ganz normal weiter.
