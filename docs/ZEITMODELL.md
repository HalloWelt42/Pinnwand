# Zeitmodell: Ticketzeit und Arbeitszeit

Beschreibt die Trennung der beiden Zeit-Größen und warum sie konsistent bleibt.

## Eine Quelle, zwei Sichten

Alle Zeiten liegen in genau einer Tabelle (`zeiteintrag`): je Eintrag eine Karte, ein
Datum, eine Dauer. Daraus ergeben sich zwei Sichten:

- **Ticketzeit** = Summe je Karte über alle Tage (Feld `erfasst_sek`). Zeigt den
  Gesamtaufwand eines Tickets; ein Ticket kann sich über viele Tage strecken.
- **Arbeitszeit** = Summe je Tag über alle Karten. Zeigt, wie viel an einem Tag
  gearbeitet wurde (Stunden-Leiste, Kalender, Berichte). Bestätigte Termine zählen
  zusätzlich als Arbeitszeit.

Es sind zwei getrennte Bedeutungen, aber dieselben Daten - deshalb können sie nie
auseinanderlaufen.

## Jede Buchung trägt ein Datum

Eine undatierte Gesamt-Eingabe der Ticketzeit gibt es bewusst nicht mehr. Zeit entsteht
nur über:

- Start/Stopp (datiert auf den Tag des Laufs; über Mitternacht taggenau zerlegt),
- manuelles Buchen auf einen beliebigen Tag,
- Korrektur eines vorhandenen Eintrags (Tag oder Dauer ändern).

Dadurch ist jede Ticket-Korrektur immer einem Tag zugeordnet: erhöht man die Zeit
eines Tickets für Tag X, wächst die Ticketzeit UND die Arbeitszeit von Tag X - nie
versehentlich die von heute. Das war früher der Stolperstein: eine Gesamt-Korrektur
landete still auf dem heutigen Tag.

## Im Karten-Detail

- "Ticketzeit gesamt" wird nur angezeigt (read-only, Summe aller Tage).
- Darunter die Aufschlüsselung nach Tagen: je Eintrag Tag und Dauer änderbar, Eintrag
  löschbar; Einträge aus Start/Stopp sind als solche markiert.
- "Tag buchen" legt einen datierten Eintrag für einen beliebigen Tag an.

## Bestand

`erfasst_sek` war schon immer die Summe der Einträge; es gibt keinen Datenbruch.
Früher fälschlich auf heute gebuchte Gesamt-Korrekturen lassen sich jetzt über die
Tages-Aufschlüsselung auf den richtigen Tag umdatieren.
