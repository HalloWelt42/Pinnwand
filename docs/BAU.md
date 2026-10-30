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
                    anhaenge, zeiterfassung, arbeitszeit; rahmen.py ist der Rahmen jeder Änderung, sicht.py die
                    Regel, wer welche Zeile sieht, stand.py die Abfragen, kartenbasis.py Lesen und Schreiben einer
                    Karte für alle Bereiche
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

## 7. Stufe 2: Zeit

Timer je Person, Zeiteinträge, Stundenzettel, Arbeitszeit und Urlaub mit Soll und Ist, Feiertage je Bundesland,
Jahreskalender und Team; am Telefon Timer und Zeit buchen. Der Server bietet die Module `zeiterfassung` und
`arbeitszeit` an (`MODULE_DA`).

### Daten

Felder wie `frontend/src/modell.ts`, dazu:

- `zeiteintraege` (Spalten konto, karte, board, datum): Zeiteintrag mit `board`, dem Board der Karte; danach richtet
  sich, wer ihn sieht. `gedeckelt` ist `{seit, bis, sekunden}`: die echte Sitzung als Zeitpunkte, die Spanne für
  Menschen rechnet die Oberfläche.
- `timer` (Spalten konto, karte, board): Timer mit `id` (gleich dem Konto, je Person einer) und `board`.
- `zeitkonten` (Spalten konto, ab): Zeitkonto mit `id`; je Konto und Tag `ab` eine Fassung.
- `abwesenheiten` (Spalten konto, von, bis): Abwesenheit.

### Wer was sieht

Eine Regel für Stand, Ereignis und Antwort (`anwendung/sicht.py`):

- Zeiteinträge und Timer: die Person selbst; dazu die Mitglieder des Boards mit dem Recht "Zeiten anderer sehen".
  Ohne das Recht ist die Zeit einer Karte die eigene, und die Oberfläche nennt sie so.
- Zeitkonten und Abwesenheiten: die Person selbst; dazu, wer mit ihr in einem Board mit dem Modul Arbeitszeit ist und
  dort das Recht "Abwesenheiten sehen" hat.
- Der Rahmen verteilt je Zeile und Person: den neuen Stand an alle, die ihn sehen; den Wegfall an alle, die nur den
  alten sahen. Die bisherigen Sonderwege (Zeilen je Board, je Person) sind Fälle dieser einen Regel.
- Ändern sich an einem Board Module, Rollen oder Mitglieder, lädt die Oberfläche den ganzen Stand neu, denn daraus folgt,
  was sie sieht.
- `stand` liefert dazu `kartennamen` (je Karte Kennung, Board, Schlüssel und Titel) für Karten, auf die sichtbare Einträge
  zeigen, die selbst nicht im Stand sind (archiviert, Board verlassen); endgültig entfernte stehen in `entfernt`.

### Ändern

- Timer und eigene Einträge: Recht "Eigene Zeit buchen" im Board der Karte; Einträge anderer: "Zeiten anderer
  bearbeiten". Ein Timer läuft nur auf Arbeit außerhalb einer Erledigt-Spalte.
- Zeitkonto und Abwesenheiten: nur die eigenen, und nur, wenn das Modul Arbeitszeit in einem eigenen Board an ist.
- Regeln einer Sitzung (`regeln/zeit.py`, wie `sitzungBuchen` der Entwürfe): gebucht wird bis jetzt; an Mitternacht
  zerlegt (jeder Teil trägt in `zerlegt` den Tag des Nachbarteils); ein Teil allein geht in den Timer-Eintrag der Karte
  an diesem Tag (`sitzungen`), sonst entstehen eigene Einträge; über 12 Stunden sind die ersten 12 gebucht, mit
  `gedeckelt`. Korrigieren bucht die Sitzung neu von `seit` bis zum genannten Ende ohne Deckel, Bestätigen nimmt nur
  den Vermerk.
- Timer enden und buchen bei: Ablegen in einer Erledigt-Spalte, Idee, Papierkorb (Karte, Spalte, Board), Entfernen
  eines Mitglieds (sein Timer im Board), Abschalten der Zeiterfassung (alle im Board). Die Meldung nennt die eigene
  gebuchte Zeit.
- Eine neue Abwesenheit ersetzt überlappende derselben Person (Serien kommen mit Stufe 3 dazu).
- Einträge eines endgültig gelöschten Boards bleiben; ohne Board gibt es keine Rechte mehr, sie ändert und löscht nur,
  wer sie gebucht hat. `Kartenname.zustand` (da, papierkorb, entfernt) sagt der Oberfläche, welche Zellen fest bleiben;
  über dem Stundenzettel steht die eigene Zeit auf entfernten Karten mit "Zeit löschen" (Nutzer 26.10.2026).

### Wege

Antwort wie immer (`{meldung, rueckgaengig, geaendert}`); Felder in camelCase.

