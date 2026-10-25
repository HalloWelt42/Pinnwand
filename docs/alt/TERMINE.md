# Termine - leichte Meeting-Zeiterfassung

Termine sind wiederkehrende Meetings, die Zeit gutschreiben, ohne das Board mit
Karten zu füllen. Abgrenzung zu den bestehenden Konzepten:

- Serien legen pro Vorkommen eine Kanban-Karte mit Soll an (Aufgaben-Vorbuchung).
- Termine legen keine Karten an. Jedes Vorkommen wird als leichte Instanz geführt
  und am Folgetag bestätigt; erst dann zählt die Zeit als geleistet (Ist).

## Ablauf

1. Eine Termin-Serie beschreibt den Rhythmus (täglich/wöchentlich/monatlich, wie
   bei Serien), eine Uhrzeit, eine geplante Dauer und die Person (Kürzel), der die
   Zeit gutgeschrieben wird. Optional werden Wochenenden, Feiertage und Urlaubstage
   der Person übersprungen.
2. Materialisierung erzeugt Instanzen nur für Vorkommen bis gestern (Status
   "schwebend"). So kann am nächsten Tag gefragt werden. Idempotent, mit einer
   Rückblick-Grenze (rueckblick_tage), damit der erste Lauf nicht riesig wird.
3. Bestätigung (niederschwellig):
   - In der Heute-Ansicht ein Bereich "Zu bestätigen (N)" mit Inline-Aktionen.
   - Einmal pro Tag ein dezentes Overlay mit "Alle wie geplant bestätigen" und
     "Später" (nicht blockierend; localStorage pw_termine_letzter_check).
   - Pro Termin: bestätigen (Dauer anpassbar), ablehnen ("fand nicht statt").
4. Erst eine bestätigte Instanz zählt. Keine Antwort -> bleibt schwebend, zählt
   nie. Korrektur jederzeit möglich (Dauer ändern oder doch ablehnen) - die
   Gutschrift wird live nachgeführt.

## Gutschrift (Ist)

Bestätigte Termine sind eine zweite Ist-Quelle neben den Zeiteinträgen der Karten.
zeiteintrag (Karten-SSOT) bleibt unverändert. Die bestätigten Termin-Minuten je
Person/Tag werden additiv eingewoben in:

- planung/kalender.py (_ist_sek_je_tag) -> Jahreskalender (Stunden-Heatmap,
  Auslastung) und Kapazitäts-Overlay.
- berichte/daten.py (_ist_je_person) -> Kapazität/Auslastung und Zeit je Person.

Die Zeiten-Ansicht zeigt bestätigte Termine als eigene, gekennzeichnete Tageszeilen
und rechnet sie in Tages- und Wochensumme.

## Datenmodell (Modul termine)

- termin_serie: Rhythmus + Person + Dauer + Skips + Backfill-Grenze + aktiv.
- termin_instanz: serie_id, datum, denormalisiert kuerzel/titel/uhrzeit, geplant_min,
  status (schwebend|bestaetigt|abgelehnt), effektiv_min, bestaetigt_am.
  UNIQUE(serie_id, datum) sorgt für Idempotenz.

Beim Löschen einer Serie bleiben bestätigte Instanzen als Verlauf/Gutschrift
erhalten (deshalb denormalisiert); schwebende/abgelehnte werden entfernt.
