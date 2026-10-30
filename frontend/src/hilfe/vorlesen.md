---
titel: Vorlesen
untertitel: Karten, Notizen, Checklisten, Kommentare, Verlauf, Tagesplan und Berichte anhören
bereich: Verbund
symbol: fa-volume-high
---
Mit dem Modul Vorlesen liest dir die Pinnwand Texte laut vor: die ganze Karte, Beschreibung, Notizen und Checkliste, einen oder alle Kommentare, den Verlauf, deinen Tagesplan und Berichte, am Rechner wie am Telefon. Das hilft, wenn du gerade nicht lesen kannst oder willst. Gesprochen wird über die App Vorlesen, die eine Stelle für Sprachausgabe aller eigenen Apps.

## Was du brauchst {#voraussetzungen}
- Das Modul **Vorlesen** ist an (siehe [Module einschalten](hilfe:module/einschalten)). An Karten und Kommentaren muss es im Board dieser Karte an sein. Für Heute und die Berichte genügt es, wenn eines deiner Boards es an hat.
- Die App Vorlesen ist mit der Pinnwand verbunden. Fehlt die Verbindung, gibt es keine Lautsprecher-Knöpfe; warum, sagt der Reiter **Module** (siehe [Wenn eine Verbindung fehlt](hilfe:module/verbindung-fehlt)).
- Die Pinnwand fragt die App Vorlesen in deinem Namen. Dein Konto muss sie also nutzen dürfen.

## Was vorgelesen werden kann {#was}
| Was | Wo | Knopf |
|---|---|---|
| Die ganze Karte: Schlüssel und Titel, Beschreibung, offene Punkte der Checkliste | Kopf des Kartendetails | Lautsprecher "Karte vorlesen: Titel, Beschreibung, offene Punkte" |
| Die Beschreibung | Kartendetail, rechts neben der Überschrift **Beschreibung** (nur, wenn sie Text hat) | Lautsprecher "Vorlesen" |
| Die Notizen | Kartendetail, rechts neben der Überschrift **Notizen** (nur, wenn sie Text haben) | Lautsprecher "Vorlesen" |
| Die Checkliste: erst die offenen, dann die erledigten Punkte | Kartendetail, neben der Überschrift **Checkliste** | Lautsprecher "Checkliste vorlesen" |
| Ein Kommentar, eingeleitet mit "Anna schrieb:" | Kartendetail, Reiter **Kommentare**, in der Kopfzeile jedes Kommentars | Lautsprecher "Kommentar vorlesen" |
| Alle Kommentare, der neueste zuerst, je mit Person und Zeit | Kartendetail, rechts in der Zeile der Reiter, solange **Kommentare** gewählt ist | Lautsprecher "Alle Kommentare vorlesen" |
| Der ganze Verlauf, der neueste Eintrag zuerst | dieselbe Stelle, solange **Verlauf** gewählt ist | Lautsprecher "Ganzen Verlauf vorlesen" |
| Am Telefon: die ganze Karte und alle Kommentare | Karte am Telefon: **Karte vorlesen** unter dem Titel, Lautsprecher neben **Kommentare** | wie am Rechner |
| Dein Tagesplan | Seite [Heute](hilfe:heute), oben im Kopf | **Vorlesen** |
| Ein Bericht in der Vorschau | Seite [Berichte](hilfe:berichte), Kopf der **Vorschau** | **Vorlesen** |
| Ein erstellter Bericht im Format Markdown | Seite Berichte, Liste **Erstellte Berichte** | Lautsprecher "Vorlesen" |

Der Tagesplan beginnt mit "Dein Tag am" und dem Datum. Dann folgen deine überfälligen Karten (mit "fällig seit"), die heute fälligen, die Karten aus Serien von heute mit Uhrzeit und deine Termine von heute mit Zeit und Ort. Ist nichts fällig, hörst du "Heute ist nichts fällig und nichts überfällig."

Einen Bericht liest die Pinnwand mit Titel und Zeitraum vor, dann je Abschnitt die Zeilen, jeden Wert mit dem Namen seiner Spalte, und am Ende die Summe.

Formatierungen wie fett oder Listenzeichen liest sie nicht mit, nur den Text.

