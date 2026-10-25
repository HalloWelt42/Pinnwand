# Pinnwand Neubau: Entwurf

Neubau der Pinnwand auf dem Appkern, auf dem Pi, mit Boards als eigenständigen Einheiten. Die Mechanik des alten
Boards bleibt vollständig erhalten (Verzeichnis in `BOARD_MECHANIK.md`), neu wird der Unterbau darunter.

## 0. Entscheidungen (geklärt am 25.10.2026)

| Nr | Frage | Wahl des Nutzers |
|---|---|---|
| E-01 | Wer arbeitet mit der neuen Pinnwand? | Mehrere, je Board eingeladen |
| E-02 | Was ist die unabhängige Einheit? | Das Board selbst: eigene Spalten, Labels, Mitglieder, Module und Einstellungen; Ordner in der Seitenleiste nur zum Sortieren, ohne Rechte |
| E-03 | Welche Rollen gibt es im Board? | Rechte je Board frei einstellbar |
| E-04 | Woran hängen die Rechte? | Rollen je Board: Start mit Besitzer, Mitglied, Leser; Rechte anpassbar, eigene Rollen möglich; jede Person hat eine Rolle; die Rechte bringt jedes Modul selbst mit |
| E-05 | Fachmodule der ersten Fassung (je Board zuschaltbar) | Zeiterfassung; Arbeitszeit und Urlaub; Serien und Termine; Berichte |
| E-06 | Anbindungen an andere Apps | Assistent; Transkripte; Vorlesen; KI an der Karte |
| E-07 | Wo hängen Arbeitszeit, Urlaub, Soll und Ist? | Je Person, für sich: eigenes Zeitkonto, gebuchte Zeiten aus allen Boards fließen hinein; ein Board zeigt mit Recht nur Zeiten und Abwesenheiten seiner Mitglieder |
| E-08 | Felder einer Karte | Feste Grundfelder plus eigene je Board (Zahl, Datum, Auswahl, Text, Verweis); Module bringen ihre Felder selbst mit |
| E-09 | Ansichten neben dem Board (Rechner) | Heute über alle Boards; Liste und Tabelle; Kalender; Zeitachse |
| E-10 | Am Telefon | Heute ansehen und abhaken; Timer und Zeit buchen; schnell erfassen (auch per Sprache); Board ansehen und verschieben |
| E-11 | Daten der alten Pinnwand | Neu anfangen; die alte Datenbank bleibt unverändert als Sicherung liegen |
| E-12 | Repo | Selbes Repo (öffentlich), die alte Fassung bleibt unter der Marke v0.74.0 und dem Zweig `alt`; Hausdaten nur in der privaten Wahrheit |
| E-13 | Wie kommen Eingeladene ins Board? | Mit Kellerwolke-Konto; der Besitzer lädt per Name ein |
| E-14 | Board-Mechanik | Die Mechanik des alten Boards ist das Maß, mit allen eingebauten funktionalen Einzelheiten (Nutzer: "die mechanik des alten boards ist entscheidender, die eingebauten funktionellen details") |
| E-15 | Anhänge und Dokumente | In der Kellerwolke: Ablage der Pinnwand, je Board ein Ordner; dazu Dateien aus der eigenen Kellerwolke anhängen; Mitglieder sehen sie über die Rechte des Boards |
| E-16 | Hinweise (zugewiesen, fällig, erwähnt, Termin) | In der Pinnwand; Push aufs Telefon; über den Assistenten |
| E-17 | Neues Board | Aus Vorlagen, eigene speicherbar; dazu leer anfangen |
| E-18 | Bau und Betrieb | In Stufen, jede läuft nach ihrer Prüfung sofort auf dem Pi |
| E-19 | Mockups | Alle Ansichten vorab, Rechner und Telefon, hell und dunkel, jeder Zustand eine Seite, altes Board zum Vergleich daneben; nach Freigabe verbindlicher Leitfaden |
| E-20 | Rahmen | Leitstand wie Fundus: eigene Seitenleiste und Kopf aus den Bausteinen des Leitstands, Schriftstufen, volle Breite für das Board |
| E-21 | Schriftstufe | Klein als Vorgabe (Nutzer: "wir nutzen die einstellung schrift klein"); Mittel und Groß wählbar |
| E-22 | Adressen | Echte Pfade im Browser (Nutzer: "wichtig wäre, dass normale pfade im browser angezeigt werden"); über die Navigation des Appkerns wie in den übrigen Apps, ohne zweites Rahmenwerk |

