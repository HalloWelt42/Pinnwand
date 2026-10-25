# Pinnwand Neubau: Bauplan

Wie der Entwurf (`ENTWURF.md`) gebaut wird. Die Entwürfe unter `mockups/` sind freigegeben und der verbindliche
Leitfaden für Aufbau und Optik; die Oberfläche der App entsteht aus ihnen. Dieser Plan legt die Verträge fest, an die
sich jeder Teil hält.

## 1. Aufbau

```
backend/app/
  main.py           Gerüst des Appkerns, Router, Begleiter
  modell/           Pydantic-Modelle, dieselben wie mockups/src/modell.ts (Namen und Felder gleich)
  regeln/           reine Regeln ohne Ein- und Ausgabe, dieselben wie mockups/src/regeln/ (Rechte, Alterung,
                    Zeitfenster, Archiv, Kürzel, Verschieben samt Mitziehen, Abschlussdatum, Suche und Filter)
  verzeichnis/      SQLite über appkern.datenbank: Schema in Stufen, Zugriff je Aggregat, Journal
  anwendung/        Anwendungsfälle, der einzige Weg zu schreiben (Rechte, Regeln, Fassung, Journal, Ereignis); je
                    Bereich ein Modul: karten, inhalt, boards, aufbau, mitglieder, ordner, papierkorb, hinweise,
                    anhaenge; rahmen.py ist der Rahmen jeder Änderung, stand.py die Abfragen
  schnittstelle/    REST unter /api/v1 und der Ereignisstrom; je Bereich ein Router, beide nur über die Anwendung;
                    Adapter auf Dienste des Gerüsts hinter Schnittstellen der Anwendung (zugang.py: Weitere Konten,
                    ablage.py: Ablage der Kellerwolke für Anhänge)
frontend/src/       die Entwürfe (mockups/src) ohne Galerie und Entwurfsleiste; beispiel/ ist ersetzt durch daten/
tools/probebetrieb.py  das Backend mit der nachgestellten Kellerwolke der Tests, zum Prüfen der Oberfläche ohne echte
                    Zugangsdaten (Startkonfiguration "pinnwand-probe")
```

## 2. Daten

- Aggregate als Dokument: eine Zeile je Board und je Karte, der Inhalt als JSON in der Form des Modells, dazu die
  Spalten, nach denen gesucht oder geordnet wird (Kennung, Board, Schlüssel, Spalte, Reihe, Fassung). So gleichen sich
  Modell, Schnittstelle und Oberfläche ohne Umrechnung, und ein Vorher-Nachher ist eine Zeile.
- Tabellen der Stufe 1: `konten`, `boards`, `karten`, `gruppen` (je Board), `laufnummern`, `ordner`, `papierkorb`,
  `entfernt`, `vorlagen`, `hinweise`, `person_einstellungen`, `journal`. Stufe 2 bringt `zeiteintraege`, `timer`, `zeitkonten`,
  `abwesenheiten`; Stufe 3 `serien`, `termine`; Stufe 4 `berichte`.
- Reihenfolge der Karten einer Spalte über die Spalte `reihe` (Gleitkomma, Platz dazwischen); ein Verschieben schreibt
  nur die bewegten Karten, nie das Board. Wird der Platz zu eng, nummeriert die Spalte neu.
- Kartennummern (HAUS-12) zählt je Board eine eigene Zeile in `laufnummern`, nicht das Board selbst: so ändert eine
  neue Karte die Fassung des Boards nicht, und der Zähler kommt wie jede Zeile im Ereignis an. Er läuft nur vorwärts;
  eine Nummer wird nie wieder vergeben, auch nicht nach Rückgängig.
- Jede Zeile trägt eine `fassung` (ganze Zahl). Schreiben mit veralteter Fassung wird abgelehnt (409 mit dem aktuellen
  Stand), nie still überschrieben (Konflikt im Kartendetail, M-55).
- Personen sind Konten der Kellerwolke. Eingeladen wird per Kontoname der Kellerwolke: das Mitglied steht mit diesem
  Namen im Board, der Name kommt in die Einstellung "Weitere Konten" des Gerüsts (über die Schnittstelle `Zugang`;
  entzogen wird dort nur von Hand), beim ersten Anmelden entsteht das Konto der Pinnwand mit Kennung, Name und Kürzel,
  und wartende Einladungen gelten ab dann mit der Kennung.

## 3. Eine Änderung

Jeder Anwendungsfall läuft im Rahmen der Anwendung (`anwendung/rahmen.py`):

1. Recht prüfen (Rolle des Kontos im Board, Regel `hat_recht`; der Server ist die einzige Wahrheit, die Oberfläche blendet
   nur aus).
