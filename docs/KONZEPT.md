# Pinnwand - Konzept und Roadmap

Dieses Dokument hält den abgestimmten Funktionsumfang und die Architektur der nächsten Ausbaustufen fest. Es beschreibt das Zielbild, nicht den Verlauf; der aktuelle Ist-Zustand steht in der README.

## Zweck

Pinnwand ist eine lokale, modulare Kanban-Plattform. Sie wird erweitert um eine agentenfähige Schnittstelle, mit der lokale KI-Werkzeuge (LM Studio, Fundus sowie MCP-Clients) das Board befüllen und als Wissensquelle lesen können, dazu um Inhalte (Markdown, Vorlesen, Transkriptionen), Planung (Wochenstunden, Urlaub), Auswertung (Berichte, PDF) und Komfort (semantische Suche, Benutzerführung).

## Architekturprinzipien

- KI ist optional, nie Pflicht: LLM, TTS, STT und semantische Suche bieten Mehrwert, sind aber kein Zwang. Die App ist ohne diese Dienste voll funktionsfähig. Jeder KI-Adapter hat einen Aus-Zustand und einen deterministischen Fallback (Erfassung regelbasiert, Suche auf Stichwort, Vorlesen auf Browser oder aus). Fehlende Dienste werden erkannt und das Feature dezent ausgeblendet.
- Stark modular: jede Fähigkeit ist ein austauschbares Modul oder ein Adapter hinter einer klaren Schnittstelle, angebunden über eine Registry statt fester Verdrahtung.
- Saubere Schichten, objektorientiert: eine Domänen-/Aktionsschicht ist die einzige Wahrheit der Operationen; Protokolle (REST, MCP, OpenAI-Tools) sind dünne Adapter darüber.
- Durchgängig typisiert: Pydantic-Modelle im Backend, TypeScript-Interfaces im Frontend, keine rohen Dicts.
- Lokal-only und datenschutzfreundlich: Standardbindung an 127.0.0.1, externe Erreichbarkeit nur bewusst per Konfiguration. Keine Cloud-Abhängigkeiten.
- Austauschbare Engines: TTS, STT, Embeddings, Such-Engine, Export-Renderer und Feiertags-Quelle sind je hinter einer Schnittstelle gekapselt.

## Externe Anbindungen (lokale Dienste)

- LM Studio (OpenAI-kompatibel): Chat und Embeddings über `/v1`. Embedding-Modell per Konfiguration, sonst Heuristik.
- Qdrant (Vektor-DB): eigene Collection in der vorhandenen Instanz auf `:6333`, Cosinus-Distanz.
- pappagei (TTS): `127.0.0.1:8765`, `POST /synthesize` liefert einen PCM-Strom (24 kHz mono), dazu `/voices` und `/health`.
- txt2voice (Transkriptionen): Backend `:10031`, `GET /api/transcribe/{id}`, Original-Audio unter `/api/transcribe/{id}/audio`, Suche `GET /api/search?source_type=transcription` (FTS5 mit Wort- und Phrasensuche, Trefferausschnitt, Segment-Zeitstempel).
- Lokales Whisper (STT fürs Mikrofon): Mitschrift `:8766` oder txt2voice-Worker; Aufnahme im Browser, Transkription lokal.
- Feiertage: gebündelte Offline-Bibliothek als Standard, optional Online-Abgleich, immer mit mehrstufiger Vorschau vor der Übernahme.

## Entscheidungen

### A - Agenten-API
REST plus MCP-Server (FastMCP, eingehängt unter `/mcp`, Streamable HTTP) plus OpenAI-Function-Schemas mit Ausführ-Endpunkt. Sicherheit: Bearer-Token je Client (gehasht), Scopes `read`/`write`/`admin`, Audit-Log jeder Aktion. Token-Verwaltung über eine Admin-Ansicht und über Konfiguration. Schutz: Idempotenz-Schlüssel gegen Doppelbuchung, Auflösung von Karten über Schlüssel oder Titel statt interner ID, Trockenlauf-Vorschau, klare Fehlertexte fürs Modell.

