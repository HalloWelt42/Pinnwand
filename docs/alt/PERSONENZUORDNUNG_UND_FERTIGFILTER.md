# Personenzuordnung und Fertig-Zeitfilter

Beschreibt, wie Zeit verlässlich der richtigen Person gutgeschrieben wird und wie
sich erledigte Karten nach Abschlusszeitraum filtern lassen.

## Warum

Die personenbezogenen Stundensummen (Stunden-Leiste, Jahreskalender, Berichte)
zählen Ist-Zeit über das Kürzel der Karte. Eine Karte ohne Kürzel fällt damit aus
der persönlichen Summe heraus, obwohl Zeit erfasst wurde. Genau das führte zu
scheinbar fehlenden Stunden. Die folgenden Punkte schließen die Lücken an der
Quelle, statt an der Auswertung zu rechnen.

## Standard-Person bei neuen Karten

Neue Karten erhalten automatisch ein Kürzel:

1. die aktive Identität (Personen-Sicht), sonst
2. das zuletzt gesetzte Kürzel (im Browser gemerkt), sonst
3. kein Kürzel.

Das Feld im Karten-Detail ist ein echtes Personen-Auswahlfeld (kein Freitext mehr).
Damit kann kein vertipptes oder leeres Kürzel mehr entstehen. Wird dort eine Person
gewählt, merkt sich die App dieses Kürzel als nächsten Standard.

## Wiederkehrende Serien mit Teilnehmern

Eine Serie trägt eine Person, und jede daraus erzeugte Karte erbt dieses Kürzel
automatisch (bestehende Backend-Logik). Bisher fehlte im Serien-Formular die Auswahl
der Person - dadurch liefen Serien ohne Person und ihre Karten blieben ohne Kürzel.

Das Formular bietet jetzt Teilnehmer-Auswahlfelder. Modell: eine eigene Karte je
Teilnehmer. Sind mehrere Teilnehmer angehakt, entsteht je Teilnehmer eine eigene
Serie mit dessen Kürzel; jeder erfasst seine eigene Zeit. So bleibt die
Pro-Person-Auswertung unverändert korrekt - es gibt kein Aufteilen einer
gemeinsamen Karte auf mehrere Personen.

## Zeitfilter im Kopf erledigter Spalten

Im Kopf jeder erledigten Spalte steht ein kleines Auswahlfeld für den Zeitraum:
Heute (Standard), Gestern, Woche, Monat, Jahr, Alle. Das Abschlussdatum richtet sich
nach der Art der Karte:

- **Serien-/REKO-Karten** haben ein festes geplantes Datum (der Termintag) und
  bleiben diesem Tag zugeordnet - egal wann sie als erledigt in die Spalte verschoben
  werden.
- **Alle anderen Karten** zählen ab ihrem Erledigt-Zeitpunkt, also dem Tag, an dem sie
  in die Fertig-Spalte gezogen wurden.

Die erfassten Zeiten sind reine Tages-Summen (aus Start/Stopp-Differenzen und
manuellen Nachträgen) und spielen für diese Datierung bewusst keine Rolle. So zeigt
die Fertig-Spalte standardmäßig nur das heute Erledigte und bleibt übersichtlich.

Details:

- Die Auswahl wird je Board und Spalte im Browser gemerkt.
- Bei aktiver Board-Suche oder aktivem Sortier- bzw. Label-Filter wird der Zeitfilter
  ausgesetzt, damit über den gesamten Bestand gesucht werden kann.
- In einer zeitgefilterten Spalte ist das Umsortieren per Ziehen gesperrt (sonst
  würde das Sortieren innerhalb einer Teilmenge die Reihenfolge verfälschen); Karten
  lassen sich weiterhin hineinziehen.
- Nach dem Verschieben in eine erledigte Spalte wird neu geladen, damit das frische
  Abschlussdatum sofort zum gewählten Zeitraum passt.