## Starten und anhalten {#anhalten}
1. Tippe auf den Lautsprecher oder auf **Vorlesen**.
2. Die Pinnwand wartet einen kleinen Vorlauf ab, bis genug gesprochen bereitliegt, meist etwa eine Sekunde. Danach folgt Satz für Satz ohne Lücke.
3. Solange vorgelesen wird, zeigt der Knopf ein Quadrat und heißt "Vorlesen anhalten", in Heute und bei den Berichten **Stopp**.
4. Ein zweites Tippen auf denselben Knopf hält an. Was noch klingt, verstummt sofort; der Rest wird nicht mehr gelesen.

Am Ende des Textes hört das Vorlesen von selbst auf, und der Knopf zeigt wieder den Lautsprecher.

## Vorlauf {#vorlauf}
Damit das Vorlesen nicht stockt, beginnt es erst, wenn mindestens anderthalb Sekunden Ton bereitliegen, bei einem kurzen Text, sobald er ganz gesprochen ist. Die Pinnwand misst dabei, wie schnell der Ton kommt. Ist der Rechner, der spricht, ausgelastet und kommt der Ton langsamer, als vorgelesen wird, wartet sie entsprechend länger, höchstens 20 Sekunden. Reißt der Ton trotzdem einmal ab, wartet sie, bis wieder genug da ist, und plant beim nächsten Mal mehr Vorlauf ein. Läuft es danach flüssig, wird der Vorlauf nach und nach wieder kürzer. Das gilt nur in diesem Browser, bis zum Neuladen.

## Immer nur eins auf einmal {#ein-ton}
Es klingt immer nur ein Text gleichzeitig:

- Tippst du auf einen anderen Lautsprecher, endet das laufende Vorlesen, und das neue beginnt.
- Startest du im Kartendetail eine Transkript-Stelle zum Abspielen (siehe [Abspielen ab der Stelle](hilfe:transkripte/abspielen)), endet das Vorlesen.

## Stimme und Tempo {#stimme}
Stimme, Sprache und Tempo wählst du nicht in der Pinnwand, sondern in der App Vorlesen, Seite **Vorlesen**; dort kannst du eine Probe hören, bevor du speicherst. Die Wahl gilt für alle Apps, die vorlesen, also auch für die Pinnwand.

- **Stimme:** eine der festen Stimmen aus dem Katalog des Sprechdienstes. Geklonte Stimmen gibt es dort nicht.
- **Tempo:** 1 ist das gewohnte Tempo. Kleinere Werte bis 0,5 lesen langsamer, größere bis 2 schneller.

Ab Werk wird deutsch gesprochen.

## Grenzen {#grenzen}
- Am Stück liest die Pinnwand höchstens 40.000 Zeichen vor. Ein längerer Text wird abgelehnt mit "Der Text ist länger als 40000 Zeichen".
- Lange Texte teilt die App Vorlesen an Satzgrenzen und spricht sie Satz für Satz. Du hörst davon nichts: Es klingt wie ein Stück.
- Leere Texte gibt es nicht zu hören; die Beschreibung zeigt ihren Lautsprecher erst, wenn sie Text hat.

## Wenn es stumm bleibt {#fehler}
Geht das Vorlesen nicht oder bricht es ab, nennt die Meldung unten rechts den Grund, eingeleitet mit "Vorlesen:".

| Meldung | Was sie heißt |
|---|---|
| "Die App Vorlesen lässt das nicht zu: ..." | Dein Konto darf die App Vorlesen nicht nutzen. |
| "Die App Vorlesen ist gerade nicht erreichbar (...)" | Die App Vorlesen läuft gerade nicht oder ist nicht erreichbar. Später noch einmal versuchen. |
| "Der Sprechdienst kann gerade nicht: ..." | Der Rechner, der spricht, schläft oder der Sprechdienst startet gerade. Später noch einmal versuchen. |
| "Vorlesen ist im Board ... aus" | Jemand hat das Modul in diesem Board inzwischen ausgeschaltet. |
| "Vorlesen ist in keinem deiner Boards an" | Für Heute und Berichte muss mindestens eines deiner Boards Vorlesen an haben. |
| "Vorlesen brach ab: keine Verbindung zur App" | Die Verbindung zur Pinnwand riss ab. |
| "Der Bericht ließ sich nicht laden" | Der erstellte Bericht war nicht abrufbar. |

Hörst du nichts, obwohl der Knopf das Quadrat zeigt, prüfe die Lautstärke deines Geräts.