2. Regeln anwenden, Zeilen lesen und schreiben in einer Transaktion; jede geschriebene Zeile kommt mit Vorher und
   Nachher ins Journal.
3. Antwort: `{meldung, rueckgaengig, geaendert}`. `geaendert` sind die neuen Stände aller berührten Aggregate (oder ihr
   Wegfall); `rueckgaengig` ist die Kennung des Journaleintrags, wenn er sich zurücknehmen lässt.
4. Ereignis an alle Mitglieder der berührten Boards und an berührte Konten (dieselben `geaendert`).

Rückgängig (`POST /api/v1/rueckgaengig/{kennung}`) stellt die Vorher-Stände her, wenn jede Zeile noch ihren
Nachher-Stand hat; sonst lehnt es mit Grund ab (409). Rückgängig geht nur für eigene Änderungen und nur einmal; Zähler
bleiben dabei stehen. Es ist selbst eine Änderung mit Journal und Ereignis. Endgültiges (Papierkorb leeren) legt keinen
Rückweg an.

## 4. Schnittstelle

- `GET /api/v1/stand`: alles, was die angemeldete Person sieht (Konten, ihre Boards mit Laufnummern und Gruppen, deren
  Karten bis zur Archivgrenze, Ordner, Papierkorb, Hinweise, Vorlagen, Einstellungen); das Archiv seitenweise über
  `/boards/{id}/archiv`, eine Karte einzeln über ihren Schlüssel (`/karten/HAUS-12`; ein direkter Pfad öffnet jede Karte, M-09).
  Was jemand nicht sieht, kommt weder im Stand noch im Ereignis an.
- Schreiben: ein Weg je Anwendungsfall, benannt wie in `mockups/src/beispiel/anwendung/` (etwa `POST
  /api/v1/karten/{id}/verschieben`), Antwort wie oben. Feste Pfade stehen vor denen mit Kennung
  (`/karten/sammel/verschieben` vor `/karten/{id}/verschieben`).
- `GET /api/v1/ereignisse`: Server-Sent Events je Person; nach einem Abbruch holt die Oberfläche `stand` neu.

## 5. Oberfläche

- `frontend/src/daten/` ersetzt `beispiel/` mit denselben Namen: `stand.svelte.ts` (derselbe Zustand, gefüllt aus
  `/stand` und den Ereignissen), `abfragen.ts` (unverändert, rechnet auf dem Zustand), `anwendung/*` (dieselben
  Funktionen; sie rufen den Server und übernehmen die neuen Stände), `format.ts`. Der Rahmen einer Änderung wird asynchron: Erfolg erst nach
  der Antwort, die Meldung mit Rückgängig ruft den Rückweg des Servers.
- `HEUTE` und `JETZT` kommen aus einer Uhr, `ICH` aus der Sitzung des Appkerns.
- Wurzel wie Fundus: Einrichtung, Anmeldung und Schale aus dem Appkern, danach die Schale der Pinnwand.
- Was eine Stufe noch nicht hat, zeigt die Oberfläche nicht (Module, die es noch nicht gibt, stehen nicht zur Wahl).

## 6. Stufe 1: Board

Boards, Spalten, Karten mit der Mechanik des alten Boards, eigene Felder, Labels, Rollen und Rechte, Mitglieder,
Vorlagen, Ordner, Papierkorb und Archiv, Rückgängig, Ereignisstrom, Heute, Hinweise der Karten, Liste, Anhänge über die
Kellerwolke, Einstellungen der Person; Telefon mit Heute, schnell erfassen, Board ansehen und verschieben.

Reihenfolge: (1) Kern: Modell, Verzeichnis, Änderung mit Journal und Ereignis, `/stand`, Verschieben von Ende zu Ende,
Oberfläche mit Anmeldung und Board. (2) Die übrigen Anwendungsfälle je Bereich, jeweils Backend mit Tests und die
Oberfläche verdrahtet. (3) Ansichtsprüfung in allen Breiten, Abnahme gegen `ABNAHME_ENTWUERFE.md`, Handbuch-Seite,
Ausrollen auf den Pi.

## 7. Prüfen

- Tests je Anwendungsfall (Recht, Regel, Fassung, Journal, Rückgängig, Ereignis) gegen eine Datenbank im Speicher; der
  Verbundtest des Gerüsts gegen die Entwicklungs-Kellerwolke.
- Typprüfung der Oberfläche ohne Befund, Ansichtsprüfung (`tools/ansicht.sh`) in 1920, 1440, 1100, 900 und 390 Pixeln,
  hell und dunkel; jede Fähigkeit einmal in der echten Oberfläche geklickt.
- Ausrollen nur nach grünem Lauf.
