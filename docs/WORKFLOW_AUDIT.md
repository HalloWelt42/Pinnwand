# Workflow- und Trennungs-Audit

Dieses Dokument beschreibt die durchgängigen Abläufe (Pipelines) von Pinnwand und
hält fest, an welchen Stellen es zu Fehlern oder zu ungewollter Vermischung zwischen
mehreren Nutzern kommen kann. Es wird Ablauf für Ablauf geprüft.

Stand der Prüfung: 2026-06-22. Methodik: Code-Analyse plus Live-Prüfung gegen die
laufende Instanz (Backend localhost:8420). Schreibende Live-Tests liefen über ein
separates Test-Profil ("QS") in einer eigenen Mappe; der Ausgangsstand der echten
Werte wurde vorher gesichert und nach jedem Test exakt wiederhergestellt (netto kein
Einfluss auf die Echtdaten).

## 1. Daten- und Profil-Modell (zentrale Erkenntnis)

Pinnwand hat KEIN Profil-, Nutzer-, Login- oder Mandanten-Konzept. Es gibt keine
Anmeldung und keine Trennung von Daten oder Sichten nach Nutzer.

- Alle Inhalte liegen in EINER gemeinsamen SQLite-Datenbank (`backend/pinnwand.db`).
  Jeder Client, der das Backend erreicht, sieht und ändert alles.
- "Person" (Tabelle `person`: Name, Kürzel, Wochenstunden, Bundesland, Urlaub ...)
  ist nur ein Etikett. Karten verweisen über das Zuständigkeits-Kürzel der Karte auf
  eine Person. Eine Person ist kein abgeschotteter Account; sie filtert keine Sicht
  und schützt keine Daten.
- Frontend-Einstellungen liegen im `localStorage` des Browsers, also pro Gerät/
  Browser, nicht pro Nutzer. Betroffene Schlüssel:
  `pw_ui`, `pw_board_<id>`, `pw_jahreskalender`, `pw_stundenleiste`, `pw_serien_check`,
  `pw_serien_nachtrag_check`, `pw_termine_letzter_check`, `pw_tts_stimme`,
  `pw_tts_tempo`, `pw_onboarding_done`, `pw_admin_token`, `pw_wk_modus`.

Folgerung:

- Zwei Nutzer am selben Browser teilen sich alle Einstellungen (Theme, zuletzt
  geöffnetes Board, eingeklappte Spalten, Filter, Admin-Token usw.).
- Ein Nutzer an zwei Geräten hat unterschiedliche Einstellungen (keine Synchronisation).
- Daten sind grundsätzlich geteilt. Die Stunden-Übersicht, der Jahreskalender und die
  Berichte summieren über ALLE Personen. Eine Aktivität der einen Person verschiebt
  die Zahlen, die die andere sieht.

### 1.1 Live-Beweis der fehlenden Trennung

Vorgehen: Ausgangswerte der Stunden-Übersicht gesichert, dann ein zweites Profil
(Person "QS", 8 h/Werktag) in einer eigenen Mappe angelegt und dort 2 h auf den
heutigen Tag gebucht. Danach erneut gemessen:

| Zeitraum | Ist vorher | Ist nachher | Soll vorher | Soll nachher |
| --- | --- | --- | --- | --- |
| Heute | 14382 s | 21582 s (+2 h) | 28800 s | 57600 s (+8 h) |
| Woche | 14382 s | 21582 s (+2 h) | 144000 s | 288000 s (+8 h/Tag) |

Das zweite Profil hat die angezeigten Ist- UND Soll-Werte des ersten Nutzers sofort
verändert. Anschließend wurde das Test-Profil restlos entfernt und der Ausgangsstand
exakt wiederhergestellt (alle Differenzen 0, keine verwaisten Zeiteinträge).

Bewertung: Profile sind KEINE echte Trennung. Solange Auswertungen über alle Personen
summieren und es keine Nutzer-Sicht gibt, schneiden sich die Werte zwangsläufig.

### 1.2 Was echte Trennung bräuchte (Optionen)

1. Single-Tenant bewusst akzeptieren: eine Instanz = ein Nutzer/Team mit gemeinsamen
   Zahlen. Dann ist der Ist-Zustand korrekt, sollte aber klar dokumentiert sein.
2. Personen-Sicht: ein "aktive Person"-Schalter, der Stunden-Leiste, Kalender,
   Berichte und Was-steht-an auf diese Person filtert (Ist je Person über das
   Zuständigkeits-Kürzel der Karte, Soll je Person über die Kapazität). Daten
   blieben geteilt, aber die Zahlen wären pro Person sauber.
