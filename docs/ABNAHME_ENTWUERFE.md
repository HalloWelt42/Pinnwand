# Abnahme der Entwürfe gegen die Board-Mechanik

**Zweck:** Prüft für jede Mechanik der alten Pinnwand (`docs/BOARD_MECHANIK.md`, M-01 bis M-126, Fassung 0.74.0), ob und
wo die Entwürfe des Neubaus (`mockups/`) sie abbilden. Maß sind die Mechanik und die Entscheidungen in `docs/ENTWURF.md`
(E-01 bis E-22).

**Stand:** 27.10.2026, Datum der Beispielwelt der Entwürfe (geprüft am 25.10.2026). Zweite Prüfung nach den Commits
05f816e bis 5c41d9a: alle Mechaniken, die vorher "teilweise" oder "fehlt" standen, neu gegen den Code bewertet, die
übrigen in Stichproben auf Brüche geprüft; die Typprüfung läuft ohne Fehler und Warnungen. Gelesen wurde der Code unter
`mockups/src/`; alle Pfade in der Spalte "Wo" sind relativ dazu, Adressen wie `/board/prod` laufen unter
http://localhost:5398. "(Gegenprobe)" heißt: im Browser der Entwürfe nachgestellt. "(aus dem Code)" heißt: aus dem Code
abgeleitet, nicht nachgestellt.

## In der App gebaut (Stufe 1, 25.10.2026)

Was die Entwürfe offen ließen oder nur vorführten, ist in der App so gebaut:

- M-01: Die Seitenleiste zeigt Boards ohne Ordner in einer eigenen Gruppe (Abfrage `boardGruppen`, auch am Telefon).
- M-06: Der Ereignisstrom nennt, wer änderte; die Karte zeigt die Person kurz, die Meldung sagt es, eine eigene
  Meldung mit Rückgängig bleibt stehen.
- M-09: Ein Pfad öffnet jede Karte, eine archivierte holt das Board einzeln vom Server.
- M-11: Ein Board, das es für dich nicht mehr gibt (gelöscht, Mitgliedschaft entzogen), verlässt die Ansicht mit
  Meldung zu Heute; abgelehnte Änderungen nennen den Grund des Servers.
- M-26: Das Archiv lädt seitenweise vom Server, mit Nachladen beim Rollen und der Gesamtzahl im Kopf.
- M-55: Ein Konflikt entsteht nur, wenn dasselbe Feld inzwischen anders ist; das Detail fragt dann nach.
- Neu, ohne Vorbild in der alten App: Karten ziehen in ein anderes Board (Kartendetail und Telefon), siehe ENTWURF,
  Abschnitt 11.

## In der App gebaut (Stufe 2, 25.10.2026)

- M-80 bis M-90: Timer, Buchen, Deckel und Zeiteinträge rechnet der Server (`regeln/zeit.py`); eine Sitzung über
  die Zeitumstellung zählt die echte Dauer. Die Rückfrage nach dem Deckel nimmt das echte Ende und bucht die Sitzung von
  ihrem Beginn bis dahin neu.
- M-83: Fremde Timer und Zeiten sieht nur, wer im Board das Recht "Zeiten anderer sehen" hat; ohne das Recht ist die
  Zeit einer Karte die eigene und heißt im Detail so. Der Ereignisstrom ersetzt die Abfrage alle 60 Sekunden.
- M-84: Auch das Abschalten der Zeiterfassung beendet die Timer des Boards und bucht.
- M-85: Solange der eigene Timer läuft, tickt die Uhr im Sekundentakt.
- Team: die Stunden kommen als Tagessummen vom Server (aus allen Boards, ohne Einträge), nur mit dem Recht
  "Abwesenheiten sehen" für alle Mitglieder.
- Vor der ersten Fassung des Zeitkontos gibt es kein Soll.

## In der App gebaut (Stufe 3, 25.10.2026)

- M-106, M-107: Die Karten der Serientage legt der Server an (beim Anlegen, Ändern, Fortsetzen und einmal je Tag);
  ob ein Tag angefasst ist, steht an seiner Karte (Spalte, erledigt, Zeit, Verlauf), nicht in einer eigenen Liste.
- M-108: Auch eine Serienkarte, die in ein anderes Board zieht, lässt ihren Tag aus.
- M-109, M-110: Ändern und Pause nehmen unberührte Vorbuchungen ohne Papierkorb zurück, Löschen legt sie in den
  Papierkorb; eine gelöschte Zielspalte gibt ihren Serien die Spalte, in die ihre Karten wanderten.
- M-111: Bestätigte Terminzeit zählt ins Ist und steht im Stundenzettel (Entscheidung des Nutzers); einen bestätigten
  Eintrag löschen nimmt die Bestätigung zurück. Serienkarten bekommen keinen Hinweis "fällig".
- Im Terminformular stehen Beginn und Ende wieder schmal nebeneinander (im Entwurf liefen sie über die ganze Breite).

## In der App gebaut (Stufe 4, Berichte, 25.10.2026)

- Den Inhalt eines Berichts rechnet der Server; die Vorschau zeigt genau ihn, mit Dateiname, und bei Markdown den Text
  der Datei. Das PDF ist mit Barlow gesetzt, die Tabelle ist CSV mit Semikolon.
- Im Stundennachweis stehen außer dir nur Personen, deren Abwesenheiten du siehst (wie im Team); im Entwurf war es das
  Recht "Zeiten anderer sehen". In Board-Berichten zählt die Zeit anderer nur mit diesem Recht.
- Vorlesen eines Berichts kommt mit der Anbindung der Vertonung; bis dahin steht dort nur Herunterladen.

## In der App gebaut (Stufe 4, Push, 25.10.2026)

- Push aufs Telefon über den Baustein des Appkerns: ein Telefon erlaubt Mitteilungen unter Hinweise (am Telefon), die
  Einstellungen am Rechner zeigen die Schritte, die Geräte und senden eine Testmitteilung; ein Tippen auf eine
  Mitteilung führt zur Karte. Welche Wege es gibt und was gilt, kommt jetzt vom Server.

## In der App gebaut (Stufe 4, KI an der Karte, 25.10.2026)

- Vorschläge über die Leitstelle: Zusammenfassung (Zauberstab im Kopf des Kartendetails, Kasten wie im Entwurf mit "In
  die Notizen übernehmen"), "Vorschlagen" an der Checkliste mit Haken je Punkt, Labels (Zauberstab hinter den Labels,
  M-115) und Karten aus Text in der Schnelleingabe der Spalte ("Aus Text"; alle angehakten in einer Änderung, ein
  Rückgängig). Übernommen wird nur, was man bestätigt. Ohne eingerichtete Leitstelle zeigt die Oberfläche keine
  Vorschläge, die Seite Module sagt warum. Am Telefon bleibt Bearbeiten am Rechner, also auch die Vorschläge.

## In der App gebaut (Stufe 4, Transkripte, 26.10.2026)

- Stellen aus der Transkription an der Karte (M-112 und M-113 in einem): suchen wie in der Transkription, eine Fundstelle
  oder das ganze Transkript verknüpfen; je Stelle Name, Zeit, Sprecher und Text aus dem Transkript, Abspielen ab der
  Stelle in der Pinnwand, "In der Transkription öffnen", eine Notiz und mit KI an der Karte ein Vorschlag dafür; lösen
  mit Rückgängig. Gefragt wird im Auftrag der Person: wer die Transkription nicht nutzen darf, sieht die Stellen, hört
  sie aber nicht.
- Spracheingabe beim Erfassen am Telefon: der Text kommt nach dem Stopp (Nutzer: "Nach dem Stopp"), nicht mitlaufend wie
  im Entwurf; erster Satz Titel, alles Beschreibung, mit Hinweis zum Prüfen.

## Nachbesserungen in der App (25.10.2026)

- M-74: Beim Zusammenführen zweier Verknüpfungen nennt die Meldung, ob die Zeit geteilt wird und welche Einstellung
  gilt.
- M-09: Ein Hinweis trägt den Schlüssel seiner Karte und führt so auch zu einer archivierten oder umgezogenen Karte;
  am Telefon öffnet ein Pfad jetzt auch eine Karte, die nicht im Stand liegt.
- Rückgängig geht auch, wenn jemand den Hinweis, den die Änderung erzeugte, schon gelesen hat (der Hinweis geht mit).
- Eine überfällige Karte, deren Timer den Start auf heute setzt, bleibt in allen Feldern bearbeitbar; abgelehnt wird
  "Start nach Fällig" nur, wenn jemand Start oder Fällig selbst so setzt.
