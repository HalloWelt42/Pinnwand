# Label-Verwaltung

Ein eigener Bereich (Seitenleiste -> "Labels"), um Labels anzulegen, umzubenennen
und ihnen eine Farbe aus der globalen Material-Palette zuzuweisen. Die Farbe gilt
überall, wo das Label an einer Karte vorkommt.

## Datenmodell (bewusst additiv)

Die Labels an einer Karte bleiben wie bisher eine Liste freier Text-Strings
(`karte.labels`). Es gibt keine Fremdschlüssel und keine Migration an der
Karten-Tabelle. Neu ist nur eine kleine Definitionstabelle:

```
label_definition (id, name, familie, erstellt_am)
```

- `name` ist der Label-Text (ohne Beachtung der Groß-/Kleinschreibung eindeutig).
- `familie` ist ein Material-Familienname (z.B. `blue`, `teal`) - nicht ein
  konkreter Hex-Wert. So bleibt die bestehende Hell-/Dunkel- und Kontrastlogik
  (`labels.ts`) unverändert: aus der Familie werden Chip-Hintergrund und lesbare
  Textfarbe abgeleitet.

## Farbauflösung

`labels.ts` löst die Farbe je Label-Name in dieser Reihenfolge auf:

1. zugewiesene Definition (aus der Verwaltung),
2. semantische Zuordnung bekannter Namen (z.B. `blocker` -> rot),
3. stabiler Hash-Fallback (kein Zufall, kein Grau).

Die Definitionen werden beim Start in `labels.ts` gespiegelt
(`setzeLabelDefinitionen`) und nach jeder Änderung in der Verwaltung erneut.
Bestehende String-Labels ohne Definition behalten also immer eine Farbe.

## Verhalten

- **Anlegen**: Name eingeben, Farbe wählen (`FarbWahl`), anlegen. Doppelte Namen
  werden ohne Beachtung der Groß-/Kleinschreibung abgewiesen.
- **Umbenennen**: Das Backend überträgt den neuen Namen JSON-sicher auf die
  `labels` aller Karten (gleiche Namen werden dabei zusammengeführt).
- **Färben**: ändert nur die zugewiesene Familie.
- **Löschen**: entfernt NUR die Definition. Der Text bleibt an den Karten
  erhalten und fällt auf die automatische (Hash-)Farbe zurück.

Die Label-Liste in Filtern (Toolbar) und die KI-Label-Vorschläge bleiben
unverändert aus den tatsächlich an Karten genutzten Labels abgeleitet - die
Definition ist reine Farb-/Verwaltungsschicht, nicht die Wahrheit über genutzte
Labels.
