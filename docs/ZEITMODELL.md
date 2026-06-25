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

## Geteilte Zeitgruppe (verknüpfte Aufgaben)

Verknüpfte Aufgaben, die man parallel abarbeitet, sollen die Zeit nur EINMAL zählen.
Das ist bewusst eine reine Anzeigeschicht über dem Modell oben - das Modell selbst
bleibt unangetastet:

- Ein `zeiteintrag` gehört weiterhin zu genau EINER Karte. Es wird nichts dupliziert.
  Alle Auswertungen (Arbeitszeit je Tag, Personenstunden, Berichte, Kalender) summieren
  aus `zeiteintrag` und zählen damit jede Sekunde von Natur aus genau einmal.
- Karten mit gleicher `gruppe_id` bilden eine Gruppe (Tabelle `kartengruppe` mit dem
  Schalter `zeit_geteilt`). Für die Anzeige berechnet `board_detail` je Karte das Feld
  `gruppe_sek`: bei `zeit_geteilt` die kombinierte `erfasst_sek` aller Mitglieder, sonst
  die eigene. So sieht man auf jeder verknüpften Karte die gemeinsame Zeit, ohne dass
  sie irgendwo doppelt zählt.
- Spezialfall einstellbar: `zeit_geteilt=false` schaltet die geteilte Anzeige ab; dann
  zeigt jede Karte wieder nur ihre eigene Zeit.

Praktisch: in einer Sitzung, die mehrere Tickets betrifft, verknüpft man sie und trackt
die Zeit einmal (auf einer der Karten). Alle zeigen die gemeinsame Summe; die
Personenstunden bleiben korrekt.
