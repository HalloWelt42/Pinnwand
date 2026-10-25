# Abnahme der Entwürfe gegen die Board-Mechanik

**Zweck:** Prüft für jede Mechanik der alten Pinnwand (`docs/BOARD_MECHANIK.md`, M-01 bis M-126, Fassung 0.74.0), ob und
wo die Entwürfe des Neubaus (`mockups/`) sie abbilden. Maß sind die Mechanik und die Entscheidungen in `docs/ENTWURF.md`
(E-01 bis E-22).

**Stand:** 27.10.2026, Datum der Beispielwelt der Entwürfe (geprüft am 25.10.2026). Gelesen wurde der Code unter
`mockups/src/`; alle Pfade in der Spalte "Wo" sind relativ dazu, Adressen wie `/board/prod` laufen unter
http://localhost:5398. "(Gegenprobe)" heißt: im Browser der Entwürfe nachgestellt. "(aus dem Code)" heißt: aus dem Code
abgeleitet, nicht nachgestellt.

## Zählung

| Stand | Zahl |
|---|---|
| abgebildet | 62 |
| teilweise | 45 |
| fehlt | 12 |
| bewusst anders | 3 |
| Fehler behoben | 4 |
| **Summe** | **126** |

## Regeln der Bewertung

- **abgebildet**: wirkt in den Entwürfen wie beschrieben oder besser. Behebt der Entwurf dabei einen bekannten Fehler der
  alten App, steht das in der Bemerkung.
- **teilweise**: sichtbar, aber ein Teil der Wirkung fehlt oder ist nur angedeutet. Tote Regler (Knöpfe, Felder oder
  Einstellungen ohne Wirkung) zählen nicht als abgebildet.
- **fehlt**: nirgends zu finden. Auch Dinge, die erst die App leisten kann (Laden über das Netz), stehen hier, wenn die
  Entwürfe sie nicht zeigen.
- **bewusst anders**: durch eine Entscheidung in `ENTWURF.md` ersetzt, mit E-Nummer.
- **Fehler behoben**: nur dort, wo die Mechanik im Kern ein Fehlverhalten der alten App beschreibt und die Entwürfe es
  richtig machen.
- Querschnitt, damit eine Lücke nicht an vielen Stellen zählt: Verlaufszeilen werden unter M-64 bewertet, das Merken des
  Ansichtszustands unter M-97, seitenweises Nachladen unter M-26, Filter und Sortierung der Werkzeugleiste unter M-92 bis
  M-94. Bei den übrigen Mechaniken zählt die Wirkung am Feld.

## Tabelle

