# Gesamt-Audit: Workflow, Datenhaltung, Rechte, Struktur, Komfort

Stand v0.67.1. Methode: 10 parallele Prüf-Dimensionen plus Benchmark-Vorrecherche;
jeder hoch-Befund von zwei unabhängigen Skeptikern, jeder mittel-Befund von einem
Skeptiker am Code gegengeprüft. Ergebnis: 128 Befunde, davon 76 verifiziert und
**alle 76 bestätigt, 0 widerlegt** (52 niedrig-Befunde unverifiziert markiert).
Reine Analyse, keine Code-Änderung. Alle Ortsangaben Datei:Zeile beziehen sich auf
v0.67.1 (Commit 8541f46).

## Gesamtbild

Der Kern trägt: Das Zeitmodell (zeiteintrag als einzige Wahrheit, Mitternachts-
Zerlegung, Konsolidierung) ist solide und die Live-DB ist aktuell vollständig
konsistent (0 Waisen, erfasst_sek stimmt überall mit der Summe überein). Die
Modularchitektur, das Fenster-/Archiv-Modell der Erledigt-Spalten, der
Aussperr-Schutz und das Backup-Modul sind gut gebaut. Die Kapazitäts- und
Planungsrechnung (Soll aus Wochenstunden, Urlaub, Feiertagen, Halbtags-Regeln)
kann mehr als viele etablierte Boards.

Die Probleme folgen fast alle **fünf roten Fäden** - einzelne Symptome gibt es
viele, aber die Wurzeln sind wenige:

1. **Zwei Wege, eine Regel fehlt.** Regeln (Move-Logik, Zeit-Eigentum,
   Projekt-Scoping) sind nur am jeweils "offiziellen" Endpunkt durchgesetzt;
   Nebenwege umgehen sie: Statuswechsel im Drawer umgeht verschiebe_karte, Timer/
   Schnell-Erfassen/Serien-Nachtrag umgehen das Zeit-Eigentum, fast alle Karten-/
   Board-/Mappen-Mutationen und die Lese-Nebenwege umgehen das Mitglieder-Scoping.
2. **Kürzel als Identität.** Das Zuständigkeits-Kürzel der Karte ist ein freier String ohne
   Eindeutigkeit und ohne Umbenennungs-Kaskade; Eigentum, Auswertungen und
   Projekt-Aufschlüsselung hängen am Live-String-Vergleich. Umbenennung oder
   Karten-Übergabe verschieben rückwirkend ganze Stundenberge.
3. **Löschen ist gefährlicher als es aussieht.** Undo ist teils nur scheinbar
   (Karten-Undo verliert Zeiten/Dokumente/Notizen; Spalten-Undo nur die sichtbare
   Fensterseite), teils fehlt es ganz (Zeiteinträge, Person, Mappe), und mehrere
   Löschkaskaden hinterlassen Waisen (mappe_mitglied, Dokumente, Transkript-Marken,
   Serien).
4. **Mehrbenutzer-Realität hinkt der Rechte-Schicht hinterher.** Globaler
   Ein-Timer über alle Personen, kein Sync zwischen Browsern, Ganz-Listen-PATCH
   überschreibt fremde Änderungen, Kommentare tragen den falschen Autor,
   Termin-Bestätigung kennt kein Eigentum.
5. **Stilles Scheitern im Frontend.** Viele mutierende Aktionen laufen ohne catch;
   "gespeichert" erscheint zeitgesteuert auch bei Fehlschlag; Netzfehler sehen aus
   wie "keine Daten"; vier fetch-Nebenpfade verlieren die Auth-Header (Berichte,
   Transkription, Vorlesen, Downloads brechen bei aktivem Login).

---

## A. Die wichtigsten bestätigten Brüche (hoch)

### Workflow / Karten-Lebenszyklus