| Weg | Inhalt | Anwendungsfall der Entwürfe |
|---|---|---|
| `POST /timer/starten` | `{karte}` | `starten` |
| `POST /timer/anhalten`, `/timer/fortsetzen`, `/timer/stoppen` | leer | `anhalten`, `fortsetzen`, `stoppen` |
| `POST /zeiten` | `{karte, datum, sekunden, notiz?}` | `buchen` |
| `POST /zeiten/tag` | `{karte, datum, sekunden}` | `setzeTageszeit` |
| `POST /zeiten/ticketzeit` | `{karte, sekunden}` (Summe der sichtbaren Einträge) | `ticketzeitSetzen` |
| `POST /zeiten/deckel` | `{ids, ende}` (Ende als `JJJJ-MM-TTTHH:MM`) | `deckelKorrigieren` |
| `POST /zeiten/deckel/bestaetigen` | `{ids}` | `deckelBestaetigen` |
| `POST /zeiten/{id}/dauer` | `{sekunden}` | `dauerAendern` |
| `POST /zeiten/{id}/datum` | `{datum}` | `datumAendern` |
| `POST /zeiten/{id}/notiz` | `{notiz}` (still, ohne Rückweg) | `notizAendern` |
| `DELETE /zeiten/{id}` | leer | Eintrag löschen |
| `POST /zeiten/entfernen` | `{karten}`: die ganze eigene Zeit auf diesen Karten, alle Tage, mit Rückweg | `zeitAufKartenLoeschen` |
| `POST /abwesenheiten` | `{von, bis, art, anteil?, notiz?}` | `eintragen` |
| `POST /abwesenheiten/entfernen` | `{ids}` | `entfernen` |
| `POST /zeitkonten` | `{ab, wochenstunden, tage, bundesland, urlaubsanspruch, resturlaubVorjahr, halbtage}` | `zeitkontoSpeichern` |
| `GET /team/{board}?von=&bis=` | Antwort `{personen, ist}`: `ist[konto][tag]` Sekunden aus allen Boards | Team |

`/team` zeigt mit dem Recht "Abwesenheiten sehen" alle Mitglieder des Boards, sonst nur dich; nur Tagessummen, keine
Einträge.

### Oberfläche

- Ansichten aus `mockups/src/ansichten/zeit/` (ohne Berichte, die kommen mit Stufe 4) und
  `mockups/src/ansichten/telefon/Zeiten.svelte`; Wege `/zeiten`, `/arbeitszeit[/kalender|urlaub|team]`, der Reiter
  Zeiten am Telefon; Timer im Kopf, Laufend in Heute, Zeiterfassung im Kartendetail.
- `daten/anwendung/timer.svelte.ts`, `zeiten.svelte.ts`, `abwesenheiten.svelte.ts` rufen die Wege oben. Solange der
  eigene Timer läuft, tickt die Uhr im Sekundentakt (M-85).

Reihenfolge: (1) Backend mit Tests gegen diesen Vertrag, (2) Oberfläche gleichzeitig dagegen, (3) zusammenführen,
Ansichtsprüfung, Rauchtest, Ausrollen.

## 8. Stufe 3: Planung

Serien und Termine je Board (Modul `serien`, dazu in `MODULE_DA`), in Heute, Kalender und Zeitachse; der Nachtrag am
Folgetag bucht die Zeit. Die Regeln der Tage sind dieselben wie `mockups/src/regeln/serien.ts`, im Server als
`regeln/serien.py`.

### Daten

- `serien` (Spalte board): Serie wie `frontend/src/modell.ts`, ohne `beruehrt`. Ob ein Serientag angefasst ist, steht
  an seiner Karte: unberührt ist sie, solange sie in der Zielspalte liegt, nicht erledigt ist, keine Zeit hat und ihr
  Verlauf nur die Zeile ihres Anlegens hat. Die Regel bekommt das über `tagKarte` (`angefasst`).
- `termine` (Spalten board, datum): Termin wie im Modell.
- Zeiteintrag: `karte` oder `termin` (genau eins), Herkunft dazu `termin`. Bestätigte Terminzeit zählt damit ins Ist
  und steht im Stundenzettel unter dem Termin (Nutzer: "Ja, nach Bestätigung").
- Serien und Termine sieht, wer Mitglied des Boards ist; ihre Zeiteinträge folgen der Regel der Stufe 2.

### Vorbuchung

Der Server legt die Karten der Serientage an, für jeden Tag von heute bis zum Ende des Vorlaufs mit dem Stand "heute"
oder "vorgebucht", der noch keine Karte hat (je Serie und Tag eine): in der Zielspalte, Titel mit Uhrzeit,
Beschreibung, Labels, die anwesenden Teilnehmer als Zuständige, fällig am Tag, Schätzung aus der Dauer, `serie`. Das
geschieht beim Anlegen, Ändern und Fortsetzen in derselben Änderung und einmal je Tag durch den Begleiter
`Vorbuchung` (als die Pinnwand selbst, Konto `pinnwand`; die Oberfläche zeigt dieses Konto als "Pinnwand").
Serienkarten bekommen keinen Hinweis "fällig"; sie stehen in Heute unter Serien.