3. Echte Mandanten: pro Nutzer ein eigener Datenraum (eigene DB oder durchgängige
   `nutzer_id` an allen Tabellen) plus Anmeldung. Größter Umbau.

## 2. Pipelines im Detail

### 2.1 Zeiterfassung

Ablauf: Timer Start/Pause/Stopp (`kanban_kern/persistence.py: timer_start`,
`_pause_intern`) schreibt bei Pause/Stopp einen `zeiteintrag`; `_recompute_erfasst`
setzt `karte.erfasst_sek` = Summe der Einträge. Manuelle Korrektur über
`setze_erfasst` (eine idempotente Korrektur-Position). Direkteingabe im Detail.
Aggregation: `planung/kapazitaet.py: stunden_uebersicht` (Stunden-Leiste),
`planung/kalender.py` (Jahreskalender), `berichte/daten.py` (Berichte).

Geprüft:

- Nur eine Karte läuft gleichzeitig: `timer_start` pausiert alle anderen. In Ordnung.
- Löschen nimmt Zeiteinträge mit: in `loesche_karte`, `loesche_spalte`,
  `loesche_board` und `loesche_mappe` werden die zugehörigen `zeiteintrag` entfernt
  (Fix v0.39.1). Vorher entstanden Geister-Einträge, die die Summen aufblähten.
- Einheitliche Anzeige H:MM:SS im Detail (Fix v0.36.0), kein Sprung mehr beim Stopp.
- Hinweis Uhr-Differenz: die Live-Anzeige rechnet Browser-Uhr gegen `laeuft_seit`
  (Server-Zeit). Laufen Server und Browser auf verschiedenen Uhren auseinander, ist
  der LIVE-Wert verschoben; der gespeicherte Wert (Server-Differenz) bleibt korrekt.
  Auf einem Rechner (Backend + Browser) tritt das nicht auf.

### 2.2 Serien (wiederkehrende Aufgaben)

Ablauf: `serien/dienst.py: materialisiere` erzeugt Karten-Instanzen im Vorlauf-Zeitraum
(Wochenende/Feiertag/Urlaub werden ausgelassen; Dedup über `serie_id`+`serie_datum`).
`loesche` räumt Instanzen auf (Karten ohne Zeit weg, mit Zeit nur entkoppelt).
Frontend bucht einmal pro Tag vor (`serienTagesabgleich`). Nicht erfasste Vorkommen
vergangener Tage werden über `offene_nachtraege` ermittelt und im Overlay
`SerienErinnerung` zum Nachtragen angeboten (`nachtragen` bucht Soll-Stunden und
verschiebt die Karte in die Erledigt-Spalte).

Geprüft:

- Vorlauf 0 ist gültig (Fix v0.39.0): nur der heutige Tag entsteht, kein Voraus-Stapel.
- Löschen hinterlässt keine verwaisten Doppelkarten mehr (Fix v0.39.0).
- Nachtrag-Flow verifiziert: offener Eintrag wird gelistet, Nachtragen bucht die
  Stunden auf den fälligen Tag und erledigt die Karte.
- Bekannte Grenze: bei Vorlauf 0 entsteht die Tageskarte nur, wenn die App an dem Tag
  geöffnet wird. Komplett verpasste Tage werden nicht nachgebildet (kein Rückblick-
  Backfill wie bei Terminen).

### 2.3 Termine (Meetings mit Zeitgutschrift)

Ablauf: `termine` materialisiert Vorkommen bis gestern (Folgetag-Logik), das
`BestaetigungsOverlay` fragt einmal pro Tag nach (bestätigen/anpassen/ablehnen).
Bestätigte Minuten sind eine ZWEITE Ist-Quelle und werden additiv in
`planung/kalender._ist_sek_je_tag` und `berichte/daten` eingewoben; `zeiteintrag`
bleibt unberührt.

Geprüft / zu beachten:

- Termine und Aufgaben-Serien sind getrennte Welten. Würde dasselbe Thema sowohl als
  Termin als auch als Aufgaben-Serie geführt, zählte die Zeit doppelt (einmal als
  Termin-Minuten, einmal als Karten-Zeiteintrag). Pro Thema nur eine Form wählen.
- Bestätigte Termin-Minuten hängen am Kürzel; ohne Kürzel landet die Zeit nur in
  den Gesamtsummen, nicht in der Person.

### 2.4 Planung / Kapazität (Soll)

Ablauf: `planung/kalender.py` rechnet je Tag das Soll (Wochenstunden je Wochentag,
minus Wochenende, Feiertag je Bundesland, Sonderregeln/Brückentage, Abwesenheit
anteilig, Wochen-Override je ISO-Woche). `kapazitaet` und der Jahreskalender nutzen
dieselbe Engine.

