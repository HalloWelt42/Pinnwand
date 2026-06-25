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
- **Planung** (Personen-, Urlaubs-, Feiertags-Verwaltung, enthält die Rollenvergabe),
- **Labels** (globale Label-Verwaltung).

Für alle offen bleiben die täglichen Ansichten: Heute, Board, Zeiten, Kalender,
Jahreskalender, Wiederkehrendes, Suche, Transkripte und Berichte. Auch das tägliche
Arbeiten inklusive Löschen von Karten/Spalten/Boards bleibt für Mitarbeiter offen.

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