### B - Erfassungs-Komfort
Natürlichsprachiges Erfassen hybrid: das Modell extrahiert Felder, Pinnwand validiert deterministisch (Dauer wie "2 Std", "1:30", "1,5h", "90min"; relative Daten wie "gestern", "Montag") und zeigt immer eine Vorschau vor dem Schreiben. "Erledigt" ist eine je Board markierte Spalte. Natürlichsprachig möglich: Zeit buchen, Aufgabe anlegen, erledigen oder verschieben, Kommentar oder Checkliste ergänzen.

### C - Semantische Suche
KI-Freifeld mit optionalem Mikrofon (lokales Whisper). Hybride Suche aus Vektor (Qdrant) und der vorhandenen Stichwort-Tiefensuche. Indiziert werden Karten, Kommentare und Checklisten, Zeit-Kommentare sowie Notizen, Dokumente und verlinkte Transkriptionen. Aktualisierung inkrementell bei Änderung plus manueller Voll-Reindex.

### D - Markdown-Inhalte
Sehr gute Darstellung über die bewährte Kette (svelte-exmarkdown mit GFM, KaTeX für Mathe, Mermaid mit dunklem Thema und Aufruf-Gate, highlight.js für Code, DOMPurify zur Absicherung). Markdown in Karten-Beschreibung, Karten-Notizen und -Dokumenten, projektweiten Mappen-Dokumenten und Kommentaren. Editor als Split aus Eingabe und Live-Vorschau, dazu Vollbild-Modus.

### E - TTS / Vorlesen
Modularer TTS-Adapter mit pappagei als Standard, Browser-Sprachausgabe als Notnagel. Vorlesbar sind Karten-Inhalte, Kommentare, das Tages-Briefing und Transkriptionen. Komfort: Stimme und Modell wählbar, Tempo einstellbar, Hervorhebung des gerade gelesenen Satzes, volle Wiedergabesteuerung.

### F - Transkriptionen
Aus txt2voice gezielt verlinken: in Pinnwand durchsuchen und auswählen. Anzeige an Karten, in einer eigenen Transkripte-Ansicht und in Mappen-Dokumenten. Vorlesen wahlweise als Text (TTS) und als Original-Audio mit Sprung zum Segment. Suche spiegelt die FTS5-Suche von txt2voice inklusive Trefferausschnitt und Zeitstempel. Bei nicht laufendem Dienst ein klarer Hinweis.

### G - Wochenstunden-Planung und Urlaub
Echte Personen ersetzen die bisherigen Kürzel; je Person Wochen-Soll und Urlaubskonto. Wochen-Soll je Wochentag mit Überschreibung einzelner Wochen. Urlaub reduziert das Soll, halbe Tage möglich. Feiertage aus wählbarer Quelle (offline oder online) mit mehrstufiger Vorschau, mehrere Länder. Wochenenden, Feiertage und Urlaub sind im Kalender klar eingefärbt.

### H - PDF, Berichte und Archiv
Server-seitiger Export über WeasyPrint. Druckbar sind alle Ansichten plus eigens reduzierte Druckansichten. Formate PDF, CSV und Markdown. Standardberichte: Wochen-Stundenzettel, Soll/Ist, Kapazität und Auslastung, Zeit je Person und Karte. Mathe und Diagramme werden für den Druck server-seitig vorgerendert. Generierte Berichte landen unveränderlich im Berichts-Archiv (Zeitraum, Person, Erstelldatum) und bleiben als Stunden-Nachweis abrufbar.

### I - Was-steht-an-Panel
Handlungsorientierte Übersicht: überfällig, heute oder diese Woche fällig, in Arbeit, zu lange liegengeblieben. Zusätzlich tägliche und wöchentliche Termine aus den Serien (siehe Q). Platzierung unter der Heatmap und als Startbildschirm "Heute". Speist auch das gesprochene Tages-Briefing.