- Ändern und Pause nehmen unberührte Vorbuchungen ab morgen zurück (sie entfallen ohne Papierkorb, die Vorbuchung legt
  sie bei Bedarf neu an); angefasste, vergangene und ausgelassene Tage bleiben.
- Löschen der Serie: unberührte Vorbuchungen in den Papierkorb, die übrigen Karten werden gelöst (`serie` leer).
- Eine Serienkarte in den Papierkorb legen lässt ihren Tag aus (`auslass`); Wiederherstellen nimmt den Auslass zurück.
- Eine ganztägige Abwesenheit nimmt die Person aus unberührten Vorbuchungen; bleibt niemand, entfällt die Karte (M-109).

### Nachtrag

Posten rechnet die Oberfläche wie `nachtrag` der Entwürfe (vergangene 31 Tage, nur eigene, nur in Boards mit
Zeiterfassung). Bestätigen bucht einen Zeiteintrag (Herkunft `serie` auf der Karte des Tags, die nach Erledigt geht und
den Tag als Abschluss behält; Herkunft `termin` mit `von` und `bis` des Termins); Verwerfen nimmt die Person heraus, ist
sie allein, geht die Karte in den Papierkorb und der Tag gilt als verworfen (beim Termin: sie ist nicht mehr
Teilnehmer). Recht dafür: "Eigene Zeit buchen".

### Rechte

"Serien verwalten": Serien und Termine anlegen, ändern, pausieren, fortsetzen, löschen, einen Tag auslassen. Zusagen,
Bestätigen und Verwerfen: die teilnehmende Person selbst. Ein neuer Termin bringt den übrigen Teilnehmern einen
Hinweis der Art `termin`.

### Wege

| Weg | Inhalt | Anwendungsfall der Entwürfe |
|---|---|---|
| `POST /serien` | Serie ohne `id`, `auslass`, `verworfen`, Pause | `serieAnlegen` |
| `PATCH /serien/{id}` | Teile der Serie (wie beim Anlegen) | `serieAendern` |
| `POST /serien/{id}/pausieren`, `/serien/{id}/fortsetzen` | leer | `pausieren`, `fortsetzen` |
| `DELETE /serien/{id}` | leer | `serieLoeschen` |
| `POST /serien/{id}/auslassen` | `{tag}` | `tagAuslassen` |
| `POST /serien/{id}/bestaetigen` | `{tag, sekunden}` | `nachtragBestaetigen` (Serie) |
| `POST /serien/{id}/verwerfen` | `{tag}` | `nachtragVerwerfen` (Serie) |
| `POST /termine` | `{board, titel, datum, von, bis, ort?, teilnehmer}` | `terminAnlegen` |
| `POST /termine/{id}/zusagen` | `{ja}` | `zusagen` |
| `POST /termine/{id}/bestaetigen`, `/termine/{id}/verwerfen` | leer | `zeitBestaetigen`, `zeitVerwerfen` |
| `POST /nachtrag` | `{posten: [{art, bezug, tag, sekunden?}]}` | `alleBestaetigen` (eine Änderung) |

### Oberfläche

Ansichten `mockups/src/ansichten/planung/` Serien, SerieBearbeiten, Teilnehmer, Nachtrag; Wege `/serien`,
`/serien/neu`, `/serien/<kennung>`; Heute, Kalender und Zeitachse lesen Serien und Termine schon aus dem Zustand. Der
Stundenzettel führt Termine als eigene Zeilen.

## 9. Stufe 4: Verbund, zuerst Berichte

Berichte brauchen keine andere App außer der Kellerwolke; sie kommen zuerst (Modul `berichte` in `MODULE_DA`). Die
Anbindungen an Assistent, Transkription, Vertonung, KI und Push folgen je mit eigenem Vertrag; Push ist ein Baustein des
Appkerns (ENTWURF §11).

### Berichte

- Arten wie `mockups/src/ansichten/zeit/bericht.ts`: Stundennachweis je Person (Soll, Ist, Differenz je Tag mit
  Karten und Abwesenheiten), Zeiten je Board und Karte, erledigte Karten. Den Inhalt (`BerichtInhalt`: Titel, Zeitraum,
  Abschnitte mit Spalten, Zeilen, Summe, Fuß) rechnet der Server, mit denselben Regeln wie die Oberfläche (Soll aus dem
  Zeitkonto mit Feiertagen, Halbtagen und Abwesenheiten in `regeln/arbeitszeit.py`).
