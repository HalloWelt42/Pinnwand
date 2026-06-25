# Rollen (Phase 1)

Jede Person hat eine Rolle: `admin` oder `mitarbeiter`. Mitarbeiter sehen die
verwaltenden Bereiche nicht in der Seitenleiste, Admins sehen alles.

## Ehrliche Einordnung

Ohne Passwort/Login ist das **reines UI-Scoping, keine Sicherheitsgrenze**. Die
aktive Person ist nur ein browser-lokaler Wert; jeder kann über das Personen-
Dropdown wieder zu einer Admin-Person wechseln, und die API-Endpunkte (inklusive
Löschen und Zurücksetzen) bleiben technisch erreichbar. Der Nutzen ist trotzdem
real: eine aufgeräumte Oberfläche für Mitarbeiter und weniger Versehen. Echte
Durchsetzung (serverseitig, mit Login) ist eine spätere Phase und hier bewusst
NICHT enthalten.

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
