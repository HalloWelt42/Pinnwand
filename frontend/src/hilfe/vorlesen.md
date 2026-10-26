---
titel: Vorlesen
untertitel: Karten, Kommentare, den Tagesplan und Berichte anhören
bereich: Verbund
symbol: fa-volume-high
---
Mit dem Modul Vorlesen liest dir die Pinnwand Texte laut vor: die Beschreibung oder die ganze Karte, einen Kommentar, deinen Tagesplan und Berichte. Das hilft, wenn du gerade nicht lesen kannst oder willst. Gesprochen wird über die Vertonung, eine eigene App, die aus Text Sprache macht.

## Was du brauchst {#voraussetzungen}
- Das Modul **Vorlesen** ist an (siehe [Module einschalten](hilfe:module/einschalten)). An Karten und Kommentaren muss es im Board dieser Karte an sein. Für Heute und die Berichte genügt es, wenn eines deiner Boards es an hat.
- Die Vertonung ist mit der Pinnwand verbunden. Fehlt die Verbindung, gibt es keine Lautsprecher-Knöpfe; warum, sagt der Reiter **Module** (siehe [Wenn eine Verbindung fehlt](hilfe:module/verbindung-fehlt)).
- Die Pinnwand fragt die Vertonung in deinem Namen. Dein Konto muss die Vertonung also nutzen dürfen.

## Was vorgelesen werden kann {#was}
| Was | Wo | Knopf |
|---|---|---|
| Die ganze Karte: Schlüssel und Titel, Beschreibung, offene Punkte der Checkliste | Kopf des Kartendetails | Lautsprecher "Karte vorlesen: Titel, Beschreibung, offene Punkte" |
| Die Beschreibung | Kartendetail, rechts neben der Überschrift **Beschreibung** (nur, wenn sie Text hat) | Lautsprecher "Vorlesen" |
| Ein Kommentar, eingeleitet mit "Anna schrieb:" | Kartendetail, Reiter **Kommentare**, in der Kopfzeile jedes Kommentars | Lautsprecher "Kommentar vorlesen" |
| Dein Tagesplan | Seite [Heute](hilfe:heute), oben im Kopf | **Vorlesen** |
| Ein Bericht in der Vorschau | Seite [Berichte](hilfe:berichte), Kopf der **Vorschau** | **Vorlesen** |
| Ein erstellter Bericht im Format Markdown | Seite Berichte, Liste **Erstellte Berichte** | Lautsprecher "Vorlesen" |

Der Tagesplan beginnt mit "Dein Tag am" und dem Datum. Dann folgen deine überfälligen Karten (mit "fällig seit"), die heute fälligen, die Karten aus Serien von heute mit Uhrzeit und deine Termine von heute mit Zeit und Ort. Ist nichts fällig, hörst du "Heute ist nichts fällig und nichts überfällig."

Einen Bericht liest die Pinnwand mit Titel und Zeitraum vor, dann je Abschnitt die Zeilen, jeden Wert mit dem Namen seiner Spalte, und am Ende die Summe.

Formatierungen wie fett oder Listenzeichen liest sie nicht mit, nur den Text.

## Starten und anhalten {#anhalten}
1. Tippe auf den Lautsprecher oder auf **Vorlesen**.
2. Der erste Satz erklingt, sobald die Vertonung ihn gesprochen hat. Danach folgt Satz für Satz ohne Lücke.
3. Solange vorgelesen wird, zeigt der Knopf ein Quadrat und heißt "Vorlesen anhalten", in Heute und bei den Berichten **Stopp**.
4. Ein zweites Tippen auf denselben Knopf hält an. Was noch klingt, verstummt sofort; der Rest wird nicht mehr gelesen.

Am Ende des Textes hört das Vorlesen von selbst auf, und der Knopf zeigt wieder den Lautsprecher.

## Immer nur eins auf einmal {#ein-ton}
Es klingt immer nur ein Text gleichzeitig:

- Tippst du auf einen anderen Lautsprecher, endet das laufende Vorlesen, und das neue beginnt.
- Startest du im Kartendetail eine Transkript-Stelle zum Abspielen (siehe [Abspielen ab der Stelle](hilfe:transkripte/abspielen)), endet das Vorlesen.

## Stimme und Tempo {#stimme}
Stimme und Tempo sind für die ganze Pinnwand eingestellt und gelten für alle gleich. Sie gehören zu den Einstellungen der App, nicht zu deinen persönlichen Einstellungen.

- **Stimme:** eine Stimme aus dem Katalog der Vertonung oder eine private Stimme, die die Vertonung für die Pinnwand freigegeben hat. Ohne Wahl spricht die Vorgabe der Vertonung.
- **Tempo:** 1 ist das gewohnte Tempo. Kleinere Werte bis 0,5 lesen langsamer, größere bis 2 schneller.

Gesprochen wird deutsch. Zahlen und Abkürzungen spricht die Vertonung ausgeschrieben.

## Grenzen {#grenzen}
- Am Stück liest die Pinnwand höchstens 40.000 Zeichen vor. Ein längerer Text wird abgelehnt mit "Der Text ist länger als 40000 Zeichen".
- Lange Texte teilt die Pinnwand an Satzgrenzen in Teile und lässt sie nacheinander sprechen. Du hörst davon nichts: Es klingt wie ein Stück.
- Leere Texte gibt es nicht zu hören; die Beschreibung zeigt ihren Lautsprecher erst, wenn sie Text hat.

## Wenn es stumm bleibt {#fehler}
Geht das Vorlesen nicht oder bricht es ab, nennt die Meldung unten rechts den Grund, eingeleitet mit "Vorlesen:".

| Meldung | Was sie heißt |
|---|---|
| "Die Vertonung lässt das nicht zu: ..." | Dein Konto oder die eingestellte Stimme ist in der Vertonung nicht freigegeben. |
| "Die Vertonung ist gerade nicht erreichbar (...)" | Die Vertonung läuft gerade nicht oder ist nicht erreichbar. Später noch einmal versuchen. |
| "Vorlesen ist im Board ... aus" | Jemand hat das Modul in diesem Board inzwischen ausgeschaltet. |
| "Vorlesen ist in keinem deiner Boards an" | Für Heute und Berichte muss mindestens eines deiner Boards Vorlesen an haben. |
| "Vorlesen brach ab: keine Verbindung zur App" | Die Verbindung zur Pinnwand riss ab. |
| "Der Bericht ließ sich nicht laden" | Der erstellte Bericht war nicht abrufbar. |

Hörst du nichts, obwohl der Knopf das Quadrat zeigt, prüfe die Lautstärke deines Geräts.