Folgt aus früheren Entscheidungen des Nutzers: Gestaltung aus dem Appkern (Grunddesign "Appkern, alle ziehen um"); eigene
Themes und das Theme-Studio der alten App entfallen, Hell, Dunkel und Schriftstufen kommen aus der Schale.

## 1. Warum neu: die fünf Ursachen und ihre Lösung im Aufbau

Das Gesamt-Audit der alten App (`GESAMT_AUDIT.md`, 128 Befunde) führt fast alle Fehler auf fünf Ursachen zurück. Der
Neubau löst jede im Aufbau, nicht durch Einzelkorrekturen:

| Ursache in der alten App | Lösung im Neubau |
|---|---|
| Regeln gelten nur am offiziellen Endpunkt, Nebenwege umgehen sie (Status im Kartendetail, Timer, Nachtragen) | Jede Änderung läuft durch genau einen Anwendungsfall, der Rechte und Regeln prüft; Oberfläche, Telefon, Assistent und Serien rufen denselben. Es gibt keinen zweiten Schreibweg in die Datenbank |
| Das Kürzel ist die Identität einer Person (freier Text) | Personen sind Konten der Kellerwolke mit fester Kennung; Kürzel und Name sind nur Anzeige |
| Löschen hinterlässt Waisen, Rückgängig ist teils nur Schein | Papierkorb je Board für Karten, Spalten und Boards mit allem, was daran hängt (Zeiten, Kommentare, Anhänge, Verknüpfungen); Wiederherstellen stellt alles wieder her. Fremdschlüssel mit festgelegtem Verhalten |
| Eine gemeinsame Datenbank für alles, ein Timer für alle, kein Abgleich zwischen Browsern | Board als Einheit mit eigenen Mitgliedern und Rollen; ein Timer je Person; Ereignisstrom je Board, jede Änderung erscheint sofort bei allen; Karten tragen eine Fassung, ein Schreiben auf veralteter Fassung wird mit Hinweis abgelehnt statt still überschrieben |
| Stilles Scheitern in der Oberfläche | Jeder Schreibvorgang meldet Erfolg erst nach der Antwort des Servers; Fehler erscheinen sichtbar mit Grund (Bausteine des Appkerns) |

## 2. Fachmodell

- **Konto**: Person aus der Kellerwolke (Anmeldung des Appkerns). Trägt ihr Zeitkonto (Wochenstunden, Bundesland,
  Urlaubsanspruch, Urlaub, Abwesenheiten, Halbtagsregeln) und ihren einen Timer.
- **Board**: die Einheit. Hat Spalten (darunter Erledigt-Spalten), Labels, eigene Felder, Rollen, Mitglieder,
  zugeschaltete Module, Einstellungen, einen Kartenschlüssel mit Laufnummer, einen Papierkorb. Liegt optional in einem
  Ordner der Seitenleiste (persönliche Sortierung, ohne Rechte).
- **Rolle**: je Board; eine Menge von Rechten. Rechte werden von Modulen erklärt (Kern: Board verwalten, Mitglieder
  verwalten, Karten anlegen, bearbeiten, verschieben, löschen, Papierkorb leeren; Zeiterfassung: eigene Zeit buchen,
  Zeiten anderer sehen, Zeiten anderer bearbeiten; Arbeitszeit: Abwesenheiten der Mitglieder sehen; usw.). Der
  Server prüft sie an einer Stelle für jeden Weg.
- **Karte**: Grundfelder (Titel, Beschreibung, Notizen, Art Arbeit oder Idee, Zuständige, Priorität, Start, Fällig,
  Labels, Checkliste, Kommentare, Cover, Blockiert-Grund), eigene Felder des Boards, Felder der Module (Schätzung,
  Serie, Transkript-Marken). Verknüpfte Aufgaben mit geteilter Zeit wie bisher.
- **Zeiteintrag**: gehört einem Konto und einer Karte; Zeit zählt genau einmal (Zeitmodell der alten App bleibt).
- **Vorlage**: Aufbau eines Boards ohne Karten (Spalten, Felder, Rollen, Module, Einstellungen).
- **Hinweis**: an ein Konto, mit Sprung zur Karte; Wege: Pinnwand, Push, Assistent.

## 3. Schichten und Module

Grundlage ist die Vorlage des Appkerns (`python -m appkern.vorlage`): Anmeldung, Schale, Caddy vorne, Ausrollen mit
Prüfungen, Versionswerkzeug, Git-Hooks, Testgerüst, Handbuch-Seite.