| Kennung | Mechanik (kurz) | Stand | Wo | Bemerkung |
|---|---|---|---|---|
| M-01 | Board öffnen | teilweise | `schale/Seite.svelte`, `routen.ts`, `/board/prod` | Seitenleiste öffnet das Board mit Spalten, Karten und Gruppen; Erledigt gefenstert; das Detail gehört zum Pfad und schließt beim Wechsel. Fehlt: ein Board ohne Ordner verschwindet aus der Seitenleiste, weil sie nur Boards in Ordnern zeigt (Gegenprobe: Haushalt auf "Ohne Ordner" gesetzt, Eintrag weg). |
| M-02 | Board anlegen | abgebildet | `ansichten/verwaltung/BoardNeu.svelte`, `regeln/kuerzel.ts`, `boardAnlegen` in `beispiel/anwendung/boards.svelte.ts`, `/boards/neu` | Aus Vorlage oder leer mit den drei Spalten wie bisher (E-17), Name, Kürzel als Vorschlag, Ordner, Einladungen. Fehler behoben: Kürzel über alle Boards eindeutig, Umlaute ausgeschrieben, leerer Name abgewiesen. Mappen entfallen (E-02). |
| M-03 | Board umbenennen und löschen | abgebildet | `ansichten/verwaltung/board/Allgemein.svelte`, `boardUmbenennen` und `boardInPapierkorb` in `beispiel/anwendung/boards.svelte.ts`, `ansichten/verwaltung/person/Papierkorb.svelte` | Umbenennen lässt das Kürzel fest, leerer Name abgewiesen; Löschen mit Rückfrage in der Fläche in den Papierkorb der App, Wiederherstellen mit Karten, Serien, Terminen und Ordner. Die Boardliste folgt der Reihenfolge im Ordner, nicht dem Alphabet. |
| M-04 | Kopfzeile | abgebildet | `board/BoardAnsicht.svelte` | Name mit Farbpunkt, Ordner, Kürzel, Mitglieder und eigene Rolle. |
| M-05 | Ansichtsumschalter | abgebildet | `board/BoardAnsicht.svelte`, `board/ansichten.ts` | Reiter Board, Liste, Kalender, Zeitachse, jeder mit eigenem Pfad (E-09, E-22). Merken je Board siehe M-97. |
| M-06 | Abgleich beim Fensterfokus | Fehler behoben | `schale/Fuss.svelte`, `beispiel/anwendung/verbindung.svelte.ts`, `/board/prod?entwurf=live` | Statt Neuladen beim Fokus ein Ereignisstrom je Board (ENTWURF Abschnitt 1): die Änderung einer anderen Person erscheint sofort an der Karte mit Meldung, der Fuß zeigt "Live verbunden" oder "Getrennt". In den Entwürfen vorgeführt. |
| M-07 | Neuladen nach Timer-Ereignis | abgebildet | `beispiel/stand.svelte.ts`, `beispiel/abfragen.ts` | Ein Zustand für alle Ansichten, die Zeit einer Karte ist die Summe ihrer Einträge; kein Neuladen nötig, in der App über den Ereignisstrom. |
| M-08 | Mappe und Board beim Start | fehlt | nirgends | Mappen entfallen (E-02). Welche Seite die App beim Start zeigt und ob das zuletzt genutzte Board wiederkommt, zeigen die Entwürfe nicht (der Pfad / ist die Galerie). Nur am Telefon ist beim Erfassen das zuletzt genutzte Board vorbelegt. |
| M-09 | Tiefe Verweise | abgebildet | `routen.ts`, `weg.svelte.ts`, `/board/prod/131` | Offene Karte steht im Pfad, Schließen nimmt sie heraus, Zurück und Vor gehen. Fehler behoben: der Pfad öffnet jede Karte des Boards, auch archivierte (`karteAusNummer`); Sprünge in andere Boards gehen, da es keine Mappen mehr gibt. |
| M-10 | Export | fehlt | nirgends | Kein Export des Boards. Die Berichte (`ansichten/zeit/Berichte.svelte`) liefern Zeit- und Erledigt-Auswertungen, keine vollständige Ausgabe der Daten. |
| M-11 | Ladefehler | teilweise | `teile/Meldung.svelte`, `beispiel/anwendung/meldung.svelte.ts`, `/heute?entwurf=getrennt` | Getrennte Verbindung vorgeführt: letzter Stand sichtbar, Schreibendes gesperrt, Meldung mit Grund. Nicht gezeigt: ein gescheitertes Laden des Boards und der Verlust der Mitgliedschaft bei offener Ansicht (alter Fehler: Board friert ein). |
| M-12 | Spalte anlegen | teilweise | `board/BoardAnsicht.svelte`, `ansichten/verwaltung/board/Spalten.svelte`, `spalteAnlegen` in `beispiel/anwendung/boards.svelte.ts` | Der Knopf "Spalte" im Board ist ohne Wirkung (kein Klick-Handler). In den Einstellungen wirkt "Neue Spalte" mit Name, Farbe und Enter, ans Ende; ein leerer Name wird abgewiesen. |
| M-13 | Umbenennen und Grenze setzen | abgebildet | `ansichten/verwaltung/board/Spalten.svelte`, `ansichten/verwaltung/Zahlfeld.svelte`, `spalteAendern` in `beispiel/anwendung/boards.svelte.ts` | Name und Grenze je Spalte in den Einstellungen (leer heißt keine, ganze Zahl ab 1, sonst Hinweis); leerer Name abgewiesen. Escape bricht im Namensfeld nicht ab, Verlassen speichert. |
| M-14 | Grenzanzeige | teilweise | `board/Spalte.svelte`, `stil/pinnwand.css` | Kopf zeigt "n/Grenze", über der Grenze Warnfarbe, Erklärung im title. Fehlen: Bernstein genau am Limit und der Füllbalken unter dem Kopf. Alter Fehler bleibt: bei Suche zählt der Kopf nur die Treffer (Gegenprobe: In Arbeit zeigt 1/4 statt 5/4, die Warnfarbe verschwindet). |
| M-15 | Grenze weich durchgesetzt | teilweise | `hinein` in `beispiel/anwendung/karten.svelte.ts`, `ansichten/telefon/Verschieben.svelte`, `ansichten/verwaltung/board/Spalten.svelte` | Ziehen, Status, Sammelverschieben, Telefon und Spalte löschen warnen nur, ohne harten Halt. Beim Anlegen einer Karte fehlt die Warnung (`anlegen` prüft die Grenze nicht). |
| M-16 | Spalten umsortieren | teilweise | `board/Spalte.svelte`, `ansichten/verwaltung/board/Spalten.svelte`, `spaltenOrdnen` in `beispiel/anwendung/boards.svelte.ts` | Im Board ist der Griff im Spaltenkopf nur ein Symbol ohne Ziehen, "Nach links" und "Nach rechts" gibt es nicht. In den Einstellungen wirkt das Ziehen am Griff und prüft die vollständige Liste. |
| M-17 | Spaltenfarben | abgebildet | `modell.ts` (Spalte), `ansichten/verwaltung/board/Spalten.svelte` | Besser: jede Spalte hat eine eigene, wählbare Farbe statt der Farbe aus der Position; Punkt im Kopf, Status in Liste und Detail. |
| M-18 | Einklappen | teilweise | `board/Spalte.svelte` | Ein- und Aufklappen wirken (schmal, senkrechter Name, Zahl). Fehlen: Farbstrich je Karte, Ablegen in eine eingeklappte Spalte (sie hat keine Ablagezone) und Umsortieren im eingeklappten Zustand. Merken siehe M-97. |
| M-19 | Erledigt-Spalte markieren | abgebildet | `zurErledigtSpalte` in `beispiel/anwendung/boards.svelte.ts`, `ansichten/verwaltung/board/Spalten.svelte` | Genau eine Erledigt-Spalte, das Recht wird geprüft. Fehler behoben: Übergangsregel (Karten der alten Spalte wieder offen mit neuem Alter, Karten der neuen mit Abschluss heute, laufende Timer halten an und buchen). |
| M-20 | Spalte löschen | abgebildet | `spalteLoeschen` in `beispiel/anwendung/boards.svelte.ts`, `spalteInPapierkorb` und `wiederherstellen` in `beispiel/anwendung/papierkorb.svelte.ts`, `/board/prod/einstellungen/spalten?entwurf=rueckfrage` | Rückfrage in der Fläche mit Kartenzahl: Karten verschieben (Gruppe zieht mit, Grenze warnt) oder mit der Spalte in den Papierkorb; Wiederherstellen an die alte Stelle mit allem. Serien bekommen eine neue Zielspalte (behebt den Fehler aus M-106). Letzte Spalte und Erledigt-Spalte bleiben. |
| M-21 | Spaltenmenü | teilweise | `board/Spalte.svelte` | Der Knopf mit drei Punkten führt in die Einstellungen der Spalten statt ein Menü zu öffnen; Umbenennen, Grenze, Erledigt-Spalte und Löschen gehen nur dort, abseits des Boards. Einklappen sitzt im Kopf. |
| M-22 | Gefenstertes Laden | abgebildet | `sichtbareKarten` und `erledigteOhneArchiv` in `beispiel/abfragen.ts`, `imFenster` in `regeln/board.ts` | Die Erledigt-Spalte zeigt nur ihr Zeitfenster, Archivierte nie, die Gesamtzahl daneben. Seitenweises Laden siehe M-26. |
| M-23 | Abschlussdatum | teilweise | `wechseln` in `beispiel/anwendung/karten.svelte.ts`, `serienzeitBuchen` in `beispiel/anwendung/serien.svelte.ts` | Ablegen in Erledigt setzt den Abschluss auf heute, der Nachtrag einer Serienkarte auf ihren Termintag. Fehlt: eine Serienkarte, die in Erledigt gezogen wird, bekommt heute statt ihres Termintags (aus dem Code). |
| M-24 | Zeitfilter im Spaltenkopf | abgebildet | `board/Spalte.svelte`, `fensterAb` in `regeln/board.ts` | Heute, Gestern, Woche, Monat, Jahr, Alle; ein Wechsel wirkt sofort. Neu: Vorgabe je Spalte in den Einstellungen. Merken der persönlichen Wahl siehe M-97. |
| M-25 | Zeitfenster ausgesetzt bei Suche | abgebildet | `board/Spalte.svelte`, `passt` in `beispiel/abfragen.ts`, `/board/prod?entwurf=suche` | Bei Suche zeigt Erledigt alle Karten außerhalb des Archivs, gefiltert. Fehler behoben: Volltext über die Werte (Notizen, Labelnamen, eigene Felder, Kommentare, Checkliste), nie über rohe Texte. Filter siehe M-92 bis M-94. |
| M-26 | Nachladen, "Mehr laden", Zähler | teilweise | `board/Spalte.svelte`, `ansichten/uebersicht/Archiv.svelte`, `ansichten/verwaltung/board/Allgemein.svelte` | Der Zähler "x von y" steht in der Erledigt-Spalte und im Archiv. Fehlen: Nachladen beim Rollen und "Mehr laden"; im Archiv steht nur der Text "Beim Rollen laden die nächsten". Die Einstellung "Karten je Ladeschritt" ist damit ein toter Regler (sie wird nirgends gelesen). |
| M-27 | Schutz gegen überholte Antworten | fehlt | nirgends | Die Entwürfe laden nicht über das Netz; der Generationszähler je Spalte gehört in die App. |
| M-28 | Reihenfolge in Erledigt-Spalten | teilweise | `board/Spalte.svelte`, `kartenDerSpalte` in `beispiel/stand.svelte.ts` | Fehlt: neueste zuerst nach Abschlussdatum; die Spalte zeigt die Reihenfolge der Ablage (Gegenprobe, Zeitfenster Alle: 26.10., 26.10., 26.10., 23.10., 22.10., 23.10., 23.10., 16.10., 21.10., 26.10.). Ziehen innerhalb Erledigt wirkt jetzt, steht aber gegen die Ordnung nach Datum. |
| M-29 | Archiv-Grenze | abgebildet | `imArchiv` und `imFenster` in `regeln/board.ts`, `ansichten/verwaltung/board/Allgemein.svelte` | Reine Ladegrenze je Board (Vorgabe 365 Tage), eine größere Zahl holt Karten zurück, Berichte zählen alle. |
| M-30 | Archiv-Ansicht | abgebildet | `ansichten/uebersicht/Archiv.svelte`, `/board/prod/archiv` | Eigene Seite mit Gesamtzahl, neueste zuerst, Schlüssel, Titel, Abschluss im deutschen Format (behebt das ISO-Format), Zuständig, Labels, Zeit, Suche, Leerzustand; Klick öffnet die Karte, "Zurück zum Board". Nachladen siehe M-26. |
| M-31 | Rückholen | abgebildet | `verschieben` und `wechseln` in `beispiel/anwendung/karten.svelte.ts` | Ziehen oder Status in eine offene Spalte: neues Alter, der Abschluss entfällt, die Gruppe zieht mit; aus dem Archiv über den Status im Detail. |
| M-32 | Karte anlegen | abgebildet | `board/Schnelleingabe.svelte`, `anlegen` in `beispiel/anwendung/karten.svelte.ts`, `/board/prod?entwurf=schnell` | Enter legt an, Umschalt+Enter bricht um, Escape schließt und leert, Arbeit oder Idee, Feld bleibt offen, geleert erst nach Erfolg, leerer Titel abgewiesen. In der Erledigt-Spalte gibt es kein "Karte" (Weg über den Status). Warnung siehe M-15. |
| M-33 | Vorbelegung neuer Karten | abgebildet | `anlegen` in `beispiel/anwendung/karten.svelte.ts` | Zuständig ist das angemeldete Konto, ans Ende, Zeitpunkte jetzt, Arbeit (ohne Zeiterfassung Idee), Verlauf "hat die Karte angelegt". Fehler behoben: kein "zuletzt gesetztes Kürzel" mehr. |
| M-34 | Kartenschlüssel und Laufnummer | abgebildet | `anlegen` in `beispiel/anwendung/karten.svelte.ts`, `regeln/kuerzel.ts`, `ansichten/verwaltung/board/Allgemein.svelte` | Kürzel plus laufende Nummer, nie wiederverwendet; der Schlüssel steht auf Karte, im Detail, in Liste und Pfad. Fehler behoben: Kürzel eindeutig über alle Boards; Wiederherstellen behält den Schlüssel. |
| M-35 | Arbeit oder Idee | abgebildet | `board/Schnelleingabe.svelte`, `detail/Kartendetail.svelte`, `artSetzen` in `beispiel/anwendung/karten.svelte.ts`, `timerErlaubt` in `beispiel/abfragen.ts` | Umschalter beim Anlegen und im Detail; eine Idee hat keinen Timer und keine Abschnitte für Zeit und Verknüpfung; Umschalten auf Idee hält den Timer an und bucht; Zeiten bleiben gespeichert. Ein Board ohne Zeiterfassung legt nur Ideen an. |
| M-36 | Duplizieren | fehlt | nirgends | Kein Knopf im Detailkopf und kein Anwendungsfall. |
| M-37 | Aufbau der Karte | teilweise | `board/Karte.svelte` | Cover, Labels, Blockade mit Grund, Titel, eigene Felder, Fortschritt der Checkliste, Fußzeile. Fehlt: der Auszug der Beschreibung auf zwei Zeilen. |
| M-38 | Zeitknopf | teilweise | `board/Karte.svelte` | Starten, Anhalten, Fortsetzen ohne Öffnen; Zeit erst ab mehr als null; laufend hervorgehoben; ein fremder Timer nur zur Ansicht. Fehlen: die Gruppenzeit bei geteilter Zeit und Rot bei überschrittener Schätzung. |
| M-39 | Fälligkeit | teilweise | `faelligText` in `beispiel/format.ts`, `board/Karte.svelte` | Rot bei überfällig mit "n Tage über", "heute" in Bernstein, "morgen" als Wort. Fehlt: Bernstein bis in zwei Tagen. Fehler behoben: erledigte Karten zeigen keine Fälligkeit. |
| M-40 | Weitere Marker | teilweise | `board/Karte.svelte` | Kette, Schlüssel, Checkliste n/m, Kommentarzahl, Anhänge, Serie, Zuständige (bis drei). Fehlen: Prioritätspunkt, Gruppengröße an der Kette, Grün bei vollständiger Checkliste. |
| M-41 | Alterung | abgebildet | `alterung` in `regeln/board.ts`, `board/Karte.svelte`, `ansichten/verwaltung/board/Allgemein.svelte` | Sanduhr mit Tagen, Warnung und Gefahr je Board einstellbar. Fehler behoben: Stufen unabhängig (0 schaltet nur eine aus); in Erledigt-Spalten steht das Abschlussdatum statt des Alters. |
| M-42 | Aktionen beim Überfahren | fehlt | nirgends | Weder Kette noch Papierkorb auf der Karte. |
| M-43 | Karte öffnen | abgebildet | `board/Karte.svelte`, die Öffnen-Hilfe in `board/BoardAnsicht.svelte` | Klick oder Enter öffnet über den Pfad; Tab erreicht jede Karte. |
| M-44 | Detail öffnen und schließen | teilweise | `detail/Kartendetail.svelte`, `board/BoardAnsicht.svelte` | Leiste rechts über dem Board, neu mit Vollbild; zeigt immer den aktuellen Stand; X schließt. Fehlen: Escape schließt nicht, obwohl der Knopf es nennt (Gegenprobe), kein Schließen per Klick daneben, der Fokus springt nicht ins Detail. |
| M-45 | Kopf des Details | teilweise | `detail/Kartendetail.svelte` | Schlüssel, Spalte, Arbeit oder Idee, Vollbild, Schließen; Blockiert steht als Feld bei den Angaben. Fehlt: Duplizieren (M-36); "Verweis kopieren" und "Karte vorlesen" sind Knöpfe ohne Wirkung. |
| M-46 | Titel | abgebildet | `detail/Kartendetail.svelte` | Speichert beim Verlassen oder mit Enter. Fehler behoben: ein leerer Titel wird nicht gespeichert. |
| M-47 | Blockiert mit Grund | abgebildet | `detail/Kartendetail.svelte`, `board/Karte.svelte`, `ansichten/uebersicht/HeuteZeile.svelte` | Feld "Grund, wenn die Karte wartet": Text blockiert, Leeren hebt auf; die Karte zeigt den Grund, Heute eine Marke. Verlauf siehe M-64. |
| M-48 | Status-Auswahl | abgebildet | `detail/Kartendetail.svelte`, `verschieben` in `beispiel/anwendung/karten.svelte.ts` | Derselbe Weg wie das Ziehen (ans Ende, Alter neu, Gruppe, Timer, Abschluss, Warnung); nur mit dem Recht "Karten verschieben". |
| M-49 | Priorität | abgebildet | `detail/Kartendetail.svelte`, `anzeige.ts` | Keine, Niedrig, Mittel, Hoch und neu Dringend; speichert sofort. |
| M-50 | Start | abgebildet | `teile/DatumFeld.svelte`, `starten` in `beispiel/anwendung/timer.svelte.ts` | Deutsches Textfeld, leer entfernt; der erste Timer-Start setzt den Start, wenn er fehlt. Fehler behoben: kein natives Datumsfeld. |
| M-51 | Fällig | abgebildet | `teile/DatumFeld.svelte`, `ansichten/planung/Kalender.svelte` | Speist Karte, Heute, Liste und Kalender; im Kalender setzt Ziehen auf einen Tag die Fälligkeit. |
| M-52 | Zuständig | abgebildet | `teile/Personenwahl.svelte`, `detail/Kartendetail.svelte` | Mehrere Zuständige aus den Mitgliedern des Boards, Textfeld mit Vorschlägen. Fehler behoben: nur Mitglieder; der Timer gehört der Person, ein Wechsel schreibt keine Sitzung um. |
| M-53 | Cover | abgebildet | `teile/Farbwahl.svelte` | "Keine" plus die Palette des Appkerns, speichert sofort. |
| M-54 | Zeitkennzahlen | abgebildet | `detail/Kartendetail.svelte` | Im Status, Durchlaufzeit, Erstellt mit Person. Fehler behoben: "Im Status" folgt der Alterung des Boards. |
| M-55 | Speichermodell des Details | teilweise | `detail/Kartendetail.svelte`, `bearbeiten` in `beispiel/anwendung/karten.svelte.ts`, `/board/prod/115?entwurf=konflikt` | Jedes Feld speichert für sich, ohne Bearbeiten-Modus, mit Rückgängig. Der Konflikt bei veralteter Fassung ist nur vorgeführt: "Ihre behalten" und "Meine übernehmen" sind ohne Wirkung. Beschreibung und Notizen speichern nicht (M-56, M-57). |
| M-56 | Beschreibung | teilweise | `detail/Textfeld.svelte`, `/board/prod/131?entwurf=bearbeiten` | Gerendert, ein Klick öffnet den Editor an Ort und Stelle, Leerzustand vorhanden. Die Wirkung fehlt: der Editor zeigt einen festen Beispieltext, "Fertig" schließt nur, ohne zu speichern; kein Autospeichern, keine Anzeige "gespeichert"; Vollbild und Vorlesen sind Knöpfe ohne Wirkung; Escape verwirft nicht, obwohl es dasteht. |
| M-57 | Notizen | teilweise | `detail/Textfeld.svelte` | Gerendert lesbar und überall in der Suche enthalten (behebt den alten Fehler der Board-Suche). Bearbeiten fehlt: ein Klick auf vorhandene Notizen tut nichts, der Vollbild-Knopf ist ohne Wirkung. |
| M-58 | Labels an der Karte | bewusst anders | `detail/Kartendetail.svelte`, `ansichten/verwaltung/board/Labels.svelte` | E-02: Labels gehören dem Board mit Name und Farbe; an der Karte schalten Chips sie ein und aus. Ein neues Label entsteht nur in den Einstellungen. Fehler behoben: Dubletten ohne Beachtung von Groß und klein werden abgewiesen. |
| M-59 | Labelfarben | abgebildet | `labelAendern` und `labelLoeschen` in `beispiel/anwendung/boards.svelte.ts` | Farbe je Label aus dem Board; Umbenennen und Umfärben gelten auf allen Karten; Löschen mit Rückfrage entfernt das Label an den Karten (bisher blieb der Text stehen). |
| M-60 | Checkliste | teilweise | `detail/Kartendetail.svelte` | Abhaken, Hinzufügen mit Enter, Entfernen mit Rückgängig, Zähler n/m, erledigte durchgestrichen, Fortschritt auf der Karte. Fehlen: Umbenennen eines Punkts und der Fortschrittsbalken im Detail. |
| M-61 | Kommentare | teilweise | `detail/Kartendetail.svelte`, `kommentieren` in `beispiel/anwendung/karten.svelte.ts`, `ansichten/telefon/TelKartendetail.svelte` | Liste mit Person, Zeit und Erwähnungen, Senden, Recht "Kommentieren". Fehler behoben: Autor ist das Konto. Fehlen: Markdown, Vorlesen am Kommentar, Enter sendet nicht; am Rechner leert sich das Feld auch bei abgelehntem Senden (alter Fehler, am Telefon behoben). |
| M-62 | Dokumente an der Karte | fehlt | nirgends | Kein Abschnitt Dokumente mit Editor. E-15 regelt nur die Ablage in der Kellerwolke, nicht den Wegfall. |
| M-63 | Anhänge | teilweise | `detail/Kartendetail.svelte` | Liste mit Name, Größe und Ablage in der Kellerwolke (E-15), Zahl auf der Karte. "Hochladen", "Aus der Kellerwolke" und "Öffnen" sind ohne Wirkung, ebenso das Ziehen auf die Fläche; Entfernen fehlt. |
| M-64 | Verlauf | teilweise | `detail/Kartendetail.svelte`, `wechseln` und `anlegen` in `beispiel/anwendung/karten.svelte.ts` | Reiter Verlauf, neueste zuerst, mit Person. Geschrieben werden nur Anlegen, Verschieben und Erledigen (dazu das Verwerfen im Nachtrag). Es fehlen Zuständig, Fällig, Priorität, Blockade, Art, Kommentar, Zeitbuchungen, Anhänge, die eigene Zeile der mitgezogenen Karte und der Leerzustand. |
| M-65 | Neue Fassung wartet | fehlt | nirgends | Gehört in die App (Neuladen bei neuer Fassung); die Entwürfe zeigen es nicht. |
| M-66 | Umsortieren in einer Spalte | abgebildet | `board/Spalte.svelte`, `ablegen` in `beispiel/anwendung/karten.svelte.ts` | Platzhalter, Reihenfolge sofort, die Gruppe bleibt. Fehler behoben: die Spalte übergibt ihre neue Reihenfolge selbst, kein Platz daneben. Ablegen an derselben Stelle meldet trotzdem "neu geordnet" mit Rückgängig (Gegenprobe). |
| M-67 | Wechsel zwischen Spalten | abgebildet | `ablegen`, `hinein` und `wechseln` in `beispiel/anwendung/karten.svelte.ts` | Neue Stelle, Alter neu, Verlauf, die Gruppe zieht mit, Warnung über der Grenze. Eingeklappte Spalten siehe M-18. |
| M-68 | Ablegen in Erledigt | abgebildet | `wechseln` in `beispiel/anwendung/karten.svelte.ts`, `timerBeenden` in `beispiel/anwendung/timer.svelte.ts`, `/board/prod?entwurf=erledigt` | Abschluss heute; Timer aller Personen auf der Karte und den mitgezogenen halten an und buchen; die Meldung nennt die Zeit. Einsortieren nach Datum siehe M-28. |
| M-69 | Ziehen gesperrt bei Filter | teilweise | `board/BoardAnsicht.svelte`, `board/Spalte.svelte` | Bei Suche ist Ziehen in allen Spalten gesperrt, "Verschieben pausiert" mit Hand steht da. Fehlt: ein Klick darauf setzt nichts zurück (nur Escape im Suchfeld leert die Suche). |
| M-70 | Rücksprung mit Grund | teilweise | `ablegen` in `beispiel/anwendung/karten.svelte.ts`, die Hilfe für Änderungen in `beispiel/anwendung/meldung.svelte.ts`, `board/Spalte.svelte` | Eine abgelehnte Änderung meldet ihren Grund. Fehlt: die Karte springt nicht zurück, weil die Spalte ihre gezogene Reihenfolge behält, solange sich der Zustand nicht ändert (aus dem Code). Fehler behoben: die Zielspalte muss zum Board der Karte gehören (`verschieben`). |
| M-71 | Optik beim Ziehen | abgebildet | `board/Spalte.svelte`, `stil/pinnwand.css`, `/board/prod?entwurf=ziehen` | Gezogene Karte angehoben, Zielplatz mit "hier ablegen" und "zieht mit"; Spalten ziehen in den Einstellungen am Griff. |
| M-72 | Kette ziehen | fehlt | nirgends | Keine Kette auf der Karte, keine Zeigergeste, kein Anwendungsfall zum Verknüpfen. |
| M-73 | Verknüpfen im Detail | teilweise | `detail/Kartendetail.svelte` | Das Feld "Karte suchen und verknüpfen" steht da, hat aber weder Bindung noch Treffer; es gibt keinen Anwendungsfall dafür. |
| M-74 | Gruppenregeln | teilweise | `gruppeLoesen` in `beispiel/anwendung/karten.svelte.ts` | Lösen wirkt, unter zwei Mitgliedern endet die Gruppe. Fehlen: Gruppe bilden, beitreten und zusammenführen. |
| M-75 | Zeit teilen | teilweise | `zeitTeilen` in `beispiel/anwendung/karten.svelte.ts`, `zeitDerGruppe` in `beispiel/abfragen.ts`, `detail/Zeiterfassung.svelte` | Der Schalter wirkt, das Detail zeigt "Zusammen mit der Gruppe"; jede Sekunde zählt einmal; laufende Zeit anderer zählt mit (behebt den alten Fehler). Fehlt: die Karte im Board zeigt die Gruppenzeit nicht (M-38). |
| M-76 | Mitziehen beim Spaltenwechsel | teilweise | `hinein` in `beispiel/anwendung/karten.svelte.ts`, `gruppenmitglieder` in `beispiel/stand.svelte.ts` | Mitglieder ziehen ans Ende der Zielspalte mit, Alter neu, Timer bei Erledigt. Fehler: Mitglieder auf anderen Boards werden nicht ausgenommen und landen in der Spalte des fremden Boards (aus dem Code; die Beispieldaten haben nur eine Gruppe in einem Board). Das Telefon zeigt nur Mitglieder desselben Boards an. |
| M-77 | Mitglieder öffnen | teilweise | `detail/Kartendetail.svelte` | Liste der anderen Mitglieder mit Schlüssel, Titel und "Lösen". Fehlt: ein Klick öffnet das Mitglied nicht (kein Verweis). |
| M-78 | Timer starten | abgebildet | `starten` in `beispiel/anwendung/timer.svelte.ts`, `timerErlaubt` in `beispiel/abfragen.ts` | Auf der Karte, im Detail, in Heute, im Kopf (Fortsetzen) und am Telefon; setzt den Start, wenn er fehlt. Fehler behoben: nicht in Erledigt, nicht auf Ideen, nur mit dem Recht "Eigene Zeit buchen". |
| M-79 | Pause und Stopp | abgebildet | `anhalten`, `fortsetzen` und `stoppen` in `beispiel/anwendung/timer.svelte.ts`, `detail/Zeiterfassung.svelte`, `schale/Kopf.svelte` | Anhalten bucht und lässt fortsetzen, Stopp bucht und beendet; die Knöpfe je Zustand wie bisher. |
| M-80 | Ein Timer je Person | Fehler behoben | `modell.ts` (Timer), `starten` in `beispiel/anwendung/timer.svelte.ts` | Der Timer gehört dem Konto, nicht dem Kürzel der Karte: ein Start beendet und bucht nur den eigenen Timer auf einer anderen Karte, fremde laufen weiter (ENTWURF Abschnitte 1 und 2). |
| M-81 | Buchung beim Stoppen | abgebildet | `sitzungBuchen` in `beispiel/anwendung/zeiten.svelte.ts`, `ansichten/zeit/TagLeiste.svelte`, `/zeiten?entwurf=deckel` | An Mitternacht zerlegt, ein Timer-Eintrag je Karte, Person und Tag mit sichtbaren Sitzungen, Handbuchungen eigenständig. Fehler behoben: die Person gehört zum Schlüssel der Zusammenfassung; über 12 Stunden gedeckelt mit Vermerk und Rückfrage nach dem echten Ende. |
| M-82 | Laufleiste | abgebildet | `schale/Kopf.svelte`, `ansichten/uebersicht/Laufend.svelte` | Im Kopf jeder Seite Schlüssel, Titel, Zeit, Anhalten oder Fortsetzen, Stopp; in Heute dazu Prozent der Schätzung und "überschritten". |
| M-83 | Abgleich laufender Timer | abgebildet | `timerVon` und `laufendAuf` in `beispiel/abfragen.ts` | Ein Zustand für Kopf, Karte, Heute und Telefon; in der App über den Ereignisstrom statt einer Abfrage alle 60 Sekunden. Fremde Timer sind an der Karte sichtbar. |
| M-84 | Automatische Stopps | abgebildet | `timerBeenden` in `beispiel/anwendung/timer.svelte.ts`, `inPapierkorb`, `mitgliedEntfernen` | Erledigen, Idee, Papierkorb und das Entfernen eines Mitglieds halten an und buchen. Besser: beim Löschen geht die Sitzung nicht mehr verloren. |
| M-85 | Live-Zeit | teilweise | `laufendSek` in `beispiel/format.ts` | Die laufende Sitzung wird überall eingerechnet. Es gibt keinen Sekundentakt: "jetzt" ist in der Beispielwelt fest, die Anzeige zählt nicht hoch. |
| M-86 | Tag buchen | abgebildet | `detail/Zeiterfassung.svelte`, `buchen` in `beispiel/anwendung/zeiten.svelte.ts`, `ansichten/zeit/Nachtragen.svelte`, `ansichten/telefon/Zeiten.svelte` | Datum (Vorgabe heute), Dauer, "Tag buchen"; der Eintrag gehört dem eigenen Konto. Fehler behoben: eine unlesbare Dauer wird rot mit Hinweis statt still ignoriert. Enter bucht nicht (M-124). |
| M-87 | Ticketzeit gesamt setzen | abgebildet | `ticketzeitSetzen` und `setzeTageszeit` in `beispiel/anwendung/zeiten.svelte.ts`, `teile/DauerFeld.svelte` | Gesperrt, solange der eigene Timer läuft; mehr bucht die Differenz heute, weniger kürzt die eigenen jüngsten Einträge von heute. Fehler behoben: fremde Einträge bleiben unberührt, Escape verwirft. |
| M-88 | Tagesliste | teilweise | `detail/Zeiterfassung.svelte`, `ansichten/zeit/TagLeiste.svelte` | An der Karte Einträge je Tag und Person mit Herkunft, Löschen mit Rückgängig, fremde mit Schloss; aktualisiert sich sofort. Fehler behoben: Rückgängig bringt den Eintrag genau zurück. Fehlt: das Datum eines Eintrags ist nirgends änderbar, die Dauer nur im Stundenzettel. |
| M-89 | Schätzung und Fortschritt | abgebildet | `detail/Zeiterfassung.svelte`, `ansichten/uebersicht/Liste.svelte` | Schätzung als Dauer, leer entfernt; Balken mit Warnfarbe über 100 Prozent; die Liste zeigt Ist und Soll mit Warnzeichen. |
| M-90 | Zeiteingabe | abgebildet | `dauerLesen` in `regeln/eingabe.ts`, `teile/DauerFeld.svelte` | Dieselben Formate (1:30, 1:30:00, 1,5, 90m, 90min, 2h, 2std); Unlesbares wird angezeigt statt verworfen. |
| M-91 | Suche | abgebildet | `board/BoardAnsicht.svelte`, `passt` in `beispiel/abfragen.ts` | Jedes Wort muss vorkommen, ohne Beachtung von Groß und klein; gilt in Board, Liste, Kalender und Zeitachse; Escape leert. Fehler behoben: Notizen werden überall gefunden. Merken siehe M-97. |
| M-92 | Prioritäts- und Labelfilter | teilweise | `board/BoardAnsicht.svelte` | Der Chip "Filter" ist ohne Wirkung (er zeigt nur bei Suche eine 1); es gibt weder Tafel noch Filter. |
| M-93 | Personenfilter | teilweise | `board/BoardAnsicht.svelte` | Der Chip "Alle Personen" ist ohne Wirkung. |
| M-94 | Sortierung | teilweise | `board/BoardAnsicht.svelte`, `ansichten/uebersicht/Liste.svelte` | Der Chip "Manuell" ist ohne Wirkung; sortieren geht nur in der Liste über die Spaltenköpfe. |
| M-95 | Gespeicherte Sichten | fehlt | nirgends | Keine Sichten, weder im Browser noch am Konto. |
| M-96 | Filtervorschläge | fehlt | nirgends | Kein Vorschlagsdienst in der Werkzeugleiste. |
| M-97 | Ansichtszustand im Browser | fehlt | nirgends | Suche, eingeklappte Spalten, Zeitfenster und Ansicht leben nur in der Komponente und gehen beim Wechsel der Seite verloren. |
| M-98 | Listenansicht | abgebildet | `ansichten/uebersicht/Liste.svelte`, `/board/prod/liste` | Dieselben Karten wie im Board, fester Kopf; Schlüssel, Titel mit Idee und Blockade, Status, Zuständig, Priorität, Fällig oder Abschluss, Labels, eigene Felder, Zeit; erledigte grau; Klick öffnet; Leerzustand. Fehler behoben: die laufende Zeit wird gezeigt. |
| M-99 | Sortieren in der Liste | abgebildet | `ansichten/uebersicht/Liste.svelte` | Klick sortiert, ein zweiter dreht, ein Pfeil zeigt die Richtung. Fehler behoben: Status sortiert nach der Folge der Spalten. |
| M-100 | Auswahl | abgebildet | `ansichten/uebersicht/Liste.svelte`, `/board/prod/liste?entwurf=auswahl` | Kästchen je Zeile ohne Öffnen, "Alle auswählen", die Auswahl räumt sich selbst auf. |
| M-101 | Sammelaktionen | abgebildet | `ansichten/uebersicht/Liste.svelte`, `sammelVerschieben`, `sammelZuweisen`, `sammelLabel`, `sammelPrioritaet` in `beispiel/anwendung/karten.svelte.ts` | Verschieben (Gruppe, Timer, Warnung), Zuweisen an jedes Mitglied, neu Label, Priorität, Papierkorb mit einem Rückgängig. Fehler behoben: alles in einem Schritt, kein halber Stand. Zuweisen fügt hinzu; "niemand" gibt es nur je Karte im Detail. |
| M-102 | Karte löschen | abgebildet | `inPapierkorb` in `beispiel/anwendung/papierkorb.svelte.ts`, `detail/Kartendetail.svelte`, `ansichten/uebersicht/Papierkorb.svelte` | "In den Papierkorb" im Detail und als Sammelaktion, nur mit dem Recht "Karten löschen"; der Timer bucht, ein Serientag wird ausgelassen, Meldung mit Rückgängig. Fehler behoben: Papierkorb je Board mit allem, was daran hängt. Papierkorb auf der Karte siehe M-42. |
| M-103 | Rückgängig einer Karte | Fehler behoben | die Hilfe für Änderungen in `beispiel/anwendung/meldung.svelte.ts`, `wiederherstellen` in `beispiel/anwendung/papierkorb.svelte.ts` | Rückgängig stellt den genauen Stand wieder her; Wiederherstellen aus dem Papierkorb bringt Schlüssel, Stelle, Zeiten, Kommentare, Anhänge, Gruppe und Serienbezug zurück. Keine Neuanlage mehr. |
| M-104 | Hinweise (Meldung unten) | abgebildet | `teile/Meldung.svelte` | Eine Meldung, sie geht nach sechs Sekunden, bleibt unter dem Zeiger, X schließt, mit Rückgängig; getrennt mit eigenem Text. |
| M-105 | Rückfragen im Überblick | abgebildet | `ansichten/verwaltung/board/Spalten.svelte`, `ansichten/verwaltung/board/Allgemein.svelte`, `ansichten/verwaltung/board/Labels.svelte`, `ansichten/uebersicht/Papierkorb.svelte`, `ansichten/planung/SerieBearbeiten.svelte` | Rückfragen in der Fläche bei Spalte, Board, Label, endgültigem Entfernen und Serie; Papierkorb und Rückgängig bei Karte, Spalte und Zeiteintrag; die letzte Spalte bleibt. Keine Browser-Dialoge. |
| M-106 | Serienkarten | abgebildet | `regeln/serien.ts`, `beispiel/anwendung/serien.svelte.ts`, `ansichten/planung/SerieBearbeiten.svelte` | Zielspalte, Titel mit Uhrzeit, Beschreibung, Labels, Teilnehmer als Zuständige, fällig am Termintag, Schätzung aus der Dauer. Fehler behoben: das Löschen der Zielspalte setzt eine neue. Das Anlegen der Karten macht in der App der Server. |
| M-107 | Vorbuchungsfenster | abgebildet | `vorkommenAm` und `vorlaufEnde` in `regeln/serien.ts`, `nachtrag` in `beispiel/abfragen.ts` | Vorlauf je Serie, Rückblick 31 Tage, Fortsetzen ab dem Tag, Feiertage wählbar, Abwesenheiten je Teilnehmer, eine Karte je Serie und Tag. |
| M-108 | Auslass | abgebildet | `auslassen` in `beispiel/anwendung/papierkorb.svelte.ts`, `tagAuslassen` in `beispiel/anwendung/serien.svelte.ts` | Ein gelöschter Serientag kommt nie wieder; Wiederherstellen nimmt den Auslass zurück. |
| M-109 | Pause, Ändern, Urlaub | teilweise | `pausieren` und `serieAendern` in `beispiel/anwendung/serien.svelte.ts`, `eintragen` in `beispiel/anwendung/abwesenheiten.svelte.ts` | Pause und Ändern fassen nur unberührte Vorbuchungen an. Fehlt: ein nachträglich eingetragener Urlaub nimmt schon angelegte Serienkarten der Person nicht zurück; er wirkt nur über die Regel (Tag ausgelassen, Person fehlt). |
| M-110 | Serie löschen | abgebildet | Serie löschen in `beispiel/anwendung/serien.svelte.ts`, vorgeführt unter `/serien/se-runde` (Zustand Löschen) | Rückfrage in der Fläche; unberührte Vorbuchungen gehen, Karten mit Zeit oder erledigte bleiben gelöst als Verlauf. |
| M-111 | Nachtrag ignorierter Serienkarten | abgebildet | `ansichten/planung/Nachtrag.svelte`, `nachtragBestaetigen`, `nachtragVerwerfen`, `alleBestaetigen` in `beispiel/anwendung/serien.svelte.ts`, `/serien?entwurf=nachtrag` | Bestätigen mit anpassbarer Dauer auf den Termintag, Karte nach Erledigt mit dem Termintag, Verwerfen, alle bestätigen, später; Termine dazu. Fehler behoben: nur eigene Posten; Verwerfen nimmt bei mehreren Teilnehmern nur dich heraus. |
| M-112 | Ein verknüpftes Transkript | teilweise | `detail/Kartendetail.svelte` (Modul Transkripte) | Abschnitt mit verknüpften Stellen. Das Suchfeld und "Abspielen ab der Stelle" sind ohne Wirkung, Lösen fehlt. |
| M-113 | Transkript-Verweise (Marken) | teilweise | `detail/Kartendetail.svelte`, `modell.ts` (TranskriptMarke) | Marken mit Aufnahme, Stelle und Text werden gezeigt. Fehlen: Zusammenfassung je Marke mit Vorschlag, Anhängen, Entfernen, Sprung an die Stelle. |
| M-114 | Vorlesen | teilweise | `detail/Kartendetail.svelte`, `detail/Textfeld.svelte`, `ansichten/uebersicht/Heute.svelte`, `ansichten/zeit/Berichte.svelte` | Knöpfe an Karte, Beschreibung, Heute und Berichten (E-06); keiner liest vor, Heute schaltet nur die Beschriftung um. Fehlen: der Lautsprecher am Kommentar, Stimme und Tempo. |
| M-115 | Labelvorschläge | fehlt | nirgends | Das Modul KI bietet eine Checkliste und eine Zusammenfassung an (beide Knöpfe ohne Wirkung), Labels nicht. |
| M-116 | Projekt-Prüfung | bewusst anders | `hatRecht` in `regeln/board.ts`, `darf` in `beispiel/abfragen.ts`, `mitRecht` in `beispiel/anwendung/boards.svelte.ts`, `ansichten/verwaltung/board/Rollen.svelte` | E-02, E-03, E-04: Rechte je Board und Rolle statt Mitgliedschaft in einer Mappe. Lücke im Entwurf: die Anwendungsfälle der Karten (anlegen, bearbeiten, verschieben, Papierkorb) prüfen kein Recht, Ziehen und Schnelleingabe ignorieren die Rolle, nur das Detail blendet aus; `hatRecht` lässt Rechte abgeschalteter Module gelten, obwohl der Kommentar das Gegenteil sagt. |
| M-117 | Zeit- und Timer-Rechte | bewusst anders | `RECHTE` in `beispiel/daten.ts`, `timerErlaubt` in `beispiel/abfragen.ts`, `detail/Zeiterfassung.svelte` | E-04, E-07: Rechte "Eigene Zeit buchen", "Zeiten anderer sehen" und "Zeiten anderer bearbeiten" je Rolle. Fehler behoben: die Oberfläche bietet Start, Ticketzeit und Löschen nur an, wo das Recht besteht. |
| M-118 | Identitätsquelle | Fehler behoben | `modell.ts` (Konto), `ansichten/verwaltung/person/Konto.svelte` | Identität ist das Konto der Kellerwolke mit fester Kennung (E-13); Zuständig, Zeiteintrag, Kommentar, Verlauf und Timer hängen an der Kennung, das Kürzel ist nur Anzeige. |
| M-119 | Glocke | abgebildet | `schale/Kopf.svelte`, `ansichten/uebersicht/Hinweise.svelte`, `beispiel/anwendung/hinweise.svelte.ts`, `/hinweise` | Die Glocke mit Zähler führt zu den Hinweisen (E-16): Arten, Filter, Sprung zur Karte, "Alle gelesen". Fehler behoben: gelesen gilt am Konto auf allen Geräten. |
| M-120 | Heute | teilweise | `ansichten/uebersicht/Heute.svelte`, `meinTag` in `beispiel/abfragen.ts`, `/heute` | Über alle Boards, nur eigene Karten: Überfällig, Heute, Diese Woche, Ohne Datum, Termine, Serien, oben der eigene Timer (behebt "Timer aller Personen"); abhaken und Timer gehen. Fehlen: die Abschnitte Liegengeblieben und Blockiert; `meinTag` rechnet sie, Heute zeigt sie nicht, eine blockierte Karte mit späterer Fälligkeit fehlt so ganz. Vorlesen ohne Wirkung, Schnell-Erfassen siehe M-123. |
| M-121 | Fälligkeitskalender | abgebildet | `ansichten/planung/Kalender.svelte`, `ansichten/planung/KalenderKarte.svelte`, `/board/prod/kalender` | Monat und Woche je Board (E-09) mit Karten nach Fälligkeit, erledigte durchgestrichen, überfällige markiert; Klick öffnet. Eine Gesamtsicht über alle Boards gibt es nicht. |
| M-122 | Sprung aus anderen Ansichten | teilweise | `routen.ts`, `ansichten/uebersicht/HeuteZeile.svelte`, `ansichten/uebersicht/Hinweise.svelte`, `ansichten/planung/KalenderKarte.svelte`, `schale/Kopf.svelte` | Sprünge gehen über den Pfad der Karte, auch in andere Boards und auf archivierte Karten. Fehlt: die Suche im Kopf "Karten in allen Boards suchen" ist ein Feld ohne Wirkung. |
| M-123 | Schnell-Erfassen | teilweise | `ansichten/zeit/Nachtragen.svelte`, `ansichten/telefon/Zeiten.svelte`, `ansichten/telefon/Erfassen.svelte` | Zeit nachtragen mit Kartensuche, Tag, Dauer und Vorschau, ohne Ideen, nur mit Recht; am Telefon dazu schnelles Anlegen von Karten. Fehlt: die eine Freitextzeile, die Schlüssel, Dauer und Datum (gestern, Wochentag) erkennt. Fehler behoben: Schlüssel sind eindeutig. |
| M-124 | Tastenbelegung | teilweise | `board/Schnelleingabe.svelte`, `board/Karte.svelte`, `detail/Kartendetail.svelte`, `teile/Personenwahl.svelte` | Enter, Umschalt+Enter und Escape beim Anlegen, Enter öffnet die Karte, Enter bei Checkliste und neuer Spalte. Fehlen: Enter sendet keinen Kommentar und bucht keine Zeit; Escape im Spaltennamen bricht nicht ab. |
| M-125 | Escape im Detail | teilweise | `detail/Kartendetail.svelte`, `teile/DauerFeld.svelte`, `teile/DatumFeld.svelte` | Fehler behoben in Dauer- und Datumsfeldern: Escape verwirft. Fehlt: Escape schließt das Detail nicht; in Titel, Blockiert und eigenen Feldern verwirft Escape nicht, Verlassen speichert. |
| M-126 | Zähler und leere Zustände | abgebildet | `board/Spalte.svelte`, `board/BoardAnsicht.svelte`, `ansichten/uebersicht/` | Zähler an Spalte, eingeklappter Spalte, Erledigt (x von y), Papierkorb, Checkliste, Kommentaren, Hinweisen und Archiv; Leerzustände in Liste, Archiv, Papierkorb, Hinweisen, Beschreibung, Zeiten und Anhängen. Leerer Verlauf siehe M-64. |

