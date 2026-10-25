---
zweck: "Plant Arbeit auf Boards: Karten in Spalten mit der Mechanik der alten Pinnwand, mehrere Boards mit eigenen Mitgliedern, Rollen und Rechten, angemeldet mit dem Konto der Kellerwolke, live für alle Beteiligten."
geraet: [pi]
abhaengigkeiten: [kellerwolke, appkern]
daten:
  - "Pi: {{wurzel}}/daten/pinnwand.sqlite, alle Boards, Karten, Ordner, Hinweise, Vorlagen, das Journal für Rückgängig und die Einstellungen"
  - "Kellerwolke: Anhänge der Karten in der Ablage der Pinnwand, ein Ordner je Board"
sicherung:
  - "Datenbank: jede Nacht ab 3 Uhr und vor jedem Ausrollen eine Kopie nach {{wurzel}}/sicherungen (die jüngsten zehn bleiben); das Werkzeug Sicherungen holt sie auf den Mac"
  - "Anhänge: liegen in der Kellerwolke und sind mit ihr gesichert"
schluessel_orte:
  - "Pi: Einstellungen in {{wurzel}}/daten/pinnwand.sqlite: App-Schlüssel der Kellerwolke (in der Oberfläche unter Einstellungen, verdeckt)"
  - "Pi: {{wurzel}}/zertifikate/, Blattzertifikat mit Schlüssel aus der Hausstelle"
  - "Mac: backend/.env.test im Klon, Modus 0600, Testzugang zur Kellerwolke der Entwicklung (nur für den Verbundtest)"
einrichten: einrichten.sh
stand: bea0d74
---

# Pinnwand

## Zweck

Die Pinnwand plant Arbeit auf Boards: Karten wandern durch Spalten, verknüpfte Karten ziehen mit, eine Erledigt-Spalte
hält das Abschlussdatum, Erledigtes geht nach einer Frist ins Archiv. Jedes Board hat eigene Mitglieder mit Rollen und
Rechten, eigene Felder und Labels; jede Person ordnet ihre Boards in eigenen Ordnern. Änderungen erscheinen sofort bei
allen, die das Board sehen, und lassen sich in der Meldung rückgängig machen.

Angemeldet wird mit dem Konto der [[Kellerwolke]]; wer zu einem Board eingeladen wird, darf die App ab dann nutzen.
Anhänge liegen in der Kellerwolke. Die Oberfläche läuft am Rechner und als eigene Ansicht am Telefon unter {{adresse}}.

Die Pinnwand entsteht in Stufen: zuerst die Boards (Stufe 1), dann Zeit, Planung und Verbund. Was eine Stufe noch nicht
hat, zeigt die Oberfläche nicht.

## Was sie braucht

- Pi nach [[Grundlage Pi]] mit Docker; die Pinnwand läuft dort als Compose-Projekt aus `compose.pi.yml` (die App und ihr
  Vorschaltdienst `vorne` mit dem Zertifikat der Hausstelle), ausgerollt vom Mac.
- Mac nach [[Grundlage Mac]] mit Python und Node.js für die Entwicklungsumgebung (`./einrichten.sh`); das Ausrollen prüft
  mit ihr (Tests, Bau der Oberfläche).
- [[Kellerwolke]]: Anmeldung mit dem eigenen Konto und ein App-Schlüssel für die Pinnwand (Kellerwolke, Einstellungen,
  Zugänge).
- [[Appkern]]: Gerüst, Anmeldung und Oberfläche; Oberfläche und Backend sind auf denselben Commit festgelegt.

## Neu einrichten

Zwei Wege. Aus der Sicherung: die jüngste Kopie der Datenbank zurück auf den Pi; dann ist alles wie vorher, auch
Besitzer, App-Schlüssel, Mitglieder und Boards. Frisch: leere Datenbank, neuer App-Schlüssel, erste Einrichtung im
Browser, Boards neu anlegen.

Die Schritte laufen am Mac, wenn nichts anderes dasteht.

### 1. Repo und Entwicklungsumgebung am Mac

```
git clone {{repo}} {{ordner}}
cd {{ordner}} && ./einrichten.sh
```

`./einrichten.sh` legt die Python-Umgebung an, holt die Pakete der Oberfläche und baut sie, legt den Appkern auf einen
Commit fest und setzt die Git-Haken.

