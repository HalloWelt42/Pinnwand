# Leitfaden der Entwürfe

Die Entwürfe der neuen Pinnwand entstehen im echten Stack: Vite, Svelte 5, TypeScript, die Bausteine des Leitstands und
die Marken des Appkerns. Nach der Freigabe werden diese Ansichten die Oberfläche der App, mit Daten aus der
Schnittstelle statt der Beispieldaten. Ein Entwurf darf deshalb nichts zeigen, was die App so nicht bauen würde.

## Erst lesen

- `../docs/ENTWURF.md`: die Entscheidungen des Nutzers (Board als Einheit, Rollen je Board, Zeitkonto je Person, Stufen)
- `../docs/BOARD_MECHANIK.md`: die Mechanik der alten Pinnwand mit Kennungen M-01 bis M-126; sie ist das Maß
- `src/modell.ts`, `src/beispiel/daten.ts`, `src/beispiel/stand.svelte.ts`, `src/beispiel/format.ts`: Typen, Beispieldaten,
  veränderlicher Zustand, Darstellung von Zeiten und Daten
- `src/weg.svelte.ts`, `src/routen.ts`, `src/zustaende.ts`: Pfade und Galerie
- `src/stil/pinnwand.css`, `src/schale/`, `src/board/`, `src/detail/`: Schale, Board, Karte, Kartendetail als Vorbild
- `node_modules/appkern-oberflaeche/oberflaeche/stil/leitstand.css` (Bausteine) und `marken.css` (die einzigen Farben,
  Schriften und Schriftgrößen)

## Aufbau

- Jeder Bereich hat seinen Ordner `src/ansichten/<bereich>/` mit seinen Ansichten, `routen.ts` (Pfad auf Ansicht),
  `zustaende.ts` (Einträge der Galerie) und bei Bedarf eigenen Beispieldaten und Typen; sein Stil steht in
  `src/stil/<bereich>.css`. Gemeinsame Dateien (Modell, Beispieldaten, Schale, Board, Detail, `pinnwand.css`, Wege,
  Galerie, App) ändert nur, wer sie verantwortet; Bedarf dort gehört in den Bericht.
- Echte Pfade wie in der App, nie Anker: `/heute`, `/hinweise`, `/zeiten`, `/arbeitszeit[/reiter]`, `/serien[/kennung]`,
  `/berichte`, `/einstellungen/<reiter>`, `/boards/neu`, `/board/<kürzel>` (Kürzel klein, etwa `/board/prod`),
  `/board/prod/131` (Karte PROD-131 im Detail), `/board/prod/liste|kalender|zeitachse`, `/board/prod/einstellungen/<reiter>`,
  `/board/prod/archiv`, `/board/prod/papierkorb`. Vorgeführte Zustände derselben Ansicht mit `?entwurf=<name>`, die
  Telefonansicht mit `?geraet=telefon`. Verweise sind gewöhnliche `<a href="/...">`; der Weg fängt sie ab.
- Eine Rechneransicht steckt in `<main class="haupt rahmen">` der Schale: oben `<div class="rahmen-kopf">` mit
  `<div class="seitenkopf">`, darunter ein eigenes Rollfeld (`<div class="rollfeld">` oder `spalten`). Die Seite rollt nie
  und nie seitlich; was zu breit ist (Tabelle), bekommt ein eigenes Rollfeld (`tabellen-raum`). Raster mit
  `minmax(0, 1fr)`, `min-width: 0` in Kindern von Flex und Raster, lange Wörter brechen um.
- Ansichten eines Boards (Liste, Kalender, Zeitachse) zeichnen unter Kopf und Werkzeugleiste des Boards in einem Raum mit
  `flex: 1; min-height: 0` und bringen ihr eigenes Rollfeld mit.

## Gemeinsame Schicht: eine Wahrheit, ein Weg

Jede Sache hat genau einen Ort. Ein Bereich hält keine eigene Kopie von Daten, keinen eigenen Zustand für geteilte
Dinge und keine eigene Fassung einer Regel; was fehlt, kommt in die gemeinsame Schicht (siehe "Bedarf").

- `src/modell.ts`: alle Typen. Was sich ergibt, steht nicht darin, sondern wird gerechnet: die Zeit einer Karte ist die
  Summe ihrer Zeiteinträge (kein `erfasstSek`), der Timer gehört der Person (`Timer`, kein `karte.laeuft`), Urlaubstage
  und der nächste Tag einer Serie ergeben sich aus den Regeln (kein gespeicherter Urlaubsstand, kein gespeicherter nächster Tag).
- `src/regeln/`: reine Regeln ohne Zustand. `tage.ts` (Kalendertage, Kalenderwoche, Monate), `feiertage.ts` (je
  Bundesland), `arbeitszeit.ts` (Wirkung der Abwesenheiten, Soll, Urlaubstage, Brückentage, Fassung des Zeitkontos),
  `eingabe.ts` (Dauer und Datum lesen), `board.ts` (Rechte, Alterung, Zeitfenster, Archiv). Regeln eines Moduls ohne
  Zustand (etwa die Tage einer Serie) gehören als eigene Datei hierher.
- `src/beispiel/` steht für die Schnittstelle. `daten.ts` und `daten-<bereich>.ts`: eine Welt von Beispieldaten, jede
  Karte, jeder Schlüssel, jeder Eintrag genau einmal. `stand.svelte.ts`: der eine Zustand mit einfachen Lesehilfen
  (`board`, `karte`, `karteAusNummer`, `boardAusKuerzel`, `konto`, `kartenDerSpalte`, `ordnerVon`). `abfragen.ts`:
  alles Gerechnete (`zeitDerKarte`, `timerVon`, `istAm`, `sollTag`, `saldo`, `urlaub`, `sichtbareKarten`, `archivVon`,
  `papierkorbVon`, `darf`, `ungelesen`, `kartenName`).
