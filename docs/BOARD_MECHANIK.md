# Board-Mechanik der Pinnwand (Verzeichnis für den Neubau)

Stand: Fassung 0.74.0 (Commit fa6430f), gelesen am 25.10.2026.

## 1. Wozu dieses Verzeichnis dient

Das Verzeichnis hält jede eingebaute Funktion des Boards und der Karte fest, damit der
Neubau (Boards als eigenständige Einheiten, Konten statt Kürzel, Rechte je Board) keine
davon verliert. Jede Mechanik hat eine Kennung (M-01 bis M-126) und beschreibt, was der
Nutzer tut (Aktion), was genau passiert (Wirkung mit Regeln, Grenzen und Vorgaben) und wo
es im Code steht (Fundstelle als Datei:Zeile, Stand 0.74.0).

Unter einer Mechanik stehen bei Bedarf Zusatzzeilen:

- **Bekannter Fehler**: steckt im Stand 0.74.0 und soll im Neubau an der Wurzel weg. Die
  Ursache steht in einem Satz dabei. "(Gegenprobe)" heißt: gegen eine Wegwerf-Datenbank
  nachgestellt und bestätigt. "(aus dem Code)" heißt: aus dem Code abgeleitet, nicht im
  Browser nachgestellt. Ohne Zusatz: im Code eindeutig ablesbar.
- **Behoben**: Befund aus dem Gesamt-Audit (Stand 0.67.1, docs/GESAMT_AUDIT.md), der
  inzwischen behoben ist. Die Regel dahinter gehört zur Mechanik und muss im Neubau von
  Anfang an gelten.

Alles andere ist Mechanik, die im Neubau wieder da sein soll.

### Wo die Dateien liegen

| Datei | Ordner |
|---|---|
| `Board.svelte`, `Column.svelte`, `Card.svelte`, `CardDrawer.svelte`, `Toolbar.svelte`, `ListenAnsicht.svelte`, `Archiv.svelte`, `Checkliste.svelte`, `MarkdownFeld.svelte`, `VerknuepfteAufgaben.svelte`, `Zeiterfassung.svelte`, `TranskriptVerweise.svelte`, `verknuepfen.svelte.ts` | `frontend/src/lib/module/kanban/` |
| `timer.svelte.ts`, `restore.ts`, `toaster.svelte.ts`, `Toast.svelte`, `LaufBar.svelte`, `kanbanKonfig.svelte.ts`, `zuletztKuerzel.svelte.ts`, `identitaet.ts`, `personSicht.svelte.ts`, `labels.ts`, `FarbWahl.svelte`, `DokumentVerwaltung.svelte`, `Glocke.svelte`, `SerienErinnerung.svelte`, `navigation.svelte.ts`, `routing.svelte.ts`, `SeitenLeiste.svelte`, `Hilfe.svelte`, `uiSpeicher.ts` | `frontend/src/lib/` |
| `api/basis.ts` | `frontend/src/lib/` |
| `App.svelte`, `main.ts` | `frontend/src/` |
| `Einstellungen.svelte` | `frontend/src/lib/module/einstellungen/` |
| `Heute.svelte` | `frontend/src/lib/module/heute/` |
| `Kalender.svelte` | `frontend/src/lib/module/auswertung/` |
| `persistence_karten.py`, `persistence_struktur.py`, `persistence_inhalte.py`, `persistence_basis.py`, `persistence_schema.py`, `models.py` | `backend/module/kanban_kern/` |
| `kanban_kern/api.py`, `auth/dienst.py`, `serien/dienst.py`, `serien/api.py` | `backend/module/` |
| `rechte.py`, `akteur.py` | `backend/module/auth/` |

## 2. Mechaniken nach Bereichen

### A. Board als Ganzes: Laden, Wechsel, Ansicht, Abgleich

- **M-01 Board öffnen.** Aktion: Board in der Seitenleiste anklicken. Wirkung: Spalten und alle
  Karten der offenen Spalten werden vollständig geladen (sortiert nach `reihenfolge`, dann Id),
  jede Karte mit ihren Gruppenangaben (Mitglieder, Gruppenzeit). Karten in Erledigt-Spalten
  kommen nicht mit, sie laden je Spalte gefenstert (M-22). Beim Boardwechsel schließt ein offenes
  Kartendetail, die Fertig-Fenster des alten Boards werden verworfen, der gemerkte Zustand des
  neuen Boards wird wiederhergestellt (M-97). Fundstelle: `Board.svelte:198-204`,
  `Board.svelte:216-229`, `persistence_struktur.py:266-286`, `kanban_kern/api.py:177-187`.

- **M-02 Board anlegen.** Aktion: "+ Board" unter der aktiven Mappe, Name eingeben, Enter
  (Escape bricht ab). Wirkung: Das Board bekommt ein Kürzel aus dem Titel (ein Wort: erste drei
  Zeichen groß; mehrere Wörter: Anfangsbuchstaben der ersten drei; nichts Verwertbares: "B"),
  Laufnummer 0 und die drei Vorgabespalten "Offen", "In Arbeit", "Erledigt" (die letzte als
  Erledigt-Spalte markiert, kein WIP-Limit). Eine neue Mappe bekommt sofort ein Board
  "Aufgaben", die anlegende Person wird Mitglied der Mappe. Eine Mappe ohne Board zeigt "Noch kein
  Board in ..." mit Knopf "Board anlegen" (legt "Aufgaben" an). Fundstelle:
  `SeitenLeiste.svelte:225-231`, `persistence_struktur.py:403-423`,
  `persistence_struktur.py:139-145`, `kanban_kern/api.py:102-112`, `App.svelte:180-185`,
  `App.svelte:364-372`.
  - Bekannter Fehler (Gegenprobe): Board-Kürzel sind nicht eindeutig und verlieren Umlaute
    ("Aufgaben" ergibt in jeder Mappe "AUF", "Übersicht" ergibt "BER"), dadurch gibt es denselben
    Kartenschlüssel in mehreren Boards; Ursache: das Kürzel wird nur mit `[A-Za-z0-9]` aus dem
    Titel geschnitten, ohne Eindeutigkeitsprüfung.

- **M-03 Board umbenennen und löschen.** Aktion: Stift-Symbol in der Seitenleiste macht den
  Namen zum Eingabefeld (Enter oder Verlassen speichert, Escape bricht ab); Papierkorb zeigt die
  Inline-Rückfrage "Board und alle Karten löschen?". Wirkung: Umbenennen ändert nur den Titel,
  das Kürzel bleibt (Kartenschlüssel bleiben stabil). Löschen entfernt Karten, Spalten,
  Zeiteinträge, Dokumente, Anhänge samt Dateien, Verlauf, Transkript-Marken, Zeitgruppen und die
  Serien des Boards, ohne Rückgängig; auch das letzte Board einer Mappe ist löschbar. Die
  Boardliste ist alphabetisch. Fundstelle: `SeitenLeiste.svelte:199-219`,
  `persistence_struktur.py:426-446`, `persistence_struktur.py:257-263`,
  `persistence_karten.py:913-963`.
  - Bekannter Fehler (aus dem Code): Escape im Umbenennen-Feld kann je nach Browser trotzdem
    speichern; Ursache: das Feld speichert beim Verlassen, und Escape entfernt das fokussierte
    Feld.
  - Bekannter Fehler: Der Server prüft den Boardtitel nicht auf leer (`kanban_kern/api.py:684-695`).

- **M-04 Kopfzeile.** Wirkung: zeigt Boardtitel, darunter Mappenname und Board-Kürzel.
  Fundstelle: `App.svelte:351-352`.

- **M-05 Ansichtsumschalter.** Aktion: Symbolknöpfe Spalten oder Liste links in der
  Werkzeugleiste. Wirkung: wechselt zwischen Spaltenansicht und Listenansicht (M-98), je Board
  gemerkt, Vorgabe Spalten. Fundstelle: `Toolbar.svelte:120-127`, `Board.svelte:578-588`.

- **M-06 Abgleich beim Fensterfokus.** Aktion: Browserfenster wieder in den Vordergrund holen.
  Wirkung: Das Board lädt neu (Änderungen aus anderen Browsern werden sichtbar), außer ein
  Kartendetail ist offen. Fundstelle: `Board.svelte:121-125`.
  - Bekannter Fehler: Es gibt keinen Live-Abgleich; zwei Browser sehen Änderungen des anderen
    erst beim nächsten Fokus oder Timer-Ereignis; Ursache: kein Änderungszähler und kein
    Ereigniskanal.

- **M-07 Neuladen nach Timer-Ereignis.** Wirkung: Jedes Starten, Pausieren, Stoppen und jede
  Zeitbuchung erhöht einen Zähler; das Board lädt daraufhin komplett neu (offene Spalten und alle
  Fertig-Fenster) und spiegelt den frischen Stand in ein offenes Detail. Fundstelle:
  `Board.svelte:256-262`, `Board.svelte:203`.

- **M-08 Mappe und Board beim Start.** Wirkung: Beim Start wird immer die erste Mappe
  (alphabetisch) aktiv, darin das zuletzt genutzte Board (`pw_ui.board`), sonst das erste.
  Fundstelle: `App.svelte:304`, `App.svelte:187-191`, `App.svelte:47-50`.
  - Bekannter Fehler (aus dem Code): Die zuletzt genutzte Mappe wird nicht gemerkt; lag das
    letzte Board in einer anderen Mappe, startet die App auf dem ersten Board der ersten Mappe;
    Ursache: `pw_ui` speichert nur das Board, die Mappenwahl beim Start ist fest `mappen[0]`.

- **M-09 Tiefe Verweise.** Aktion: Adresse `/board/<boardId>/<Kartenschlüssel>` aufrufen,
  Zurück/Vor im Browser. Wirkung: Die offene Karte wird in die Adresse gespiegelt und beim
  Schließen wieder entfernt; ein Verweis per Schlüssel öffnet die Karte, wenn sie in einer
  offenen Spalte oder im geladenen Fertig-Fenster liegt; ein Sprung per interner Id (Suche,
  Heute, Glocke, Kalender) lädt eine nicht geladene fertige Karte einzeln nach. Fundstelle:
  `routing.svelte.ts:22-37`, `Board.svelte:95-117`, `Board.svelte:128-131`,
  `kanban_kern/api.py:535-543`.
  - Bekannter Fehler (aus dem Code): Ein Verweis per Schlüssel auf eine fertige Karte außerhalb
    des Zeitfensters oder im Archiv öffnet nichts; Ursache: der Nachlade-Weg greift nur für die
    Id, nicht für den Schlüssel (`Board.svelte:108`).
  - Bekannter Fehler (aus dem Code): Ein Sprung zu einer Karte auf einem Board einer nicht
    aktiven Mappe bleibt wirkungslos, und der Wunsch hängt bis zum nächsten Mappenwechsel;
    Ursache: gesucht wird nur in der Boardliste der aktiven Mappe (`App.svelte:109-117`,
    `App.svelte:161-168`).

- **M-10 Export.** Aktion: Knopf "Export" neben "+ Spalte". Wirkung: lädt das Board als
  JSON-Datei `board-<Kürzel>.json` herunter (Board, Spalten, alle Karten einschließlich erledigter
  und archivierter, Zeiteinträge, Karten-Dokumente); Anhänge, Verlauf und Transkript-Marken
  fehlen. Download mit Anmeldung, Fehler als Hinweis "Export fehlgeschlagen". Fundstelle:
  `Board.svelte:645-648`, `persistence_inhalte.py:281-326`, `kanban_kern/api.py:242-250`.

- **M-11 Ladefehler.** Wirkung: Scheitert das Laden, erscheint nur der allgemeine Hinweis
  "Aktion fehlgeschlagen: ..." (globales Sicherheitsnetz), das Board bleibt auf dem alten Stand.
  Fundstelle: `main.ts:24-33`, `Board.svelte:198-204`.
  - Bekannter Fehler: Verliert jemand die Projekt-Mitgliedschaft bei offener Ansicht, friert
    das Board ohne klare Meldung ein; Ursache: `laden()` fängt eine Ablehnung (403) nicht ab.

### B. Spalten

- **M-12 Spalte anlegen.** Aktion: "+ Spalte" rechts neben der letzten Spalte, Titel eingeben,
  Enter oder "Hinzufügen" (Escape oder "Abbrechen" verwirft). Wirkung: leerer Titel wird
  ignoriert; die Spalte kommt ans Ende, ohne WIP-Limit, nicht erledigt; während der Eingabe sind
  "Archiv" und "Export" ausgeblendet. Fundstelle: `Board.svelte:508-515`,
  `Board.svelte:633-650`, `persistence_struktur.py:303-314`.
  - Bekannter Fehler: Der Server prüft weder leeren Titel noch negatives WIP-Limit
    (`kanban_kern/api.py:714-726`).

- **M-13 Spalte umbenennen und WIP-Limit setzen.** Aktion: Spaltenmenü (drei Punkte),
  "Umbenennen / WIP". Wirkung: Titelfeld (Enter speichert, Escape bricht ab) und Zahlenfeld
  "WIP-Limit (leer = keins)"; leer heißt kein Limit, sonst ganzzahlig und mindestens 1; ein leerer
  Titel wird nicht gespeichert. Fundstelle: `Column.svelte:84-96`, `Column.svelte:137-147`.