### J - Detailansicht
Beschreibung steht oben. Split- und Vollbild-Editor für mehr Raum. Automatisches Speichern (verzögert) mit sichtbarem Status (geändert oder gespeichert) und lokalem Entwurf gegen Datenverlust.

### K - UI-Einstellungen merken
Im Browser (localStorage) gemerkt: Thema und Seitenleisten-Zustand, eingeklappte Spalten, zuletzt geöffnetes Board und Ansicht sowie Filter, Sortierung und Suche.

### L - Routing
History-API mit echten Pfaden ohne Hashes, tief verlinkbar (Board, Karte über Schlüssel, Ansichten). Server-Fallback auf `index.html`.

### N - Flow-Ansicht (entfernt)
War als eigene Ansicht umgesetzt (zuletzt als automatisch geschichtetes Abhängigkeitsdiagramm mit kritischem Pfad), wurde aber auf Wunsch wieder entfernt, da ohne erkennbaren Mehrwert. Mit entfernt: das Feld blockiert_von, der Graph-Endpunkt und die Abhängigkeits-Pflege im Karten-Detail.

### O - Benutzerführung und Hilfe
Überspringbarer Einrichtungs-Assistent beim ersten Start (Mappe, Board und Spalten samt Erledigt-Spalte, Personen und Wochenstunden, Feiertage und Region, optional API-Token), dazu dezente Erklärungen im Betrieb. Globaler Hilfe-Knopf öffnet ein durchsuchbares Panel.

### P - Git-Schutz
Hooks unter `.githooks` (per `core.hooksPath` aktiv) prüfen vor Commit und Push und blockieren: Erwähnungen von KI-Assistenten oder deren Herstellern sowie Mitautoren-Angaben in Commits, typografische Sonderzeichen, falsche Umlaut-Ersetzungen in Doku sowie eingecheckte Geheimnisse und Schlüssel. Konfigurationsvorlagen mit Platzhaltern sind erlaubt (`.env.example`, `.env.muster`); echte `.env` und jegliche Produktivdaten bleiben ausgeschlossen.

### Q - Wiederkehrende Termine und Aufgaben
Serien mit einfachem Rhythmus (täglich, wöchentlich, monatlich), benutzerdefiniert (z.B. Mo und Mi, alle zwei Wochen, jeder erste Werktag) und als Sprechzeiten (feste Uhrzeit plus Dauer, etwa eine wiederkehrende Telefonkonferenz). Serien überspringen Feiertage und Urlaub oder verschieben sich. Automatisches Vorbuchen: kommende Instanzen werden im Voraus als Termine oder Karten angelegt, die geplante Zeit (Soll) wird vorgebucht, und sie sind wie Aufgaben per Timer (Start, Pause, Stopp) für die Ist-Zeit nutzbar. Erinnerungen erscheinen im eigenen UI (kein Browser-Dialog) und tauchen im Was-steht-an-Panel auf.

### R - Backup und Wiederherstellung
Gesichert werden Datenbank, Inhalte und Dokumente, das Berichts-Archiv und die Konfiguration (ohne Geheimnisse; der Vektor-Index bleibt außen vor, da neu aufbaubar). Modus: Sofort-Backup auf Knopfdruck und zeitgesteuerte Sicherung. Lokale Snapshots enthalten das Schema und die Version, sind also über Versionswechsel konsistent. Wiederherstellung mit Vorschau vor der Übernahme.