Jedes Fachmodul (Kern-Board, Zeiterfassung, Arbeitszeit, Serien und Termine, Berichte, Verbund) hat dieselben Schichten:

- **Regeln**: reine Funktionen ohne Ein- und Ausgabe (Verschieben samt Mitziehen der Gruppe, Abschlussdatum, Soll aus
  Wochenstunden und Feiertagen, Serienfälligkeit).
- **Anwendung**: die Anwendungsfälle, einzige Stelle für Änderungen; prüft Rechte, ruft Regeln, schreibt, sendet
  Ereignisse.
- **Verzeichnis**: Datenbank des Moduls.
- **Schnittstelle**: REST für die Oberfläche und Werkzeuge für den Assistenten, beide nur über die Anwendung.
- **Oberfläche**: Svelte-Modul mit seinen Ansichten, Kartenfeldern und Einstellungen.

Ein Modul meldet sich bei der Registry mit Rechten, Kartenfeldern, Ansichten, Einstellungen und Ereignissen. Module
sind je Board zuschaltbar; ein abgeschaltetes Modul verschwindet aus Board und Karten, seine Daten bleiben.

## 4. Mechanik des alten Boards

Das Verzeichnis `BOARD_MECHANIK.md` (Stand 0.74.0) nennt 126 Mechaniken des alten Boards in 18 Bereichen mit Kennung
(M-01 bis M-126) und Fundstelle, dazu alle Einstellungen mit Vorgabewerten. Jede Mechanik kommt in den Neubau und wird
Punkt der Abnahme; wo das Verzeichnis einen bekannten Fehler nennt (an 66 Mechaniken, sechs davon an einer
Wegwerf-Datenbank nachgestellt), bleibt die Mechanik und die Ursache fällt durch den neuen Aufbau weg. Das
Gesamt-Audit beschreibt 0.67.1; was seitdem behoben ist, steht im Verzeichnis als "Behoben seit", damit die Regel
dahinter übernommen wird.

## 5. Stufen

1. **Board**: Boards, Spalten, Karten mit der ganzen alten Mechanik, eigene Felder, Rollen und Rechte, Mitglieder,
   Vorlagen, Papierkorb, Ereignisstrom, Heute, Liste und Tabelle, Kalender und Zeitachse der Karten, Hinweise in der
   Pinnwand, Anhänge über die Kellerwolke, Telefon (Heute, schnell erfassen, Board ansehen und verschieben).
2. **Zeit**: Timer je Person, Zeiteinträge, Stundenzettel, Arbeitszeit und Urlaub mit Soll und Ist, Feiertage je
   Bundesland, Jahreskalender und Auslastung; Telefon: Timer und Zeit buchen.
3. **Planung**: Serien und Termine (auch in Heute, Kalender und Zeitachse).
4. **Verbund**: Berichte, Assistent, Transkripte, Vorlesen, KI an der Karte, Hinweise über Push und den Assistenten,
   Spracheingabe beim Erfassen.

Jede Stufe geht nach ihrer Prüfung (Tests, Ansichtsprüfung in allen Breiten, Vergleich mit den Mockups, Abnahme der
Mechanik) auf den Pi.

## 6. Ansichten

- **Rechner**: Heute; Board; Liste und Tabelle; Kalender; Zeitachse; Kartendetail; Zeiten (Stundenzettel);
  Arbeitszeit (Zeitkonto, Jahreskalender, Auslastung der Mitglieder mit Recht); Serien; Berichte; Hinweise;
  Papierkorb; Board-Einstellungen (Spalten, Felder, Labels, Rollen und Rechte, Mitglieder, Module, Vorlagen);
  Board anlegen aus Vorlage.
- **Telefon** (eigene, reduzierte Ansicht): Heute mit Abhaken per Halten; Timer und Zeit buchen; schnell erfassen,
  auch per Sprache; Board spaltenweise mit Kartendetail und Verschieben.

### Pfade