- Vorschläge der KI und das Umsetzen der Sprache warten ohne die Zeitgrenze von 20 Sekunden der Oberfläche (ein Modell
  braucht oft länger); abbrechen kann man selbst.
- Der Auszug der Beschreibung auf der Karte zeigt keine Zeichen des Markdowns mehr; steht am Telefon nur ein Knopf in
  der Leiste unten, nimmt er die ganze Breite.
- Die Knöpfe der Schnelleingabe stehen in einer Zeile (eine Regel für den Knopf "Karte" im Fuß der Spalte zog sie auf
  volle Breite); "Erstellt ... von" hat wieder sein Leerzeichen.

## Zählung

| Stand | Zahl |
|---|---|
| abgebildet | 108 |
| teilweise | 1 |
| fehlt | 3 |
| später | 7 |
| bewusst anders | 3 |
| Fehler behoben | 4 |
| **Summe** | **126** |

## Regeln der Bewertung

- **abgebildet**: wirkt in den Entwürfen wie beschrieben oder besser. Behebt der Entwurf dabei einen bekannten Fehler der
  alten App, steht das in der Bemerkung.
- **teilweise**: sichtbar, aber ein Teil der Wirkung fehlt oder ist nur angedeutet. Tote Regler (Knöpfe, Felder oder
  Einstellungen ohne Wirkung) zählen nicht als abgebildet.
- **fehlt**: nirgends zu finden.
- **später**: wird in den Entwürfen bewusst nicht gebaut, weil es erst in der echten App Sinn ergibt (Laden über das
  Netz, Uhr, neue Fassungen) oder zu einer Anbindung einer späteren Stufe gehört; mit der Stufe aus `ENTWURF.md`
  Abschnitt 5 und einem Satz Begründung.
- **bewusst anders**: durch eine Entscheidung in `ENTWURF.md` ersetzt, mit E-Nummer.
- **Fehler behoben**: nur dort, wo die Mechanik im Kern ein Fehlverhalten der alten App beschreibt und die Entwürfe es
  richtig machen.
- Querschnitt, damit eine Lücke nicht an vielen Stellen zählt: Verlaufszeilen werden unter M-64 bewertet, das Merken des
  Ansichtszustands unter M-97, seitenweises Nachladen unter M-26, Filter und Sortierung der Werkzeugleiste unter M-92 bis
  M-94, Vorlesen unter M-114. Bei den übrigen Mechaniken zählt die Wirkung am Feld.

## Tabelle