Geprüft: Wochenende/Feiertag/Urlaub/Halbtag wurden in früheren Runden rechnerisch
bestätigt. Die Stunden-Übersicht summiert das Soll über alle Personen (siehe 1.1).

### 2.5 Backup / Reset

Ablauf: `backup/dienst.py` erzeugt ZIP-Snapshots (SQLite-Online-Backup), Restore mit
Integritätsprüfung und DB-Swap, automatischer Snapshot beim Start, Reset in den
Modi "beispiel" und "leer". Der Reset-Modus "leer" löscht eine fest verdrahtete
Tabellenliste.

Zu prüfen (im automatisierten Audit vertieft): ob die Tabellenliste für "leer"
wirklich alle Inhaltstabellen umfasst (u. a. `termin_serie`, `termin_instanz`,
`dokument`, `wochen_override`) und ob nach Reset keine Waisen bleiben.

### 2.6 Agenten-API / MCP

Die einzige Stelle mit clientweiser Unterscheidung: Bearer-Token mit Scopes
(read/write/admin), Audit-Log, akteursgebundene Idempotenz. Das trennt Rechte und
Protokoll je Client, aber NICHT die Daten: alle Akteure schreiben in dieselbe
gemeinsame Datenbank.

## 3. Befunde (adversativer Audit, 27 bestätigt)

Ergebnis eines mehrstufigen, read-only Audits (mehrere Prüfer je Pipeline, jeder
Befund unabhängig gegengeprüft). Viele Befunde sind aktuell latent (eine Person,
keine Termine, kein Override in den Echtdaten), aber strukturell real und greifen,
sobald das jeweilige Feature/der Mehrbenutzer-Fall genutzt wird.

### Trennung und Sicherheit

| Nr | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- |
| T1 | hoch | Keine Authentifizierung auf der Haupt-API: alle ~99 Routen (inkl. Schreiben, Löschen, Backup-Reset) sind ungeschützt; Token nur auf `/api/agent/*`. Jeder im Netz Erreichbare kann alles lesen, ändern und die DB zurücksetzen. | Mindestens an localhost binden (Standard) und so dokumentieren; bei LAN-Nutzung Auth/Reverse-Proxy davor. |
| T2 | hoch | Keine Nutzer-/Profil-Trennung; Auswertungen summieren über alle Personen (live belegt, 1.1). Zeit ist nicht stabil an eine Person gebunden: ein Wechsel der zugewiesenen Person rechnet rückwirkend alle Zeiten der Karte der neuen Person zu (Ist wird zur Laufzeit über das aktuelle Zuständigkeits-Kürzel berechnet). | Personen-Sicht (Option 2) oder bewusst Single-Tenant; Zeit beim Buchen an eine Person fixieren statt über die Karte abzuleiten. |
| T3 | mittel | Einstellungen liegen pro Browser (`localStorage`), nicht pro Nutzer; gemeinsamer Browser teilt Theme/Filter/Admin-Token, getrennte Geräte synchronisieren nicht. | Pro-Nutzer-Einstellungen erst mit einem Nutzer-Konzept; bis dahin dokumentieren. |
| T4 | mittel | Ein einziger globaler Timer: startet Client B einen Timer, wird der laufende Timer von Client A überall gestoppt. | Bei echtem Mehrbenutzer den Laufzustand pro Person führen. |

### Zeiterfassung

| Nr | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- |
| Z1 | hoch | Die Stunden-Leiste/Tab-Titel summiert ALLE Zeiteinträge; Jahreskalender und Berichte verwerfen still Einträge auf Karten OHNE zugewiesene Person. Dieselbe Zeit erscheint je Ansicht unterschiedlich (live: 4:00 h vs 3:09 h, Differenz 51 min). | Eine einzige Ist-Definition. Zeit ohne Person nicht stillschweigend verwerfen, sondern als Eimer "ohne Person" führen, damit Summe(je Person) == Gesamt. |
| Z2 | mittel | Folgefehler von Z1: Stundenzettel/Heatmap (alles) vs Jahreskalender-Stunden-Ebene (nur mit Person) widersprechen sich. | Mit Z1 zusammen lösen (gemeinsame Quelle/Definition). |
| Z3 | mittel | Live-Timer rechnet Browser-Uhr gegen Server-Zeit ohne Zeitzonen-Offset; bei abweichender Uhr/Zeitzone ist die laufende Anzeige verschoben (gespeicherter Wert bleibt korrekt). | Startzeit mit Offset/UTC ausliefern oder Restzeit serverseitig berechnen. |
| Z4 | mittel | Im Stundenzettel ist das Dauer-Feld mit gerundeten Minuten vorbelegt; Bearbeiten/Speichern schreibt die Rundung zurück und verliert die Sekunden (Sub-Minuten-Einträge fallen auf 0). | Sekundengenaues Format (H:MM:SS) im Feld nutzen oder nur bei echter Änderung speichern. |
| Z5 | niedrig | Timer über Mitternacht schreibt die gesamte Dauer dem Starttag gut; tagesgenaue Auswertung beider Tage wird ungenau. | An der Tagesgrenze splitten oder dokumentieren. |