## Was zu tun ist (teilweise und fehlt, nach Wichtigkeit für die Arbeit am Board)

### Hoch: tägliche Arbeit am Board, Daten richtig

1. **M-56** (teilweise): Beschreibung als echten Editor bauen, der den Text der Karte lädt, nach kurzer Pause und bei "Fertig" über `bearbeiten` speichert und "gespeichert" erst nach der Bestätigung zeigt.
2. **M-57** (teilweise): Notizen bearbeitbar machen (Vollbild-Editor mit Vorschau) und den Vollbild-Knopf anschließen.
3. **M-76** (teilweise): Das Mitziehen in `hinein` auf Mitglieder desselben Boards beschränken, damit keine Karte in die Spalte eines fremden Boards gerät.
4. **M-70** (teilweise): Nach einer abgelehnten Ablage die Spalten auf den Zustand zurücksetzen, damit die Karte sichtbar zurückspringt.
5. **M-01** (teilweise): Boards ohne Ordner in der Seitenleiste zeigen, etwa unter "Ohne Ordner".
6. **M-92** (teilweise): Filtertafel mit Priorität und Labels (ODER, Zahl am Chip) bauen, die Board, Liste, Kalender und Zeitachse filtert und das Ziehen sperrt.
7. **M-93** (teilweise): Personenfilter über die Zuständigen anschließen, mehrere kombinierbar, auch in Erledigt-Spalten.
8. **M-94** (teilweise): Sortierung Manuell, Fällig und Priorität für die offenen Spalten anschließen.
9. **M-44** (teilweise): Escape und Klick neben das Detail schließen lassen und den Fokus beim Öffnen ins Detail setzen.
10. **M-125** (teilweise): Escape in allen Feldern des Details verwerfen lassen wie im Dauerfeld und den zweiten Escape das Detail schließen lassen.
11. **M-14** (teilweise): Zahl und Grenzfarbe aus allen Karten der Spalte statt aus den Treffern rechnen und Bernstein am Limit sowie den Füllbalken ergänzen.
12. **M-12** (teilweise): Den Knopf "Spalte" im Board an `spalteAnlegen` anschließen, mit Eingabe am Ende des Streifens.
13. **M-16** (teilweise): Spalten im Board am Griff ziehbar machen, über denselben Anwendungsfall `spaltenOrdnen`.
14. **M-21** (teilweise): Ein Spaltenmenü im Board mit Umbenennen, Grenze, Erledigt-Spalte, Einklappen und Löschen anbieten, statt in die Einstellungen zu springen.
15. **M-28** (teilweise): Erledigt-Spalten nach Abschlussdatum ordnen, neueste zuerst, und das Ziehen innerhalb einer Erledigt-Spalte sperren.
16. **M-23** (teilweise): In `wechseln` bei Serienkarten den Termintag als Abschluss setzen.
17. **M-36** (fehlt): Anwendungsfall und Knopf Duplizieren bauen (Kopie mit " (Kopie)", Checkliste offen, ohne Zeiten, Kommentare und Anhänge, danach öffnen).
18. **M-42** (fehlt): Kette und Papierkorb beim Überfahren der Karte zeigen.
19. **M-72** (fehlt): Die Kette als eigene Zeigergeste mit einem Anwendungsfall `verknuepfen` bauen (nur Arbeit, nie Ideen).
20. **M-73** (teilweise): Das Suchfeld "Karte suchen und verknüpfen" mit Treffern, auch fertigen und aus anderen Boards, an denselben Anwendungsfall anschließen.
21. **M-74** (teilweise): Gruppe bilden, beitreten und zusammenführen umsetzen, ohne die Einstellung "Zeit teilen" zu verlieren.

