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

## 3. Befunde

| Nr | Art | Schwere | Befund | Empfehlung |
| --- | --- | --- | --- | --- |
| B1 | Trennung | hoch | Keine Nutzer-/Profil-Trennung; Auswertungen summieren über alle Personen (live belegt, siehe 1.1). | Personen-Sicht (Option 2) oder Single-Tenant bewusst dokumentieren. |
| B2 | Einstellungen | mittel | `localStorage` ist pro Browser, nicht pro Nutzer; gemeinsamer Browser teilt Theme/Filter/Admin-Token. | Pro-Nutzer-Einstellungen erst mit einem Nutzer-Konzept; bis dahin dokumentieren. |
| B3 | Datenintegrität | mittel | `POST /api/kanban/karten` prüft `board_id`/`spalte` nicht; leere/ungültige Werte erzeugen eine Waisen-Karte ohne Board. | Existenz von Board und Spalte vor dem Anlegen prüfen (sonst 400/404). |
| B4 | Korrektheit | niedrig | Live-Timer mischt Browser-Uhr mit Server-`laeuft_seit`; bei Uhr-Differenz ist die Live-Anzeige verschoben (gespeicherter Wert korrekt). | Auf einem Rechner unkritisch; bei getrennten Uhren Startzeit clientseitig verankern. |
| B5 | Korrektheit | niedrig | Doppelzählung möglich, wenn ein Thema gleichzeitig als Termin und als Aufgaben-Serie geführt wird. | Pro Thema nur eine Form; ggf. Hinweis in der UI. |

Weitere Befunde aus dem automatisierten Pipeline-Audit werden hier ergänzt.

## 4. Empfehlung (priorisiert)

1. Entscheidung zur Mehrbenutzung treffen: bewusst Single-Tenant ODER Personen-Sicht
   einbauen (Filter auf aktive Person in Stunden-Leiste, Kalender, Berichte,
   Was-steht-an). Das ist der wirksamste Schritt gegen das Schneiden der Werte.
2. B3 (Board-/Spalten-Prüfung beim Karten-Anlegen) schließen - günstig und
   verhindert Waisen.
3. Reset-/Backup-Tabellenliste gegen das aktuelle Schema abgleichen.