- Wer was im Bericht sieht: im Stundennachweis du und, wen du über "Abwesenheiten sehen" siehst (wie im Team), Ist aus
  allen Boards, Karten nur, wo du ihre Zeit siehst; in den Board-Berichten nur Boards mit dem Modul Berichte und dem Recht
  "Berichte erstellen", Zeiten anderer nur mit "Zeiten anderer sehen".
- Formate: PDF (Schrift Barlow, eingebettet), Tabelle (CSV mit Semikolon, UTF-8 mit Kennung, für Tabellenprogramme),
  Markdown. Die Datei liegt in der Ablage der Pinnwand in der Kellerwolke im Ordner `Berichte`; der Eintrag
  (`berichte`, Spalte konto) gehört der Person, die ihn erstellt hat, und nur sie sieht und lädt ihn.

| Weg | Inhalt |
|---|---|
| `POST /berichte/vorschau` | Auswahl `{art, von, bis, boards, personen, format}`; Antwort `BerichtInhalt` |
| `POST /berichte` | dieselbe Auswahl; erstellt die Datei und den Eintrag |
| `GET /inhalt/berichte/{id}` | die Datei (über das Inhalts-Cookie wie bei Anhängen) |

### KI an der Karte

Modul `ki` in `MODULE_DA`, ohne eigene Rechte: Vorschläge holt, wer das Passende darf. Die KI schlägt nur vor; übernommen
wird nur, was die Person in der Vorschau bestätigt, und zwar über die gewohnten Anwendungsfälle (mit Rückgängig).

- Vier Vorschläge: **Zusammenfassung** der Karte aus Titel, Beschreibung, Notizen, Checkliste und Kommentaren (jedes
  Mitglied; übernehmen in die Notizen mit "Karten bearbeiten"); **Checkliste** mit neuen Punkten, ohne die vorhandenen
  ("Karten bearbeiten"); **Labels** aus denen des Boards, die die Karte noch nicht hat ("Karten bearbeiten"); **Karten aus
  Text** mit Titel, Beschreibung und Checkliste je Karte ("Karten anlegen").
- Gerechnet wird über die Leitstelle (Anschluss `Sprachmodell` in der Anwendung, umgesetzt in
  `schnittstelle/sprachmodell.py` mit `geruest.leitstelle`). Das Modell wählt die Einstellung `ki_modell` aus den
  Textmodellen der Leitstelle; leer gilt die Kette der App. Ohne eingerichtete Leitstelle zeigt die Oberfläche keine
  Vorschläge (`ki_bereit` im Stand), die Seite der Module sagt warum.
- Jede Anfrage hat eine feste Antwortform (JSON-Schema); Begründung vor Listen. Labels wählt das Modell über Kennungen
  der Anfrage (L1, L2, ...), der Server bildet sie auf die echten ab und verwirft Unbekanntes. Alles vom Modell
  Geschriebene geht durch die Säuberung des Appkerns (nur gerade Zeichen); Punkte und Titel werden gekürzt,
  Doppeltes und Vorhandenes fällt weg.
- Fehler der Leitstelle kommen als Ablehnung mit Grund (503 nicht eingerichtet oder kann gerade nicht, 502 Antwort nicht
  lesbar); nichts wartet still. Priorität "hoch", weil eine Person wartet.

| Weg | Inhalt |
|---|---|
| `POST /karten/{id}/ki/zusammenfassung` | Antwort `{text}` |
| `POST /karten/{id}/ki/checkliste` | Antwort `{punkte}` (Texte) |
| `POST /karten/{id}/ki/labels` | Antwort `{labels}` (Kennungen des Boards) |
| `POST /boards/{id}/ki/karten` | `{text}`; Antwort `{karten: [{titel, beschreibung, checkliste}]}` |
| `POST /boards/{id}/karten/mehrere` | `{spalte, art, karten}`; legt alle in einer Änderung an (ein Rückgängig) |

### Transkripte

Modul `transkripte` in `MODULE_DA`, ohne eigene Rechte. Die Transkription ist eine App des Verbunds; ihre Adresse steht
in der Einstellung `transkription_adresse`. Die Pinnwand ruft sie über den Baustein `appkern.verbund` mit ihrem
App-Schlüssel der Kellerwolke und **im Auftrag der Person** (Kopf `X-Kellerwolke-Sitzung`): suchen, abspielen und
sprechen kann nur, wer die Transkription selbst nutzen darf. Was an der Karte steht, sehen alle Mitglieder.

- **Marke** an der Karte (`TranskriptMarke`, Mechanik M-112 und M-113): Kennung, Transkript, Name, Sekunde (ohne: das
  ganze Transkript), Sprecher und Text des Abschnitts an der Stelle, eine Notiz, wer und wann. Name, Sprecher und Text
  holt der Server beim Verknüpfen aus dem Transkript (die Oberfläche schickt nur Transkript und Sekunde). Verknüpfen,
  Notiz und Entfernen mit "Karten bearbeiten", mit Verlaufszeile und Rückgängig.