### Mittel: vollständige Mechanik

22. **M-38** (teilweise): Der Zeitknopf zeigt bei geteilter Zeit die Gruppenzeit und färbt sich bei überschrittener Schätzung rot.
23. **M-75** (teilweise): Die Gruppenzeit auch auf der Karte im Board zeigen (gemeinsam mit M-38).
24. **M-77** (teilweise): Mitglieder in "Verknüpfte Aufgaben" als Verweis auf ihre Karte setzen, auch in anderen Boards.
25. **M-40** (teilweise): Prioritätspunkt, Gruppengröße an der Kette und Grün bei vollständiger Checkliste auf die Karte bringen.
26. **M-18** (teilweise): Eingeklappte Spalten als Ablagezone mit einem Farbstrich je Karte bauen.
27. **M-97** (fehlt): Den Ansichtszustand je Board und Person merken (Suche, Filter, eingeklappte Spalten, Zeitfenster, Ansicht).
28. **M-69** (teilweise): Ein Klick auf "Verschieben pausiert" setzt Suche, Filter und Sortierung zurück.
29. **M-55** (teilweise): "Ihre behalten" und "Meine übernehmen" bei einem Konflikt an Anwendungsfälle anschließen.
30. **M-60** (teilweise): Punkte der Checkliste umbenennbar machen (Enter speichert, Escape verwirft) und den Fortschrittsbalken ins Detail setzen.
31. **M-61** (teilweise): Das Kommentarfeld erst nach Erfolg leeren wie am Telefon, Markdown darstellen und Enter senden lassen.
32. **M-64** (teilweise): Verlaufszeilen für Zuständig, Fällig, Priorität, Blockade, Art, Kommentar, Zeitbuchungen, Anhänge und Mitziehen in den Anwendungsfällen schreiben und den Leerzustand zeigen.
33. **M-26** (teilweise): Erledigt-Spalte und Archiv seitenweise nach "Karten je Ladeschritt" laden, mit "Mehr laden", damit der Regler wirkt.
34. **M-15** (teilweise): `anlegen` warnt wie `hinein`, wenn die Spalte danach über der Grenze liegt.
35. **M-120** (teilweise): Die Abschnitte Liegengeblieben und Blockiert in Heute zeigen.
36. **M-88** (teilweise): Datum und Dauer eines Eintrags an der Karte änderbar machen, das Datum auch im Stundenzettel.
37. **M-63** (teilweise): Hochladen, Wahl aus der Kellerwolke, Öffnen und Entfernen mit Rückgängig anschließen.
38. **M-62** (fehlt): Dokumente an der Karte mit Editor und Vorschau bauen, abgelegt in der Kellerwolke (E-15).
39. **M-45** (teilweise): "Verweis kopieren" anschließen, mit Ersatzweg außerhalb eines sicheren Kontexts.
40. **M-122** (teilweise): Die Suche im Kopf über alle Boards mit Sprung zur Karte anschließen.
41. **M-95** (fehlt): Gespeicherte Sichten bauen, am Konto statt im Browser.
42. **M-37** (teilweise): Einen Auszug der Beschreibung auf der Karte zeigen.
43. **M-39** (teilweise): Bernstein für die Fälligkeit von heute bis in zwei Tagen setzen.
44. **M-124** (teilweise): Enter für Kommentar senden und Tag buchen belegen, Escape im Spaltennamen abbrechen lassen.
45. **M-11** (teilweise): Ladefehler des Boards und den Verlust der Mitgliedschaft bei offener Ansicht als eigenen Zustand vorführen.
46. **M-109** (teilweise): Ein eingetragener Urlaub nimmt unberührte Serienkarten der Person an diesen Tagen zurück.

