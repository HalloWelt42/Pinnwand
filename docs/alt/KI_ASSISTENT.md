# KI-Assistent (optionale zweite Option)

An datenreichen Stellen - langen Listen, großen Auswahlen, vielen Labels - kann
das große lokale Sprachmodell gezielt unterstützen. Leitgedanke: die KI ist
immer die zweite Option. Der Mensch arbeitet wie gewohnt; die KI schlägt nur
vor, und jeder Vorschlag ist eine korrigierbare Checkliste. Angewendet wird
ausschließlich, was der Mensch bestätigt. Ist kein Modell erreichbar,
verschwinden die KI-Knöpfe einfach - der normale Weg bleibt unberührt.

## Aufbau

Ein eigenes, modulares Backend-Modul und eine einzige wiederverwendbare
Oberflächen-Komponente. Neue Stellen docken mit wenigen Zeilen an.

### Backend: Modul `ki`

- `modell.py` - der zentrale, fehlertolerante Zugang zum Modell (lokaler
  OpenAI-kompatibler Dienst). `chat()` für Text, `chat_json()` für strukturierte
  JSON-Antworten (schneidet robust das erste JSON-Objekt aus der Antwort). Jeder
  Fehler (Dienst aus, Timeout, kaputte Antwort) ergibt `None`, nie eine Ausnahme.
- Modellwahl: `PINNWAND_KI_MODELL` hat Vorrang; ohne Vorgabe automatische Auswahl
  unter den geladenen Modellen (echte Instruct-/Chat-Modelle bevorzugt,
  Coder-Modelle nachrangig, Embedding/Vision/Audio ausgeschlossen).
- `aufgaben.py` - die Aufgaben-Registry (Dispatcher). Jede Aufgabe ist eine
  austauschbare Einheit hinter klarer Schnittstelle: sie baut aus Kontext +
  Anweisung einen Prompt (`baue`) und deutet die JSON-Antwort in einheitliche
  Vorschläge (`deute`). Ein Vorschlag ist immer gleich geformt:
  `{id, text, begruendung, vorgewaehlt}`.
- `api.py` - `GET /api/ki/status` (zum Ausgrauen der Oberfläche),
  `GET /api/ki/typen`, `POST /api/ki/aufgabe` mit `{typ, kontext, anweisung}`.
- `persistence.py` - leichtes Protokoll der Aufrufe (Typ, Modell, Anzahl,
  Erfolg; keine Dateninhalte), fire-and-forget.

### Aufgabentypen (aktuell)

- `auswahl` - aus einer großen Liste die passenden Einträge wählen. Kontext:
  `{elemente: [{id, text}]}`. Genau der Fall "Auswahl aus großen Listen".
- `labels` - Schlagworte für eine Karte aus Titel/Beschreibung vorschlagen.
  Kontext: `{titel, beschreibung, vorhandene_labels, bereits_an_karte}`.
- `filter` - eine Filter-Kombination für ein Board vorschlagen. Kontext:
  `{labels, prioritaeten, sortierungen}`.
- `bericht` - aus einem Wunsch ein Berichtsformular ausfüllen. Kontext:
  `{typen: [{id, name}], personen: [{kuerzel, name}], formate, heute}`. Liefert
  je Feld einen Vorschlag (Typ, Format, Von, Bis, Person).
- `analyse` - Daten beurteilen und Befunde/Warnungen liefern (reine Anzeige, kein
  Anwenden). Kontext: `{daten}`. Liefert eine Liste von Befunden.

### Frontend: eine Komponente für alle Stellen

- `lib/ki.svelte.ts` - geteilter Zustand (erreichbar? welches Modell?) über
  `/api/ki/status`.
- `lib/ki/KiAssistent.svelte` - der wiederverwendbare KI-Knopf. Er erscheint nur,
  wenn das Modell erreichbar ist. Klick öffnet ein Panel: Anweisung eintippen,
  "Vorschlagen", dann die Vorschläge als Checkliste (Vorauswahl ankreuzbar, mit
  Begründung), schließlich "Übernehmen". Die aufrufende Stelle übergibt nur: den
  `typ`, eine `kontext`-Funktion und einen `onUebernehmen`-Rückruf mit den
  bestätigten Vorschlägen. Was "Übernehmen" konkret tut, entscheidet die Stelle -
  die Komponente wendet nie selbst etwas an.
  - Mit `nurAnzeige` wird das Panel zur reinen Auswertung: die Befunde erscheinen
    ohne Auswahlkästchen und ohne "Übernehmen" (nur "Schließen"), `onUebernehmen`
    entfällt. `aktionText` benennt den Auslöse-Knopf (z.B. "Analysieren").

## Eingebaute Stellen

1. Transkripte, Arbeitspool: relevante Transkripte aus dem ganzen Bestand in den
   Arbeitspool aufnehmen lassen (typ `auswahl`).
2. Karten-Detail, Labels: Schlagworte aus Titel/Beschreibung vorschlagen
   (typ `labels`).
3. Stundenzettel, Zeit nachtragen: in einer langen Kartenliste die gemeinte Karte
   finden (typ `auswahl`).
4. Board-Werkzeugleiste, Filter: aus einem Wunsch eine Filter-Kombination
   vorschlagen (typ `filter`).
5. Wiederkehrendes, Teilnehmer: passende Personen für eine Serie vorschlagen
   (typ `auswahl`).
6. Berichte, Bericht erzeugen: aus einem Wunsch das Formular ausfüllen
   (typ `bericht`).
7. Einstellungen, Snapshot-Vorschau: die Änderungen vor dem Wiederherstellen
   beurteilen lassen (typ `analyse`, nur Anzeige).

## Eine neue Stelle anbinden

1. Passenden Aufgabentyp wählen oder in `aufgaben.py` einen neuen registrieren
   (eine `Aufgabe` mit `baue` und `deute`).
2. An der Stelle `<KiAssistent typ=... kontext={...} onUebernehmen={...} />`
   einsetzen. Fertig - Modellzugang, Panel, Vorschau und Ausgrauen kommen aus dem
   gemeinsamen Fundament.

## Konfiguration

- `PINNWAND_LLM_URL` - Adresse des lokalen Modelldienstes (Standard
  `http://localhost:1234`).
- `PINNWAND_KI_MODELL` - festes Modell erzwingen; leer = automatische Auswahl.