- **M-14 WIP-Anzeige.** Wirkung: Zähler im Spaltenkopf "n" oder "n/Limit", amber genau am Limit,
  rot darüber; dünner Füllbalken unter dem Kopf (Akzentfarbe, amber am Limit, rot darüber);
  Tooltip erklärt die Bedeutung. Fundstelle: `Column.svelte:78-82`, `Column.svelte:154`,
  `Column.svelte:182-184`.
  - Bekannter Fehler (aus dem Code): Bei aktivem Filter zählt der Kopf nur die gefilterten
    Karten, Zähler und WIP-Farbe stimmen dann nicht; Ursache: die Spalte zählt die angezeigte
    Liste statt aller Karten der Spalte.

- **M-15 WIP-Limit weich durchgesetzt.** Wirkung: Schiebt ein Spaltenwechsel, das Anlegen, ein
  Statuswechsel im Detail oder eine Sammel-Verschiebung die Zielspalte über ihr Limit, erscheint
  der Hinweis 'Spalte "X" ist über dem WIP-Limit (n/Limit).'; die Karte bleibt, es gibt bewusst
  keinen harten Block. Fundstelle: `Board.svelte:350-356`, `Board.svelte:409-417`,
  `Board.svelte:427`, `Board.svelte:459`, `Board.svelte:500`.

- **M-16 Spalten umsortieren.** Aktion: am linken Kopfbereich (Griff, Punkt, Titel, Zähler)
  oder am Griff einer eingeklappten Spalte ziehen; alternativ "Nach links" / "Nach rechts" im
  Menü (am Rand deaktiviert). Wirkung: gezogene Spalte wird angehoben und umrandet, Platzhalter
  gestrichelt; Ziehen speichert die komplette Reihenfolge, der Server prüft, dass die Liste genau
  die Spalten des Boards enthält; bei Fehler lädt das Board neu. Fundstelle:
  `Board.svelte:381-388`, `Board.svelte:590-595`, `Column.svelte:112`, `Column.svelte:150`,
  `Column.svelte:175-176`, `persistence_struktur.py:354-378`.

- **M-17 Spaltenfarben.** Wirkung: Spalten haben keine eigene Farbe; die Akzentfarbe ergibt sich
  aus der Position (acht feste Farben im Umlauf) und erscheint als Punkt im Kopf, im WIP-Balken und
  als Kartenstriche in eingeklappten Spalten; sie wechselt beim Umsortieren mit der Position.
  Fundstelle: `Board.svelte:82`, `Board.svelte:607`.

- **M-18 Einklappen.** Aktion: Doppelpfeil im Kopf oder Menü "Einklappen". Wirkung: Die Spalte
  wird 46 px schmal mit senkrechtem Titel, Kartenzahl und je Karte einem kurzen Farbstrich
  (Tooltip = Kartentitel); Klick, Enter oder Leertaste klappt aus; Karten lassen sich weiter
  hineinziehen; die Spalte bleibt umsortierbar; der Zustand wird je Board im Browser gemerkt.
  Fundstelle: `Column.svelte:107-134`, `Column.svelte:166`, `Column.svelte:174`,
  `Board.svelte:329-333`, `Board.svelte:212`.

- **M-19 Erledigt-Spalte markieren.** Aktion: Menü "Als Erledigt-Spalte" (nur bei nicht
  erledigten Spalten). Wirkung: Es gibt genau eine Erledigt-Spalte je Board; das Markieren nimmt
  der bisherigen Erledigt-Spalte die Markierung. Fundstelle: `Column.svelte:171-173`,
  `Board.svelte:524-527`, `persistence_struktur.py:327-335`.
  - Bekannter Fehler: Die Markierung lässt sich nicht aufheben, nur umsetzen, und beim Umsetzen
    erscheinen alle fertigen Karten der alten Spalte schlagartig ungefenstert als offene Karten;
    laufende Timer auf Karten der neu markierten Spalte laufen weiter; Ursache: die Rolle ist ein
    Spaltenflag ohne Übergangsregel.
  - Bekannter Fehler: Der Endpunkt prüft die Projekt-Mitgliedschaft nicht; Ursache:
    `spalte_als_erledigt` nimmt keinen Akteur entgegen (`kanban_kern/api.py:729-735`).

- **M-20 Spalte löschen.** Aktion: Menü "Löschen" (rot; deaktiviert, wenn es die einzige Spalte
  ist; der Server lehnt die letzte Spalte mit 409 ab). Wirkung: Offene Spalte wird sofort samt
  Karten und deren Restdaten gelöscht, danach Hinweis 'Spalte "X" gelöscht' mit Rückgängig (legt
  die Spalte neu an und die Karten aus dem Schnappschuss). Erledigt-Spalte: Dialog
  'Erledigt-Spalte "X" löschen?' mit Kartenzahl, "Abbrechen" oder "Endgültig löschen", kein
  Rückgängig. Server-Ablehnungen werden als Hinweis gemeldet. Fundstelle: `Column.svelte:178`,
  `Board.svelte:531-572`, `Board.svelte:679-694`, `persistence_struktur.py:381-398`,
  `kanban_kern/api.py:747-756`.
  - Bekannter Fehler (Gegenprobe): Der Dialog nennt eine zu kleine Zahl und behauptet
    "einschließlich archivierter"; Ursache: gezählt wird über das Fertig-Fenster, das archivierte
    Karten ausschließt (`Board.svelte:549`, `persistence_karten.py:239`).
  - Bekannter Fehler: Eine offene Spalte wird ohne Rückfrage gelöscht; das Rückgängig stellt sie
    am Ende statt an der alten Stelle wieder her, verliert erfasste Zeiten, Dokumente und Anhänge
    und sagt das nicht; Ursache: Wiederherstellen ist eine Neuanlage aus einem Schnappschuss statt
    weiches Löschen.
  - Bekannter Fehler: Zeigt eine Serie auf die gelöschte Spalte, legt sie weiter Karten in die
    nicht mehr existierende Spalte (M-106).
  - Behoben seit 0.68.3 (Audit A2): Die Erledigt-Spalte hatte nur ein Rückgängig, das die geladene
    Fensterseite zurückbrachte; seit 0.68.1 erzeugt eine Server-Ablehnung keinen falschen
    Erfolgshinweis mehr, dessen Rückgängig Karten verdoppelte.

- **M-21 Spaltenmenü.** Aktion: Knopf mit drei Punkten im Kopf. Wirkung: Menü mit Umbenennen /
  WIP, Als Erledigt-Spalte, Einklappen, Nach links, Nach rechts, Trennlinie, Löschen; jede
  Auswahl schließt das Menü. Fundstelle: `Column.svelte:167-180`.
  - Bekannter Fehler: Das Menü (wie die Filtertafel der Werkzeugleiste) schließt weder bei Klick
    daneben noch mit Escape; Ursache: kein Außenklick-Handler.

### C. Erledigt-Spalten: Fenster, Zeitfilter, Nachladen, Archiv

- **M-22 Gefenstertes Laden.** Wirkung: Jede Erledigt-Spalte lädt ihre Karten getrennt vom
  Board: eine Seite mit höchstens der eingestellten Seitengröße (Vorgabe 50), dazu Gesamtzahl und
  "hat mehr"; archivierte Karten sind ausgeschlossen. Das Frontend hält nie den ganzen Bestand.
  Fundstelle: `Board.svelte:156-185`, `persistence_karten.py:221-261`,
  `kanban_kern/api.py:194-211`.

- **M-23 Abschlussdatum.** Wirkung: Serienkarten (mit Serie und Fälligkeit) haben als Abschluss
  fest ihren Termintag, egal wann sie erledigt wurden; alle anderen das Datum ihres letzten
  Spaltenwechsels (`bewegt_am`, also das Ablegen in Erledigt). Erfasste Zeiten spielen keine
  Rolle. Fundstelle: `persistence_karten.py:152-155`, `persistence_karten.py:167-173`,
  `models.py:71-74`.

- **M-24 Zeitfilter im Spaltenkopf.** Aktion: Auswahlfeld im Kopf jeder Erledigt-Spalte.
  Wirkung: Heute (Vorgabe), Gestern, Woche (Montag bis Sonntag der laufenden Woche), Monat
  (Kalendermonat), Jahr (Kalenderjahr), Alle (ohne Archiv); ein Wechsel lädt die erste Seite
  serverseitig neu; die Wahl wird je Board und Spalte gemerkt. Fundstelle:
  `Column.svelte:156-165`, `Board.svelte:324-327`, `persistence_karten.py:176-193`.

- **M-25 Zeitfenster ausgesetzt bei Suche und Filter.** Wirkung: Sobald Suche, Label-,
  Prioritäts- oder Personenfilter oder eine Sortierung außer "Manuell" aktiv ist, lädt die
  Erledigt-Spalte ohne Zeitfenster, aber gefiltert: jedes Suchwort muss vorkommen (Volltext über
  Titel, Schlüssel, Beschreibung, Notizen, Zuständig, Priorität, Labels, Checkliste, Kommentare),
  Labels ODER-verknüpft, Priorität, Personen; Änderungen werden 250 ms entprellt. Fundstelle:
  `Board.svelte:147-152`, `Board.svelte:244-253`, `persistence_karten.py:200-218`,
  `persistence_karten.py:241-251`.
  - Bekannter Fehler (aus dem Code): Der Personenfilter lädt die Erledigt-Spalten nicht neu und
    wirkt dort erst beim nächsten Laden; Ursache: `filterZustaendig` fehlt in den Abhängigkeiten
    des Neulade-Effekts (`Board.svelte:245-249`).
  - Bekannter Fehler (aus dem Code): Die Serversuche durchsucht die rohen JSON-Texte von Labels,
    Checkliste und Kommentaren; Wörter wie "text", "erledigt", "autor" oder "true" treffen jede
    Karte mit Checkliste oder Kommentar; Ursache: `LIKE` über JSON statt über die Werte.

- **M-26 Nachladen, "Mehr laden", Zähler.** Aktion: in der Erledigt-Spalte nach unten scrollen
  oder "Mehr laden" klicken. Wirkung: ab 80 px vor dem Spaltenende lädt die nächste Seite (Offset =
  bisher geladene Anzahl); Knopf zeigt "Lädt ..." während des Ladens; unter der Liste steht "X von
  Y", sobald es fertige Karten gibt; Dubletten werden beim Anhängen herausgefiltert. Fundstelle:
  `Column.svelte:63-67`, `Column.svelte:205-214`, `Board.svelte:169-173`.
  - Bekannter Fehler: Ladefehler werden still verschluckt, der alte Stand bleibt ohne Meldung
    (`Board.svelte:174-178`).

- **M-27 Schutz gegen überholte Antworten.** Wirkung: Je Spalte läuft ein Generationszähler;
  eine spätere Anfrage (Filterwechsel, Boardwechsel) überholt eine laufende, deren Antwort wird
  verworfen; Nachladen startet nicht doppelt, ein Neuladen hat Vorrang. Fundstelle:
  `Board.svelte:154-168`.

- **M-28 Reihenfolge in Erledigt-Spalten.** Wirkung: neueste zuerst nach Abschlussdatum, bei
  gleichem Datum nach `reihenfolge`, dann Id; Ablegen in Erledigt hängt die Karte ans Ende
  (Position 1 000 000, danach Verdichtung). Fundstelle: `persistence_karten.py:256`,
  `Board.svelte:357-361`.
  - Bekannter Fehler: Ziehen innerhalb einer Erledigt-Spalte ist erlaubt, wirkt aber nicht; die
    Karte springt nach dem Neuladen an ihren Datumsplatz zurück (am selben Tag ans Ende);
    Ursache: die Oberfläche bietet manuelles Sortieren an, das die Datumssortierung überstimmt.

- **M-29 Archiv-Grenze.** Wirkung: Fertige Karten, deren Abschluss älter ist als die
  Archiv-Schwelle (Vorgabe 365 Tage), erscheinen nie im Board, nur im Archiv; das ist eine reine
  Ladegrenze ohne Datenumbau, eine größere Schwelle holt sie zurück; Auswertungen bleiben
  unberührt. Fundstelle: `persistence_karten.py:196-197`, `persistence_karten.py:239`,
  `persistence_karten.py:264-304`.

- **M-30 Archiv-Ansicht.** Aktion: Knopf "Archiv" (Kistensymbol) neben "+ Spalte". Wirkung:
  Dialog "Archiv - <Boardtitel>" mit Gesamtzahl; Liste aller archivierten Karten aller
  Erledigt-Spalten des Boards, neueste zuerst, je Eintrag Schlüssel, Titel, Abschlussdatum,
  Zuständig, Labels; Suche (250 ms entprellt, gleicher Volltext); Nachladen beim Scrollen und
  "Mehr laden"; Leerzustand mit Hinweis; Klick öffnet das Kartendetail und schließt das Archiv;
  Escape und Klick auf den Hintergrund schließen. Fundstelle: `Board.svelte:644`,
  `Board.svelte:654-661`, `Archiv.svelte:24-90`, `kanban_kern/api.py:214-220`.
  - Bekannter Fehler (aus dem Code): Eine Sucheingabe während eines laufenden Ladevorgangs wird
    verworfen, die Liste zeigt dann den alten Stand; Ursache: `if (laden) return` sperrt auch
    das Neuladen (`Archiv.svelte:25`).
  - Bekannter Fehler: Das Abschlussdatum erscheint im ISO-Format statt deutsch
    (`Archiv.svelte:76`); die Hilfe beschreibt den Zugang falsch (Uhr-Symbol im Spaltenkopf,
    `Hilfe.svelte:16`).