Probe: `test -f frontend/dist/index.html && backend/.venv/bin/python -m pytest -q` ist grün (der Verbundtest ist ohne
`backend/.env.test` übersprungen).

### 2. Betrieb auf dem Pi

Auf dem Pi den Ordner vorbereiten, bevor Docker ihn anlegt (sonst gehört er root):

```
mkdir -p {{wurzel}}/daten {{wurzel}}/sicherungen
```

Aus der Sicherung zusätzlich die jüngste Kopie als `{{wurzel}}/daten/pinnwand.sqlite` ablegen (Besitzer `pi`, Benutzer
1000 im Container). Dann am Mac `tools/ausrollen.sh`: es prüft (Tests, Bau), holt den Stand auf den Pi, stellt das
Zertifikat aus, baut das Abbild, startet die Pinnwand mit ihrem Vorschaltdienst und prüft Fassung und Antwort.

Probe: `curl -s --cacert zertifikate/rootCA.pem {{adresse}}/api/v1/app` meldet `"fassung": "{{fassung}}"`.

### 3. Erste Einrichtung

Aus der Sicherung entfällt sie: die Datenbank bringt Besitzer und App-Schlüssel mit. Frisch: in der [[Kellerwolke]]
einen App-Schlüssel für die Pinnwand anlegen, dann {{adresse}} im Browser öffnen und mit dem Einrichtungscode aus
`{{wurzel}}/daten/einrichtungscode` (auf dem Pi) die Adresse der Kellerwolke und den Schlüssel eintragen; danach mit
dem eigenen Kellerwolke-Konto anmelden. Wem der App-Schlüssel gehört, ist Besitzer der App.

Probe: `curl -s --cacert zertifikate/rootCA.pem {{adresse}}/api/v1/app` meldet `"einrichtung_noetig": false` und den
Besitzer; nach der Anmeldung zeigt die Pinnwand Heute und "Live verbunden" im Fuß.

### 4. Weitere Personen

Andere Personen kommen über ein Board dazu: in den Einstellungen des Boards unter Mitglieder per Kontoname der
Kellerwolke einladen. Die Einladung trägt den Namen unter Einstellungen, Weitere Konten ein; ab dann darf die Person
sich anmelden und sieht das Board. Entzogen wird der Zugang dort nur von Hand.

Probe: die eingeladene Person meldet sich an und sieht das Board in der Seitenleiste.

## Sicherung und Rückspielen

Datenbank: die App legt jede Nacht ab 3 Uhr, das Ausrollen vor jedem Neustart eine stimmige Kopie von `pinnwand.sqlite`
nach `{{wurzel}}/sicherungen/pinnwand-<Zeit>.sqlite`; die jüngsten zehn bleiben. Das Werkzeug
`~/Entwicklung/Werkzeuge/Sicherungen` holt sie jeden Morgen auf den Mac nach `~/Sicherungen/pinnwand`. Zurückspielen: auf dem Pi im Ordner
{{wurzel}} `docker compose -f compose.pi.yml stop pinnwand`, die Kopie als `daten/pinnwand.sqlite` ablegen (die Dateien
`pinnwand.sqlite-wal` und `pinnwand.sqlite-shm` daneben entfernen), `docker compose -f compose.pi.yml start pinnwand`.

Probe: `/api/v1/app` antwortet, nach der Anmeldung stehen die Boards mit ihren Karten in der Oberfläche.

Anhänge liegen in der Kellerwolke und werden mit ihr gesichert; die Pinnwand merkt sich nur, welche Datei an welcher
Karte hängt.

## Wenn etwas klemmt

- Die Anmeldung meldet "Das Konto darf diese App nicht nutzen": die Person ist zu keinem Board eingeladen und steht
  nicht unter Einstellungen, Weitere Konten. Einladen oder den Namen dort eintragen.
- Im Fuß steht "Getrennt, verbinde neu": der Ereignisstrom ist abgerissen (Neustart, Netz). Die Pinnwand verbindet sich
  von selbst neu und holt den ganzen Stand; Änderungen sind solange gesperrt, damit nichts scheinbar gespeichert wird.
- Eine Änderung wird mit "inzwischen geändert" abgelehnt: jemand anders hat dasselbe Feld kurz vorher geändert. Das
  Kartendetail fragt, ob der jetzige Stand bleiben oder die eigene Änderung gelten soll.
- Docker legt `daten/` oder `sicherungen/` für root an: die Ordner vor dem ersten Start als `pi` anlegen (Schritt 2).