### Serien und Termine

| Nr | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- |
| S1 | hoch | Doppelzählung: wird dasselbe Thema sowohl als Aufgaben-Serie (Zeiteintrag) als auch als bestätigter Termin geführt, zählt die Zeit in Stunden-Leiste/Kalender/Berichten doppelt - ohne UI-Hinweis. | Termin an Karte/Serie koppeln und entdoppeln, oder im UI klar trennen + Konsistenz-Warnung. |
| S2 | mittel | Serien-Dedup nur applikativ (Check und Insert in getrennten Transaktionen/Verbindungen), kein DB-UNIQUE wie bei Terminen; bei Nebenläufigkeit sind Geister-/Doppelkarten möglich. | UNIQUE-Index (serie_id, serie_datum) als Teilindex + INSERT OR IGNORE bzw. Check+Insert in einer Transaktion. |
| S3 | mittel | Bei Vorlauf 0 entsteht nur die heutige Karte; komplett verpasste Tage werden nie nachgebildet (kein Rückblick-Backfill wie bei Terminen). | Ab letztem erzeugten Datum (bzw. Start) materialisieren oder Rückblick-Parameter einführen. |
| S4 | mittel | Tagesabgleich/Bestätigung sind über gerätelokale `localStorage`-Marken gegated; ohne serverseitigen Tages-Trigger hängt es vom zuerst geöffneten Gerät ab, ob Vorbuchung/Nachtrag/Bestätigung laufen. | Den "einmal pro Tag"-Lauf serverseitig führen (Marker je Tag/Scheduler). |
| S5 | niedrig | Kürzel-Bezug (Urlaub-Skip, Termin-Gutschrift) ist nur ein loser String-Vergleich ohne Validierung; Tippfehler/Umbenennen entkoppelt still. | Kürzel beim Anlegen validieren oder über Personen-ID referenzieren. |
| S6 | niedrig | "Nachtragen" auf einem Board ohne Erledigt-Spalte bucht die Zeit, lässt die Karte aber in einer aktiven Spalte stehen. | In jedem Fall in einen erledigten Zustand bringen bzw. Filter angleichen. |

### Planung und Kapazität

| Nr | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- |
| P1 | mittel | Brückentag-Erkennung ignoriert Wochen-Override (prüft Standard-Wochenstunden statt der Override-Werte); Soll an Brückentagen in Override-Wochen falsch. | Wirksame Wochenstunden je Tag aus dem Override beziehen (gemeinsamer Tages-Helfer). |
| P2 | mittel | Regionale (Bundesland-)Feiertage werden nie automatisch geladen (nur bundesweite); für Personen mit Bundesland fehlen Feiertage, Soll wird zu hoch. | Beim Setzen des Bundeslands die regionalen Feiertage je Jahr nachladen (Vorschau vor Anwenden). |
| P3 | niedrig | Stunden-Leiste summiert Soll auch über INAKTIVE Personen, Jahreskalender nur über aktive; Soll-Werte weichen ab, sobald jemand deaktiviert ist. | In der Soll-Summe nur aktive Personen zählen. |
| P4 | niedrig | Urlaubskonto zählt rohe Tage, auch wenn der Tag (Feiertag/frei) gar kein Soll hatte; verbleibendes Kontingent kann zu niedrig sein. | Genommen-Tage an die tatsächliche Soll-Wirkung koppeln. |
| P5 | niedrig | Wochen-Override: Lookup per ISO-Jahr, Eingabe als freies Kalenderjahr; in Grenzwochen (KW1/52/53) greift der Override am falschen Zeitraum. | ISO-Jahr/-Woche durchgängig erzwingen (KW aus Datum ableiten). |
| P6 | niedrig | Halbtags-Regel und Urlaubsanteil multiplizieren sich: voller Urlaub auf einem Halbtag (Heiligabend/Silvester) kostet 1,0 Konto-Tag bei halber Soll-Wirkung. | Konto-Anteil an effektive Soll-Reduktion koppeln oder im UI halben Urlaub vorschlagen. |