- **M-31 Rückholen.** Aktion: fertige Karte in eine offene Spalte ziehen oder im Detail einen
  offenen Status wählen. Wirkung: neues `bewegt_am` (Alterung beginnt neu), verknüpfte
  Mitglieder ziehen mit, Board und Fenster laden neu. Aus dem Archiv geht Rückholen nur über die
  Status-Auswahl im Detail. Fundstelle: `Board.svelte:418-431`, `persistence_karten.py:411-465`,
  `persistence_karten.py:476-484`.
  - Behoben seit 0.68.0 (Audit A1): Der Statuswechsel im Detail lief an `verschiebe_karte`
    vorbei (kein neues `bewegt_am`, Gruppe blieb zurück, Karte verschwand aus der Ansicht);
    heute delegiert `aktualisiere_karte` jeden Spaltenwechsel an `verschiebe_karte`.

### D. Karten anlegen und Kartenidentität

- **M-32 Karte anlegen.** Aktion: "+ Karte" unten in jeder Spalte (auch Erledigt), Titel tippen,
  Enter oder "Hinzufügen"; Umschalt+Enter macht einen Zeilenumbruch; Escape oder "Abbrechen"
  schließt und leert; Haken "Ideenticket (Notiz, ohne Zeiten)" legt eine Idee an. Wirkung: Das
  Eingabefeld bleibt nach dem Anlegen offen und fokussiert für die nächste Karte (Schnelleingabe);
  der Text wird erst nach Server-Erfolg geleert, der Ideen-Haken zurückgesetzt; danach lädt das
  Board neu und warnt bei WIP-Überschreitung. Fundstelle: `Column.svelte:97-104`,
  `Column.svelte:216-229`, `Board.svelte:497-501`.
  - Bekannter Fehler: Der Server prüft den Titel nicht (leer, nur Leerzeichen oder mit
    Zeilenumbruch möglich) (`kanban_kern/api.py:420-446`).
  - Behoben seit 0.68.1: Die Eingabe wurde vor dem Server-Erfolg geleert.

- **M-33 Vorbelegung neuer Karten.** Wirkung: Zuständig ist das Kürzel der aktiven Identität (bei
  Anmeldung die angemeldete Person, sonst die gewählte Personen-Sicht), sonst das zuletzt im
  Detail gesetzte Kürzel (`pw_zuletzt_kuerzel`), sonst niemand. Die Karte kommt ans Ende der
  Spalte; `erstellt_am` und `bewegt_am` sind jetzt (minutengenau); Typ Arbeit, falls nicht
  anders gewählt; Verlauf "Karte angelegt". Der Server prüft, dass Board und Spalte existieren und
  zusammenpassen. Fundstelle: `Board.svelte:88-91`, `zuletztKuerzel.svelte.ts:8-15`,
  `identitaet.ts:28-32`, `persistence_karten.py:384-408`, `kanban_kern/api.py:422-429`.
  - Bekannter Fehler (Fallstrick): Wer im Detail eine Karte einer anderen Person zuweist, macht
    diese Person zum Standard für alle eigenen neuen Karten, solange keine Identität gewählt ist;
    Ursache: "zuletzt gesetzt" wird bei jeder Zuweisung überschrieben
    (`CardDrawer.svelte:74-78`).

- **M-34 Kartenschlüssel und Laufnummer.** Wirkung: Schlüssel = Board-Kürzel, Bindestrich,
  laufende Nummer (z.B. R3-131); der Zähler läuft je Board ab 1, wird nie wiederverwendet (auch
  nicht nach dem Löschen) und auch von Serienkarten, Kopien und Rückgängig-Neuanlagen verbraucht;
  ohne Board-Kürzel heißt das Präfix "K". Der Schlüssel steht auf der Karte, im Detailkopf, in der
  Liste und in der Adresse; Schnell-Erfassen und Schnittstellen lösen Karten über ihn auf (ohne
  Beachtung von Groß/Klein). Fundstelle: `persistence_karten.py:391-401`,
  `persistence_karten.py:115-141`.
  - Bekannter Fehler: Schlüssel sind über Boards nicht eindeutig (M-02); die Auflösung ohne Board
    nimmt die erstbeste Karte mit diesem Schlüssel.

- **M-35 Arbeit oder Idee.** Aktion: Haken beim Anlegen oder Umschalter im Detailkopf
  ("Arbeit" mit Aktentasche, "Idee" mit Glühbirne). Wirkung: Eine Idee hat auf der Karte statt des
  Zeitknopfs den Chip "Idee" und keine Kette; im Detail steht ein Hinweis statt Zeiterfassung und
  verknüpfter Aufgaben; der Server weist Timer-Start, Zeitbuchung und Ticketzeit mit 409 ab; der
  Wechsel auf Idee stoppt einen laufenden Timer sauber (Sitzung wird gebucht); erfasste Zeiten
  bleiben gespeichert und erscheinen beim Zurückschalten wieder; Verlauf "In eine Idee
  umgewandelt" bzw. "In Arbeit umgewandelt". Fundstelle: `CardDrawer.svelte:52-53`,
  `CardDrawer.svelte:255-257`, `CardDrawer.svelte:326-331`, `Card.svelte:122`,
  `Card.svelte:164-171`, `persistence_karten.py:487-491`, `kanban_kern/api.py:562-563`,
  `kanban_kern/api.py:625-626`, `kanban_kern/api.py:645-646`.
  - Bekannter Fehler (aus dem Code): Mit der Kette lässt sich eine Idee in eine Zeitgruppe ziehen,
    obwohl die Suche im Detail Ideen ausschließt; Ursache: weder die Zeigergeste noch
    `verknuepfe_karten` prüfen den Typ (`Card.svelte:30-37`, `persistence_karten.py:309-338`).
  - Behoben seit 0.68.0 (Audit B): Ein laufender Timer überlebte den Wechsel zu Idee, Nebenwege
    buchten Zeit auf Ideen.

- **M-36 Duplizieren.** Aktion: Kopiersymbol im Detailkopf. Wirkung: Kopie in derselben Spalte
  (am Ende) mit Titel plus " (Kopie)", gleicher Beschreibung, Labels, Priorität, Cover, Start,
  Fällig, Zuständig, Typ, Notizen und Schätzung; Checkliste mit allen Punkten unerledigt; ohne
  Zeiten, Kommentare, Blockade, Transkript, Gruppe, Dokumente und Anhänge; danach öffnet die
  Kopie, Hinweis 'Karte als "..." dupliziert'. Fundstelle: `CardDrawer.svelte:261-265`,
  `Board.svelte:484-490`, `restore.ts:36-59`.

### E. Karte auf dem Board

- **M-37 Aufbau der Karte.** Wirkung: von oben nach unten Cover-Streifen (6 px) in Coverfarbe,
  Label-Chips (Farbe je Label, M-59), Titel vollständig, Beschreibung als Rohtext auf zwei Zeilen
  gekürzt (Markdown-Zeichen sichtbar), Fußzeile mit Markern. Fundstelle: `Card.svelte:148-162`,
  `Card.svelte:332-342`.

- **M-38 Zeitknopf.** Aktion: Play/Pause in der Fußzeile. Wirkung: startet oder pausiert, ohne
  das Detail zu öffnen; die Zeit erscheint erst, wenn sie läuft oder größer 0 ist (M:SS bzw.
  H:MM:SS); bei geteilter Gruppe zeigt er die Gruppenzeit; Akzentrahmen, solange er läuft; rot,
  wenn die Schätzung überschritten ist; Tooltip "Starten", "Starten (Zeit geteilt)" oder
  "Pausieren". Fundstelle: `Card.svelte:52-64`, `Card.svelte:167-170`.

- **M-39 Fälligkeit.** Wirkung: Uhr-Badge mit "TT.MM."; rot bei überfällig, amber von heute bis
  in zwei Tagen, sonst neutral. Fundstelle: `Card.svelte:66-80`, `Card.svelte:176-178`.
  - Bekannter Fehler: Auch erledigte Karten zeigen rote Überfällig-Badges; Ursache: die Karte
    kennt die Rolle ihrer Spalte nicht.

- **M-40 Weitere Marker.** Wirkung: Ketten-Pille mit Gruppengröße (gefüllt bei geteilter Zeit,
  Tooltip mit Zahl der weiteren Karten), Schlüssel in Festbreitenschrift, Checklisten-Zähler
  "erledigt/gesamt" (grün bei vollständig), Kommentarzahl, rote Hand bei Blockade (Tooltip mit
  Grund), rechts Prioritätspunkt (hoch, mittel, niedrig farbig) und rundes Kürzel-Avatar des
  Zuständigen. Fundstelle: `Card.svelte:172-198`.

- **M-41 Alterung.** Wirkung: Sanduhr mit den Tagen seit `bewegt_am` (letzter Spaltenwechsel
  oder Anlage); amber ab der Einstellung "amber" (Vorgabe 4), rot ab "rot" (Vorgabe 8), 0 = aus;
  Tooltip "Liegt n Tage in dieser Spalte". Fundstelle: `Card.svelte:82-95`,
  `Card.svelte:188-190`, `kanbanKonfig.svelte.ts:6-16`.
  - Bekannter Fehler: Die Alterung erscheint auch in Erledigt-Spalten (etwa bei Zeitfilter Woche
    oder Alle), wo sie nichts bedeutet; Ursache wie M-39.
  - Bekannter Fehler: amber = 0 schaltet auch rot ab, obwohl beide Werte einzeln "0 = aus"
    anbieten (`Card.svelte:92`).
  - Behoben seit 0.72.0 (Audit D): Die Schwellen waren fest 4 und 8 Tage.

- **M-42 Aktionen beim Überfahren.** Aktion: Maus über die Karte oder Fokus in der Karte.
  Wirkung: oben rechts erscheinen die Kette zum Verknüpfen (nur bei Arbeit, M-72) und der
  Papierkorb zum sofortigen Löschen (M-102). Fundstelle: `Card.svelte:121-147`,
  `Card.svelte:243-246`.

- **M-43 Karte öffnen.** Aktion: Klick auf die Karte oder Enter auf der fokussierten Karte (Tab
  erreicht jede Karte). Wirkung: öffnet das Detail; ein Klick bis 160 ms nach einem Zug wird
  ignoriert, damit das Ablegen nicht öffnet. Doppelklick ist nicht belegt. Fundstelle:
  `Card.svelte:105-120`, `Board.svelte:391-394`.

### F. Kartendetail: Rahmen und Felder

- **M-44 Detail öffnen und schließen.** Wirkung: Seitenpanel rechts (540 px, höchstens 94 % der
  Breite) über abgedunkeltem Hintergrund; der Fokus springt beim Öffnen ins Panel; Schließen per X,
  Klick auf den Hintergrund oder Escape (steckt der Fokus in einem Eingabefeld, verlässt der erste
  Escape nur das Feld, M-125); das Panel zeigt nach jedem Neuladen den frischen Stand.
  Fundstelle: `CardDrawer.svelte:231-250`, `Board.svelte:663-677`.

- **M-45 Kopf des Details.** Wirkung: Schlüssel-Chip, Name der aktuellen Spalte, Umschalter
  Arbeit/Idee, Umschalter Frei/Blockiert, Duplizieren, Schließen. Fundstelle:
  `CardDrawer.svelte:251-268`.

- **M-46 Titel.** Aktion: im großen Titelfeld tippen. Wirkung: speichert beim Verlassen oder mit
  Enter (Änderungsereignis); Titeländerungen landen bewusst nicht im Verlauf. Fundstelle:
  `CardDrawer.svelte:271`, `persistence_basis.py:64-69`.
  - Bekannter Fehler: Ein leerer Titel wird gespeichert; Ursache: keine Prüfung in
    `KarteUpdate` oder `aktualisiere_karte`.

- **M-47 Blockiert mit Grund.** Aktion: Knopf "Frei" im Kopf. Wirkung: setzt die Blockade mit dem
  Platzhaltergrund "Grund noch offen" (Knopf wird rot "Blockiert"); darunter erscheint die rote
  Zeile "Warum blockiert?", eine Änderung speichert beim Verlassen; Leeren der Zeile oder Klick
  auf "Blockiert" hebt die Blockade auf; Verlauf "Blockiert: ...", "Blockade-Grund geändert: ...",
  "Blockade aufgehoben"; blockierte offene Karten erscheinen in Heute unter "Blockiert".
  Fundstelle: `CardDrawer.svelte:54-57`, `CardDrawer.svelte:258-260`,
  `CardDrawer.svelte:272-278`, `persistence_basis.py:82-90`, `persistence_inhalte.py:455-456`.

- **M-48 Status-Auswahl.** Aktion: Auswahlliste "Status" mit allen Spalten des Boards. Wirkung:
  ein echtes Verschieben (ans Ende der Zielspalte, neues `bewegt_am`, Gruppen-Mitzug, Timer-Stopp
  bei Erledigt, Verdichtung), danach laden Board und Fenster neu, WIP-Warnung. Fundstelle:
  `CardDrawer.svelte:291-295`, `Board.svelte:418-431`, `persistence_karten.py:476-484`.

- **M-49 Priorität.** Aktion: Auswahl keine, Hoch, Mittel, Niedrig. Wirkung: speichert sofort,
  Verlauf "Priorität: ..." bzw. "Priorität entfernt". Fundstelle: `CardDrawer.svelte:296-303`,
  `persistence_basis.py:78-81`.

- **M-50 Start.** Aktion: Datumsfeld. Wirkung: speichert sofort, leeren entfernt; ist es leer,
  setzt der erste Timer-Start es auf den Starttag, danach wird es nie überschrieben. Fundstelle:
  `CardDrawer.svelte:304-306`, `persistence_karten.py:718-723`.
  - Bekannter Fehler: Start, Fällig und die Tagesliste nutzen native Datumsfelder, deren Format von
    der Browsersprache abhängt; Ursache: kein eigenes deutsches Datumsfeld.