`/heute`, `/hinweise`, `/zeiten`, `/arbeitszeit[/kalender|urlaub|team]`, `/serien[/<kennung>]`, `/berichte`,
`/einstellungen/<reiter>`, `/boards/neu`, `/board/<kürzel>` (Kürzel klein, etwa `/board/prod`), `/board/prod/131` (Karte
PROD-131 im Detail über dem Board), `/board/prod/liste|kalender|zeitachse`, `/board/prod/einstellungen/<reiter>`,
`/board/prod/archiv`, `/board/prod/papierkorb`. Das Kürzel bleibt beim Umbenennen fest und ist eindeutig, Verweise
brechen also nie. Das Backend liefert für jeden Pfad außerhalb von `/api` die Oberfläche aus; am Telefon gelten dieselben
Pfade mit der Telefonansicht.

## 7. Verbund

- **Kellerwolke**: Anmeldung; Anhänge in der Ablage der Pinnwand (je Board ein Ordner); Dateiwahl aus der eigenen
  Kellerwolke.
- **Assistent**: Werkzeuge zum Anlegen, Verschieben, Abfragen und Buchen, immer mit den Rechten der angemeldeten
  Person; ersetzt den alten Agenten-Zugang. Hinweise fließen in seine proaktiven Hinweise.
- **Transkription**: Karte mit Aufnahme und Transkript verknüpfen, Sprung zur Fundstelle; Spracheingabe beim Erfassen.
- **Vertonung**: Vorlesen von Karten, Tagesplan und Berichten.
- **Leitstelle**: KI an der Karte (zusammenfassen, Checkliste vorschlagen, aus Text Karten machen).
- **Push**: Mitteilungen auf das Telefon über die Web-App, je Art abschaltbar.

## 8. Betrieb

- Pi, Port 8420 (frei geprüft am 25.10.2026), Adresse und Datenordner aus der privaten Wahrheit
  (`handbuch ziel pinnwand`).
- Ausrollen über die Vorlage des Appkerns, Handbuch-Seite und Einrichtungsskript mit Probelauf je Fassung.
- Sicherung über das zentrale Sicherungswerkzeug (`~/Sicherungen`).
- Alte App: läuft nicht mehr; ihre Datenbank (`backend/pinnwand.db`, nicht im Repo) bleibt unverändert liegen.

## 9. Mockups

Im Ordner `mockups/` im echten Stack (Vite, Svelte 5, Bausteine des Leitstands, Marken des Appkerns) mit Beispieldaten:
nach der Freigabe werden diese Ansichten die Oberfläche der App, ein Entwurf kann also nicht schöner sein als die App.
Jeder Zustand hat seinen echten Pfad (vorgeführte Zustände mit `?entwurf=`, Telefon mit `?geraet=telefon`), eine
Galerie unter `/entwuerfe` ist der Einstieg; Regeln in `mockups/LEITFADEN.md`. Geprüft mit der Ansichtsprüfung des
Appkerns in 1920, 1440, 1100, 900 und 390 Pixeln, hell und dunkel. Das alte Board läuft dazu lokal mit einer Kopie seiner
Datenbank zum Vergleich. Nach der Freigabe sind die Entwürfe der Leitfaden; Änderungen an Aufbau und Optik erst dort.

## 10. Später

- Regeln je Board (etwa Grenzen je Spalte mit Warnung, Folgen beim Ablegen in einer Spalte)
- Lesefreigabe eines Boards per Link ohne Konto
- Urlaub mit Freigabe durch eine verantwortliche Person
- Pinnwand als Quelle im Fundus

## 11. Annahmen zu offenen Fragen (änderbar)

Wo der Entwurf eine Frage offen ließ, gilt bis zu einer anderen Entscheidung:

- Kartennummern werden nie wieder vergeben, auch nicht nach Rückgängig oder Löschen.
- Neue Karten bekommen die Kartenart ihres Boards (aus der Vorlage: Ideen legt Ideen an, die übrigen Arbeit), nicht
  eine aus der Zeiterfassung abgeleitete; mit Zeiterfassung wählt man beim Anlegen.
- Module bietet der Server erst mit ihrer Stufe an; vorher lassen sie sich nicht einschalten, und keine Ansicht zeigt sie.
- Eine Einladung schaltet die Person in der App frei (Einstellung Weitere Konten); entzogen wird der Zugang nur von Hand.
- Ein Konflikt entsteht nur, wenn dasselbe Feld inzwischen anders ist; andere Felder speichern weiter.
- Der Papierkorb leert sich nicht von selbst. Das Kürzel eines Boards im Papierkorb bleibt vergeben.
- Gebuchte Zeit bleibt bei endgültigem Entfernen einer Karte stehen und trägt deren gemerkten Namen (Stufe 2).
- Ein Termin ohne Karte zählt nicht ins Ist (Stufe 3).