| Kennung | Mechanik (kurz) | Stand | Wo | Bemerkung |
|---|---|---|---|---|
| M-01 | Board öffnen | abgebildet | `schale/Seite.svelte`, `routen.ts`, `board/ansicht.svelte.ts`, `/board/prod` | Seitenleiste öffnet das Board mit Spalten, Karten und Gruppen; Erledigt gefenstert; der gemerkte Ansichtszustand des Boards kommt wieder; das Detail gehört zum Pfad. Fehlt weiter: ein Board ohne Ordner verschwindet aus der Seitenleiste, weil sie nur Boards in Ordnern zeigt (Gegenprobe aus der ersten Prüfung, die Seitenleiste ist unverändert). In der App behoben, siehe die Abschnitte oben. |
| M-02 | Board anlegen | abgebildet | `ansichten/verwaltung/BoardNeu.svelte`, `regeln/kuerzel.ts`, `boardAnlegen` in `beispiel/anwendung/boards.svelte.ts`, `/boards/neu` | Aus Vorlage oder leer mit den drei Spalten wie bisher (E-17), Name, Kürzel als Vorschlag, Ordner, Einladungen. Fehler behoben: Kürzel über alle Boards eindeutig, Umlaute ausgeschrieben, leerer Name abgewiesen. Mappen entfallen (E-02). |
| M-03 | Board umbenennen und löschen | abgebildet | `ansichten/verwaltung/board/Allgemein.svelte`, `boardUmbenennen` und `boardInPapierkorb` in `beispiel/anwendung/boards.svelte.ts`, `ansichten/verwaltung/person/Papierkorb.svelte` | Umbenennen lässt das Kürzel fest, leerer Name abgewiesen; Löschen mit Rückfrage in der Fläche in den Papierkorb der App, Wiederherstellen mit Karten, Serien, Terminen und Ordner. Die Boardliste folgt der Reihenfolge im Ordner, nicht dem Alphabet. |
| M-04 | Kopfzeile | abgebildet | `board/BoardAnsicht.svelte` | Name mit Farbpunkt, Ordner, Kürzel, Mitglieder und eigene Rolle. |
| M-05 | Ansichtsumschalter | abgebildet | `board/BoardAnsicht.svelte`, `board/ansichten.ts` | Reiter Board, Liste, Kalender, Zeitachse, jeder mit eigenem Pfad (E-09, E-22); alle bekommen dieselben Filter. |
| M-06 | Abgleich beim Fensterfokus | Fehler behoben | `schale/Fuss.svelte`, `beispiel/anwendung/verbindung.svelte.ts`, `/board/prod?entwurf=live` | Statt Neuladen beim Fokus ein Ereignisstrom je Board (ENTWURF Abschnitt 1): die Änderung einer anderen Person erscheint sofort an der Karte mit Meldung, der Fuß zeigt "Live verbunden" oder "Getrennt". In den Entwürfen vorgeführt. |
| M-07 | Neuladen nach Timer-Ereignis | abgebildet | `beispiel/stand.svelte.ts`, `beispiel/abfragen.ts` | Ein Zustand für alle Ansichten, die Zeit einer Karte ist die Summe ihrer Einträge; kein Neuladen nötig, in der App über den Ereignisstrom. |
| M-08 | Mappe und Board beim Start | später (Stufe 1) | nirgends | Der Pfad / ist in den Entwürfen die Galerie, womit die App startet, zeigt sich erst in der App; Mappen entfallen (E-02), den Zustand je Board merkt schon M-97. |
| M-09 | Tiefe Verweise | abgebildet | `routen.ts`, `weg.svelte.ts`, `/board/prod/131` | Offene Karte steht im Pfad, Schließen nimmt sie heraus, Zurück und Vor gehen. Fehler behoben: der Pfad öffnet jede Karte des Boards, auch archivierte (`karteAusNummer`); Sprünge in andere Boards gehen, da es keine Mappen mehr gibt. |
| M-10 | Export | fehlt | nirgends | Kein Export des Boards. Die Berichte (`ansichten/zeit/Berichte.svelte`) liefern Zeit- und Erledigt-Auswertungen, keine vollständige Ausgabe der Daten. |
| M-11 | Ladefehler | später (Stufe 1) | `teile/Meldung.svelte`, `beispiel/anwendung/meldung.svelte.ts`, `/heute?entwurf=getrennt` | Gescheitertes Laden und eine entzogene Mitgliedschaft gibt es erst mit der Schnittstelle der App; der getrennte Zustand (letzter Stand sichtbar, Schreiben gesperrt, Meldung mit Grund) ist schon vorgeführt. |
| M-12 | Spalte anlegen | abgebildet | `board/BoardAnsicht.svelte`, `spalteAnlegen` in `beispiel/anwendung/boards.svelte.ts`, `/board/prod?entwurf=neue-spalte` | "Spalte" am Ende des Streifens öffnet Name und Farbe; Enter legt an, Escape bricht ab; ans Ende, ohne Grenze, offen; leerer Name abgewiesen (behebt die fehlende Prüfung). Nur mit dem Recht "Board verwalten". |
| M-13 | Umbenennen und Grenze setzen | abgebildet | `board/SpaltenMenue.svelte`, `ansichten/verwaltung/board/Spalten.svelte`, `teile/Zahlfeld.svelte` | Im Spaltenmenü des Boards und in den Einstellungen: Name (Enter speichert, Escape stellt im Menü den alten Namen her) und Grenze (leer heißt keine, ganze Zahl ab 1, sonst Hinweis); leerer Name abgewiesen. |
| M-14 | Grenzanzeige | abgebildet | `board/Spalte.svelte`, `spalteninhalt` in `beispiel/abfragen.ts`, `stil/board.css` | Kopf "n/Grenze" aus allen Karten der Spalte, Bernstein genau an der Grenze, rot darüber, Füllbalken darunter, Erklärung im title. Fehler behoben: bei Suche bleibt die Zahl (Gegenprobe: In Arbeit zeigt 5/4 in Rot, die Leiste darunter "1 von 5 passen"). |
| M-15 | Grenze weich durchgesetzt | abgebildet | `hinein` und `anlegen` in `beispiel/anwendung/karten.svelte.ts`, `board/SpaltenMenue.svelte`, `ansichten/telefon/Verschieben.svelte` | Ziehen, Status, Sammelverschieben, Anlegen, Telefon und Spalte löschen warnen nur, ohne harten Halt. |
| M-16 | Spalten umsortieren | abgebildet | `board/BoardAnsicht.svelte`, `board/Spalte.svelte`, `board/SpaltenMenue.svelte`, `spaltenOrdnen` in `beispiel/anwendung/boards.svelte.ts` | Griff im Kopf, auch an der eingeklappten Spalte; die gezogene Spalte hebt sich ab, der Platz ist gestrichelt; "Nach links" und "Nach rechts" im Menü (am Rand ausgeblendet); der Anwendungsfall prüft die vollständige Liste. Nur mit dem Recht "Board verwalten". |
| M-17 | Spaltenfarben | abgebildet | `modell.ts` (Spalte), `board/SpaltenMenue.svelte`, `ansichten/verwaltung/board/Spalten.svelte` | Besser: jede Spalte hat eine eigene, wählbare Farbe statt der Farbe aus der Position; Punkt im Kopf, Füllbalken, Striche der eingeklappten Spalte, Status in Liste und Detail. |
| M-18 | Einklappen | abgebildet | `board/Spalte.svelte`, `board/ansicht.svelte.ts` | Schmal mit senkrechtem Namen, Zahl und einem Farbstrich je Karte (Titel im Hinweis); Klick auf den Kopf klappt aus; Karten lassen sich hineinziehen; umsortierbar am Griff; gemerkt je Board an diesem Gerät. |
| M-19 | Erledigt-Spalte markieren | abgebildet | `zurErledigtSpalte` in `beispiel/anwendung/boards.svelte.ts`, `board/SpaltenMenue.svelte` | Im Menü und in den Einstellungen; genau eine Erledigt-Spalte, das Recht wird geprüft. Fehler behoben: Übergangsregel (Karten der alten Spalte wieder offen mit neuem Alter, Karten der neuen mit Abschluss heute, laufende Timer halten an und buchen). |
| M-20 | Spalte löschen | abgebildet | `board/SpaltenMenue.svelte`, `spalteInPapierkorb` und `wiederherstellen` in `beispiel/anwendung/papierkorb.svelte.ts`, `ansichten/verwaltung/board/Spalten.svelte` | Rückfrage in der Fläche, im Menü wie in den Einstellungen: Karten verschieben (Gruppe zieht mit, Grenze warnt) oder mit der Spalte in den Papierkorb; Wiederherstellen an die alte Stelle mit allem. Serien bekommen eine neue Zielspalte (behebt den Fehler aus M-106). Letzte Spalte und Erledigt-Spalte bleiben. |
| M-21 | Spaltenmenü | abgebildet | `board/SpaltenMenue.svelte`, `/board/prod` (Zustand Spaltenmenü) | Menü am Knopf mit drei Punkten: Name, Farbe, Grenze oder Zeitfenster für alle, Einklappen, Nach links, Nach rechts, Zur Erledigt-Spalte, Löschen. Fehler behoben: Escape und ein Klick daneben schließen es (Gegenprobe). |
| M-22 | Gefenstertes Laden | abgebildet | `spalteninhalt`, `sichtbareKarten` und `erledigteOhneArchiv` in `beispiel/abfragen.ts`, `imFenster` in `regeln/board.ts` | Die Erledigt-Spalte zeigt nur ihr Zeitfenster, Archivierte nie, dazu "x von y". Seitenweises Laden siehe M-26. |
| M-23 | Abschlussdatum | abgebildet | `abschluss` und `wechseln` in `beispiel/anwendung/karten.svelte.ts`, `serienzeitBuchen` in `beispiel/anwendung/serien.svelte.ts` | Ablegen in Erledigt setzt heute, eine Serienkarte bekommt fest ihren Termintag, auch beim Ziehen und im Nachtrag. |
| M-24 | Zeitfilter im Spaltenkopf | abgebildet | `board/Spalte.svelte`, `board/ansicht.svelte.ts`, `fensterAb` in `regeln/board.ts` | Heute, Gestern, Woche, Monat, Jahr, Alle; ein Wechsel wirkt sofort und gilt für dich an diesem Gerät, gemerkt je Board und Spalte. Neu: Vorgabe für alle im Spaltenmenü. |
| M-25 | Zeitfenster ausgesetzt bei Suche und Filter | abgebildet | `board/Spalte.svelte`, `spalteninhalt` in `beispiel/abfragen.ts`, `/board/prod?entwurf=suche` | Bei Suche, Filter oder Sortierung zeigt Erledigt "Ohne Zeitfenster" alle passenden Karten außerhalb des Archivs. Fehler behoben: Volltext über die Werte, nie über rohe Texte; Personenfilter wirkt auch hier. |
| M-26 | Nachladen, "Mehr laden", Zähler | abgebildet | `board/Spalte.svelte`, `ansichten/uebersicht/Archiv.svelte`, `/board/prod?entwurf=mehr` | In der Erledigt-Spalte abgebildet: Seiten nach "Karten je Ladeschritt", "Mehr laden (n weitere)", Nachladen beim Rollen ab 80 Pixeln vor dem Ende, Zähler "x von y" (Gegenprobe: 3 von 10, nach dem Klick 6 von 10). Im Archiv steht weiter nur der Hinweis "Beim Rollen laden die nächsten", ohne Nachladen. In der App behoben, siehe die Abschnitte oben. |
| M-27 | Schutz gegen überholte Antworten | später (Stufe 1) | nirgends | Die Entwürfe laden nicht über das Netz, überholte Antworten gibt es erst mit der Schnittstelle der App. |
| M-28 | Reihenfolge in Erledigt-Spalten | abgebildet | `board/Spalte.svelte`, `spalteninhalt` in `beispiel/abfragen.ts` | Neueste zuerst nach Abschluss, am selben Tag die zuletzt abgelegte zuerst (Gegenprobe, Zeitfenster Alle: 26.10. viermal, dann 23.10.). Fehler behoben: in Erledigt bleibt eine Karte beim Ziehen an ihrem Platz, eine neue landet oben; kein Umsortieren, das nicht wirkt. |
| M-29 | Archiv-Grenze | abgebildet | `imArchiv` und `imFenster` in `regeln/board.ts`, `ansichten/verwaltung/board/Allgemein.svelte` | Reine Ladegrenze je Board (Vorgabe 365 Tage), eine größere Zahl holt Karten zurück, Berichte zählen alle. |
| M-30 | Archiv-Ansicht | abgebildet | `ansichten/uebersicht/Archiv.svelte`, `/board/prod/archiv` | Eigene Seite mit Gesamtzahl, neueste zuerst, Schlüssel, Titel, Abschluss im deutschen Format (behebt das ISO-Format), Zuständig, Labels, Zeit, Suche, Leerzustand; Klick öffnet die Karte, "Zurück zum Board". Nachladen siehe M-26. |
| M-31 | Rückholen | abgebildet | `verschieben` und `wechseln` in `beispiel/anwendung/karten.svelte.ts` | Ziehen oder Status in eine offene Spalte: neues Alter, der Abschluss entfällt, die Gruppe zieht mit; aus dem Archiv über den Status im Detail. |
| M-32 | Karte anlegen | abgebildet | `board/Schnelleingabe.svelte`, `anlegen` in `beispiel/anwendung/karten.svelte.ts`, `/board/prod?entwurf=schnell` | Enter legt an, Umschalt+Enter bricht um, Escape schließt und leert, Arbeit oder Idee, Feld bleibt offen, geleert erst nach Erfolg, leerer Titel abgewiesen, Warnung über der Grenze. "Karte" nur mit dem Recht "Karten anlegen"; in der Erledigt-Spalte kein "Karte" (Weg über den Status). |
| M-33 | Vorbelegung neuer Karten | abgebildet | `anlegen` in `beispiel/anwendung/karten.svelte.ts` | Zuständig ist das angemeldete Konto, ans Ende, Zeitpunkte jetzt, Arbeit (ohne Zeiterfassung Idee), Verlauf "hat die Karte angelegt". Fehler behoben: kein "zuletzt gesetztes Kürzel" mehr. |
| M-34 | Kartenschlüssel und Laufnummer | abgebildet | `anlegen` und `duplizieren` in `beispiel/anwendung/karten.svelte.ts`, `regeln/kuerzel.ts` | Kürzel plus laufende Nummer, nie wiederverwendet, auch von Kopien verbraucht; der Schlüssel steht auf Karte, im Detail, in Liste und Pfad. Fehler behoben: Kürzel eindeutig über alle Boards; Wiederherstellen behält den Schlüssel. |
| M-35 | Arbeit oder Idee | abgebildet | `board/Schnelleingabe.svelte`, `detail/Karteninhalt.svelte`, `artSetzen` in `beispiel/anwendung/karten.svelte.ts`, `timerErlaubt` in `beispiel/abfragen.ts` | Umschalter beim Anlegen und im Detail; eine Idee hat weder Timer noch Kette noch Abschnitte für Zeit und Verknüpfung; Umschalten auf Idee hält den Timer an und bucht; Zeiten bleiben; Verlauf. Fehler behoben: Verknüpfen nimmt nur Arbeitskarten an. |
| M-36 | Duplizieren | abgebildet | `duplizieren` in `beispiel/anwendung/karten.svelte.ts`, `detail/Karteninhalt.svelte` | Knopf im Detailkopf (Recht "Karten anlegen"): Kopie am Ende derselben Spalte mit " (Kopie)", Inhalt und Angaben gleich, Checkliste offen, ohne Zeiten, Kommentare, Blockade, Transkripte, Gruppe und Anhänge; danach öffnet die Kopie, Meldung mit Rückgängig. |
| M-37 | Aufbau der Karte | abgebildet | `board/Karte.svelte`, `stil/board.css` | Cover, Labels, Blockade mit Grund, Titel, Auszug der Beschreibung auf zwei Zeilen (Markdown-Zeichen sichtbar wie bisher), eigene Felder, Fortschritt der Checkliste, Fußzeile. |
| M-38 | Zeitknopf | abgebildet | `board/Karte.svelte` | Starten, Anhalten, Fortsetzen ohne Öffnen; Zeit erst ab mehr als null; bei geteilter Zeit die Zeit der Gruppe; rot über der Schätzung; fremder Timer nur zur Ansicht; Hinweis nennt Gruppe und Schätzung. |
| M-39 | Fälligkeit | abgebildet | `beispiel/format.ts` (Text der Fälligkeit), `board/Karte.svelte` | Rot bei überfällig mit "n Tage über", Bernstein von heute bis in zwei Tagen. Fehler behoben: erledigte Karten zeigen keine Fälligkeit. |
| M-40 | Weitere Marker | abgebildet | `board/Karte.svelte` | Kette mit Gruppengröße (Hinweis nennt die weiteren Karten und ob die Zeit geteilt ist), Schlüssel, Checkliste n/m (grün, wenn vollständig), Kommentare, Anhänge, Serie, Prioritätspunkt, Zuständige (bis drei). |
| M-41 | Alterung | abgebildet | `alterung` in `regeln/board.ts`, `board/Karte.svelte`, `ansichten/verwaltung/board/Allgemein.svelte` | Sanduhr mit Tagen, Warnung und Gefahr je Board einstellbar. Fehler behoben: Stufen unabhängig (0 schaltet nur eine aus); in Erledigt-Spalten steht das Abschlussdatum statt des Alters. |
| M-42 | Aktionen beim Überfahren | abgebildet | `board/Karte.svelte`, `stil/board.css` | Beim Überfahren oder mit dem Fokus oben rechts die Kette (nur Arbeit, Recht "Karten bearbeiten") und der Papierkorb (Recht "Karten löschen", mit Rückgängig). |
| M-43 | Karte öffnen | abgebildet | `board/Karte.svelte`, die Öffnen-Hilfe in `board/BoardAnsicht.svelte` | Klick oder Enter öffnet über den Pfad; Tab erreicht jede Karte. |
| M-44 | Detail öffnen und schließen | abgebildet | `detail/Kartendetail.svelte` | Leiste rechts über dem Board, mit Vollbild; der Fokus springt beim Öffnen ins Detail; X, Escape (Gegenprobe) und ein Klick daneben schließen, ein Klick auf eine andere Karte öffnet diese; steckt der Fokus in einem Feld, gilt das erste Escape dem Feld; zeigt immer den aktuellen Stand. |
| M-45 | Kopf des Details | abgebildet | `detail/Karteninhalt.svelte`, `teile/zwischenablage.ts` | Schlüssel, Spalte, Arbeit oder Idee, Duplizieren, Verweis kopieren (mit Ersatzweg ohne sicheren Kontext, die Meldung nennt die Adresse), Vollbild, Schließen; Blockiert steht als Feld bei den Angaben. Vorlesen siehe M-114. |
| M-46 | Titel | abgebildet | `detail/Karteninhalt.svelte`, `teile/verwerfen.ts` | Speichert beim Verlassen oder mit Enter, Escape verwirft. Fehler behoben: ein leerer Titel wird abgewiesen. |
| M-47 | Blockiert mit Grund | abgebildet | `detail/Karteninhalt.svelte`, `board/Karte.svelte`, `ansichten/uebersicht/Heute.svelte` | Feld "Grund, wenn die Karte wartet": Text blockiert, Leeren hebt auf, Escape verwirft; die Karte zeigt den Grund, Heute einen eigenen Abschnitt und eine Marke; Verlauf. |
| M-48 | Status-Auswahl | abgebildet | `detail/Karteninhalt.svelte`, `verschieben` in `beispiel/anwendung/karten.svelte.ts` | Derselbe Weg wie das Ziehen (ans Ende, Alter neu, Gruppe, Timer, Abschluss, Warnung); der Anwendungsfall prüft das Recht "Karten verschieben". |
| M-49 | Priorität | abgebildet | `detail/Karteninhalt.svelte`, `anzeige.ts` | Keine, Niedrig, Mittel, Hoch und neu Dringend; speichert sofort, mit Verlauf. |
| M-50 | Start | abgebildet | `teile/DatumFeld.svelte`, `starten` in `beispiel/anwendung/timer.svelte.ts` | Deutsches Textfeld, leer entfernt; der erste Timer-Start setzt den Start, wenn er fehlt. Fehler behoben: kein natives Datumsfeld. |
| M-51 | Fällig | abgebildet | `teile/DatumFeld.svelte`, `ansichten/planung/Kalender.svelte` | Speist Karte, Heute, Liste, Sortierung und Kalender; im Kalender setzt Ziehen auf einen Tag die Fälligkeit; Verlauf. |
| M-52 | Zuständig | abgebildet | `teile/Personenwahl.svelte`, `detail/Karteninhalt.svelte` | Mehrere Zuständige aus den Mitgliedern des Boards, Textfeld mit Vorschlägen, Verlauf. Fehler behoben: nur Mitglieder; der Timer gehört der Person, ein Wechsel schreibt keine Sitzung um. |
| M-53 | Cover | abgebildet | `teile/Farbwahl.svelte` | "Keine" plus die Palette des Appkerns, speichert sofort. |
| M-54 | Zeitkennzahlen | abgebildet | `detail/Karteninhalt.svelte` | Im Status, Durchlaufzeit, Erstellt mit Person. Fehler behoben: "Im Status" folgt der Alterung des Boards. |
| M-55 | Speichermodell des Details | abgebildet | `detail/Karteninhalt.svelte`, `detail/entwuerfe.ts`, `/board/prod/115?entwurf=konflikt` | Jedes Feld speichert für sich, ohne Bearbeiten-Modus, mit Rückgängig. Der Konflikt bei veralteter Fassung wirkt: "Ihre behalten" verwirft die eigene Änderung mit Meldung, "Meine übernehmen" speichert sie über den Anwendungsfall. |
| M-56 | Beschreibung | abgebildet | `detail/Textfeld.svelte`, `teile/markdown.ts`, `/board/prod/131?entwurf=bearbeiten` | Markdown gerendert; Klick oder Stift öffnet den Editor an Ort und Stelle, Vollbild mit Vorschau; "Fertig" oder Strg und Enter speichert, Escape und "Verwerfen" stellen den Stand vom Öffnen her; "Nicht gespeichert" zeigt offene Eingaben; getrennt bleibt der Editor offen. Statt Autospeichern im Takt speichert der Editor beim Schließen des Details und beim Kartenwechsel an seiner Karte, die alte 600-ms-Lücke ist zu (Gegenprobe: "Fertig" speichert, Meldung mit Rückgängig, Auszug auf der Karte neu). |
| M-57 | Notizen | abgebildet | `detail/Textfeld.svelte`, `/board/prod/131?entwurf=notizen` | Gerendert lesbar; ein Klick öffnet das Vollbild mit Eingabe links und Vorschau rechts; Speichern wie M-56. Fehler behoben: Notizen sind überall in der Suche. |
| M-58 | Labels an der Karte | bewusst anders | `detail/Karteninhalt.svelte`, `ansichten/verwaltung/board/Labels.svelte` | E-02: Labels gehören dem Board mit Name und Farbe; an der Karte schalten Chips sie ein und aus. Ein neues Label entsteht nur in den Einstellungen. Fehler behoben: Dubletten ohne Beachtung von Groß und klein werden abgewiesen. |
| M-59 | Labelfarben | abgebildet | Anwendungsfälle der Labels in `beispiel/anwendung/boards.svelte.ts` | Farbe je Label aus dem Board; Umbenennen und Umfärben gelten auf allen Karten; Löschen mit Rückfrage entfernt das Label an den Karten (bisher blieb der Text stehen). |
| M-60 | Checkliste | abgebildet | `detail/Checkliste.svelte` | Abhaken, Klick auf den Text benennt um (Enter oder Verlassen speichert, Escape verwirft, leer bleibt der alte Text), Hinzufügen mit Enter, Entfernen mit Rückgängig, "n/m" und Fortschrittsbalken (grün bei vollständig), erledigte durchgestrichen. Der KI-Knopf "Vorschlagen" siehe M-115. |
| M-61 | Kommentare | abgebildet | `detail/Aktivitaet.svelte`, `kommentieren` in `beispiel/anwendung/karten.svelte.ts` | Person, Zeit, Text als Markdown mit Erwähnungen; Enter sendet, Umschalt und Enter bricht um; das Feld leert sich erst nach dem Speichern; Leerzustand; Recht "Kommentieren"; Verlauf. Fehler behoben: Autor ist das Konto, auch das Rechner-Feld leert sich nicht mehr bei abgelehntem Senden. Vorlesen siehe M-114. |
| M-62 | Dokumente an der Karte | fehlt | nirgends | Kein Abschnitt Dokumente mit Editor. E-15 regelt nur die Ablage in der Kellerwolke, nicht den Wegfall. |
| M-63 | Anhänge | abgebildet | `detail/Anhaenge.svelte`, `detail/Kellerwolkewahl.svelte`, `beispiel/anwendung/anhaenge.svelte.ts`, `/board/prod/131?entwurf=kellerwolke` | Hochladen über die Dateiwahl (mehrere) oder durch Ziehen auf den Abschnitt, Grenze 25 MB, leere abgelehnt, gleiche Namen mit Zähler; Wahl aus der eigenen Kellerwolke (E-15); Öffnen in neuem Reiter; Entfernen mit Rückgängig (behebt das sofortige Löschen); Verlauf; nur mit dem Recht "Karten bearbeiten". |
| M-64 | Verlauf | abgebildet | `detail/Aktivitaet.svelte`, `beispiel/anwendung/verlauf.ts` | Neueste zuerst, mit Person und Zahl am Reiter, Leerzustand "Noch kein Verlauf.". Geschrieben werden Anlegen, Duplizieren, Verschieben samt eigener Zeile der Mitgezogenen, Erledigen, Zuständig, Start, Fällig, Priorität, Blockade, Art, Kommentar, Verknüpfen, Timer-Start und -Buchung (mit Deckel), Nachtragen, Setzen, Verlegen und Löschen von Zeit, Anhänge; Titel und Beschreibung bewusst nicht. |
| M-65 | Neue Fassung wartet | später (Stufe 1) | nirgends | Neue Programmfassungen gibt es erst beim Ausrollen der App über den Appkern; die Entwürfe zeigen schon offene Eingaben ("Nicht gespeichert") und speichern beim Schließen. |
| M-66 | Umsortieren in einer Spalte | abgebildet | `board/Spalte.svelte`, `ablegen` in `beispiel/anwendung/karten.svelte.ts` | Gestrichelter Platzhalter, Reihenfolge sofort, die Gruppe bleibt. Fehler behoben: die Spalte übergibt ihre neue Reihenfolge selbst, kein Platz daneben; ein Ablegen an derselben Stelle meldet nichts mehr. |
| M-67 | Wechsel zwischen Spalten | abgebildet | `ablegen`, `hinein` und `wechseln` in `beispiel/anwendung/karten.svelte.ts` | Neue Stelle, Alter neu, Verlauf, die Gruppe desselben Boards zieht mit, Warnung über der Grenze; auch in eingeklappte Spalten. |
| M-68 | Ablegen in Erledigt | abgebildet | `wechseln` in `beispiel/anwendung/karten.svelte.ts`, `timerBeenden` in `beispiel/anwendung/timer.svelte.ts`, `/board/prod?entwurf=erledigt` | Abschluss heute (Serienkarte: Termintag); Timer aller Personen auf der Karte und den mitgezogenen halten an und buchen; die Karte steht oben; die Meldung nennt die Zeit. |
| M-69 | Ziehen gesperrt bei Filter | abgebildet | `board/BoardAnsicht.svelte`, `board/ansicht.svelte.ts` | Bei Suche, Filter oder Sortierung ist Ziehen in allen Spalten gesperrt; "Verschieben pausiert" mit Schloss setzt per Klick Suche, Filter, Personen und Sortierung zurück (Gegenprobe: 7 Karten, danach 27). |
| M-70 | Rücksprung mit Grund | abgebildet | `board/Spalte.svelte`, `ablegen` in `beispiel/anwendung/karten.svelte.ts`, `/board/prod?entwurf=getrennt` | Lehnt der Anwendungsfall ab, zeigt die Spalte wieder den Stand und die Karte steht an ihrem Platz; die Meldung nennt den Grund (Gegenprobe: PROD-139 bleibt in Geplant, "Keine Verbindung"). Fehler behoben: die Zielspalte muss zum Board der Karte gehören, das Recht wird geprüft. |
| M-71 | Optik beim Ziehen | abgebildet | `board/Spalte.svelte`, `board/schatten.ts`, `stil/board.css`, `/board/prod?entwurf=ziehen` | Gezogene Karte angehoben und leicht gedreht, gestrichelter Platz "hier ablegen" mit "zieht mit"; gezogene Spalte angehoben und umrandet; eingeklappte Spalten zeigen einen kleinen gestrichelten Platz. |
| M-72 | Kette ziehen | abgebildet | `board/kette.svelte.ts`, `board/Karte.svelte`, `/board/prod?entwurf=kette` | Eigene Zeigergeste: Quelle halbtransparent gestrichelt, Marke am Zeiger ("Auf eine Arbeitskarte ziehen", "Hier verknüpfen"), Ziel hervorgehoben; Loslassen verknüpft über den Anwendungsfall mit Meldung, daneben oder Escape bricht ab; nur sichtbare Arbeitskarten desselben Boards. |
| M-73 | Verknüpfen im Detail | abgebildet | `detail/Verknuepfte.svelte`, Treffersuche in `beispiel/abfragen.ts`, `/board/prod/131` (Zustand Verknüpfen) | Suche in den offenen Arbeitskarten dieses Boards nach Titel oder Schlüssel, ohne bisherige Mitglieder, höchstens 8 Treffer, Pfeile und Enter oder Klick; das Feld leert sich erst nach dem Verknüpfen. Gruppen bleiben in einem Board (wie M-76), damit ist der alte Widerspruch weg. |
| M-74 | Gruppenregeln | abgebildet | Verknüpfen und Lösen in `beispiel/anwendung/karten.svelte.ts` | Bilden (mit "Zeit teilen" an), beitreten, zusammenführen und lösen wirken; unter zwei Mitgliedern endet die Gruppe. Alter Fehler bleibt: beim Zusammenführen gilt still die Einstellung "Zeit teilen" der Gruppe der ersten Karte, und die Meldung sagt immer "Zeit wird geteilt" (aus dem Code). In der App behoben, siehe die Abschnitte oben. |
| M-75 | Zeit teilen | abgebildet | `zeitTeilen` in `beispiel/anwendung/karten.svelte.ts`, `zeitDerGruppe` in `beispiel/abfragen.ts`, `board/Karte.svelte`, `detail/Zeiterfassung.svelte` | Der Schalter wirkt; Karte und Detail zeigen die gemeinsame Zeit; jede Sekunde zählt einmal; laufende Zeit anderer zählt mit (behebt den alten Fehler). |
| M-76 | Mitziehen beim Spaltenwechsel | abgebildet | `hinein` in `beispiel/anwendung/karten.svelte.ts` | Mitglieder desselben Boards ziehen ans Ende der Zielspalte mit, Alter neu, eigene Verlaufszeile, Timer bei Erledigt; Mitglieder auf anderen Boards bleiben stehen; reines Umsortieren lässt die Gruppe stehen. |
| M-77 | Mitglieder öffnen | abgebildet | `detail/Verknuepfte.svelte` | Die anderen Mitglieder als Verweis auf ihre Karte, mit dem Board, wenn es ein anderes ist; Lösen daneben. Fehler behoben: das Öffnen geht über den Pfad, also auch für Karten außerhalb des geladenen Fensters. |
| M-78 | Timer starten | abgebildet | `starten` in `beispiel/anwendung/timer.svelte.ts`, `timerErlaubt` in `beispiel/abfragen.ts` | Auf der Karte, im Detail, in Heute, im Kopf (Fortsetzen) und am Telefon; setzt den Start, wenn er fehlt; Verlauf. Fehler behoben: nicht in Erledigt, nicht auf Ideen, nur mit dem Recht "Eigene Zeit buchen". |
| M-79 | Pause und Stopp | abgebildet | `anhalten`, `fortsetzen` und `stoppen` in `beispiel/anwendung/timer.svelte.ts`, `detail/Zeiterfassung.svelte`, `schale/Kopf.svelte` | Anhalten bucht und lässt fortsetzen, Stopp bucht und beendet; die Knöpfe je Zustand wie bisher. |
| M-80 | Ein Timer je Person | Fehler behoben | `modell.ts` (Timer), `starten` in `beispiel/anwendung/timer.svelte.ts` | Der Timer gehört dem Konto, nicht dem Kürzel der Karte: ein Start beendet und bucht nur den eigenen Timer auf einer anderen Karte, fremde laufen weiter (ENTWURF Abschnitte 1 und 2). |
| M-81 | Buchung beim Stoppen | abgebildet | `sitzungBuchen` in `beispiel/anwendung/zeiten.svelte.ts`, `ansichten/zeit/TagLeiste.svelte`, `/zeiten?entwurf=deckel` | An Mitternacht zerlegt, ein Timer-Eintrag je Karte, Person und Tag mit sichtbaren Sitzungen, Handbuchungen eigenständig, Verlauf. Fehler behoben: die Person gehört zum Schlüssel der Zusammenfassung; über 12 Stunden gedeckelt mit Vermerk und Rückfrage nach dem echten Ende. |
| M-82 | Laufleiste | abgebildet | `schale/Kopf.svelte`, `ansichten/uebersicht/Laufend.svelte` | Im Kopf jeder Seite Schlüssel, Titel, Zeit, Anhalten oder Fortsetzen, Stopp; in Heute dazu Prozent der Schätzung und "überschritten". |
| M-83 | Abgleich laufender Timer | abgebildet | `timerVon` und `laufendAuf` in `beispiel/abfragen.ts` | Ein Zustand für Kopf, Karte, Heute und Telefon; in der App über den Ereignisstrom statt einer Abfrage alle 60 Sekunden. Fremde Timer sind an der Karte sichtbar. |
| M-84 | Automatische Stopps | abgebildet | `timerBeenden` in `beispiel/anwendung/timer.svelte.ts`, `inPapierkorb`, `mitgliedEntfernen` | Erledigen, Idee, Papierkorb und das Entfernen eines Mitglieds halten an und buchen. Besser: beim Löschen geht die Sitzung nicht mehr verloren. |
| M-85 | Live-Zeit | später (Stufe 2) | `laufendSek` in `beispiel/format.ts` | Die Beispielwelt hat ein festes "jetzt", ein Sekundentakt ergibt erst mit der Uhr der App Sinn (Stufe Zeit); die laufende Sitzung wird überall schon eingerechnet. |
| M-86 | Tag buchen | abgebildet | `detail/Zeiterfassung.svelte`, `buchen` in `beispiel/anwendung/zeiten.svelte.ts`, `ansichten/zeit/Nachtragen.svelte`, `ansichten/telefon/Zeiten.svelte` | Datum (Vorgabe heute), Dauer, "Tag buchen" oder Enter in Tag oder Dauer; die Dauer leert sich erst nach dem Buchen; der Eintrag gehört dem eigenen Konto; Verlauf. Fehler behoben: eine unlesbare Dauer wird rot mit Hinweis statt still ignoriert. |
| M-87 | Ticketzeit gesamt setzen | abgebildet | `ticketzeitSetzen` und `setzeTageszeit` in `beispiel/anwendung/zeiten.svelte.ts`, `teile/DauerFeld.svelte` | Gesperrt, solange der eigene Timer läuft; mehr bucht die Differenz heute, weniger kürzt die eigenen jüngsten Einträge von heute; Verlauf. Fehler behoben: fremde Einträge bleiben unberührt, Escape verwirft. |
| M-88 | Tagesliste | abgebildet | `detail/Zeiterfassung.svelte`, Anwendungsfälle der Zeiteinträge in `beispiel/anwendung/zeiten.svelte.ts` | Einträge je Tag und Person mit Herkunft; ein Klick auf den Tag ändert das Datum (deutsches Feld, Escape verwirft), die Dauer ist direkt änderbar, X löscht mit Rückgängig; eigene Einträge, fremde nur mit Recht, sonst Schloss; aktualisiert sich sofort. Fehler behoben: Rückgängig bringt den Eintrag genau zurück. |
| M-89 | Schätzung und Fortschritt | abgebildet | `detail/Zeiterfassung.svelte`, `ansichten/uebersicht/Liste.svelte` | Schätzung als Dauer, leer entfernt; Balken mit Warnfarbe über 100 Prozent; die Liste zeigt Ist und Soll mit Warnzeichen, der Zeitknopf wird rot. |
| M-90 | Zeiteingabe | abgebildet | `dauerLesen` in `regeln/eingabe.ts`, `teile/DauerFeld.svelte` | Dieselben Formate (1:30, 1:30:00, 1,5, 90m, 90min, 2h, 2std); Unlesbares wird angezeigt statt verworfen. |
| M-91 | Suche | abgebildet | `board/BoardAnsicht.svelte`, Volltextsuche in `beispiel/abfragen.ts` | Jedes Wort muss vorkommen, ohne Beachtung von Groß und klein; gilt in Board, Liste, Kalender und Zeitachse; Escape leert; gemerkt je Board. Fehler behoben: Notizen werden überall gefunden. |
| M-92 | Prioritäts- und Labelfilter | abgebildet | `board/Filtertafel.svelte`, `board/ansicht.svelte.ts`, Filterabfrage in `beispiel/abfragen.ts`, `/board/prod?entwurf=filter` | Chip "Filter" mit Zahl öffnet die Tafel: Prioritäten (auch "Ohne"), Labels und eigene Auswahlfelder, in einer Zeile oder, über die Zeilen und; gilt in Board, Liste, Kalender und Zeitachse; gemerkt je Board; "Filter zurücksetzen". Fehler behoben: angeboten wird jedes Label des Boards, auch eins, das nur an erledigten Karten hängt. |
| M-93 | Personenfilter | abgebildet | `board/Filtertafel.svelte`, `board/BoardAnsicht.svelte` | Zeile "Zuständig" mit allen Mitgliedern, mehrere kombinierbar; der Chip nennt die Person oder die Zahl. Fehler behoben: keine Grenze von sieben Personen, gilt auch in Erledigt-Spalten, gemerkt je Board und nicht auf andere Boards übertragen. |
| M-94 | Sortierung | abgebildet | `board/Filtertafel.svelte`, Sortierung in `beispiel/abfragen.ts` | Manuell, Fällig (früheste zuerst, ohne Datum am Ende) oder Priorität; nur offene Spalten, Erledigt bleibt nach Abschluss; gemerkt je Board; außer "Manuell" ist Ziehen gesperrt. Die Liste sortiert über ihre Spaltenköpfe. |
| M-95 | Gespeicherte Sichten | fehlt | nirgends | Keine Sichten unter einem Namen, weder im Browser noch am Konto; gemerkt wird nur der letzte Zustand je Board (M-97). |
| M-96 | Filtervorschläge | später (Stufe 4) | nirgends | Vorschläge in Worten liefert die Leitstelle (KI an der Karte, E-06), eine Anbindung der Stufe Verbund. |
| M-97 | Ansichtszustand im Browser | abgebildet | `board/ansicht.svelte.ts` | Je Board an diesem Gerät gemerkt: Suche, Filter, Personen, Sortierung, eingeklappte Spalten, Zeitfenster je Erledigt-Spalte; beim Lesen gegen das Board geprüft; geschützt, wenn der Speicher fehlt; vorgeführte Zustände merken nichts (Gegenprobe: Suche und eingeklappte Spalte nach dem Neuladen wieder da). Die Ansicht selbst steht im Pfad (E-22). |
| M-98 | Listenansicht | abgebildet | `ansichten/uebersicht/Liste.svelte`, `/board/prod/liste` | Dieselbe Abfrage wie die Spalten mit Suche und Filter; fester Kopf; Schlüssel, Titel mit Idee und Blockade, Status, Zuständig, Priorität, Fällig oder Abschluss, Labels, eigene Felder, Zeit; erledigte grau; Klick öffnet; Leerzustand. Fehler behoben: die laufende Zeit wird gezeigt. Die Liste nimmt für Erledigt die Vorgabe der Spalte, nicht die persönliche Wahl im Board. |
| M-99 | Sortieren in der Liste | abgebildet | `ansichten/uebersicht/Liste.svelte` | Klick sortiert, ein zweiter dreht, ein Pfeil zeigt die Richtung. Fehler behoben: Status sortiert nach der Folge der Spalten. |
| M-100 | Auswahl | abgebildet | `ansichten/uebersicht/Liste.svelte`, `/board/prod/liste?entwurf=auswahl` | Kästchen je Zeile ohne Öffnen, "Alle auswählen", die Auswahl räumt sich selbst auf. |
| M-101 | Sammelaktionen | abgebildet | `ansichten/uebersicht/Liste.svelte`, Sammelaktionen in `beispiel/anwendung/karten.svelte.ts` | Verschieben (Gruppe, Timer, Warnung, Recht), Zuweisen an jedes Mitglied, neu Label, Priorität, Papierkorb mit einem Rückgängig; Verlauf. Fehler behoben: alles in einem Schritt, kein halber Stand. Zuweisen fügt hinzu; "niemand" gibt es nur je Karte im Detail. |
| M-102 | Karte löschen | abgebildet | `inPapierkorb` in `beispiel/anwendung/papierkorb.svelte.ts`, `board/Karte.svelte`, `detail/Karteninhalt.svelte`, `ansichten/uebersicht/Papierkorb.svelte` | "In den Papierkorb" auf der Karte, im Detail und als Sammelaktion, nur mit dem Recht "Karten löschen"; der Timer bucht, ein Serientag wird ausgelassen, Meldung mit Rückgängig. Fehler behoben: Papierkorb je Board mit allem, was daran hängt. |
| M-103 | Rückgängig einer Karte | Fehler behoben | die Hilfe für Änderungen in `beispiel/anwendung/meldung.svelte.ts`, `wiederherstellen` in `beispiel/anwendung/papierkorb.svelte.ts` | Rückgängig stellt den genauen Stand wieder her; Wiederherstellen aus dem Papierkorb bringt Schlüssel, Stelle, Zeiten, Kommentare, Anhänge, Gruppe und Serienbezug zurück. Keine Neuanlage mehr. |
| M-104 | Hinweise (Meldung unten) | abgebildet | `teile/Meldung.svelte` | Eine Meldung, sie geht nach sechs Sekunden, bleibt unter dem Zeiger, X schließt, mit Rückgängig; getrennt mit eigenem Text. |
| M-105 | Rückfragen im Überblick | abgebildet | `board/SpaltenMenue.svelte`, `ansichten/verwaltung/board/Allgemein.svelte`, `ansichten/verwaltung/board/Labels.svelte`, `ansichten/uebersicht/Papierkorb.svelte`, `ansichten/planung/SerieBearbeiten.svelte` | Rückfragen in der Fläche bei Spalte, Board, Label, endgültigem Entfernen und Serie; Papierkorb und Rückgängig bei Karte, Spalte, Zeiteintrag, Anhang und Checklistenpunkt; die letzte Spalte bleibt. Keine Browser-Dialoge. |
| M-106 | Serienkarten | abgebildet | `regeln/serien.ts`, `beispiel/anwendung/serien.svelte.ts`, `ansichten/planung/SerieBearbeiten.svelte` | Zielspalte, Titel mit Uhrzeit, Beschreibung, Labels, Teilnehmer als Zuständige, fällig am Termintag, Schätzung aus der Dauer, Termintag als Abschluss. Fehler behoben: das Löschen der Zielspalte setzt eine neue. Das Anlegen der Karten macht in der App der Server. |
| M-107 | Vorbuchungsfenster | abgebildet | `vorkommenAm` und `vorlaufEnde` in `regeln/serien.ts`, `nachtrag` in `beispiel/abfragen.ts` | Vorlauf je Serie, Rückblick 31 Tage, Fortsetzen ab dem Tag, Feiertage wählbar, Abwesenheiten je Teilnehmer, eine Karte je Serie und Tag. |
| M-108 | Auslass | abgebildet | `auslassen` in `beispiel/anwendung/papierkorb.svelte.ts`, `tagAuslassen` in `beispiel/anwendung/serien.svelte.ts` | Ein gelöschter Serientag kommt nie wieder; Wiederherstellen nimmt den Auslass zurück. |
| M-109 | Pause, Ändern, Urlaub | abgebildet | `pausieren` in `beispiel/anwendung/serien.svelte.ts`, `eintragen` in `beispiel/anwendung/abwesenheiten.svelte.ts` | Pause und Ändern fassen nur unberührte Vorbuchungen an. Ein eingetragener ganzer Abwesenheitstag nimmt unberührte Serienkarten der Person zurück: sie fällt aus den Zuständigen, bleibt niemand, geht die Karte; die Meldung nennt die Zahl; angefasste Karten bleiben. |
| M-110 | Serie löschen | abgebildet | Serie löschen in `beispiel/anwendung/serien.svelte.ts`, vorgeführt unter `/serien/se-runde` (Zustand Löschen) | Rückfrage in der Fläche; unberührte Vorbuchungen gehen, Karten mit Zeit oder erledigte bleiben gelöst als Verlauf. |
| M-111 | Nachtrag ignorierter Serienkarten | abgebildet | `ansichten/planung/Nachtrag.svelte`, Anwendungsfälle des Nachtrags in `beispiel/anwendung/serien.svelte.ts`, `/serien?entwurf=nachtrag` | Bestätigen mit anpassbarer Dauer auf den Termintag, Karte nach Erledigt mit dem Termintag, Verwerfen, alle bestätigen, später; Termine dazu. Fehler behoben: nur eigene Posten; Verwerfen nimmt bei mehreren Teilnehmern nur dich heraus. |
| M-112 | Ein verknüpftes Transkript | abgebildet | `detail/Transkripte.svelte`, `backend/app/anwendung/transkripte.py` | In der App (Stufe 4, Transkripte): das ganze Transkript als Stelle ohne Zeit; Suche nach der letzten Taste, Öffnen in der Transkription, Lösen mit Rückgängig. |
| M-113 | Transkript-Verweise (Marken) | abgebildet | `detail/Transkripte.svelte`, `detail/Vorschlag.svelte`, `backend/app/anwendung/transkripte.py` | In der App: bis zu 100 Stellen je Karte mit Name, Zeit, Sprecher und Text (vom Server aus dem Transkript), Notiz speichert beim Verlassen, Vorschlag der Notiz mit Vorschau, Abspielen ab der Stelle, Lösen mit Rückgängig. Fehler behoben: Speicher- und Ladefehler kommen als Meldung, nichts wird verschluckt. |
| M-114 | Vorlesen | später (Stufe 4) | `detail/Karteninhalt.svelte`, `detail/Textfeld.svelte`, `ansichten/uebersicht/Heute.svelte`, `ansichten/zeit/Berichte.svelte` | Vorlesen ist die Anbindung Vertonung der Stufe Verbund (E-06); die Knöpfe an Karte, Beschreibung, Heute und Berichten stehen schon und lesen noch nicht vor, am Kommentar fehlt der Lautsprecher noch. |
| M-115 | Labelvorschläge | abgebildet | `detail/Karteninhalt.svelte`, `detail/Vorschlag.svelte`, `backend/app/anwendung/ki.py` | In der App (Stufe 4, KI an der Karte): Zauberstab hinter den Labels, das Modell wählt aus den Labels des Boards, die die Karte noch nicht hat; gesetzt wird nur, was angehakt bleibt. Ebenso Checkliste, Zusammenfassung und Karten aus Text. |
| M-116 | Projekt-Prüfung | bewusst anders | `hatRecht` in `regeln/board.ts`, `darf` in `beispiel/abfragen.ts`, `mitRecht` in `beispiel/anwendung/boards.svelte.ts`, `ansichten/verwaltung/board/Rollen.svelte` | E-02, E-03, E-04: Rechte je Board und Rolle statt Mitgliedschaft in einer Mappe. Die Oberfläche blendet jetzt überall nach dem Recht aus, und Verschieben prüft es im Anwendungsfall; Anlegen, Bearbeiten, Duplizieren, Kommentieren und Papierkorb prüfen es dort noch nicht (siehe Befunde). |
| M-117 | Zeit- und Timer-Rechte | bewusst anders | `RECHTE` in `beispiel/daten.ts`, `timerErlaubt` in `beispiel/abfragen.ts`, `detail/Zeiterfassung.svelte` | E-04, E-07: Rechte "Eigene Zeit buchen", "Zeiten anderer sehen" und "Zeiten anderer bearbeiten" je Rolle. Fehler behoben: die Oberfläche bietet Start, Ticketzeit, Ändern und Löschen nur an, wo das Recht besteht. |
| M-118 | Identitätsquelle | Fehler behoben | `modell.ts` (Konto), `ansichten/verwaltung/person/Konto.svelte` | Identität ist das Konto der Kellerwolke mit fester Kennung (E-13); Zuständig, Zeiteintrag, Kommentar, Verlauf und Timer hängen an der Kennung, das Kürzel ist nur Anzeige. |
| M-119 | Glocke | abgebildet | `schale/Kopf.svelte`, `ansichten/uebersicht/Hinweise.svelte`, `beispiel/anwendung/hinweise.svelte.ts`, `/hinweise` | Die Glocke mit Zähler führt zu den Hinweisen (E-16): Arten, Filter, Sprung zur Karte, "Alle gelesen". Fehler behoben: gelesen gilt am Konto auf allen Geräten. |
| M-120 | Heute | abgebildet | `ansichten/uebersicht/Heute.svelte`, `meinTag` in `beispiel/abfragen.ts`, `/heute` | Über alle Boards, nur eigene Karten: Überfällig, Heute, Diese Woche, Liegengeblieben, Blockiert, Ohne Datum, Termine, Serien, oben der eigene Timer; jede Karte genau einmal, dazu Marken; abhaken und Timer gehen. Fehler behoben: Liegengeblieben folgt der Alterung des Boards, oben steht nur der eigene Timer. Vorlesen siehe M-114, Schnell-Erfassen M-123. |
| M-121 | Fälligkeitskalender | abgebildet | `ansichten/planung/Kalender.svelte`, `ansichten/planung/KalenderKarte.svelte`, `/board/prod/kalender` | Monat und Woche je Board (E-09) mit Karten nach Fälligkeit, erledigte durchgestrichen, überfällige markiert; Klick öffnet; Suche und Filter des Boards wirken. Eine Gesamtsicht über alle Boards gibt es nicht. |
| M-122 | Sprung aus anderen Ansichten | abgebildet | `schale/Kopf.svelte`, `routen.ts`, `ansichten/uebersicht/HeuteZeile.svelte`, `ansichten/uebersicht/Hinweise.svelte`, `ansichten/planung/KalenderKarte.svelte` | Sprünge aus Heute, Hinweisen, Kalender, Archiv und der Suche im Kopf (alle eigenen Boards, höchstens acht Treffer, Enter öffnet den ersten) gehen über den Pfad der Karte, auch in andere Boards und auf archivierte Karten (behebt M-09). |
| M-123 | Schnell-Erfassen | teilweise | `ansichten/zeit/Nachtragen.svelte`, `ansichten/telefon/Zeiten.svelte`, `ansichten/telefon/Erfassen.svelte` | Zeit nachtragen mit Kartensuche, Tag, Dauer und Vorschau, ohne Ideen, nur mit Recht; am Telefon dazu schnelles Anlegen. Fehlt weiter: die eine Freitextzeile, die Schlüssel, Dauer und Datum (gestern, Wochentag) erkennt. Fehler behoben: Schlüssel sind eindeutig. |
| M-124 | Tastenbelegung | abgebildet | `board/Schnelleingabe.svelte`, `board/BoardAnsicht.svelte`, `board/SpaltenMenue.svelte`, `detail/Aktivitaet.svelte`, `detail/Zeiterfassung.svelte`, `detail/Checkliste.svelte` | Enter, Umschalt+Enter und Escape beim Anlegen; neue Spalte und Spaltenname Enter und Escape; Enter öffnet die Karte; Enter in Checkliste, Kommentar, Tag buchen und Verknüpfen; Strg und Enter im Editor; Escape schließt Menü, Tafel, Kette und Detail. Globale Kürzel gibt es wie bisher keine. |
| M-125 | Escape im Detail | abgebildet | `detail/Kartendetail.svelte`, `teile/verwerfen.ts`, `teile/DauerFeld.svelte`, `teile/DatumFeld.svelte` | Steckt der Fokus in einem Feld, verwirft das erste Escape die Eingabe und verlässt das Feld, das zweite schließt das Detail. Fehler behoben: Titel, Blockiert, eigene Felder, Checkliste, Kommentar, Dauer und Datum übernehmen beim Escape nichts mehr. |
| M-126 | Zähler und leere Zustände | abgebildet | `board/Spalte.svelte`, `board/BoardAnsicht.svelte`, `detail/Aktivitaet.svelte`, `ansichten/uebersicht/` | Zähler an Spalte (mit Grenze), eingeklappter Spalte, Erledigt (x von y), "x von y passen" bei Filter, Filterchip, Gruppe, Checkliste, Kommentaren, Verlauf, Papierkorb, Hinweisen und Archiv; Leerzustände in Liste, Archiv, Papierkorb, Hinweisen, Beschreibung, Notizen, Kommentaren, Verlauf, Zeiten und Anhängen. |

