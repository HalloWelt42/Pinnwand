# Fertige Karten: Fenster, Nachladen und Archiv

Ziel: Das Board wird bei vielen erledigten Karten nicht mehr geflutet. Erledigt-Spalten
laden serverseitig gefiltert und gedeckelt; der Rest kommt beim Scrollen nach. Sehr alte
fertige Karten wandern automatisch ins Archiv und belasten das Board nicht mehr.

## Grundprinzip

- Der Board-Ladeweg (`GET /api/kanban/boards/{id}`) liefert die Karten der OFFENEN Spalten
  voll, aber KEINE Karten aus Erledigt-Spalten.
- Erledigt-Spalten holen ihre Karten getrennt und gefenstert:
  `GET /api/kanban/spalten/{id}/fertige?zeitraum=&offset=&limit=&q=&labels=&prioritaet=`.
- Der Filter wirkt im BACKEND: geliefert wird nur, was auch angezeigt werden soll
  (Zeitfenster und Anzahl-Deckel). Das Frontend hält keine vollständige Liste vor.

## Reihenfolge und Zeitfenster

- Fertige Karten sind nach Abschlussdatum sortiert (neueste zuerst). Das Abschlussdatum
  ist bei Serien-/REKO-Karten das feste geplante Datum, sonst der Erledigt-Zeitpunkt.
  Manuelles Umsortieren innerhalb einer Erledigt-Spalte ist damit nicht mehr entscheidend;
  Hineinziehen (erledigt setzen) und Herausziehen (wieder aufnehmen) funktionieren weiter.
- Der Zeitfilter je Spalte (Heute, Gestern, Woche, Monat, Jahr, Alle) steuert das Backend.
  Bei aktiver Board-Suche oder Label-/Prio-Filterung wird das Zeitfenster ausgesetzt und
  serverseitig über die passenden fertigen Karten gesucht (entprellt gegen Tippen).

## Nachladen (kein Fluten)

- Die erste Seite umfasst höchstens die eingestellte Seitengröße (Standard 50 Karten).
- Beim Scrollen ans Ende der Spalte wird die nächste Seite nachgeladen; zusätzlich gibt es
  einen Knopf "Mehr laden" samt Zähler "X von Y".

## Archiv (automatisch)

- Fertige Karten, deren Abschluss älter ist als die eingestellte Schwelle (Standard 365
  Tage), werden nie ins Board geladen. Es findet KEIN Datenumbau statt - die Grenze ist
  eine reine Ladegrenze und voll umkehrbar durch Ändern der Schwelle.
- Der Archiv-Knopf am Board öffnet die Archiv-Ansicht: eine paginierte, durchsuchbare
  Liste aller archivierten fertigen Karten des Boards; ein Klick öffnet die Karte.
  Endpunkt: `GET /api/kanban/boards/{id}/archiv?offset=&limit=&q=`.

## Einstellbar in der Oberfläche

Unter Einstellungen, Abschnitt "Fertig-Karten und Archiv":

- "Karten je Ladeschritt" (Seitengröße, 1 bis 500)
- "Archiv ab (Tage)" (Schwelle, 1 bis 100000)

Gespeichert wird über `PUT /api/kanban/einstellungen` (bei aktiver Anmeldung nur für
Admins, wie die anderen verwaltenden Einstellungen). Gelesen wird über
`GET /api/kanban/einstellungen`.

## Auswirkung auf Auswertungen

Keine. Berichte, Stundenzettel und Kalender summieren weiterhin aus den Zeiteinträgen -
unabhängig davon, ob eine Karte im Board, gefenstert oder im Archiv liegt. Das Archiv ist
eine reine Anzeige- und Ladegrenze, kein Entfernen von Daten.