Umsetzung (Modul backup): Ein Snapshot ist eine ZIP-Datei mit fester Struktur (manifest.json mit Version, Zeit, Art, Schema und Datensatz-Zähler; db/pinnwand.db als konsistente Online-Kopie über die SQLite-Backup-Schnittstelle; berichte/ als Archiv-Kopie; konfig/ mit Vorlage und vorhandener .env). Snapshots liegen unter backend/data/backups (per .gitignore nie im Repo). Es gibt drei Arten: manuell, automatisch (beim Start höchstens einmal in 24 Stunden, Aufbewahrung der letzten zehn) und vor_wiederherstellung (Sicherheitsnetz, das vor jeder Wiederherstellung automatisch erzeugt wird). Die Metadaten-Tabelle backup_archiv liegt selbst in der Datenbank; da eine Wiederherstellung die Datenbank zurücksetzt, wird der Index danach aus den vorhandenen Dateien neu aufgebaut (selbstheilend, die Kennung steckt im Manifest). Die Wiederherstellung prüft die entpackte Datenbank per integrity_check, tauscht sie zwischen Anfragen aus (Verbindungen sind kurzlebig) und ersetzt das Berichts-Archiv. Die Vorschau stellt die Zähler des Snapshots dem aktuellen Stand gegenüber und warnt bei abweichender Version oder fehlenden Tabellen und Spalten.

### S - Jahreskalender (Anwesenheit, Ebenen, Halbtags-Regeln)
Ein klassischer Jahreskalender, umschaltbar zwischen 12-Monats-Gitter (über alle Mitarbeiter aggregiert, je Tag Zahl und Farbe) und Team-Matrix (Zeile je Person, Spalte je Tag). Vier gleichzeitig schaltbare Ebenen färben die Tage: Anwesenheit/Abwesenheit, Feiertage, geleistete Stunden (Heatmap) und Auslastung (Ist gegen Soll). Abwesenheit gibt es in mehreren Arten (Urlaub, Krankheit, Sonderurlaub, Unbezahlt, Homeoffice/Dienstreise), jede mit eigener Farbe und konfigurierbarer Anrechnung auf den Urlaubsanspruch; Homeoffice gilt als anwesend und reduziert das Soll nicht. Einträge werden direkt im Kalender per Klick/Ziehen gemacht.

Umsetzung: Neue Tabellen abwesenheit_typ (Farbe, reduziert_soll, anrechnen, anwesend) und tagesregel (Halbtags-/Sonderregeln). Die Soll-Logik liegt zentral in module/planung/kalender.py mit klarer Reduktions-Reihenfolge (Nicht-Arbeitstag, Feiertag je Bundesland, Sonderregel mit personenbezogenem Vorrang, Abwesenheit). Halbtags-Regeln: feste Jahrestage (z.B. 24.12./31.12.), bestimmte Wochentage und automatische Brückentage (Werktag zwischen Feiertag und Wochenende). Aggregations-Endpunkt GET /api/planung/kalender liefert je Person je Tag {soll, ist_sek, abwesenheit, feiertag, regel, status}; das Frontend (Ansicht jahreskalender im Auswertungs-Modul) verdichtet daraus das Gitter und nutzt es direkt für die Matrix. kapazitaet.py und die Berichte teilen sich dieselbe Tageslogik. Vereinfachung: ein Abwesenheits-Typ je Person und Tag.

## Phasenplan