- **M-51 Fällig.** Aktion: Datumsfeld. Wirkung: speichert sofort, leeren entfernt; Verlauf
  "Fällig am ..." bzw. "Fälligkeit entfernt"; speist Badge, Heute, Fälligkeitskalender und
  Sortierung. Fundstelle: `CardDrawer.svelte:307-309`, `persistence_basis.py:74-77`.

- **M-52 Zuständig.** Aktion: Auswahl "(niemand)" plus alle Personen mit Kürzel ("Kürzel -
  Name"). Wirkung: speichert sofort; ein unbekanntes Alt-Kürzel der Karte erscheint als zusätzliche
  Option; die Wahl wird als Standard für neue Karten gemerkt (M-33); Verlauf "Zuständig: ..." bzw.
  "Zuständigkeit entfernt"; die Zuständigkeit bestimmt Glocke, Timer-Recht und die
  Ersatz-Person für Zeiteinträge. Fundstelle: `CardDrawer.svelte:59-78`,
  `CardDrawer.svelte:310-315`.
  - Bekannter Fehler: Deaktivierte Personen werden angeboten; Ursache: gefiltert wird nur auf
    vorhandenes Kürzel (`CardDrawer.svelte:63`).
  - Bekannter Fehler: Ein Wechsel bei laufendem Timer schreibt die ganze laufende Sitzung der neuen
    Person gut; Ursache: die Sitzung erbt das Kürzel erst beim Stoppen
    (`persistence_karten.py:654`, `persistence_karten.py:698`).

- **M-53 Cover.** Aktion: Farbpalette "Keine Farbe" plus 14 feste Farben, keine Freiwahl.
  Wirkung: Klick speichert sofort, die Karte zeigt den Streifen. Fundstelle:
  `CardDrawer.svelte:316-318`, `FarbWahl.svelte:17-21`.

- **M-54 Zeitkennzahlen.** Wirkung: Kasten mit "Im Status: n Tage" (seit `bewegt_am`, rot ab 8
  Tagen), "Durchlaufzeit: n Tage" (seit Anlage), "Erstellt: Datum". Fundstelle:
  `CardDrawer.svelte:217-228`, `CardDrawer.svelte:320-324`.
  - Bekannter Fehler: Die Warnschwelle "Im Status" ist fest 8 Tage und folgt nicht der
    Alterungs-Einstellung (`CardDrawer.svelte:321`).

- **M-55 Speichermodell des Details.** Wirkung: Jedes Feld speichert einzeln: Auswahl, Datum und
  Farbe sofort, Titel und kurze Textfelder beim Verlassen, Beschreibung und Notizen per
  Autospeichern; es gibt keinen Bearbeiten-Modus und keinen Speichern-Knopf
  (bewusst so). Die Server-Antwort ersetzt die Karte im Board und im Detail, egal ob sie in einer
  offenen Spalte oder einem Fertig-Fenster liegt. Fundstelle: `Board.svelte:395-407`,
  `Board.svelte:418-431`.
  - Bekannter Fehler: Labels werden als ganze Liste geschrieben, gleichzeitige Änderungen in zwei
    Browsern überschreiben sich (`CardDrawer.svelte:184`, `CardDrawer.svelte:201`).

### G. Inhalte der Karte

- **M-56 Beschreibung.** Aktion: Klick auf den gerenderten Text. Wirkung: Markdown wird sauber
  dargestellt (Überschriften, Listen, Code, Tabellen, Formeln, Diagramme); der Klick öffnet einen
  einspaltigen Editor an Ort und Stelle mit Autofokus; Autospeichern 600 ms nach der letzten
  Eingabe, "gespeichert" erscheint erst nach Server-Bestätigung, bei Fehler rot "nicht
  gespeichert" und der Text bleibt im Editor; "Vollbild" vergrößert, "Fertig" speichert sofort und
  schließt; leerer Text wird zu "keine Beschreibung"; bei vorhandenem Text gibt es "Vorlesen" /
  "Stopp"; Leerzustand "Keine Beschreibung. Klicken zum Bearbeiten." Fundstelle:
  `CardDrawer.svelte:280-284`, `MarkdownFeld.svelte:58-122`.
  - Bekannter Fehler (aus dem Code): Wer innerhalb von 600 ms nach der letzten Eingabe das Detail
    schließt oder zu einer anderen Karte wechselt, verliert diese Eingaben still; Ursache: der
    verzögerte Speicheraufruf läuft erst danach, und `karteAendern` verwirft ihn ohne offene Karte
    (`MarkdownFeld.svelte:58-68`, `Board.svelte:419`).
  - Behoben seit 0.68.1 (Audit A17): "gespeichert" erschien zeitgesteuert auch bei Fehlschlag.

- **M-57 Notizen.** Aktion: Klick auf die Notizen oder "Vollbild" (nur bei vorhandenem Text).
  Wirkung: Notizen sind gerendert und nur lesbar; bearbeitet wird direkt im Vollbild-Editor mit
  Live-Vorschau daneben; Autospeichern wie M-56, "Fertig" speichert und schließt; Leerzustand
  "Keine Notizen. Klicken zum Bearbeiten." Fundstelle: `CardDrawer.svelte:286-289`,
  `MarkdownFeld.svelte:81-84`, `MarkdownFeld.svelte:100-101`.
  - Bekannter Fehler: derselbe 600-ms-Verlust wie M-56; die Board-Suche in offenen Spalten findet
    Notizen nicht, die Serversuche in Erledigt-Spalten schon; Ursache: `volltext()` ohne
    `notizen` (`Board.svelte:271-285` gegenüber `persistence_karten.py:159-164`).

- **M-58 Labels an der Karte.** Aktion: Eingabe "+ Label", Enter oder Feld verlassen; X am Chip
  entfernt. Wirkung: Labels sind freie Texte an der Karte; getrimmt; eine exakte Dublette wird
  verworfen; Entfernen sofort; Vorschläge per Vorschlagsdienst (M-115). Filter und Vorschläge
  nutzen die tatsächlich an Karten vorhandenen Labels. Fundstelle: `CardDrawer.svelte:178-202`,
  `CardDrawer.svelte:333-340`.
  - Bekannter Fehler: Dubletten in anderer Schreibweise ("Bug" und "bug") sind möglich, obwohl
    Farbe und Umbenennen Groß/Klein ignorieren; Ursache: Prüfung mit `includes`.
  - Bekannter Fehler: Escape in der Label-Eingabe fügt das angefangene Label hinzu (M-125).

- **M-59 Labelfarben.** Wirkung: Farbe je Label-Name aus der Label-Verwaltung, sonst feste
  Zuordnung bekannter Namen (blocker, bug, risiko rot; software blau; design violett; doku amber;
  test, abnahme, infra grün; mechanik türkis; meilenstein indigo), sonst stabile Hash-Farbe; der
  Textkontrast wird für hell und dunkel berechnet. Umbenennen in der Verwaltung zieht den Namen
  auf allen Karten mit (Dubletten werden zusammengeführt), Löschen der Definition lässt die Texte an
  den Karten stehen. Fundstelle: `labels.ts`, `persistence_inhalte.py:149-208`.

- **M-60 Checkliste.** Aktion: Kästchen anklicken, Text anklicken zum Umbenennen (Enter oder
  Verlassen speichert, Escape bricht ab), X entfernt, "+ Punkt hinzufügen" mit Enter. Wirkung:
  Überschrift mit "n von m" und grünem Fortschrittsbalken; erledigte Punkte durchgestrichen; jede
  Aktion ist eine eigene atomare Server-Operation (Anhängen, Ändern, Entfernen je Index); ein
  veralteter Index meldet 409 und lädt frisch nach; leerer Text wird abgewiesen; Entfernen ohne
  Rückfrage; die Karte zeigt "n/m". Fundstelle: `Checkliste.svelte:17-56`,
  `CardDrawer.svelte:85-91`, `CardDrawer.svelte:342-347`, `persistence_karten.py:515-565`,
  `kanban_kern/api.py:468-513`.
  - Bekannter Fehler (aus dem Code): Escape im Umbenennen-Feld kann den getippten Text übernehmen
    statt ihn zu verwerfen; Ursache: das Feld speichert beim Verlassen, und Escape führt zum
    Verlassen.
  - Behoben seit 0.73.5 (Audit B): Der Ganz-Listen-Ersatz überschrieb gleichzeitige Änderungen.

- **M-61 Kommentare.** Aktion: Feld "Kommentar schreiben ...", Enter oder "Senden". Wirkung:
  Abschnitt "Aktivität" listet alle Kommentare mit Initialen-Avatar, Autor, Zeit (minutengenau),
  Lautsprecher zum Vorlesen und Text als Markdown; Anhängen ist atomar; Verlauf "Kommentar
  hinterlassen"; Kommentare lassen sich weder bearbeiten noch löschen; das Feld ist einzeilig.
  Autor ist das Kürzel der aktiven Identität, sonst das zuletzt genutzte Kürzel, sonst der
  Zuständige, sonst "Ich". Fundstelle: `CardDrawer.svelte:203-208`,
  `CardDrawer.svelte:397-404`, `Board.svelte:432-438`, `persistence_karten.py:568-579`.
  - Bekannter Fehler: Das Feld wird sofort geleert, auch wenn das Senden scheitert; Ursache: der
    Aufruf wird nicht abgewartet (`CardDrawer.svelte:203-208`).
  - Bekannter Fehler: Der Autor kommt vom Browser und wird vom Server ungeprüft übernommen
    (`kanban_kern/api.py:516-523`); über die Ersatzregel kann eine fremde Person als Autor
    erscheinen.
  - Bekannter Fehler (aus dem Code): Zwei Kommentare derselben Person in derselben Minute haben
    denselben Listenschlüssel (`CardDrawer.svelte:398`), das kann die Darstellung stören.
  - Behoben seit 0.69.1 (Audit A18): Autor war immer der Zuständige der Karte.

- **M-62 Dokumente an der Karte.** Aktion: Abschnitt "Dokumente": neues Dokument mit Titel,
  Dokument öffnen, "Liste" zurück. Wirkung: Liste nach Titel mit Änderungszeit; Editor mit Eingabe
  links und Live-Vorschau rechts, Vollbild, Autospeichern nach 600 ms mit "gespeichert" bzw.
  "nicht gespeichert - Text bleibt im Editor"; Titel änderbar (Enter oder Verlassen); Löschen mit
  Inline-Rückfrage; Dokumente gehen beim Löschen der Karte mit. Fundstelle:
  `CardDrawer.svelte:349-350`, `DokumentVerwaltung.svelte:11-120`.
  - Bekannter Fehler (aus dem Code): Wer innerhalb von 600 ms nach einer Eingabe über "Liste" ein
    anderes Dokument öffnet, überschreibt das alte Dokument mit dem Inhalt des neuen; Ursache: die
    Id wird beim Tippen festgehalten, der Inhalt aber erst beim Speichern gelesen
    (`DokumentVerwaltung.svelte:53-70`).
  - Bekannter Fehler: Lesen, Ändern und Löschen eines Dokuments per Id prüfen die
    Projekt-Mitgliedschaft nicht (`kanban_kern/api.py:368-395`).

- **M-63 Anhänge.** Aktion: "Datei anhängen" (auch mehrere), Klick auf eine Datei, X. Wirkung:
  Grenze 25 MB je Datei, leere Datei abgelehnt, während des Hochladens "Lädt hoch ..."; Liste mit
  Name und Größe (B, KB, MB); Klick lädt mit Originalnamen herunter (Umlaute sicher kodiert); X
  löscht sofort; Dateien liegen je Karte neben der Datenbank und sind im Backup enthalten; Verlauf
  "Anhang hinzugefügt" bzw. "Anhang entfernt"; das Löschen der Karte räumt die Dateien ab.
  Fundstelle: `CardDrawer.svelte:93-127`, `CardDrawer.svelte:373-395`,
  `persistence_inhalte.py:216-278`, `kanban_kern/api.py:295-343`.
  - Bekannter Fehler: Ein Anhang wird ohne Rückfrage und ohne Rückgängig gelöscht, die Datei ist
    sofort weg (`CardDrawer.svelte:119-122`).
  - Bekannter Fehler: Ein Ladefehler der Liste sieht aus wie "keine Anhänge"
    (`CardDrawer.svelte:103`).

- **M-64 Verlauf.** Aktion: "Verlauf" aufklappen. Wirkung: lädt erst beim Aufklappen (bis 200
  Einträge, neueste zuerst): Datum und Uhrzeit, Kürzel der handelnden Person, Text; protokolliert
  werden Anlage, Verschieben (auch Mitgezogene), Zuständig, Fällig, Priorität, Blockade, Typ,
  Kommentar, Zeitbuchungen (manuell, Timer-Stopp, Ticketzeit) und Anhänge, bewusst nicht Titel und
  Beschreibung; jede Zeile entsteht in derselben Transaktion wie die Änderung; Leerzustand "Noch
  kein Verlauf."; ein Kartenwechsel klappt zu. Fundstelle: `CardDrawer.svelte:129-150`,
  `CardDrawer.svelte:406-423`, `persistence_basis.py:53-94`, `persistence_inhalte.py:380-388`.
  - Bekannter Fehler: Der Timer-Stopp wird dem Zuständigen statt der handelnden Person
    zugeschrieben (`persistence_karten.py:680-681`); Datumsangaben im Verlaufstext stehen im ISO-Format.

- **M-65 Neue Fassung wartet.** Wirkung: Eine neue Programmfassung lädt die Seite nicht neu,
  solange im Detail ein Editor ungespeicherten Text hat, ein Kommentar oder Label angefangen ist,
  ein Dokument ungespeichert ist oder ein Upload läuft. Fundstelle: `CardDrawer.svelte:99`,
  `MarkdownFeld.svelte:44`, `DokumentVerwaltung.svelte:24`.

### H. Ziehen und Ablegen

- **M-66 Umsortieren in einer Spalte.** Aktion: Karte greifen (überall außer an den Knöpfen) und
  an eine andere Stelle derselben Spalte ziehen. Wirkung: Platzhalter als gestrichelte
  abgerundete Fläche; die Oberfläche übernimmt die Reihenfolge sofort, der Server setzt die Karte
  auf den Zielindex und verdichtet; bei reinem Umsortieren in offenen Spalten wird nicht neu
  geladen; die Gruppe bleibt unberührt. Fundstelle: `Board.svelte:336-376`,
  `Column.svelte:187-203`, `persistence_karten.py:411-422`.
  - Bekannter Fehler (Gegenprobe): Ein Zug nach unten innerhalb derselben Spalte landet
    serverseitig einen Platz zu hoch (A B C D E, B an die vierte Stelle gezogen, ergibt nach dem
    nächsten Laden A C B D E); Ursache: der Server rechnet den Zielindex, als stünde die Karte noch
    an ihrer alten Stelle.

- **M-67 Wechsel zwischen Spalten.** Aktion: Karte in eine andere Spalte ziehen, auch in eine
  eingeklappte. Wirkung: neue Position, `bewegt_am` = jetzt (Alterung beginnt neu), Verlauf
  'Verschoben nach "X"', Gruppe zieht mit (M-76), Quell- und Zielspalte werden verdichtet,
  WIP-Warnung, danach laden Board und Fenster neu. Fundstelle: `Board.svelte:340-376`,
  `persistence_karten.py:423-465`.

- **M-68 Ablegen in Erledigt.** Wirkung: Die Karte kommt ans Ende (wird nach Datum einsortiert);
  alle laufenden Timer auf Karten der Zielspalte werden gestoppt und gebucht (auch die der
  mitgezogenen Mitglieder); Abschluss = heute; Neuladen, damit die Karte im Zeitfilter "Heute"
  sofort sichtbar ist. Fundstelle: `Board.svelte:357-368`, `persistence_karten.py:452-462`.
  - Behoben seit 0.68.0: Erledigen stoppte keinen laufenden Timer.

- **M-69 Ziehen gesperrt bei Filter.** Wirkung: Bei aktiver Suche, Label-, Prioritäts- oder
  Personenfilter oder Sortierung außer "Manuell" ist Ziehen in allen Spalten gesperrt (weder
  aufnehmen noch ablegen); die Werkzeugleiste zeigt "Verschieben pausiert" mit Schloss, ein Klick
  darauf setzt Suche, Filter, Personen und Sortierung zurück. Fundstelle: `Board.svelte:85`,
  `Board.svelte:604`, `Toolbar.svelte:85-91`, `Toolbar.svelte:187-191`.

- **M-70 Rücksprung mit Grund.** Wirkung: Scheitert das Verschieben, erscheint "Verschieben
  fehlgeschlagen: <Grund>" und das Board lädt neu, die Karte springt zurück. Fundstelle:
  `Board.svelte:369-373`.
  - Bekannter Fehler: Der Server prüft nicht, ob die Zielspalte zum Board der Karte gehört (Move
    und Status-Änderung); per Schnittstelle kann eine Karte in eine fremde Spalte geraten und
    verschwindet aus allen Boards (`persistence_karten.py:411-422`,
    `kanban_kern/api.py:459-465`).

- **M-71 Optik beim Ziehen.** Wirkung: gezogene Karte angehoben mit Schatten, ohne eckigen
  Fokusrahmen; gezogene Spalte angehoben und umrandet; eingeklappte Spalten zeigen einen kleinen
  gestrichelten Platzhalter. Fundstelle: `Board.svelte:732-757`, `Column.svelte:518-550`.

### I. Verknüpfte Aufgaben (Zeitgruppe)

- **M-72 Kette ziehen.** Aktion: Kettensymbol einer Arbeitskarte greifen und auf eine andere
  Karte ziehen. Wirkung: eigene Zeigergeste, getrennt vom Kartenziehen; die Quellkarte wird
  halbtransparent gestrichelt, eine schwebende Marke folgt dem Zeiger ("Auf eine Karte ziehen ..."
  bzw. "Hier koppeln"), die Zielkarte wird hervorgehoben; Loslassen über einer anderen Karte
  verknüpft beide, lädt neu und zeigt "Aufgaben verknüpft - Zeit wird geteilt"; Loslassen daneben
  bricht ab; geht über Spaltengrenzen, aber nur auf sichtbare Karten (nicht in eingeklappte
  Spalten). Fundstelle: `Card.svelte:17-48`, `Card.svelte:122-138`, `Card.svelte:202-208`,
  `verknuepfen.svelte.ts:11-28`, `Board.svelte:503-507`.

- **M-73 Verknüpfen im Detail.** Aktion: Feld "Aufgabe suchen und verknüpfen ..." im Abschnitt
  "Verknüpfte Aufgaben", Treffer anklicken. Wirkung: sucht in den offenen Karten dieses Boards
  nach Titel oder Schlüssel, ohne Ideen und ohne bisherige Mitglieder, höchstens 8 Treffer; ein
  Kartenwechsel leert das Feld. Fundstelle: `VerknuepfteAufgaben.svelte:22-46`,
  `VerknuepfteAufgaben.svelte:72-79`.
  - Bekannter Fehler: Fertige Karten und Karten anderer Boards sind über die Suche nicht
    erreichbar, obwohl Gruppen boardübergreifend sein dürfen.

- **M-74 Gruppenregeln.** Wirkung: Haben beide Karten keine Gruppe, entsteht eine neue ("Zeit
  teilen" an); hat eine eine Gruppe, tritt die andere bei; haben beide verschiedene Gruppen, wird
  die zweite in die erste überführt. "Diese Karte loslösen" nimmt die Karte heraus; bleiben weniger
  als zwei Mitglieder, löst sich die Gruppe auf; dasselbe gilt beim Löschen von Karten.
  Fundstelle: `persistence_karten.py:309-355`, `persistence_karten.py:613-619`,
  `VerknuepfteAufgaben.svelte:47-50`, `VerknuepfteAufgaben.svelte:70`.
  - Bekannter Fehler: Beim Zusammenführen geht die Einstellung "Zeit teilen" der zweiten Gruppe
    still verloren; das Loslösen prüft die Projekt-Mitgliedschaft nicht
    (`kanban_kern/api.py:580-585`).

- **M-75 Zeit teilen.** Aktion: Schalter "Zeit teilen (zählt einmal über die Gruppe)". Wirkung:
  an: jede Karte der Gruppe zeigt die Summe der erfassten Zeit aller Mitglieder (über alle Boards)
  im Zeitknopf und im Detail "Geteilt über n Aufgaben: H:MM:SS - zählt einmal"; aus: jede Karte
  zeigt nur die eigene Zeit. Reine Anzeige: jeder Zeiteintrag gehört genau einer Karte,
  Auswertungen zählen jede Sekunde einmal. Fundstelle: `VerknuepfteAufgaben.svelte:51-55`,
  `VerknuepfteAufgaben.svelte:69`, `persistence_karten.py:66-103`,
  `Zeiterfassung.svelte:125-127`.
  - Bekannter Fehler (aus dem Code): Die laufende Zeit eines anderen Mitglieds fehlt in der
    angezeigten Gruppensumme bis zu dessen Stopp (`Card.svelte:53-58`).

- **M-76 Mitziehen beim Spaltenwechsel.** Wirkung: Wechselt eine verknüpfte Karte die Spalte
  (Ziehen, Status, Sammelaktion, Schnittstelle), ziehen alle Mitglieder desselben Boards, die nicht
  schon in der Zielspalte stehen, ans Ende der Zielspalte mit; ihr `bewegt_am` wird gesetzt, Verlauf
  'Mit verknüpfter Karte verschoben nach "X"'; bei Erledigt stoppen auch ihre Timer; reines
  Umsortieren lässt die Gruppe stehen; Mitglieder auf anderen Boards bleiben stehen. Fundstelle:
  `persistence_karten.py:433-451`.

- **M-77 Mitglieder öffnen.** Aktion: Mitglied in der Liste "Verknüpfte Aufgaben" anklicken.
  Wirkung: Liste der anderen Mitglieder mit Schlüssel und Titel; Klick öffnet das Mitglied im
  Detail. Fundstelle: `VerknuepfteAufgaben.svelte:59-67`.
  - Bekannter Fehler (aus dem Code): Liegt das Mitglied auf einem anderen Board, außerhalb des
    geladenen Fertig-Fensters oder im Archiv, schließt sich das Detail, statt das Mitglied zu
    öffnen; Ursache: die Funktion zum Öffnen einer Karte im Board sucht nur in geladenen Karten
    und setzt sonst nichts (`Board.svelte:391-394`).

### J. Timer und Zeit an der Karte

- **M-78 Timer starten.** Aktion: Play auf der Karte, "Start" oder "Fortsetzen" im Detail oder
  "Fortsetzen" in der Laufleiste. Wirkung: setzt `laeuft_seit` (sekundengenau); setzt das
  Startdatum der Karte, falls leer; abgewiesen bei Ideen (409) und bei Anmeldung auf fremden
  Karten (erlaubt: Admin, Zuständiger, Karte ohne Zuständigen). Fundstelle:
  `timer.svelte.ts:48-51`, `persistence_karten.py:703-724`, `kanban_kern/api.py:555-567`,
  `rechte.py:39-42`.
  - Bekannter Fehler: Ein Start ist auch auf Karten in der Erledigt-Spalte möglich (keine Prüfung).

- **M-79 Pause und Stopp.** Aktion: "Pause" oder "Stopp" im Detail oder in der Laufleiste, Pause
  auf der Karte. Wirkung: Pause bucht die Sitzung und lässt die Karte als "Pausiert" in der
  Laufleiste (Fortsetzen möglich); Stopp bucht genauso und blendet die Leiste aus; serverseitig
  sind beide derselbe Vorgang. Im Detail: läuft er, "Pause" und "Stopp"; ist die Karte pausiert und
  aktiv, "Fortsetzen" und "Stopp"; sonst "Start". Fundstelle: `timer.svelte.ts:53-63`,
  `Zeiterfassung.svelte:14-16`, `Zeiterfassung.svelte:101-110`.

- **M-80 Ein Timer je Person.** Wirkung: Ein Start pausiert und bucht alle anderen laufenden
  Karten mit demselben Zuständigkeits-Kürzel; Karten ohne Zuständigen gelten zusammen als eine
  Person; fremde Timer laufen weiter. Fundstelle: `persistence_karten.py:708-716`.
  - Bekannter Fehler: "Je Person" heißt in Wahrheit "je Zuständigkeits-Kürzel der Karte": eine
    Person kann zwei Timer haben (eigene Karte und Karte ohne Zuständigen), und ein Start auf einer
    Karte ohne Zuständigen stoppt die Timer aller anderen auf solchen Karten; Ursache: der Timer
    gehört der Karte, nicht dem startenden Konto.
  - Behoben seit 0.69.1 (Audit A4): Ein Start stoppte die Timer aller Personen.

- **M-81 Buchung beim Stoppen.** Wirkung: Die Sitzung wird an Mitternacht taggenau zerlegt; über
  12 Stunden wird auf die ersten 12 Stunden gedeckelt (vergessener Timer); je Karte und Tag gibt es
  höchstens einen automatischen Eintrag, neue Sitzungen werden hineingerechnet (Summe, früheste
  Start-, späteste Endzeit); manuelle Buchungen bleiben eigenständig; die Ticketzeit wird aus der
  Summe der Einträge neu berechnet; Verlauf "Timer gestoppt: n min erfasst". Fundstelle:
  `persistence_karten.py:646-700`, `persistence_basis.py:36-50`.
  - Bekannter Fehler (Gegenprobe): Die Tageszusammenfassung verschmilzt Sitzungen verschiedener
    Personen zu einem Eintrag der ersten Person (Zuständig A 30 min, dann B 20 min ergibt einen
    Eintrag A mit 50 min); Ursache: der Schlüssel der Zusammenfassung ist Karte und Tag ohne
    Person, und die Sitzung erbt das Kürzel der Karte statt des Startenden.
  - Bekannter Fehler: Der 12-Stunden-Deckel kürzt still, ohne Rückfrage oder Hinweis.

- **M-82 Laufleiste.** Wirkung: Leiste ganz oben, solange eine Karte aktiv ist: pulsierender Punkt,
  "Läuft" bzw. "Pausiert", Schlüssel, Titel, Live-Uhr; mit Schätzung ein Ring mit Prozent und "von
  H:MM Std", rot und "überschritten" über 100 %; Knöpfe "Pause" bzw. "Fortsetzen" und "Stopp". Ein
  Klick auf die Leiste öffnet die Karte nicht. Fundstelle: `LaufBar.svelte:1-55`.

- **M-83 Abgleich laufender Timer.** Wirkung: beim Start, alle 60 s und bei Fensterfokus fragt die
  Oberfläche die laufende Karte der eigenen Identität ab; wurde sie anderswo gestoppt, zeigt die
  Leiste den pausierten Stand statt weiterzuzählen; Nicht-Admins sehen nur die eigene laufende
  Karte. Fundstelle: `timer.svelte.ts:18-46`, `kanban_kern/api.py:546-552`,
  `persistence_karten.py:735-746`.

- **M-84 Automatische Stopps.** Wirkung: Ablegen in Erledigt (M-68) und Umschalten auf Idee (M-35)
  stoppen und buchen; das Löschen einer Karte mit laufendem Timer schließt die Laufleiste, die
  Sitzung geht mit der Karte unter. Fundstelle: `Board.svelte:443-444`, `Board.svelte:472`.

- **M-85 Live-Zeit.** Wirkung: Karte und Detail zählen sekündlich hoch (ein gemeinsamer
  Sekundentakt), aus erfasster Zeit plus Laufzeit seit `laeuft_seit`. Fundstelle:
  `timer.svelte.ts:18-23`, `timer.svelte.ts:65-71`, `Card.svelte:54-58`.

- **M-86 Tag buchen.** Aktion: Datumsfeld (Vorgabe heute), Dauerfeld ("z.B. 0:30 oder 1,5"), "Tag
  buchen" oder Enter. Wirkung: legt einen manuellen Eintrag auf diesen Tag an; Person = Bediener
  (Ersatz: Zuständiger); jede Person mit Kürzel darf auch auf fremden Karten buchen (es ist ihre
  eigene Zeit); Verlauf "Zeit gebucht: n min (Datum)"; eine Dauer von 0 oder weniger wird
  ignoriert. Fundstelle: `Zeiterfassung.svelte:74-81`, `Zeiterfassung.svelte:133-139`,
  `persistence_karten.py:804-822`, `kanban_kern/api.py:617-633`, `rechte.py:31-36`.
  - Bekannter Fehler: Eine unlesbare Dauer wird hier kommentarlos ignoriert, anders als beim
    Ticketzeit-Feld.

- **M-87 Ticketzeit gesamt setzen.** Aktion: neben dem Start-Knopf die Gesamtzeit überschreiben.
  Wirkung: nur wenn der Timer nicht läuft (sonst reine Anzeige mit Tooltip "erst stoppen"); mehr
  bucht die Differenz als manuellen Eintrag "Korrektur" auf heute, weniger zieht von den jüngsten
  Einträgen ab (löscht oder kürzt), alles in einer Transaktion; unlesbare Eingabe ergibt den Hinweis
  "Dauer bitte wie 1:30, 1,5 oder 90min eingeben."; nur Zuständiger oder Admin. Fundstelle:
  `Zeiterfassung.svelte:86-97`, `Zeiterfassung.svelte:111-118`, `persistence_karten.py:825-862`,
  `kanban_kern/api.py:636-650`.
  - Bekannter Fehler (Gegenprobe): Verringern löscht oder kürzt auch Einträge anderer Personen
    (jüngster Eintrag zuerst, ohne Blick auf die Person am Eintrag); Ursache: das Recht wird an der
    Karte geprüft, nicht an den betroffenen Einträgen.
  - Bekannter Fehler: Escape im Feld bucht die angefangene Eingabe (M-125).
  - Behoben seit 0.71.0 (Audit B): Die Korrektur war eine nicht atomare Folge von Einzelanfragen.

- **M-88 Tagesliste.** Aktion: in einer Zeile Datum oder Dauer ändern, X klicken. Wirkung: alle
  Einträge der Karte, neueste Tage zuerst; Datum und Dauer direkt änderbar (Änderung speichert);
  Stoppuhr-Symbol bei Einträgen aus Start/Stopp; X löscht und zeigt "Zeiteintrag (Dauer, Datum)
  gelöscht" mit Rückgängig; nur eigene Einträge änderbar (Server lehnt sonst ab); ein Ladefehler
  zeigt "Zeiteinträge konnten nicht geladen werden." mit "Nochmal versuchen". Fundstelle:
  `Zeiterfassung.svelte:24-73`, `Zeiterfassung.svelte:140-157`, `kanban_kern/api.py:653-671`.
  - Bekannter Fehler (aus dem Code): Nach Pause oder Stopp im Detail aktualisiert sich die
    Tagesliste nicht, erst beim erneuten Öffnen; Ursache: die Liste lädt nur bei Kartenwechsel
    (`Zeiterfassung.svelte:31-37`).
  - Bekannter Fehler (aus dem Code): Rückgängig legt den Eintrag als manuellen Eintrag des
    Bedieners neu an, Person, Start und Ende und die Herkunft aus dem Timer gehen verloren
    (`Zeiterfassung.svelte:68-72`, `kanban_kern/api.py:627-630`).
  - Behoben seit 0.68.3 (Audit A19): Löschen hatte weder Rückfrage noch Rückgängig.

- **M-89 Schätzung und Fortschritt.** Aktion: Zahlenfeld "Schätzung ... Std" (Schritt 0,25).
  Wirkung: gespeichert in Minuten, leer oder 0 entfernt; Fortschrittsbalken und "n % von H:MM
  Std", rot und "überschritten" über 100 %; speist das Projekt-Soll und den roten Zeitknopf.
  Fundstelle: `Zeiterfassung.svelte:119-124`, `Zeiterfassung.svelte:129-132`.

- **M-90 Zeiteingabe.** Wirkung: verstanden werden "1:30" (Stunden:Minuten), "1:30:00", "1,5" bzw.
  "1.5" (Stunden), "90m" bzw. "90min" (Minuten), "2h" bzw. "2std"; eine Zahl ohne Einheit sind
  Stunden; Unlesbares gilt als keine Eingabe. Anzeige im Detail immer H:MM:SS, auf der Karte M:SS
  bzw. H:MM:SS. Fundstelle: `timer.svelte.ts:73-109`.
  - Behoben seit 0.71.0 (Audit B): "90m" hieß 90 Stunden.

### K. Filter, Suche, Sortierung, gespeicherte Sichten

- **M-91 Suche.** Aktion: Feld "Suchen in Titel, Inhalt, Labels, Kommentaren ...", X leert.
  Wirkung: jedes Wort muss vorkommen (ohne Groß/Klein); offene Spalten werden im Browser
  durchsucht (Titel, Schlüssel, Beschreibung, Zuständig, Priorität, Labels, Checklistentexte,
  Kommentartexte und -autoren), Erledigt-Spalten serverseitig (M-25); je Board gemerkt.
  Fundstelle: `Toolbar.svelte:128-132`, `Board.svelte:271-298`.
  - Bekannter Fehler: Notizen werden nur in Erledigt-Spalten gefunden (M-57).

- **M-92 Prioritäts- und Labelfilter.** Aktion: Knopf "Filter" (mit Zahl aktiver Filter) öffnet
  eine Tafel. Wirkung: Priorität Hoch, Mittel, Niedrig (eine Wahl, erneuter Klick hebt auf),
  Labels als Chips (mehrere, ODER); die Labelauswahl stammt aus den Karten der offenen Spalten;
  je Board gemerkt. Fundstelle: `Toolbar.svelte:134-161`, `Board.svelte:86`,
  `Board.svelte:287-298`.
  - Bekannter Fehler: Labels, die nur an fertigen Karten hängen, fehlen in der Auswahl; der
    Labelfilter unterscheidet im Browser Groß/Klein, im Server nicht.

- **M-93 Personenfilter.** Aktion: Kürzel-Avatar in der Werkzeugleiste anklicken (die
  Zuständigen der offenen Karten). Wirkung: zeigt nur Karten der Person(en), mehrere kombinierbar
  (ODER), gilt auch für Erledigt-Spalten (serverseitig). Fundstelle: `Toolbar.svelte:193-201`,
  `Board.svelte:87`, `Board.svelte:289`.
  - Bekannter Fehler: Nur die ersten sieben Personen sind anklickbar ("+n" filtert nicht); der
    Filter wird nicht gemerkt, beim Boardwechsel nicht zurückgesetzt (wandert auf das nächste
    Board) und lädt die Erledigt-Spalten nicht neu; Ursache: `filterZustaendig` fehlt in Merken,
    Wiederherstellen und Neulade-Effekt (`Board.svelte:206-253`).

- **M-94 Sortierung.** Aktion: Auswahl Manuell (Vorgabe), Fällig, Priorität. Wirkung: Fällig =
  früheste zuerst, ohne Datum ans Ende; Priorität = hoch, mittel, niedrig, ohne; wirkt nur in
  offenen Spalten, Erledigt bleibt nach Abschluss sortiert; je Board gemerkt. Fundstelle:
  `Toolbar.svelte:176-184`, `Board.svelte:300-314`.

- **M-95 Gespeicherte Sichten.** Aktion: in der Filtertafel "Sicht speichern", Name eingeben,
  Enter oder "Speichern"; Lesezeichen-Chip anklicken; X am Chip. Wirkung: abgelegt wird die ganze
  Sicht (Suche, Sortierung, Priorität, Labels, Personen), gleicher Name überschreibt; je Board im
  Browser (`pw_filtersets_<boardId>`); Klick auf einen Chip wendet die Sicht an und schließt die
  Tafel, Klick auf die gerade aktive Sicht setzt alles zurück, X entfernt die Sicht. Fundstelle:
  `Toolbar.svelte:38-80`, `Toolbar.svelte:154-160`, `Toolbar.svelte:164-175`.
  - Bekannter Fehler: Sichten gelten nur im eigenen Browser, sie sind weder geteilt noch an ein
    Konto gebunden.

- **M-96 Filtervorschläge.** Aktion: Knopf für Filtervorschläge, Wunsch in Worten eingeben ("Was
  willst du sehen?"), Strg/Befehl+Enter oder Knopf. Wirkung: optionaler Vorschlagsdienst liefert
  Labels, Priorität und Sortierung als Auswahlliste, übernommen wird nur das Abgehakte; ohne
  erreichbaren Dienst ist der Knopf ausgeblendet. Fundstelle: `Toolbar.svelte:98-117`,
  `Toolbar.svelte:185`.

- **M-97 Ansichtszustand im Browser.** Wirkung: je Board `pw_board_<boardId>` mit Suche,
  Sortierung, Priorität, Labels, eingeklappten Spalten, Zeitfilter je Erledigt-Spalte und Ansicht;
  wird beim Öffnen des Boards wiederhergestellt und bei jeder Änderung geschrieben. Fundstelle:
  `Board.svelte:206-240`, `uiSpeicher.ts:33-51`.

### L. Listenansicht und Sammelaktionen

- **M-98 Listenansicht.** Wirkung: flache Tabelle derselben gefilterten Karten wie die
  Spaltenansicht (offene Spalten plus geladene Fertig-Fenster), Kopfzeile bleibt beim Scrollen
  stehen; Spalten Nr., Titel (mit Ideen- und Blockade-Symbol und bis zu drei Labels), Status,
  Zuständig, Priorität, Fällig, Zeit ("Ist h / Soll h"); fertige Zeilen grau mit durchgestrichenem Titel; Klick auf eine
  Zeile öffnet das Detail; Leerzustand "Keine Karten (Filter aktiv?)." Fundstelle:
  `ListenAnsicht.svelte:140-186`, `Board.svelte:318-322`.
  - Bekannter Fehler: Von Erledigt-Spalten erscheint nur das geladene Fenster (Vorgabe: nur heute
    erledigte), die Zeitspalte zeigt keine laufende Zeit.

- **M-99 Sortieren in der Liste.** Aktion: Spaltenkopf anklicken, erneut klicken dreht die
  Richtung. Wirkung: Pfeil zeigt die Richtung; Vorgabe Status aufsteigend. Fundstelle:
  `ListenAnsicht.svelte:64-98`.
  - Bekannter Fehler: "Status" sortiert alphabetisch nach Spaltentitel statt nach der
    Spaltenreihenfolge des Boards (`ListenAnsicht.svelte:76`).

- **M-100 Auswahl.** Aktion: Kästchen je Zeile (öffnet nicht), "Alle auswählen" im Kopf. Wirkung:
  die Auswahl räumt sich selbst auf, wenn Karten durch Filter oder Neuladen verschwinden.
  Fundstelle: `ListenAnsicht.svelte:32-50`, `ListenAnsicht.svelte:144`,
  `ListenAnsicht.svelte:160-162`.

- **M-101 Sammelaktionen.** Aktion: Leiste "n ausgewählt" mit "Status setzen ...", "Zuständig
  ...", "Priorität ...", "Löschen", "Auswahl aufheben". Wirkung: Status setzt jede Karte ans Ende
  der Zielspalte (mit Gruppen-Mitzug und Timer-Stopp); Zuständig auf eine Person des Boards oder
  niemand; Priorität oder keine; Löschen mit einem Hinweis und einem Rückgängig für alle (Zusatz
  "erfasste Zeiten gehen verloren", wenn Zeit erfasst war); die Aktionen laufen nacheinander über
  die Einzelendpunkte, die Bedienelemente sind währenddessen gesperrt, danach ein Neuladen und die
  WIP-Warnung. Fundstelle: `ListenAnsicht.svelte:112-138`, `Board.svelte:455-482`.
  - Bekannter Fehler: Zuständig lässt sich nur auf Personen setzen, die schon eine offene Karte im
    Board haben; scheitert eine Einzelaktion mittendrin, bleibt ein halber Stand ohne Neuladen;
    vor dem Sammel-Löschen gibt es keine Rückfrage.

### M. Löschen, Rückgängig, Rückfragen, Hinweise

- **M-102 Karte löschen.** Aktion: Papierkorb auf der Karte, "Karte löschen" unten im Detail
  oder Sammel-Löschen. Wirkung: ohne Rückfrage; schließt ein offenes Detail und die Laufleiste
  dieser Karte; der Server löscht Karte, Dokumente, Zeiteinträge, Verlauf, Anhänge samt Dateien
  und Transkript-Marken, löst verwaiste Gruppen auf, verdichtet die Spalte und merkt bei
  Serienkarten einen Auslass; der Suchindex wird bereinigt; Hinweis 'Karte "X" gelöscht' (plus
  " - erfasste Zeiten gehen verloren", wenn Zeit erfasst war) mit Rückgängig. Fundstelle:
  `Card.svelte:139-146`, `CardDrawer.svelte:425-427`, `Board.svelte:439-454`,
  `persistence_karten.py:591-622`, `kanban_kern/api.py:526-530`.
  - Bekannter Fehler: Jedes Projektmitglied darf jede Karte löschen, und es gibt keinen
    Papierkorb.

- **M-103 Rückgängig einer Karte.** Aktion: "Rückgängig" im Hinweis (6 Sekunden). Wirkung: legt
  die Karte aus dem Schnappschuss neu an: Titel, Beschreibung, Labels, Priorität, Cover, Start,
  Fällig, Zuständig, Typ, dann Checkliste, Notizen, Schätzung und Transkript-Verweis, dann jeden
  Kommentar einzeln. Fundstelle: `restore.ts:10-34`.
  - Bekannter Fehler: Rückgängig ist eine Neuanlage: neuer Schlüssel, Platz am Spaltenende, neues
    `bewegt_am` (eine alte fertige Karte springt in "Heute"), Kommentare mit neuer Zeit; verloren
    gehen Zeiten, Blockade, Gruppe, Dokumente, Anhänge, Transkript-Marken, Verlauf und der
    Serienbezug (der Auslass bleibt gesetzt); der Hinweis nennt nur die Zeiten; Ursache: hartes
    Löschen statt weichem Löschen.
  - Behoben seit 0.68.3 (Audit A3, teilweise): Notizen, Schätzung, Typ und Transkript-Verweis
    kommen inzwischen mit, der Hinweis nennt den Zeitverlust.

- **M-104 Hinweise.** Wirkung: unten mittig gestapelt, verschwinden nach 6 Sekunden, mit X
  schließbar, optional "Rückgängig" (nur innerhalb der 6 Sekunden); ungefangene Fehler erscheinen
  als "Aktion fehlgeschlagen: <Grund>" (höchstens ein Hinweis je 1,5 Sekunden); Netzfehler heißen
  "Server nicht erreichbar". Fundstelle: `toaster.svelte.ts:13-22`, `Toast.svelte:1-20`,
  `main.ts:24-33`, `api/basis.ts:24`.

- **M-105 Rückfragen im Überblick.** Wirkung: echte Rückfrage beim Löschen von Erledigt-Spalte
  (Dialog), Board, Mappe und Dokument (jeweils inline); Rückgängig statt Rückfrage bei Karte,
  offener Spalte, Sammel-Löschen und Zeiteintrag; weder noch bei Anhang, Transkript-Marke,
  Transkript-Verknüpfung, Checklistenpunkt und Label. Die letzte Mappe und die letzte Spalte eines
  Boards sind nicht löschbar. Fundstelle: `SeitenLeiste.svelte:172-178`,
  `SeitenLeiste.svelte:189`, `SeitenLeiste.svelte:204-211`, `persistence_struktur.py:231-239`,
  sonst siehe die einzelnen Mechaniken.

### N. Serienkarten im Board

- **M-106 Serienkarten.** Wirkung: Eine Serie (je Board) legt ihre Termine als normale Karten an:
  in der Zielspalte der Serie, sonst in der ersten Spalte des Boards; Titel "HH:MM Titel" bei
  Uhrzeit; Beschreibung, Labels und Zuständig aus der Serie; Fällig = Termintag; Schätzung =
  geplante Dauer; Schlüssel aus dem Board-Zähler; Verlauf "Karte angelegt" ohne Person.
  Serienkarten sind timerfähig wie jede Karte und haben fest den Termintag als Abschluss (M-23).
  Fundstelle: `serien/dienst.py:19-26`, `serien/dienst.py:41-102`.
  - Bekannter Fehler (aus dem Code): Wird die Zielspalte gelöscht, legt die Serie weiter Karten in
    die nicht mehr existierende Spalte; sie sind auf keinem Board sichtbar, erscheinen aber in
    Heute; Ursache: `_zielspalte` prüft die Spalte nicht, und das Löschen einer Spalte räumt
    Serien nicht nach.
  - Behoben seit 0.68.3 (Audit A15): derselbe Fehler bei gelöschten Boards und Mappen.

- **M-107 Vorbuchungsfenster.** Wirkung: Vorlauf je Serie (Vorgabe 14 Tage, 0 = nur heute);
  verpasste Tage höchstens 31 Tage zurück; nach dem Reaktivieren erst ab dem Reaktivierungstag;
  Feiertage optional übersprungen; Urlaubstage der zuständigen Person übersprungen; höchstens eine
  Karte je Serie und Tag (eindeutiger Index, eine Doppelkarte wird wieder verworfen); der Lauf
  geschieht beim Serverstart und einmal täglich je Browser (`pw_serien_check`). Fundstelle:
  `serien/dienst.py:41-102`, `App.svelte:265-274`, `persistence_schema.py:258-264`.

- **M-108 Auslass.** Wirkung: Wird eine Serienkarte bewusst gelöscht (einzeln, per Spalte oder
  Board), wird ihr Tag gemerkt und nicht wieder angelegt. Fundstelle:
  `persistence_karten.py:596-605`, `persistence_karten.py:920-928`, `serien/dienst.py:75-81`.

- **M-109 Pause, Ändern, Urlaub.** Wirkung: Pausieren löscht offene, zeitlose Zukunftskarten der
  Serie; Ändern der Serie zieht offene, zeitlose, nicht erledigte Karten nach (Titel, Beschreibung,
  Person, Schätzung); ein nachträglich eingetragener Urlaub löscht offene, zeitlose Serienkarten
  der Person an diesen Tagen (mit Auslass). Fundstelle: `serien/dienst.py:111-167`.

- **M-110 Serie löschen.** Wirkung: löscht reine Vorbuchungen; Karten mit erfasster Zeit oder in
  der Erledigt-Spalte bleiben als Verlauf stehen und werden von der Serie gelöst. Fundstelle:
  `serien/dienst.py:174-197`.
  - Behoben seit 0.70.0 (Audit A14): Per Ziehen erledigte Instanzen ohne Zeit wurden mitgelöscht.

- **M-111 Nachtrag ignorierter Serienkarten.** Aktion: Dialog am Folgetag ("Stunden
  nachtragen"), Stunden anpassen, nachtragen, verwerfen oder später. Wirkung: angeboten werden
  Serienkarten vergangener Tage ohne Zeit und nicht erledigt, einmal täglich
  (`pw_serien_nachtrag_check`); Nachtragen bucht die angegebene Dauer (Vorschlag: Serien-Soll,
  sonst 60 Minuten) auf den Termintag ("Nachgetragen") und verschiebt die Karte in die
  Erledigt-Spalte (ohne Erledigt-Spalte in die letzte Spalte); Verwerfen löscht die Karte; nur
  eigene Serienkarten. Fundstelle: `serien/dienst.py:200-246`, `serien/api.py:18-34`,
  `SerienErinnerung.svelte:1-60`.
  - Bekannter Fehler: Die Liste ist weder nach Person noch nach Projekt gefiltert; fremde Karten
    lassen sich ohne Rückfrage verwerfen (`serien/api.py:18-21`).

### O. Transkripte, Vorlesen, Vorschläge

- **M-112 Ein verknüpftes Transkript.** Aktion: im Abschnitt "Transkript" suchen und einen
  Treffer wählen; "Öffnen"; X. Wirkung: Suche entprellt 220 ms, bis 12 Treffer; Id und Name werden
  an der Karte gespeichert; "Öffnen" wechselt in die Transkript-Ansicht und öffnet es; X löst die
  Verknüpfung. Fundstelle: `CardDrawer.svelte:158-176`, `CardDrawer.svelte:352-369`.

- **M-113 Transkript-Verweise (Marken).** Aktion: im Abschnitt "Transkript-Verweise" suchen und
  anhängen, Zusammenfassung tippen, Vorschlag anfordern, "Öffnen", X. Wirkung: beliebig viele
  Marken je Karte mit Name, Position (M:SS), Sprecher und Segmenttext; Zusammenfassung speichert
  600 ms nach der Eingabe; ein Zusammenfassungsvorschlag des Vorschlagsdienstes erscheint als
  Vorschau mit "Übernehmen" und "Verwerfen" (Meldung, wenn kein Dienst erreichbar ist); "Öffnen"
  springt im Transkript an die Position und hebt das Segment hervor; neue Marken entstehen hier
  (ohne Position) oder in der Transkript-Ansicht per Anheften an ein Segment (mit Position, Text,
  Sprecher); Marken gehen mit Karte, Spalte oder Board unter. Fundstelle:
  `TranskriptVerweise.svelte:19-112`, `persistence_karten.py:582-588`.
  - Bekannter Fehler: Speicherfehler der Zusammenfassung werden verschluckt
    (`TranskriptVerweise.svelte:55`, `TranskriptVerweise.svelte:77`); ein Ladefehler sieht aus wie
    "keine Verweise" (`TranskriptVerweise.svelte:30`); Entfernen ohne Rückfrage.

- **M-114 Vorlesen.** Aktion: "Vorlesen" / "Stopp" an der Beschreibung (nur bei Text),
  Lautsprecher an jedem Kommentar, "Vorlesen" in Heute. Wirkung: liest den Text vor, Stimme und
  Tempo werden im Browser gemerkt (`pw_tts_stimme`, `pw_tts_tempo`). Fundstelle:
  `CardDrawer.svelte:152-156`, `CardDrawer.svelte:399`, `MarkdownFeld.svelte:97-99`.

- **M-115 Labelvorschläge.** Aktion: Knopf neben der Überschrift "Labels", optional ein Hinweis,
  Vorschläge abhaken, "Hinzufügen". Wirkung: der optionale Vorschlagsdienst schlägt aus Titel und
  Beschreibung Labels vor; übernommen werden nur neue; ohne Dienst ist der Knopf ausgeblendet.
  Fundstelle: `CardDrawer.svelte:187-199`, `CardDrawer.svelte:333`.

### P. Rechte und Identität an der Karte

- **M-116 Projekt-Prüfung.** Wirkung: Karten-, Spalten-, Board-, Kommentar-, Checklisten-,
  Anhang-, Verlaufs-, Verknüpfungs-, Fertig-, Archiv- und Export-Anfragen prüfen, ob die Mappe für
  die Person sichtbar ist (Mappe ohne Mitglieder ist für alle sichtbar, Admin sieht alles), sonst
  403. Ohne aktive Anmeldung ist alles offen (handelnde Person mit Adminrecht und ohne Kürzel).
  Fundstelle: `kanban_kern/api.py:62-68`, `persistence_struktur.py:67-77`,
  `akteur.py:36-39`, `akteur.py:50-63`.
  - Bekannter Fehler: Lücken ohne Prüfung: Erledigt-Markierung, Verknüpfung lösen, Timer-Pause,
    Dokument lesen, ändern und löschen per Id (`kanban_kern/api.py:368-395`,
    `kanban_kern/api.py:580-605`, `kanban_kern/api.py:729-735`).
  - Behoben seit 0.69.1 (Audit A7, A8): Die Prüfung galt nur für vier Lesewege.

- **M-117 Zeit- und Timer-Rechte.** Wirkung: Timer starten und stoppen: Admin, Zuständiger oder
  Karte ohne Zuständigen; Zeit buchen: Admin oder jede Person mit Kürzel (der Eintrag trägt die
  eigene Person); Zeiteintrag ändern und löschen: Admin oder die Person des Eintrags (Ersatz:
  Zuständiger der Karte); Ticketzeit setzen: Admin oder Zuständiger; globale Kanban-Einstellungen
  und Label-Verwaltung schreiben nur Admins. Alle diese Grenzen gelten nur bei aktiver Anmeldung. Fundstelle: `rechte.py:21-42`,
  `auth/dienst.py:73-80`.
  - Bekannter Fehler: Die Oberfläche bietet Start, Ticketzeit-Feld und Bearbeiten der Tageszeilen
    auch dort an, wo der Server ablehnt; der Nutzer erfährt es erst durch "Aktion fehlgeschlagen".

- **M-118 Identitätsquelle.** Wirkung: Identität ist bei aktiver Anmeldung die angemeldete Person
  (verbindlich), sonst die im Browser gewählte Personen-Sicht (`pw_aktive_person`); daraus kommen
  das Kürzel für Vorbelegung, Kommentar-Autor, Timer-Abgleich und Glocke. Fundstelle:
  `identitaet.ts:17-32`, `personSicht.svelte.ts:6-14`, `App.svelte:86-88`.
  - Bekannter Fehler (Wurzel): Identität, Eigentum und Auswertungen hängen am Kürzel-Text
    (Zuständig, Zeiteintrag, Kommentar-Autor, Verlauf, Timer) statt an einer Konto-Id.

- **M-119 Glocke.** Aktion: Glockensymbol in der Kopfleiste, Eintrag anklicken, "Alles gelesen".
  Wirkung: Zähler und Liste der Ereignisse anderer (oder des Systems) auf Karten, für die die
  eigene Person zuständig ist, seit dem zuletzt gelesenen Eintrag (je Person im Browser,
  `pw_glocke_<Kürzel>`); Abfrage alle 60 s und bei Fokus, höchstens 50 Einträge; ein Klick öffnet
  die Karte; Mitarbeiter sehen nur die eigene Glocke. Fundstelle: `Glocke.svelte:13-60`,
  `persistence_inhalte.py:391-417`, `kanban_kern/api.py:272-282`.
  - Bekannter Fehler: Der Gelesen-Stand gilt nur im eigenen Browser, ein anderes Gerät zeigt alles
    erneut.

### Q. Karten außerhalb des Boards

- **M-120 Heute.** Wirkung: Abschnitte Überfällig, Heute fällig, Diese Woche (bis 7 Tage), Läuft
  gerade, Liegengeblieben (offen, nicht laufend, nicht schon wegen Fälligkeit gelistet, seit mehr
  als 7 Tagen nicht bewegt) und Blockiert (offen); "offen" heißt nicht in der Erledigt-Spalte;
  Klick öffnet die Karte; Vorlesen des Überblicks; Schnell-Erfassen (M-123). Fundstelle:
  `persistence_inhalte.py:420-473`, `Heute.svelte:72-100`.
  - Bekannter Fehler: "Liegengeblieben" ist fest 7 Tage und folgt nicht der
    Alterungs-Einstellung; "Läuft gerade" zeigt die Timer aller Personen der sichtbaren Projekte.

- **M-121 Fälligkeitskalender.** Wirkung: Monatsgitter mit Markern je Tag (rot = offen, grün =
  alles erledigt) und Liste "Fällig im Monat" mit durchgestrichenen erledigten Karten, auch
  erledigte Karten zählen mit; Klick öffnet die Karte. Fundstelle:
  `persistence_inhalte.py:352-377`, `Kalender.svelte:34-60`, `Kalender.svelte:241`.

- **M-122 Sprung aus anderen Ansichten.** Wirkung: Suche, Heute, Glocke, Kalender und Transkripte
  öffnen eine Karte über einen Navigationswunsch (Board-Id plus Karten-Id oder Schlüssel); die App
  wechselt ins Board, das Board öffnet die Karte, eine fertige außerhalb des Fensters per
  Einzelabruf. Fundstelle: `navigation.svelte.ts:11-15`, `App.svelte:109-117`,
  `Board.svelte:95-117`.
  - Bekannter Fehler: andere Mappe und Schlüssel ohne Nachladen, siehe M-09.

- **M-123 Schnell-Erfassen.** Aktion: Freitext in Heute, etwa "R3-130 1:30 Doku geschrieben
  gestern", Enter oder "Vorschau", dann buchen. Wirkung: Karte wird über den Schlüssel, dann den
  exakten Titel, dann einen Titelteil aufgelöst (zuletzt bewegte zuerst); Dauer und Datum
  (gestern, Wochentage) werden erkannt; erst Vorschau, dann Buchung mit der Person des Bedieners;
  Projektsichtbarkeit wird beachtet, Ideen werden abgewiesen. Fundstelle: `Heute.svelte:13-43`,
  `kanban_kern/api.py:400-415`, `persistence_karten.py:115-141`.
  - Bekannter Fehler: Bei gleichem Schlüssel in mehreren Boards bucht es auf eine beliebige dieser
    Karten (M-02).

### R. Tastatur und Komfort

- **M-124 Tastenbelegung.** Wirkung: Karten-Eingabe Enter legt an, Umschalt+Enter Zeilenumbruch,
  Escape schließt; Spalten-Eingabe und Spalten-Umbenennen Enter speichert, Escape bricht ab;
  eingeklappte Spalte Enter oder Leertaste klappt aus; fokussierte Karte Enter öffnet; im Detail
  Enter in Label, Checklistenpunkt, Kommentar und "Tag buchen"; Dokumenttitel Enter; Vorschläge
  Strg/Befehl+Enter; Seitenleiste Board und Mappe Enter oder Escape. Es gibt keine globalen
  Tastenkürzel (etwa neue Karte, Suche, Verschieben per Tastatur). Fundstelle:
  `Column.svelte:111`, `Column.svelte:141`, `Column.svelte:220`, `Board.svelte:637`,
  `Card.svelte:113-119`, `CardDrawer.svelte:339`, `CardDrawer.svelte:402`,
  `Checkliste.svelte:50`, `Checkliste.svelte:56`, `Zeiterfassung.svelte:136`.

- **M-125 Escape im Detail.** Aktion: Escape drücken. Wirkung: steckt der Fokus in einem
  Eingabefeld, verlässt der erste Escape das Feld, der zweite schließt das Detail; ohne Fokus in
  einem Feld schließt der erste. Fundstelle: `CardDrawer.svelte:238-248`.
  - Bekannter Fehler: Escape übernimmt den getippten Wert, statt ihn zu verwerfen: Titel,
    Blockade-Grund, Schätzung, Ticketzeit (bucht Zeit), Datum und Dauer der Tageszeilen speichern
    beim Verlassen, die Label-Eingabe fügt das Label hinzu; Ursache: Escape ruft `blur()`, und die
    Felder speichern bei blur bzw. change.
  - Behoben seit 0.72.0 (Audit E20): Escape und Fokus im Detail fehlten.

- **M-126 Zähler und leere Zustände.** Wirkung: Zähler an Spaltenkopf (mit WIP), eingeklappter
  Spalte, Fertig-Fenster ("X von Y"), Filterknopf, Gruppen-Pille, Checkliste, Kommentaren, Glocke
  und Archiv; leere Zustände: Listenansicht "Keine Karten (Filter aktiv?).", Archiv mit Hinweis,
  Verlauf "Noch kein Verlauf.", Beschreibung und Notizen mit "Klicken zum Bearbeiten", Mappe ohne
  Board mit "Board anlegen"; eine leere Spalte zeigt nur "+ Karte". Fundstelle:
  `Column.svelte:116`, `Column.svelte:154`, `Column.svelte:205-214`, `Toolbar.svelte:136`,
  `ListenAnsicht.svelte:184-186`, `CardDrawer.svelte:420-422`, `App.svelte:364-372`.

## 3. Einstellungen des Boards mit Vorgabewerten

Ein Board hat im Stand 0.74.0 keine eigenen Einstellungen; alle Grenzen gelten global für alle
Boards. Im Neubau mit eigenständigen Boards sind sie die Kandidaten für Einstellungen je Board.

### 3.1 Global einstellbar (Einstellungen, Abschnitt "Fertig-Karten und Archiv")

Schreiben nur für Admins bei aktiver Anmeldung. Fundstelle: `models.py:115-127`,
`persistence_inhalte.py:30-57`, `Einstellungen.svelte:155-183`.

| Einstellung | Schlüssel | Vorgabe | Bereich |
|---|---|---|---|
| Karten je Ladeschritt | `fertig_seitengroesse` | 50 | 1 bis 500 |
| Archiv ab (Tage) | `archiv_tage` | 365 | 1 bis 100000 |
| Alterung amber ab (Tagen) | `aging_amber_tage` | 4 | 0 bis 365, 0 = aus |
| Alterung rot ab (Tagen) | `aging_rot_tage` | 8 | 0 bis 365, 0 = aus |

- Bekannter Fehler (Gegenprobe): Nach dem Speichern zeigen Formular und Karten wieder 4 und 8,
  bis die Seite neu geladen wird (gespeichert ist der richtige Wert); Ursache:
  `setze_kanban_einstellungen` gibt die Alterungswerte nicht zurück, und die Antwort füllt sie mit
  Vorgaben auf (`persistence_inhalte.py:57`, `kanban_kern/api.py:230-231`,
  `Einstellungen.svelte:172-177`). Jeder Speicherfehler wird als "nur Admins" gemeldet.

### 3.2 Je Board gespeichert

| Wert | Vorgabe |
|---|---|
| Titel | Eingabe beim Anlegen; neue Mappe: "Aufgaben" |
| Kürzel | aus dem Titel beim Anlegen (M-02), danach fest |
| Laufnummer | 0 (erste Karte bekommt 1) |
| Spalten beim Anlegen | "Offen", "In Arbeit", "Erledigt" (Erledigt markiert), ohne WIP-Limit |
| Beispieldaten einer frischen Installation | Mappe "Gerät R3", Board "Produktionsplanung", Kürzel R3, Laufnummer 131, Spalten Backlog, In Arbeit (WIP 3), Prüfung, Fertig (erledigt) |

Fundstelle: `persistence_struktur.py:139-145`, `persistence_struktur.py:403-423`,
`persistence_schema.py:271-283`.

### 3.3 Je Spalte

| Wert | Vorgabe |
|---|---|
| Titel | Eingabe |
| WIP-Limit | keins; sonst ganze Zahl ab 1 |
| Reihenfolge | ans Ende |
| Erledigt | aus; genau eine Erledigt-Spalte je Board |
| Akzentfarbe | aus der Position: #4f9be8, #ffb300, #a5d6a7, #b39ddb, #f48fb1, #80cbc4, #ff8a65, #9fa8da im Umlauf |
| Zeitfilter (nur Erledigt, im Browser) | Heute |

### 3.4 Je Zeitgruppe und je Serie (soweit das Board betroffen ist)

| Wert | Vorgabe |
|---|---|
| Zeit teilen (Gruppe) | an |
| Zielspalte (Serie) | erste Spalte des Boards |
| Vorlauf (Serie) | 14 Tage, 0 = nur heute |
| Feiertage überspringen, Wochenenden überspringen (Serie) | aus |
| Aktiv (Serie) | an |

### 3.5 Im Browser gemerkt (je Gerät)

| Schlüssel | Inhalt und Vorgabe |
|---|---|
| `pw_board_<boardId>` | Suche leer, Sortierung "manuell", Priorität keine, Labels keine, eingeklappte Spalten keine, Zeitfilter je Erledigt-Spalte "heute", Ansicht "board" |
| `pw_filtersets_<boardId>` | gespeicherte Sichten, Vorgabe keine |
| `pw_ui` | Seitenleiste offen (an), Breite 264 px (200 bis 480), letzte Ansicht, letztes Board |
| `pw_zuletzt_kuerzel` | Standard-Zuständiger neuer Karten, Vorgabe leer |
| `pw_aktive_person`, `pw_person_gewaehlt` | Personen-Sicht ohne Anmeldung, Vorgabe "Alle" |
| `pw_glocke_<Kürzel>` | Gelesen-Marke der Glocke |
| `pw_serien_check`, `pw_serien_nachtrag_check` | Tagesmarken für Vorbuchung und Nachtrag |
| `pw_tts_stimme`, `pw_tts_tempo` | Vorlesen |
| `pw_stundenleiste` | Stunden-Leiste offen (an) |

Nicht gemerkt werden Personenfilter, Sortierung der Listenansicht und die Archivsuche.

### 3.6 Fest im Code (heute nicht einstellbar)

| Wert | Festwert | Fundstelle |
|---|---|---|
| Anzeigedauer der Hinweise | 6 s | `toaster.svelte.ts:16` |
| Drossel für Fehlerhinweise | 1,5 s | `main.ts:27` |
| Autospeichern (Beschreibung, Notizen, Dokumente, Transkript-Zusammenfassung) | 600 ms | `MarkdownFeld.svelte:67`, `DokumentVerwaltung.svelte:69`, `TranskriptVerweise.svelte:55` |
| Entprellung Fertig-Suche und Archivsuche | 250 ms | `Board.svelte:252`, `Archiv.svelte:40` |
| Entprellung Transkriptsuche | 220 ms, bis 12 Treffer | `CardDrawer.svelte:166-167` |
| Klicksperre nach dem Ziehen | 160 ms | `Board.svelte:392` |
| Nachladeschwelle | 80 px vor dem Spaltenende | `Column.svelte:66` |
| Ablageposition in Erledigt | 1 000 000 (ans Ende) | `Board.svelte:360` |
| Deckel je Timer-Sitzung | 12 h | `persistence_karten.py:667` |
| Abgleich laufender Timer | 60 s und bei Fokus | `timer.svelte.ts:27-28` |
| Fälligkeit amber | heute bis in 2 Tagen | `Card.svelte:79` |
| "Im Status" rot im Detail | ab 8 Tagen | `CardDrawer.svelte:321` |
| Heute: Diese Woche, Liegengeblieben | 7 Tage, 7 Tage | `persistence_inhalte.py:428-429` |
| Anklickbare Personen-Avatare | 7 | `Toolbar.svelte:196` |
| Treffer der Gruppensuche | 8 | `VerknuepfteAufgaben.svelte:30` |
| Glocke | alle 60 s, höchstens 50 Einträge | `Glocke.svelte:34`, `persistence_inhalte.py:392` |
| Verlauf | höchstens 200 Einträge | `persistence_inhalte.py:380` |
| Anhang | höchstens 25 MB je Datei | `persistence_inhalte.py:216` |
| Serien | Vorlauf 14 Tage (je Serie änderbar), Rückblick 31 Tage | `serien/dienst.py:47-57` |
| Kopie | Titelzusatz " (Kopie)" | `restore.ts:43` |
| Blockade | Platzhaltergrund "Grund noch offen" | `CardDrawer.svelte:56` |
| Maße | Spalte 286 px, eingeklappt 46 px, Detail 540 px | `Column.svelte:235`, `Column.svelte:247`, `CardDrawer.svelte:475` |
| Präfix ohne Board-Kürzel | "K" | `persistence_karten.py:392` |
