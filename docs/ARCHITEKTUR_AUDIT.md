# Architektur-Audit

Mehrere Durchgänge durch Backend und Frontend mit Blick auf objektorientierten
Aufbau, Typisierung, CSS-Regeln, Zentralisierung, Modularisierung und auf doppelten
oder fast gleichen Code. Festgehalten ist, was geprüft wurde, was sofort behoben
wurde und was als bewusster Rest für spätere Runden offen bleibt.

## Gesamtbild

Die App folgt ihren Konventionen weitgehend sauber. Das Backend ist modular: jedes
Fachgebiet liegt unter `backend/module/<name>` mit der immer gleichen Schichtung
`persistence` (SQLite, reine Datenzugriffe), `dienst` (Fachlogik), `api` (FastAPI-Router)
und `models` (Pydantic). Eine Manifest-Registry hängt die Module ein, statt sie fest
zu verdrahten. Das Frontend ist in Svelte 5 durchgängig mit Runes und TypeScript
geschrieben; `svelte-check` läuft mit 0 Fehlern und 0 Warnungen, `npm run build`
ist grün.

Die wiederkehrenden Funktionsnamen über die Module hinweg (`liste`, `hole`,
`erstelle`, `aktualisiere`, `loesche`, `init_db`) sind keine Dubletten, sondern das
gewollte gleiche Vokabular je Modul mit jeweils eigenem Rumpf - das ist gute
Modularisierung, nicht Wiederholung.

## Behobene Dubletten (wortgleicher Code an mehreren Stellen)

1. Feiertage und Urlaubstage im Backend
   `_feiertage` und `_urlaubstage` waren in `module/serien/dienst.py` und
   `module/termine/dienst.py` wortgleich vorhanden. Die Logik liegt jetzt zentral in
   `module/planung/persistence.py` als `feiertage_set(von, bis)` und
   `urlaubstage_set(...)`. Serien und Termine rufen über dünne Adapter nur noch diese
   eine Quelle. Verifiziert: beide Adapter liefern für denselben Zeitraum exakt
   dieselbe Menge wie die zentrale Funktion.

2. Zeit-Parsing im Frontend
   Die Funktion zum Lesen von "H:MM", "H:MM:SS" und Dezimalstunden ("1,5") existierte
   textgleich als `parseZeit` im Karten-Detail und als `parseDauer` in der
   Zeit-Auswertung. Beide nutzen jetzt das zentrale `parseZeit` aus
   `lib/timer.svelte.ts` - dem natürlichen Gegenstück zu `formatDauer`.

3. Kurze Position M:SS im Frontend
   `mmss` (Transkript-Ansicht) und `mmssZeit` (Karten-Detail) formatierten beide eine
   Sekundenzahl als M:SS. Jetzt gibt es ein gemeinsames `mmss` in `lib/timer.svelte.ts`,
   das auch `null` sauber zu einem leeren String macht.

4. Audit-Referenz in der Agenten-API
   `_ziel(ergebnis)` (Kartenschlüssel, sonst Board-Id fürs Protokoll) stand wortgleich
   in `module/agent_api/api.py` und `module/agent_api/werkzeuge.py`. Die Funktion heisst
   jetzt `ziel_referenz` und lebt einmal in `werkzeuge.py`; die HTTP-Schicht ruft sie von
   dort.

## Versionierung

Die Version ist nicht zufällig verstreut, sondern bewusst an drei klar benannten
Stellen gepflegt: `frontend/src/lib/version.ts`, `frontend/package.json` und
`backend/app/config.py` (von dort beziehen Backend und Snapshots ihren Wert). Sie wird
streng erhöht (Patch +0.0.1 je Änderung, Feature +0.1.0). Das ist sauber, aber drei
Stellen müssen von Hand gleich gehalten werden - siehe Backlog.

## Offener Rest (bewusst, für spätere Runden)

- localStorage-Zugriff: rund 40 direkte Zugriffe in 13 Dateien. Funktioniert, ist aber
  ein Kandidat für einen kleinen zentralen Helfer (`lib/storage.ts`) mit defensivem
  Lesen und Schreiben (try/catch, JSON), damit das Muster nicht überall wiederholt wird.
- Eine Versionsquelle: ein einzelnes `VERSION`-File, aus dem Frontend und Backend lesen,
  würde das Dreifach-Pflegen ersetzen.
- persistence liefert teils rohe dicts: die Datenschicht könnte durchgängig die
  vorhandenen Pydantic-Modelle zurückgeben statt dicts, dann fällt manche Umwandlung in
  der dienst- und api-Schicht weg.
- `response_model` ist nicht auf allen Endpunkten gesetzt; flächendeckend gesetzt
  schärft das die API-Verträge und die OpenAPI-Doku.

Diese Punkte sind grössere, querschnittliche Umbauten - bewusst nicht in einem Rutsch
erledigt, sondern als nächste Runde notiert.