1. **Statuswechsel im Karten-Detail umgeht verschiebe_karte**
   (CardDrawer.svelte:181, Board.svelte:376, persistence.py:853). Nur der
   Move-Endpunkt setzt bewegt_am, zieht Gruppenmitglieder mit und kompaktiert.
   Über das Status-Select bekommt die Karte ein falsches Abschlussdatum
   (bewegt_am bleibt alt), verschwindet sofort aus der Ansicht (Erledigt-Spalten
   speisen sich nur aus fertigDaten, das nicht nachgeladen wird) und die Gruppe
   bleibt zurück. Widerspricht KARTEN_DETAIL.md ("greift unabhängig davon, wie die
   Karte verschoben wurde"). Betrifft auch den einzigen Rückhol-Weg aus dem Archiv.
2. **Erledigt-Spalte löschen vernichtet den ganzen Fertig-Bestand, Undo bringt nur
   die geladene Fensterseite zurück** (Board.svelte:434, persistence.py:1483).
   400 fertige Karten samt Zeiten weg, Undo stellt die 3 sichtbaren wieder her -
   als normale Spalte ohne erledigt-Flag. Kein Bestätigungsdialog.
3. **Karten-Undo ist unvollständig** (restore.ts:6, persistence.py:887). Zeiten,
   Dokumente, Notizen, Schätzung, Typ, Gruppen- und Transkript-Verknüpfung gehen
   verloren; der Toast suggeriert vollständige Wiederherstellung. Projekt-Ist
   schrumpft still.

### Zeiterfassung / Mehrbenutzer

4. **Globaler Ein-Timer:** timer_start pausiert ALLE laufenden Karten ohne
   Personen-Bezug (persistence.py:1090). Startet Person B irgendeinen Timer, wird
   Person A still gestoppt - und As Leiste zählt optisch weiter (kein Polling von
   /laufend), alles danach geht verloren.
5. **Kürzel-Umbenennung kappt Eigentum und Auswertungen** (planung/api.py:69,
   persistence.py:285). Die Kürzel-Felder an Karte, Serie und Termin-Serie
   und mappe.owner werden nicht mitgezogen: persönliches Ist fällt auf 0, die
   Person darf ihre eigenen alten Zeiten nicht mehr bearbeiten. Zusätzlich:
   Kürzel-Eindeutigkeit wird nirgends erzwungen (zweites "MP" = verschmolzene
   Identitäten).
6. **Karten-Übergabe bucht die gesamte Zeithistorie um** (kapazitaet.py:44).
   zeiteintrag trägt keine Person; A arbeitet 10 h, Übergabe an B, B sieht 12 h,
   A sieht 0. Empfohlener Kern-Fix: Kürzel beim Buchen am Eintrag snapshotten.

### Rechte / Scoping

7. **Mappe ändern/löschen ohne jede Prüfung** (kanban_kern/api.py:118-132).
   Einzige Mappen-Endpunkte ohne Akteur: ein Mitarbeiter kann ein für ihn
   unsichtbares Projekt samt fremder Zeiten löschen (204) oder Budget/Status/Titel
   ändern - während ein einzelner fremder Zeiteintrag korrekt 403 liefert. UI
   bietet Umbenennen/Löschen zudem jedem an.
8. **Projekt-Scoping gilt nur für vier Lese-Endpunkte** - alle Mutationen
   (Karten, Spalten, Boards, Dokumente) und die Lese-Nebenwege (GET /zeiteintraege
   liefert alles inkl. Mappen-Titel, /heute, /suche, fertige/archiv, /laufend,
   Berichte) ignorieren die Mitgliedschaft. Das Sichtbarkeitsversprechen gilt
   praktisch nur für die Board-Navigation.
9. **Zeit-Eigentum über Nebenwege umgehbar:** timer/start, timer/pause,
   schnell-erfassen und serien/nachtragen buchen ohne Akteur-Prüfung auf fremde
   Karten - dieselbe Buchung über POST /zeiteintraege liefert 403.
10. **Termin-Bestätigung ohne Eigentum** (termine/api.py:81-99,
    BestaetigungsOverlay). Das Overlay lädt die schwebenden Instanzen ALLER
    Personen; "Alle wie geplant bestätigen" schreibt fremden Personen Ist-Zeit
    gut (zweite Ist-Quelle in Planung/Berichten).

### Personen / Serien

11. **Person löschen hinterlässt mappe_mitglied-Waisen** (planung/persistence.py:301,
    kanban_kern/persistence.py:284). War die Person einziges Mitglied, bleibt das
    Projekt für alle Mitarbeiter dauerhaft unsichtbar, und der Mitglieder-Dialog
    kann den Zustand weder anzeigen noch reparieren (Waise wird nicht gerendert).
    Außerdem verwaisen wochen_override und tagesregel.
12. **Person löschen ohne Rückfrage** (Planung.svelte:244): ein Fehlklick aufs
    Papierkorb-Icon vernichtet Person + Urlaubshistorie + Sitzungen ohne Modal
    und ohne Undo.
13. **Serien ohne Startdatum kollabieren zu täglichen Karten**
    (wiederholung.py:79, Serien-UI hat kein Startfeld): der Phasen-Anker wandert
    mit jedem Vorbuchungslauf; "alle 2 Tage" wird nach kurzer Zeit täglich,
    "wöchentlich ohne Wochentag" sofort täglich. Karten-Spam plus aufgeblähtes
    Soll in den Projektzahlen.
14. **Serie löschen vernichtet per Drag erledigte Instanzen ohne Zeiteintrag**
    (serien/dienst.py:102): nur hat_zeit schützt; erledigte Karten mit Kommentaren/
    Checklisten aber ohne Timer gelten als "reine Vorbuchung" und werden mitsamt
    Dokumenten gelöscht - der Erledigt-Verlauf des Boards ist weg.
15. **Board-/Mappen-Löschung lässt Serien zurück, die Geisterkarten erzeugen**
    (serien/dienst.py:19, persistence.py:794): _zielspalte gibt die tote
    spalte_id ungeprüft zurück, erstelle_karte prüft das Board nicht; die Karten
    erscheinen als überfällig in Heute, sind aber auf keinem Board erreichbar.

### Frontend-Verlässlichkeit

16. **Vier fetch-Nebenpfade ohne Auth-Header** (api.ts:379, 511, 565 + zwei
    Download-URLs als nacktes href): bei aktivem Login brechen Berichte erzeugen,
    Transkription, Vorlesen und die Downloads mit 401 - Meldung nur generisch.
17. **Speichern kann still scheitern, "gespeichert" lügt** (MarkdownFeld.svelte:53,
    Board.svelte:376, CardDrawer onchange-Handler, DokumentVerwaltung.svelte:48):
    Fehler enden als unbehandelte Rejections ohne Toast; der gespeichert-Chip
    erscheint rein zeitgesteuert. Ein 30-Minuten-Dokumenttext kann komplett
    verloren gehen, wenn das Backend beim letzten Autosave weg ist.
18. **Kommentare tragen den falschen Autor** (Board.svelte:380): Autor ist immer
    das Kürzel des Karten-Zuständigen, nicht der angemeldete Bediener - die
    Historie zeigt systematisch falsche Urheber.
19. **Zeiteinträge löschen ohne Rückfrage und ohne Undo** (Zeiterfassung.svelte:56,
    Zeiten.svelte:81): ausgerechnet die abrechnungsrelevanten Daten haben als
    einzige weder Confirm noch Undo-Toast, obwohl beide Muster im Projekt existieren.

---

## B. Mittlere Brüche (bestätigt, Auswahl nach Gewicht)

- **Idee-Gating löchrig:** Laufender Timer überlebt den Wechsel zu "Idee" und
  bucht weiter (api.py:308/357); Schnell-Erfassen, Agent-API und POST
  /zeiteintraege buchen auf Ideentickets, wo die Zeit im Detail unsichtbar ist.
- **Gelöschte Serien-Instanz wird wieder angelegt** (serien/dienst.py:57):
  Löschen der heutigen Serienkarte setzt letztes_serie_datum zurück; der nächste
  Lauf (anderer Browser, Neustart) legt sie neu an. Es fehlt ein Auslass-Marker.
- **Serien-Pause räumt nicht auf, Reaktivieren bucht die Pause nach**
  (dienst.py:53): Vorbuchungen bleiben stehen; nach Reaktivierung materialisiert
  der Backfill rückwirkend die gesamte Pausenzeit.
- **Serien-PATCH wirkt nicht auf bestehende Instanzen** (termine/persistence.py:114):
  Personenwechsel an der Termin-Serie lässt schwebende Instanzen auf dem alten
  Kürzel - Zeit wird weiter der falschen Person gutgeschrieben.
- **Monatstag 29/30/31 fällt in kürzeren Monaten still aus** (wiederholung.py:48):
  "monatlich am 31." erzeugt in 5 von 12 Monaten keine Karte.
- **Nachträglicher Urlaub räumt Vorbuchungen nicht** (dienst.py:69): Karten
  bleiben die Urlaubswoche stehen; danach fragt der Nachtrag-Dialog jeden
  Urlaubstag ab.
- **Erstes Mitglied kippt die Mappe still auf "beschränkt"** (MappenMitglieder):
  alle anderen verlieren ohne Warnung den Zugriff; und ein Mitarbeiter kann sein
  selbst angelegtes Projekt niemandem freigeben (Mitglieder-Verwaltung admin-only).
- **Mitgliedschaftsverlust bei offener Ansicht:** unbehandelte 403, Board friert
  ein, Timer läuft unsichtbar weiter (Board.svelte:181).
- **Kein Browser-Sync + Ganz-Listen-PATCH:** Checkliste/Labels überschreiben
  fremde Änderungen unbemerkt (CardDrawer:105, persistence.py:853).
- **Restore/Reset tauschen die DB im laufenden Betrieb ohne Schreibsperre**
  (backup/dienst.py:352) und die Oberfläche lädt danach nicht neu
  (Einstellungen.svelte:103) - Arbeiten auf dem alten Stand gegen die neue DB.
- **Ticketzeit direkt setzen ist nicht atomar** (Zeiterfassung.svelte:73):
  Lösch-Schleife einzelner Requests; bricht einer weg, ist die Korrektur halb.
- **409 beim Spalten-Löschen wird verschluckt, Undo erzeugt dann Duplikate**
  (Board.svelte:434, api.py:508).
- **Netz-/Serverfehler sehen aus wie "keine Daten"** (catch -> leere Liste,
  z. B. Zeiterfassung.svelte:36).
- **Urlaubskonto nur für das laufende Jahr korrekt** (persistence.py:369):
  "aus Vorjahr" ignoriert den alten Übertrag; Rückblick auf Vorjahre liefert
  heutige Stammwerte.
- **Person deaktivieren existiert nur per API** (kein UI-Schalter) und inaktive
  Personen werden inkonsistent gefiltert (Drawer bietet sie an, Leiste nicht).
- **Urlaub-Eintragen prüft rohe Wochenstunden** statt der Tageslogik
  (api.py:133): Overrides/Tagesregeln werden beim Überspringen ignoriert.
- **Agent-API und MCP als Seitentüren:** eigener Token-Kreis ignoriert Rollen,
  Mitgliedschaften und Zeit-Eigentum; bei aktivem Login spricht /mcp ohne
  jede Anmeldung (fester Akteur "mcp", read+write). Mindestens dokumentieren.
- **Eingaben wie "90m" werden zu 90 Stunden** (timer.svelte.ts:76, parseFloat).
- **UTC-Datum im Serien-Tagesabgleich** (App.svelte:285): nach Mitternacht bis
  zu 2 h verspätete Vorbuchung; lokaler ymd-Helfer existiert bereits.

### Code-Struktur (bestätigt)

- **kanban_kern/persistence.py (2536 LOC, 11 Themen)** und **App.svelte (992 LOC:
  Routing + Gating + Mappen-Baum + Drawer + 8 Modal-Flags)** sind God-Files;
  **Planung.svelte** bündelt sechs Fachbereiche.
- **api.ts/types.ts als Ein-Topf** für 12 Module plus doppelt gepflegte
  Re-Export-Liste (50 Typnamen an zwei Stellen).
- **Manifest-Abstraktion entwertet:** REIHENFOLGE, GLOBALE_ANSICHTEN,
  ADMIN_ANSICHTEN hart in App.svelte statt als Manifest-Felder - neue Module
  landen falsch, bis man drei Listen editiert.
- **Rollen-Ableitung doppelt** (App.svelte:80 vs. Planung.svelte:25) und
  **Personen-Laden 10x ad hoc**; Wochentags-Arrays 7x kopiert (3x in einer Datei);
  Modal-Muster ca. 8x neu implementiert.
- **Tote Abstraktion:** cardFields/mappeTabs/commands ohne Konsument.
- **Kohäsion auswertung/berichte/projekte/heute: trägt - nicht zusammenlegen.**

### Datenmodell (bestätigt)

- **Keine FOREIGN KEYs, PRAGMA foreign_keys aus, nur 5 Indizes** - alle Kaskaden
  handgeführt; genau dort sind die Waisen-Lücken entstanden. Heiße Pfade ohne
  Index: zeiteintrag(karte_id), zeiteintrag(mappe_id, datum), karte(board_id, spalte).
- **rolle kann NULL werden** (erstelle_person setzt rolle nicht; TST in der
  Live-DB ist der Beleg). Serverseitig normalisiert (kein Rechte-Bruch), aber
  die Quelle gehört geschlossen.
- 8-Hex-IDs (32 Bit) ohne Kollisionsbehandlung; wachsende Neben-Tabellen
  (sitzung, agent_audit, zeiteintrag_roh_backup) ohne Aufräumpfad.
- **Positiv:** Live-DB waisenfrei, Denormalisierung zeiteintrag.board_id/mappe_id
  konsistent (Karten wechseln konstruktiv nie das Board), Backup-Modul mit
  Online-Backup-API, integrity_check und Token-Scrubbing vorbildlich.

---

## C. Bewusst so lassen (geprüft und für sinnvoll befunden)

- Weiches WIP-Limit (kein harter Block) - dokumentierte Absicht.
- Projektstatus "pausiert/abgeschlossen" als reine Anzeige.
- Gruppen-Mitzug beim Erledigen (nach Fix von Befund A1 gilt er dann überall).
- Serien-/REKO-Abschluss = festes Fälligkeitsdatum (FERTIG_ARCHIV.md).
- Projekt-Ist (nur zeiteintrag) vs. Stunden-Ist (plus bestätigte Termine) -
  dokumentiert verschieden; höchstens Fußnote "ohne Termine" in der Projekte-Ansicht.
- Login AUS = alles offen (lokal-first); bei LAN-Betrieb UI-Token setzen.
- Zwei Konfig-Tabellen (kanban_einstellung/app_einstellung) = Modul-Eigentum.
- 31-Tage-Backfill-Deckel und 14-Tage-Termin-Rückblick.
- Geteilte Gruppen-Zeit als reine Anzeigeschicht (zählt genau einmal).
- Drawer-Bedienmuster (Inline-Edit, Auto-Speichern) - nur das Feedback absichern.
- Kein Zusammenlegen der Ansichts-Module.

---

## D. Benchmark: Was ein Ticket-Board leisten kann

Fähigkeiten-Landkarte (generisch) gegen den Pinnwand-Stand:

| Bereich | Stand |
|---|---|
| Board-Mechanik (WIP, Erledigt-Politik, Aging, Archiv) | gut; keine Swimlanes (bewusst) |
| Karten-Modell (Checkliste, Labels, Prio, Schätzung, Dokumente) | solide; keine Anhänge, keine Vorlagen, keine benutzerdef. Felder |
| Automation (Serien, Termine, Auto-Archiv) | stark bei Wiederholung; bewusst keine freie Regel-Engine |
| Zusammenarbeit (Kommentare, Benachrichtigung, Aktivitätslog, Live-Sync) | **schwächster Bereich**: keine Erwähnungen, kein Karten-Aktivitätslog, kein Sync |
| Ansichten (Board, Heute, Projekte, Kalender, Berichte) | eigenwillig gut; keine Tabellen-/Fälligkeits-Kalender-Sicht der Karten |
| Planung/Kapazität (Soll aus Wochenstunden/Urlaub/Feiertagen) | über Marktniveau für die Größe |
| Zeiterfassung (Timer, SSOT, taggenau, geteilte Gruppen) | Kernstärke; Grenze: keine Person am Eintrag |
| Suche/Filter | gut; keine benannten gespeicherten Filter, kein Personen-Filter |
| API/Export (Agenten-API, MCP, Berichte, Backup) | überdurchschnittlich; kein selektiver Board-Export |
| Rollen/Verwaltung | passgenau fürs Kleinteam; kein allgemeines Änderungs-Audit |

**Fehlt und lohnt** (priorisiert, Kontext lokal-first / 1-5 Nutzer):

| Aufwand | Feature | Kernnutzen |
|---|---|---|
| mittel | Aktivitätsprotokoll je Karte | Nachvollziehbarkeit im Mehrbenutzer-Betrieb (größte Lücke) |
| mittel | Leichtes Live-Update (Polling/Änderungszähler) | zwei Browser sehen denselben Stand, keine verlorenen Updates |
| mittel | Listen-/Tabellenansicht (sortierbar) | Aufräumen/Massenpflege; Backend liefert schon alles |
| klein | Fälligkeits-Kalender (Fällig-Datum der Karten + Termine) | "Was ist wann fällig" jenseits der Heute-Liste |
| mittel | Benachrichtigungs-Glocke (lokal, quittierbar) | zugewiesen/kommentiert/überfällig ohne Zuruf |
| mittel | Datei-Anhänge an Karten (im Backup enthalten) | Foto/PDF-Fälle im Familienalltag |
| klein | Benannte gespeicherte Filter je Board | wiederkehrende Blickwinkel |
| klein | Karten-Vorlagen | strukturelle Wiederholung (Checkliste vorbelegt) |
| klein | Blockiert-Flag mit Grund | 90 % des entfernten Abhängigkeits-Graphen, ohne Komplexität |
| klein | Selektiver Board-/Mappen-Export (JSON) | Weitergabe/Archivierung einzelner Projekte |

**Zu streng umgesetzt:**

- Zeit-Eigentum ausschließlich über das Zuständigkeits-Kürzel der Karte: zwei Personen können auf
  derselben Karte keine getrennten Zeiten erfassen -> optionale Kürzel-Spalte am
  zeiteintrag (Akteur beim Buchen, Fallback ist das Karten-Kürzel).
- Aging-Schwellen hart 4/8 Tage -> zwei Werte in kanban_einstellung.
- Mitglieder-Verwaltung strikt admin-only -> Ersteller darf die Mitglieder der
  eigenen Mappe pflegen (Owner-Regel).
- Termin-Serien genau eine Person -> Teilnehmerliste mit Fanout wie bei Serien.
- Board-Filter kennt keine Person -> Zuständig-Filter/klickbare Avatare
  ("nur meine" ist der häufigste Filterwunsch überhaupt).

**Bewusst weglassen** (deckt sich mit den Hausprinzipien): Swimlanes, freie
Automations-Engine (widerspricht "Vorschau vor Anwenden"), SLA/Eskalation/
Kennzahlen-Theater, echte Karten-Hierarchie mit Roll-up, Sprints/Velocity/
Burndown, feingranulare Rechte/Mandanten, externe Benachrichtigungskanäle
(Mail/Push), benutzerdefinierte Feld-Baukästen, Echtzeit-Koop-Editing (CRDT).

---

## E. Roadmap-Vorschlag (gestuft, jede Stufe eigenständig lieferbar)

### Stufe 1 - Verlässlichkeit zuerst (Quick-Wins, höchste Alltagswirkung)

1. Statuswechsel im Drawer über verschiebe_karte leiten + danach neu laden (A1).
2. Zentrale Frontend-Fehlerbehandlung: Fehler-Hook in hole() (Toast mit
   Server-detail), mitToast-Wrapper für Mutationen, "gespeichert" nur nach
   erfolgreichem Promise, Fehlerzustand statt leerer Listen (A17, B).
3. Die vier fetch-Nebenpfade auf hole()/Header-Fabrik umstellen; Downloads per
   Blob (A16).
4. Kürzel härten: UNIQUE (nocase) + 409, Umbenennungs-Kaskade auf
   Karten-/Serien-/Termin-Kürzel und mappe.owner, rolle-Default +
   NULL-Migration (A5, Datenmodell).
5. Lösch-Schutz: Bestätigungs-Modal für Person und Erledigt-Spalte (mit
   Kartenzahl), Undo-Toast für Zeiteinträge, ehrlicher Undo-Text bei Karten;
   Kaskaden-Lücken schließen (mappe_mitglied/wochen_override/tagesregel bei
   Person; Dokumente bei Spalte; Serien + Marken + Suchindex bei Board/Mappe)
   über eine gemeinsame Aufräum-Hilfsfunktion je Karten-Id-Menge (A2, A3, A11,
   A12, A15).

### Stufe 2 - Mehrbenutzer konsequent machen

6. Timer je Person (Start pausiert nur eigene Karten) + /laufend-Abgleich beim
   Board-Laden oder leichtes Polling (A4).
7. Ein wiederverwendbarer Scoping-/Eigentums-Helfer (karte_id/board_id/mappe_id
   -> mappe_sichtbar_fuer bzw. darf_zeiteintrag_bearbeiten) und damit: Mappen-
   PATCH/DELETE, Karten-/Board-/Spalten-Mutationen, timer/start+pause,
   schnell-erfassen, serien/nachtragen, Termin-Bestätigung (self-or-admin),
   GET /zeiteintraege + Suche + Heute scopen; ROLLEN.md danach ehrlich
   aktualisieren (A7-A10).
8. Kommentar-Autor = angemeldete Identität (A18).
9. Kürzel-Snapshot am zeiteintrag (Spalte kuerzel, beim Buchen gefüllt,
   Auswertungen/Rechte bevorzugen den Snapshot) - löst Übergabe-Umbuchung und
   erlaubt getrennte Zeiten zweier Personen auf einer Karte (A6, "zu streng").
10. Leichtes Board-Polling/Fokus-Reload + Checkliste als Einzeloperationen (B).

### Stufe 3 - Serien/Termine härten

11. Startdatum: beim Anlegen persistieren, termine() nie am Lauf-Fenster
    verankern, Startfeld in beide Formulare (A13).
12. Auslass-Marker für gelöschte Instanzen; Pause räumt Zukunfts-Vorbuchungen,
    Reaktivieren ohne Rückwirkung; Monatstag-Clamp; Urlaub räumt Vorbuchungen;
    Serien-PATCH zieht schwebende Instanzen nach; Serien-Bearbeiten-UI
    (Teilnehmer nachpflegen); Serien-API scopen (B).
13. Termin-Overlay personenscharf filtern (self-or-admin) (A10).

### Stufe 4 - Struktur und Fundament

14. kanban_kern/persistence.py in Themen-Dateien zerlegen (Re-Export behalten);
    App.svelte: SeitenLeiste.svelte + routing.svelte.ts extrahieren;
    Planung.svelte in Fachbereichs-Komponenten; api.ts/types.ts je Modul
    (hole() nach lib/http.ts), identitaet.svelte.ts als einzige Rollen-Quelle,
    gemeinsame Modal.svelte, Wochentags-/Datums-Helfer nach zeit.ts.
15. Manifest um reihenfolge/global/adminOnly erweitern, die drei Hartlisten in
    App.svelte ersetzen; tote Erweiterungspunkte streichen.
16. Fundament: Indizes auf heiße Pfade, PRAGMA busy_timeout, optional FKs +
    foreign_keys=ON; Restore mit Schreibsperre + location.reload();
    Sitzungs-/Audit-Aufräumpfad; Timer-Plausibilitäts-Cap (> 12 h nachfragen);
    parseZeit strikt ("90m"-Falle); UTC-ymd-Fix.

### Stufe 5 - Komfort und Ausbau (aus dem Benchmark)

17. Zuständig-Filter + klickbare Avatare; benannte gespeicherte Filter.
18. Aktivitätsprotokoll je Karte -> darauf aufbauend Benachrichtigungs-Glocke.
19. Tabellen-/Listenansicht; Fälligkeits-Kalender.
20. Bulk-Auswahl mit Sammel-Undo; Karten-Vorlagen; Blockiert-Flag; Anhänge;
    Aging konfigurierbar; Escape/Fokus im Drawer; Hilfe/Onboarding auf den
    Funktionsstand heben; selektiver Export.

---

## F. Verifikation dieses Audits

- 76 hoch/mittel-Befunde adversarial geprüft (hoch: 2 Skeptiker, mittel: 1);
  alle bestätigt, Detail-Korrekturen der Skeptiker sind eingearbeitet.
- Live-Instanz während des Audits unberührt (health 200 vorher/nachher),
  DB nur read-only inspiziert, keine Code-Änderung.