- **Suchen** wie in der Transkription (Name und Text, Fundstellen mit Zeit und Ausschnitt); verknüpft wird eine Fundstelle
  oder das ganze Transkript.
- **Abspielen ab der Stelle** in der Pinnwand: `GET /inhalt/transkripte/{karte}/{marke}/ton` reicht die Abspielfassung
  der Transkription durch (Bereichsanfragen, damit Springen in langen Aufnahmen nur das Nötige lädt); dazu "In der
  Transkription öffnen" (`<adresse>/transkripte/<id>/<sekunde>`).
- **Notiz vorschlagen** (mit dem Modul KI an der Karte): aus den Abschnitten um die Stelle (30 Sekunden davor, 90 danach).
- **Spracheingabe beim Erfassen** am Telefon mit dem Aufnahme-Baustein des Appkerns (Nutzer: "Ja, stückweise live"):
  die Live-Mitschrift schneidet an Sprechpausen (5 bis 15 Sekunden) und schickt jedes Stück an `POST /boards/{id}/sprache`
  (weiter an `/api/v1/hoeren` der Transkription); der Text wächst beim Sprechen, nach dem Stopp kommt das letzte Stück.
  Der erste Satz wird Titel, alles die Beschreibung, sichtbar vor dem Anlegen; die Aufnahme selbst wird verworfen.
- Ohne eingetragene Adresse zeigt die Oberfläche das Modul nicht an (`transkription_adresse` im Stand leer); Fehler der
  Transkription kommen als Ablehnung mit Grund (503 nicht erreichbar, 403 kein Zugang).

| Weg | Inhalt |
|---|---|
| `GET /karten/{id}/transkripte/suche?text=&ab=` | Seite der Treffer mit Fundstellen |
| `POST /karten/{id}/transkripte` | `{transkript, sekunde}`; verknüpft eine Stelle |
| `POST /karten/{id}/transkripte/{marke}/notiz` | `{notiz}` |
| `DELETE /karten/{id}/transkripte/{marke}` | entfernt die Marke |
| `POST /karten/{id}/transkripte/{marke}/ki/notiz` | Vorschlag `{text}` |
| `GET /inhalt/transkripte/{karte}/{marke}/ton` | Ton der Aufnahme, auch mit dem Inhalts-Cookie |
| `POST /boards/{id}/sprache` | ein Stück Ton (mehrteilig, Feld `datei`, wie der Hördienst der Transkription); Antwort `{text}` |

### Vorlesen

Modul `vorlesen` in `MODULE_DA`, ohne eigene Rechte (Mechanik M-114). Die Vertonung ist eine App des Verbunds; ihre
Adresse steht in `vertonung_adresse`, Stimme und Tempo in `vorlesen_stimme` und `vorlesen_tempo` (angeboten werden nur
Stimmen aus dem Katalog der Vertonung und private, die sie der Pinnwand freigibt; nie gesammelte fremde). Gefragt wird
über `appkern.verbund` im Auftrag der Person.

- Vorgelesen wird, was die Oberfläche zeigt: die Beschreibung (Knopf am Feld), die ganze Karte (Kopf des Details: Titel,
  Beschreibung, offene Punkte), ein Kommentar (Lautsprecher am Kommentar), der Tagesplan in Heute (Überfälliges, Heute,
  Termine, Serien) und ein Bericht (in der Vorschau, in der Liste bei Markdown). Markdown wird vorher zu Klartext.
- `POST /vorlesen` mit `{text, board}` (ohne Board: Heute und Berichte, dann muss das Modul in einem Board der Person an
  sein): der Server prüft Modul und Länge (höchstens 40 000 Zeichen), teilt an Satzgrenzen in Teile von höchstens 7500
  Zeichen (die Vertonung nimmt je Aufruf 8000) und reicht den Strom der Vertonung Satz für Satz weiter
  (`application/x-ndjson`, Zeilen `satz`, `ende`, `fehler` wie bei der Vertonung, die Sätze über alle Teile
  durchgezählt). Fehler vor dem ersten Satz als HTTP-Ablehnung, danach als Zeile `fehler`.
- Gespielt wird mit dem Vorleser des Appkerns (Satz für Satz lückenlos, im Tippen gestartet, ein zweites Tippen hält an,
  immer nur ein Ton). Ohne eingetragene Adresse zeigt die Oberfläche keine Knöpfe zum Vorlesen.