### Backup/Reset und Agenten-API

| Nr | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- |
| R1 | mittel | Reset-Modus "beispiel" löscht die Berichts-Dateien auf der Platte nicht (nur die DB-Einträge); verwaiste Dateien bleiben und landen in späteren Snapshots. | Beim Beispiel-Reset die Dateien unter `data/berichte` mitlöschen (wie bei "leer"). |
| R2 | niedrig | Reset-Modus "leer" lässt personenspezifische `tagesregel`-Zeilen stehen (keine DB-Referenzintegrität); latente Waisen. | `tagesregel` in die Leeren-Liste aufnehmen bzw. Fremdschlüssel/Cascade. |
| R3 | niedrig | Snapshot enthält die komplette `agent_token`/`agent_audit`-Tabelle, obwohl er als "teilbar ohne Geheimnisse" deklariert ist (Hashes, aber Scopes und Audit-Details im Klartext). | Beim Snapshot ausschließen/maskieren oder den Anspruch streichen. |
| A1 | hoch | MCP-Server umgeht Token/Scopes/Akteur komplett: bei aktivem `PINNWAND_MCP` kann jeder, der `/mcp` erreicht, ohne Token mit festem read+write schreiben (Standard: aus, nur localhost). | MCP an Token/Scope binden oder klar als ungeschützten Vollzugriff dokumentieren und strikt localhost. |
| A2 | mittel | Token-Akteure liefern keine Daten-Trennung - alle schreiben in dieselbe globale DB; read sieht den gesamten Bestand. | Owner-Spalte + Filter, oder dokumentieren, dass Token nur Rechte (nicht Datentrennung) bieten. |
| A3 | niedrig | Konfig-Bootstrap-Token = statisches Master-Secret mit Vollzugriff, nicht über die normale Verwaltung widerrufbar und in der Liste unsichtbar. | Nach Anlage eines regulären Admin-Tokens entfernen; im Audit kennzeichnen. |
| A4 | niedrig | REST-Lese-Endpunkte `/suche` und `/briefing` protokollieren nicht (tools/execute und MCP dagegen schon) - Audit-Lücke für diese zwei Routen. | Auch diese Lesezugriffe protokollieren. |
| A5 | niedrig | Bootstrap-Sackgasse: ohne `PINNWAND_AGENT_TOKEN` ist über die UI kein erstes Admin-Token anlegbar. | Einmal-Setup (erster Token erlaubt, solange leer) oder kleines CLI-Skript. |

Zusätzlich (eigener Live-Test): `POST /api/kanban/karten` prüft `board_id`/`spalte`
nicht; leere/ungültige Werte erzeugen eine Waisen-Karte ohne Board (Nr K1, mittel).

## 4. Empfehlung (priorisiert)

1. Grundsatzentscheidung Mehrbenutzung: bewusst Single-Tenant ODER Personen-Sicht
   einbauen (Filter auf aktive Person in Stunden-Leiste, Kalender, Berichten,
   Was-steht-an). Das ist der wirksamste Schritt gegen das Schneiden der Werte und
   adressiert T2 und Z1 zugleich.
2. Konsistente Ist-Definition (Z1/Z2): Zeit ohne Person nicht still verwerfen, damit
   alle Ansichten dieselbe Summe zeigen. Kleiner Eingriff, hoher Vertrauensgewinn.
3. Schnelle, risikoarme Korrekturen: K1 (Board-/Spalten-Prüfung beim Anlegen),
   P3 (nur aktive Personen im Gesamt-Soll), Z4 (sekundengenaues Dauer-Feld),
   R1 (Berichts-Dateien beim Beispiel-Reset mitlöschen), S2 (UNIQUE-Index für Serien).
4. Bei Mehrbenutzung/Netzbetrieb: Authentifizierung (T1) und MCP-Absicherung (A1);
   solange localhost, akzeptiert und dokumentiert.
5. Latente Feature-Fehler dokumentieren oder beheben, sobald das Feature genutzt
   wird: P1 (Brückentag+Override), P2 (regionale Feiertage), S1 (Doppelzählung
   Serie/Termin), S3 (Backfill), P4/P5/P6 (Urlaubs-/Override-Feinheiten).

Hinweis: Diese Befunde sind eine Bestandsaufnahme, keine akute Störung - in den
aktuellen Echtdaten (eine Person, keine Termine, kein Override) ist der Betrieb
stimmig. Sie werden relevant, sobald mehrere Nutzer arbeiten oder die genannten
Funktionen aktiv genutzt werden.