## Was noch offen ist (nach Wichtigkeit für die Arbeit am Board)

1. **M-01** (in der App erledigt, Stufe 1): Die Seitenleiste soll auch Boards ohne Ordner zeigen, etwa unter "Ohne Ordner"; heute verschwindet so ein Board aus der Navigation.
2. **M-74** (in der App erledigt): Beim Zusammenführen zweier Gruppen darf "Zeit teilen" nicht still wechseln; die Meldung soll die geltende Einstellung nennen.
3. **M-26** (in der App erledigt, Stufe 1): Das Archiv soll wie die Erledigt-Spalte seitenweise nach dem Ladeschritt laden, mit "Mehr laden"; heute steht dort nur der Hinweis.
4. **M-62** (fehlt): Dokumente an der Karte mit Editor und Vorschau bauen, abgelegt in der Kellerwolke (E-15).
5. **M-95** (fehlt): Gespeicherte Sichten bauen (Suche, Filter, Sortierung unter einem Namen), am Konto statt im Browser.
6. **M-123** (teilweise): Eine Freitextzeile für Zeitbuchungen bauen, die Schlüssel, Dauer und Datum erkennt und erst eine Vorschau zeigt.
7. **M-10** (fehlt): Einen Export des ganzen Boards anbieten (Board, Spalten, Karten, Zeiten, Anhänge als Verweise).

## Befunde neben der Wertung

- Zu M-116 (bewusst anders): Verschieben prüft das Recht inzwischen im Anwendungsfall (`beispiel/anwendung/karten.svelte.ts`). Anlegen, Bearbeiten, Duplizieren und Kommentieren dort und der Papierkorb in `beispiel/anwendung/papierkorb.svelte.ts` prüfen es weiter nicht; die Oberfläche blendet die Wege ohne Recht aus, der Anwendungsfall selbst lehnt sie aber nicht ab, anders als die Verwaltung mit `mitRecht`.
- `hatRecht` in `regeln/board.ts` beachtet abgeschaltete Module nicht, obwohl der Kommentar es zusagt; das Timer-Recht fängt es nur über `timerErlaubt` ab.
- Am Telefon (`ansichten/telefon/TelBoard.svelte`) zeigt die Erledigt-Spalte ihre Karten noch in der Reihenfolge der Ablage statt neueste zuerst (M-28); dort und im Kopf der Liste steht als Ersatz für ein fehlendes Zeitfenster "woche", die Vorgabe ist "heute".