### Niedrig: Komfort, Verbund und App-Sachen

47. **M-123** (teilweise): Eine Freitextzeile für Zeitbuchungen bauen, die Schlüssel, Dauer und Datum erkennt und erst eine Vorschau zeigt.
48. **M-10** (fehlt): Einen Export des ganzen Boards anbieten (Board, Spalten, Karten, Zeiten, Dokumente).
49. **M-08** (fehlt): Festlegen und zeigen, womit die App beim Start öffnet (zuletzt genutztes Board oder Heute).
50. **M-85** (teilweise): Den gemeinsamen Sekundentakt für laufende Zeiten in der App bauen.
51. **M-112** (teilweise): Transkript suchen, verknüpfen, lösen und an die Stelle springen anschließen.
52. **M-113** (teilweise): Marken anhängen und entfernen, Zusammenfassung je Marke mit Vorschlag bauen.
53. **M-114** (teilweise): Vorlesen an Karte, Beschreibung, Kommentar, Heute und Berichten anschließen, mit Stimme und Tempo.
54. **M-115** (fehlt): Labelvorschläge im Modul KI anbieten.
55. **M-96** (fehlt): Filtervorschläge im Modul KI anbieten.
56. **M-27** (fehlt): In der App überholte Antworten je Spalte verwerfen (Generationszähler).
57. **M-65** (fehlt): In der App das Neuladen einer neuen Fassung aufschieben, solange ungespeicherte Eingaben offen sind.

## Befunde neben der Wertung

- Zu M-116 (bewusst anders): Die Anwendungsfälle in `beispiel/anwendung/karten.svelte.ts` und `beispiel/anwendung/papierkorb.svelte.ts` prüfen keine Rechte, anders als `beispiel/anwendung/boards.svelte.ts` mit `mitRecht`. Ein Leser kann im Board ziehen und über die Schnelleingabe anlegen.
- `hatRecht` in `regeln/board.ts` beachtet abgeschaltete Module nicht, obwohl der Kommentar es zusagt; das Timer-Recht fängt es nur über `timerErlaubt` ab.
