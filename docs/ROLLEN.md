# Rollen (Phase 1)

Jede Person hat eine Rolle: `admin` oder `mitarbeiter`. Mitarbeiter sehen die
verwaltenden Bereiche nicht in der Seitenleiste, Admins sehen alles.

## Ehrliche Einordnung

Ohne aktive Anmeldung ist das Rollen-Gating **reines UI-Scoping, keine
Sicherheitsgrenze**: die aktive Person ist nur ein browser-lokaler Wert, jeder kann
über das Personen-Dropdown wechseln, und die API bleibt offen.

Mit aktiver **Anmeldung** (siehe LOGIN.md) werden die Rollen dagegen **serverseitig
durchgesetzt**: die Identität kommt aus der Sitzung (nicht aus dem Dropdown), und die
Admin-Bereiche sind echt geschützt (403). Dann ist es eine echte Zugriffskontrolle.

## Was ist admin-nur?

- **Einstellungen** (Datensicherung, Zurücksetzen, Agenten-Token),
- **Labels** (globale Label-Verwaltung),
- innerhalb der **Planung** nur die globale Konfiguration: Rollen und Passwörter,
  Feiertags-Import, Abwesenheits-Arten und globale Sonderregeln.

Für alle offen bleiben die täglichen Ansichten: Heute, Board, Projekte, Zeiten,
Kalender, Jahreskalender, Wiederkehrendes, Suche, Transkripte und Berichte. Auch das
tägliche Arbeiten inklusive Löschen von Karten/Spalten/Boards bleibt für Mitarbeiter
offen. Die **Planung** ist ebenfalls für alle sichtbar, aber rollenbewusst (siehe unten).

## Self-Service in der Planung (Phase 2)

Mitarbeiter pflegen in der Planung ausschließlich ihre **eigenen** Daten: Wochen-Soll,
Wochen-Override, eigenes Bundesland, Urlaubsanspruch und Urlaub. Die Auswahlfelder sind
fest auf die eigene Person gesetzt, die globalen Konfigurationsblöcke sind ausgeblendet.
Admins sehen die volle Team-Planung.

Serverseitig setzt eine kleine, typisierte Schicht das durch (nur bei aktiver
Anmeldung, sonst bleibt alles offen):

- `module/auth/akteur.py` - `Akteur` (person_id, kürzel, rolle; `ist_admin`; `offen()`
  für den passwortlosen Modus) und die Dependency `aktueller_akteur`, die die Identität
  aus der Sitzung auflöst.
- `module/auth/rechte.py` - reine Entscheidungsfunktionen ohne DB-Zugriff:
  `darf_person_bearbeiten(akteur, ziel)` (Admin oder man selbst),
  `darf_zeiteintrag_bearbeiten(akteur, karte_zustaendig)` (Admin oder eigenes Kürzel,
  fail-closed) und `verlange(erlaubt)` (wirft 403).
- `module/auth/dienst.py::_admin_only` ist eine kleine Regel-Tabelle und deckt nur noch
  rein-globale Pfade ab; die Self-Service-Pfade prüfen den Akteur direkt im Endpunkt,
  weil das Ziel erst dort bekannt ist.

## Eigentum an Zeiteinträgen

Ein Zeiteintrag gehört der Person, der die Karte zugewiesen ist (das
Zuständigkeits-Kürzel der Karte). Nur diese Person oder ein Admin darf ihn anlegen,
ändern oder löschen; fremde Einträge sind schreibgeschützt. Karten selbst bleiben im
Team gemeinsam.

## Projekt-Sichtbarkeit pro Mitglied

Eine Mappe ist ein Projekt (siehe PROJEKTE.md). Über die Tabelle `mappe_mitglied` wird
die Sichtbarkeit gesteuert: eine Mappe **ohne** Mitglieder ist für alle sichtbar
(geteilt, rückwärts-kompatibel); sobald Mitglieder hinterlegt sind, sehen nur diese
plus Admin das Projekt und seine Boards. Das Scoping wirkt serverseitig in
`GET /api/kanban/mappen`, `.../boards`, `GET /api/kanban/boards/{id}` und
`/api/kanban/projekte`; die Mitglieder-Verwaltung ist admin-nur.

## Datenmodell und Sicherungen

Additives Feld `rolle` an der Person (Backend `planung`). Migration setzt bestehende
Personen auf `admin`, damit beim Einführen niemand ausgesperrt wird; neue Personen
sind `mitarbeiter`. Die Rolle wird in der Personen-Verwaltung (nur für Admins
sichtbar) per Auswahl gesetzt. Ein Aussperr-Schutz verhindert das Herabstufen des
letzten verbleibenden Admins.

Im Frontend leitet sich die Rolle aus der aktiven Person ab (`rolleAus` in
`personSicht`); ist keine Person gewählt, gilt `admin` - so bleibt eine frische
Installation voll bedienbar. Das Gating sitzt an einer Stelle in `App.svelte`
(gefilterte Ansichtsliste).