- `src/beispiel/anwendung/`: die Anwendungsfälle, der einzige Weg zu ändern. `karten` (verschieben, ablegen, erledigen,
  anlegen, bearbeiten, artSetzen, kommentieren, Sammelaktionen, Gruppen), `timer` (starten, anhalten, fortsetzen,
  stoppen), `zeiten` (buchen, Tageszeit und Ticketzeit setzen, Dauer und Notiz ändern, löschen, Deckel), `abwesenheiten`
  (eintragen, entfernen, zeitkontoSpeichern), `papierkorb` (inPapierkorb, spalteInPapierkorb, wiederherstellen,
  entfernen), `hinweise` (gelesen, alleGelesen). Jede Änderung läuft über die eine Hilfe in `meldung.svelte.ts`: die
  Meldung kommt mit Rückgängig, bei getrennter Verbindung ist Schreibendes gesperrt. Ansichten ändern `stand` nie direkt.
- `src/anzeige.ts`: Namen für Menschen (Farben, Zeitfenster, Prioritäten, Herkunft, Hinweisarten und -wege, Module).
- `src/teile/`: gemeinsame Bausteine. `Meldung.svelte` (die eine Meldung; die Schale zeigt sie, am Telefon die Schale des
  Telefons mit `ort="telefon"`), `DatumFeld`, `DauerFeld`, `Farbwahl`, `Personenwahl` (Kandidaten gibt der Aufrufer).
- `src/darstellung.svelte.ts`: Thema und Schriftstufe, eine Wahrheit für die Einstellung Darstellung und die Leiste.
- Ansichten eines Boards bekommen `board`, `entwurf`, `suche` und `ziehenGesperrt` (`board/ansichten.ts`).
- Vorgeführte Zustände (`?entwurf=...`), die Daten brauchen, die es sonst nicht gibt, setzen sie beim Öffnen über einen
  Anwendungsfall oder eine Lesehilfe der Ansicht, nie über eigene Kopien der Daten.

## Gestaltung

- Farben, Schriften und Schriftgrößen nur aus Marken (`var(--...)`), Mischungen mit `color-mix` aus Marken. Abstände mit
  `--a1` bis `--a7`, Ecken mit `--r1` bis `--r3`.
- Bausteine des Leitstands nutzen (`knopf`, `chip`, `karte`, `bereich`, `reiter`, `untergruppen`, `einstellung`,
  `tabelle`, `eingabe`, `wahl`, `schalter`, `zaehler`, `pille`, `zustand`, `hinweis`, `etikett`, `kennzahl`), nie eine
  ihrer Klassen umdefinieren; Eigenes mit `pw-` und dem Bereichswort (`pw-heute-...`, `pw-zeiten-...`). Auch `kopf`,
  `fuss`, `leer`, `karte`, `seite`, `haupt`, `marke` und `wahl` sind Bausteine des Leitstands (`.kopf` setzt etwa
  `grid-area`); als eigene Klassennamen zerlegen sie das Layout. Keine `style`-Angaben im Markup außer berechneten Werten.
- Keine einseitigen Ränder oder Streifen, kein `!important`. Wort und Farbe, nie Farbe allein. Bernstein (Akzent) nur
  für die eine Hauptsache einer Ansicht und für das, was läuft. Zahlen und Zeiten in `var(--schrift-zahl)`.
- Schriftstufe Klein ist die Vorgabe; nichts kleiner als `--marke`.
- Personen als `Person.svelte`, Karten als `Karte.svelte`, Zeiten und Daten über `format.ts`.

## Bedienung

- Keine Browser-Dialoge; Rückfragen stehen in der Fläche (`hinweis` mit Knöpfen). Löschen legt in den Papierkorb.
- Abläufe als sichtbare Schritte, links tun, rechts das Ergebnis; jede Sache an genau einem Ort.
- Datumsfelder als Textfeld im deutschen Format, keine nativen Datums- oder Farbwähler. Verweise auf Personen als
  Textfeld mit Vorschlägen, keine lange Auswahlliste.
- Am Telefon eine eigene, reduzierte Ansicht: Berührflächen ab 44 Pixeln, Folgenreiches (erledigen, löschen) per
  Drücken und Halten mit füllendem Ring, sichere Ränder oben und unten.

## Texte

- Deutsch mit echten Umlauten in allen Texten, Kommentaren und Beispieldaten; nur Bezeichner im Code in ASCII.
- Keine typografischen Zeichen (kein Gedankenstrich, keine typografischen Anführungszeichen), in Fließtext nie ein
  doppelter Bindestrich. Keine fremden Marken- oder Produktnamen. Erfundene Personen und Firmen, keine echten Adressen.
- Kurze Beschriftungen; Fachbegriffe im `title` erklärt.

## Prüfen

1. `npx svelte-check --tsconfig ./tsconfig.json`: keine Fehler, keine Warnungen.
2. Seitenliste `pruefung/<bereich>.json` (`{"anmeldung": false, "seiten": [{"name": "...", "pfad": "..."}]}`) und
   `node node_modules/appkern-oberflaeche/oberflaeche/werkzeuge/ansicht.mjs http://localhost:5398 --seiten pruefung/<bereich>.json --breiten 1920,1440,1100,900 --ausgabe <ordner>`
   (Telefon: `--breiten 390`): seitliches Rollen, Überlauf und Kontrast, hell und dunkel, bis "Keine Befunde".
3. Die Bilder selbst ansehen, mindestens 1440 und 900, hell und dunkel: nichts abgeschnitten oder überlappend, ruhig
   und gleich gebaut wie das Board.