- Nachtrag vom 30.10.2026 (HELF-34, Nutzer: "Alle Kommentare vorlesbar machen ... mit leichtem Vorlauf ... bei
  Auslastung mehr Vorlauf", "Alles vorlesbar machen"): dazu Notizen, Checkliste (offene, dann erledigte Punkte), alle
  Kommentare und der Verlauf (je neueste zuerst, wie angezeigt), am Telefon die ganze Karte und alle Kommentare. Der
  Vorleser des Appkerns (ab 0.61) spielt mit Vorlauf: erst ab 1,5 Sekunden bereitem Ton, bei langsamer Vertonung
  gemessen mehr (höchstens 20), nach einem Abriss wieder mit Vorlauf und für die nächsten Läufe mehr.

| Weg | Inhalt |
|---|---|
| `POST /vorlesen` | `{text, board}`; Antwort: Strom der Sätze |

### Endgültig löschen und Konten

Nachträge vom 26.10.2026 (Wünsche des Nutzers): Karten und Boards lassen sich ohne Papierkorb endgültig löschen, Konten
zurücksetzen und löschen. Alles ohne Rückweg; zur Sicherheit tippt die Person ein Wort ein, das der Server prüft
(Schlüssel der Karte, Kürzel des Boards, Name des Kontos; Groß und klein egal).

- Karte: Rechte "Karten löschen" und "Papierkorb leeren"; sie geht wie über den Papierkorb (Timer bucht, Serientag
  ausgelassen) und gleich weiter wie beim Leeren (ihr Name bleibt in `entfernt`, gebuchte Zeiten bleiben).
- Board: Rechte "Board verwalten" und "Papierkorb leeren"; mit Karten, Gruppen, Laufnummer, Serien und Terminen, das
  Kürzel wird frei, gebuchte Zeiten bleiben. Auch das Leeren eines Board-Eintrags im Papierkorb nimmt jetzt Serien und
  Termine mit.
- Konto: selbst oder als Besitzer der App (Kontoname des App-Schlüssels, Anschluss `Zugang.besitzer`; der Stand meldet
  `app_besitzer`). Boards, in denen das Konto allein angemeldet ist, gehen endgültig; aus geteilten wird es ausgetragen
  (`mitglieder.austragen`: Timer bucht, Zuständigkeit offener Karten, Serien, Termine, Ordner), als einziger Besitzer
  geht der Besitz an das nächste angemeldete Mitglied. Ganz weg: Zeiteinträge, Timer, Zeitkonten, Abwesenheiten,
  Hinweise, Ordner, Vorlagen, Berichte, persönliche Einstellungen, sein Journal (Rückgängig) und seine Geräte für
  Mitteilungen. Zurücksetzen legt das Konto gleich neu an, mit neuer `anlage`; die Oberfläche vergisst dann ihre
  Merker je Board und Telefon und lädt neu. Löschen nimmt die Zeile heraus; die Oberfläche des Kontos meldet sich ab,
  und eine neue Anmeldung legt es neu an.

| Weg | Inhalt |
|---|---|
| `POST /karten/{id}/endgueltig` | `{bestaetigung}` (Schlüssel) |
| `POST /boards/{id}/endgueltig` | `{bestaetigung}` (Kürzel) |
| `POST /konten/{id}/zuruecksetzen` | `{bestaetigung}` (Name des Kontos) |
| `POST /konten/{id}/entfernen` | `{bestaetigung}` (Name des Kontos) |
| `POST /boards/{id}/ordner` | `{ordner, stelle}`: Stelle im Ordner ab 0 (Ziehen in der Seitenleiste), ohne ans Ende |

### App-Zugang als eigene Person

Nachtrag vom 30.10.2026 (HELF-43, Nutzer: "du als Helfer bist also auch eine Board-Person, ich sehe deine Zeiten").
Wer sich mit dem App-Schlüssel eines Zugangs der Kellerwolke anmeldet (Anmeldung mit `app`, nicht im Auftrag eines
Menschen), ist eine eigene Person: Kennung `<Person>.app-<zugang>`, Name und Kürzel aus dem Zugang, eigene Farbe,
`kellerwolke` = `Konto/Zugang` (admin/Helfer), `app` und `inhaber`. Eingeladen wird sie mit diesem Namen (`KONTONAME`
erlaubt den Schrägstrich, "Weitere Konten" bekommt ihn nicht); als Besitzer der App zählt sie wie ihr Inhaber
(`Konto.kellerwolke_konto`). Beim ersten Anmelden übernimmt sie nur sicher Erkennbares: Zeiteinträge des Inhabers mit
der Notiz "Zugang: ..." und die Mitgliedschaft (Rolle Mitglied) im Board, das wie der Zugang heißt. Kommentare und
Verlauf von früher bleiben beim Inhaber (darin ist nicht zu unterscheiden, wer schrieb).

### Gesamtnummer der Karten

Nachtrag vom 30.10.2026 (HELF-49, Nutzer: "Alle Tickets müssen durchnummeriert sein als 2. ID ... das muss eine Logik
im Programm hart regeln"). Neben dem Schlüssel im Board (HAUS-12) trägt jede Karte `nummer`, fortlaufend über alle
Boards, angezeigt als "# 101" klein über dem Titel, kopierbar und durchsuchbar (#101).

- Vergabe nur im Rahmen einer Änderung über `Kontext.neue_nummern` (Schlüssel und Gesamtnummer zusammen), aus dem Zähler
  `karten` in der Tabelle `zaehler` (Schemastufe 5, nur vorwärts wie die Laufnummern, für niemanden sichtbar). Jeder Weg,
  auf dem eine Karte entsteht (anlegen, mehrere, Duplizieren, Serien), holt sie dort; scheitert die Änderung, rollt die
  Transaktion den Zähler mit zurück, es entsteht keine Lücke.
- Eindeutig auch in der Datenbank: Spalte `karten.nummer` mit eindeutigem Index. Umzug, Papierkorb (die Karte trägt ihre
  Nummer im Eintrag) und Löschen ändern keine Nummer; eine Nummer wird nie wieder vergeben, nie wird neu nummeriert.
- Nachtrag beim ersten Start mit der Stufe (`anwendung/gesamtnummer.py`): alle vorhandenen Karten samt Papierkorb in der
  Reihenfolge der Anlage (in derselben Sekunde nach der Nummer im ersten Board), die älteste ist # 1; Rückgängig von
  Änderungen aus der Zeit davor gilt danach nicht mehr (es ginge auf Stände ohne Nummer zurück).

### Ordnung der Spalten

Nachtrag vom 30.10.2026 (HELF-50, Nutzer: "das neueste Ticket landet immer oben", "nach unten scrollen wir in die
Vergangenheit", "offene Tickets sortieren sich nach Prio", "erledigte nur nach Abarbeitung", Sortierung je Spalte bei
neuen Boards festlegbar wie das Zeitfenster, "mit Mini-Icons umschaltbar", "ab 50 laden automatisch nach beim
Weiterscrollen, durchsucht werden kann aber immer alles").

- Jede Spalte hat eine Sortierung (`Spalte.sortierung`, `Spaltensortierung`): `prioritaet` (Dringend bis ohne, bei
  gleicher Priorität die neueste Karte oben), Fälligkeit (früheste oben, ohne Datum unten), `arbeitsbeginn`
  (zuletzt in die Spalte gekommen oben; in einer Spalte wie Dran ist das der Beginn der Arbeit), `erledigung` (zuletzt
  erledigt oben, am selben Tag die zuletzt abgelegte), `anlage` (zuletzt angelegt oben) und `hand` (Reihe von Hand).
  Ohne Angabe gilt `erledigung` für die Erledigt-Spalte und `prioritaet` für alle anderen. Bei Gleichstand bleibt die
  Reihe von Hand. Eine Wahrheit für Board, Liste und Telefon: `spaltenOrdnung` in `frontend/src/daten/abfragen.ts`.
- Die Sortierung der Spalte ist die Vorgabe für alle (Menü der Spalte und Einstellungen, Spalten; Recht "Board
  verwalten"; Weg zum Ändern der Spalte mit `sortierung`). Jede Person stellt sie sich wie das Zeitfenster für sich an
  diesem Gerät um, mit dem kleinen Symbol im Kopf der Spalte (Ansichtszustand, `ansicht.svelte.ts`). Die
  Werkzeugleiste hat keine eigene Sortierung mehr; sie war dieselbe Sache an zweiter Stelle.
- Vorlagen tragen die Sortierung je Spalte (`VorlageSpalte.sortierung`), eine aus einem Board gespeicherte Vorlage
  übernimmt sie. Mitgeliefert: offene Spalten `prioritaet`, in Arbeit (Dran, In Arbeit, Umsetzen) `arbeitsbeginn`,
  Erledigt `erledigung`.
- Neue Karten kommen oben in die Spalte: anlegen, mehrere, duplizieren, umziehen, Serienkarten und jedes Verschieben
  ohne Platz (Status im Detail, Telefon, Liste, Sammelaktion; mitgezogene Verknüpfte direkt darunter). `einreihen` ohne
  Platz heißt oben. Ziehen von Hand legt nur in einer Spalte mit `hand` an den Platz; in einer sortierten Spalte steht
  die Karte, wo die Sortierung sie hinstellt, und innerhalb der Spalte umsortieren geht nicht.
- Jede Spalte zeigt zuerst so viele Karten wie der Ladeschritt des Boards (anfangs 50) und lädt beim Rollen ans Ende die
  nächsten; ebenso die Liste und die Spalte am Telefon. Suche und Filter laufen immer über alle Karten des Stands, nicht
  nur über die gezeigten; Zahl und Grenze im Kopf zählen alle.

### Commits an Karten

Nachtrag vom 30.10.2026 (HELF-35, Nutzer: Commits "in Tickets verankert", Quellen "GitHub oder GitLab, lokal oder
online", "Einrichtungslogik wegen multipler Services ... alles gleichsam nutzbar"; Entscheide: Kennung im Commit plus von
Hand, alle Quellen mit Ziel je Repo, Nachtrag automatisch und dann prüfen; Auftrag: lokaler Sammler als eigenes kleines
Programm, in Stufen ausrollen).

- Ein eigenes kleines Programm, der Commitsammler (`sammler/commitsammler.py`, nur Python und git), liest Commits aus
  den Git-Repos eines Rechners und spielt sie ein. Alle Einstellungen und Zugänge zu Git-Verwaltungen bleiben bei ihm
  (`~/.config/pinnwand/commits.toml`, Vorlage `sammler/commits.beispiel.toml`): Adresse der Pinnwand, Schlüsseldatei,
  beliebig viele Git-Verwaltungen gleichberechtigt (Name, Rechner wie im Remote, Muster des Verweises), Wurzeln und
  Besitzer der Repos, je Repo das Ziel des Verweises oder "lokal". Die Pinnwand bekommt nur die Werte.
- `POST /commits/einspielen` mit `{repo: {kennung, name, quelle, verweis}, commits: [{hash, autor, zeit, nachricht,
  dateien}]}` (höchstens 500 je Sendung), nur der Besitzer der App; Antwort `{neu, verknuepft}`. `verweis` ist das
  Muster mit `{hash}`; ohne zeigt die Pinnwand den Commit selbst (Nachricht, Autor, Zeit, Dateien). Wiederholtes
  Einspielen schreibt nur Neues oder Geändertes; ein geänderter Verweis zieht in alle Bezüge nach. Eingespieltes kommt
  nicht ins Journal (kein Rückweg, sonst wüchse es mit jeder Sendung).
- Tabelle `commits` (Schemastufe 6, Spalten repo, zeit; Kennung `repo@hash`): jeder bekannte Commit, für niemanden im
  Stand. Tabelle `commitbezuege` (Spalten commitkennung, karte, board; Kennung fest aus Commit und Karte): je Commit und Karte eine
  Zeile mit allem, was die Karte zeigt, und `art` (`kennung`: Schlüssel in der Nachricht, `hand`: von Hand),
  sichtbar für die Mitglieder des Boards wie Karten. Eine umziehende Karte nimmt ihre Bezüge mit.
- Verknüpft wird jeder Schlüssel in der Nachricht (Kürzel, Bindestrich, Nummer, etwa HELF-12; auch frühere Schlüssel
  einer umgezogenen Karte), wenn es die Karte gibt. Von Hand: `GET /karten/{id}/commits/suche?text=` (Anfang des Hashs
  oder Wörter der Nachricht, neueste zuerst, höchstens 20), `POST /karten/{id}/commits` mit `{commit}`, lösen mit
  `DELETE /karten/{id}/commits/{bezug}`; beides mit dem Recht "Karten bearbeiten", Verlaufszeile und Rückgängig. Ein
  gelöster Bezug aus der Nachricht bleibt als `geloest` stehen, damit der nächste Abgleich ihn nicht wieder anhängt.
- Der Nachtrag ist ein Lauf des Sammlers über die ganze Geschichte (`--alles`); danach sendet er je Repo nur, was
  seit dem letzten Lauf dazukam.
- Stufe 1: Sammler für Repos auf dem Rechner, Verknüpfen über die Kennung und von Hand, Anzeige im Kartendetail und
  am Telefon.
- Stufe 2: Vorschläge für unsichere Zuordnungen (`art` "vorschlag" mit `grund`): ein bekannter Hash (7 bis 40
  Zeichen, mindestens ein Buchstabe, eindeutig) in Beschreibung oder Kommentaren einer Karte, und Commits ohne
  Kartenschlüssel aus dem Repo, das der Titel vorn nennt ("Pinnwand: ..."), aus der Arbeitszeit der Karte (vom Wechsel
  in eine Spalte, die weder die erste noch Erledigt ist, bis zum nächsten Wechsel oder Abschluss); höchstens 20 je Karte
  und Lauf. `POST /commits/vorschlaege` (Besitzer der App, der Sammler ruft es nach jedem Lauf), am Ticket
  `POST /karten/{id}/commits/{bezug}/bestaetigen` (wird wie von Hand) oder verwerfen über Lösen (bleibt gelöst).
- Später: Git-Verwaltungen ohne lokale Kopie über ihre Schnittstelle (Zugang im Sammler), regelmäßiger Lauf des
  Sammlers (wartet auf das Ja des Nutzers).

## 10. Prüfen

- Tests je Anwendungsfall (Recht, Regel, Fassung, Journal, Rückgängig, Ereignis) gegen eine Datenbank im Speicher; der
  Verbundtest des Gerüsts gegen die Entwicklungs-Kellerwolke.
- Typprüfung der Oberfläche ohne Befund, Ansichtsprüfung (`tools/ansicht.sh`) in 1920, 1440, 1100, 900 und 390 Pixeln,
  hell und dunkel; jede Fähigkeit einmal in der echten Oberfläche geklickt.
- Ausrollen nur nach grünem Lauf.