0. Fundament: Konzept, Git-Guard für Vorlagen, Konfigurations- und Diensterkennungs-Schicht (optionale Dienste).
1. Agenten-API-Fundament und Erfassungs-Komfort (A, B): REST plus Auth, Scopes und Audit-Log; Zeiten nachtragen, Schnell-Erledigt, natürlichsprachig mit Vorschau, Retrieval und Tages-Briefing.
2. MCP-Server und OpenAI-Function-Schemas (A).
3. Semantische Suche und KI-Freifeld mit Mikrofon (C).
4. Markdown-Inhalte und Vorlesen (D, E).
5. Transkriptionen (F).
6. Wiederkehrende Termine und Aufgaben mit Erinnerungen (Q).
7. Personen, Wochenstunden, Urlaub und Feiertage (G).
8. Berichte, PDF, CSV und Archiv (H).
9. Flow-Ansicht, Was-steht-an, Detailansicht, UI-Persistenz, Routing und Benutzerführung (N, I, J, K, L, O).
10. Backup und Wiederherstellung (R).
11. Mehrere Security-Audit-Runden.
12. Personen-Identität, Personen-Sicht und optionaler Zugangsschutz: Wer-bist-du-Erstwahl, aktive Person filtert Kennzahlen (Stunden-Leiste, Tab-Titel), Eigentum an Zeiteinträgen (eigene editierbar, fremde nur lesbar), opt-in UI-Token.
13. Personenzuordnung: neue Karten bekommen automatisch ein Kürzel (aktive Identität, sonst zuletzt genutztes); Karten-Zuständig als echte Personen-Auswahl; Serien mit Teilnehmer-Auswahl, je Teilnehmer eine eigene Serie.
14. Fertig-Zeitfilter im Spaltenkopf erledigter Spalten (Heute, Gestern, Woche, Monat, Jahr, Alle). Datierung: Serien-/REKO-Karten nach ihrem festen geplanten Datum, alle anderen nach dem Erledigt-Zeitpunkt. Erfasste Zeiten sind reine Tages-Summen und zählen hier nicht.
15. Transkript-Verknüpfung mit Tickets: Marken verbinden eine Karte mit einer Sprechposition samt editierbarer Zusammenfassung (KI-Vorschlag als Vorschau); Öffnen springt im Transkript an die Position; Anheften direkt am Segment; Gegenrichtung über verknüpfte Tickets.
16. UI-Lückenschluss zu fertigen Backend-Fähigkeiten: Spalte als Erledigt-Spalte markieren, Karten-Cover-Farbe, Zeitbuchung auf beliebige Tage (im Karten-Detail und im Stundenzettel, dessen Woche dem gebuchten Tag folgt).

17. Zeitmodell sauber getrennt (siehe ZEITMODELL.md): Ticketzeit (Summe je Karte, read-only) und Arbeitszeit (Summe je Tag) speisen sich aus denselben datierten Eintraegen. Die undatierte Gesamt-Eingabe (die still auf heute buchte) entfaellt; im Karten-Detail werden die Zeiten eines Tickets nach Tagen aufgeschluesselt und je Tag korrigierbar.

18. WIP-Durchsetzung: das WIP-Limit einer Spalte wird sichtbar gemacht und weich durchgesetzt. Die Spalte zeigt das Erreichen des Limits (amber) und die Überschreitung (rot) an; schiebt ein Spaltenwechsel die Zielspalte über ihr Limit, erscheint eine Warnung. Bewusst kein harter Block, damit kurzfristiges Überschreiten möglich bleibt.

19. Mehrbenutzer und Anmeldung (siehe ROLLEN.md, LOGIN.md): Rollen (Admin/Mitarbeiter) je Person; optionale echte Anmeldung mit Name oder Kürzel und Passwort, serverseitige Durchsetzung der Admin-Bereiche, Aussperr-Schutz.

20. Fertige Karten: Fenster, Nachladen und Archiv (siehe FERTIG_ARCHIV.md): Erledigt-Spalten laden serverseitig gefiltert (Zeitfenster je Spalte) und gedeckelt, der Rest wird beim Scrollen nachgeladen - das Board wird nicht mehr geflutet. Fertige Karten älter als eine einstellbare Schwelle (Standard ein Jahr) wandern automatisch ins Archiv (eigene Archiv-Ansicht am Board, durchsuchbar); Deckelgröße und Schwelle sind in den Einstellungen editierbar. Reine Ladegrenze, kein Datenumbau; Auswertungen bleiben unberührt.

Querschnitt: strenge Versionierung (Patch je Änderung, Feature je Ausbaustufe), saubere Commits, README hält den Ist-Zustand.
