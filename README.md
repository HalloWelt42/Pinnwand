# Pinnwand

Lokale, modulare Kanban-Plattform. Das Board ist nur das erste Modul - Ansichten, Karten-Felder und weitere Funktionalität kommen über Module dazu, ohne den Kern umzubauen. Themes (hell und dunkel gleichwertig) sind über Token austauschbar.

## Stack

- Frontend: Svelte 5 + TypeScript + Vite
- Backend: Python + FastAPI + Pydantic, SQLite
- Schriften: Chakra Petch (Display), Inter (Text), JetBrains Mono (Mono) via @fontsource
- Icons: Font Awesome
- Highlight-Farben: echte Material-Design-Werte (siehe `frontend/src/lib/theme/palette.ts`)

## Start

```bash
./start.sh
```

- Frontend: http://localhost:5198
- Backend: http://localhost:8420 (API-Doku unter `/docs`)

Beim ersten Lauf werden das Python-venv und die npm-Pakete eingerichtet.

## Aufbau

```
backend/
  app/            Host (domänenneutral): generische DB-Verbindung,
                  Modul-Registry, FastAPI-App
  module/         Backend-Module (je eigenes Modell, Schema, Router)
    kanban_kern/  models.py, persistence.py, api.py, manifest.json
frontend/
  src/
    lib/
      theme/      Palette, Token, Theme-Engine
      module/     Frontend-Module + Registry
        kanban/   Board-, Spalten-, Karten-Komponenten
```

## Module

Ein Modul beschreibt sich über `manifest.json` und bringt sein eigenes Datenmodell und Schema mit - der Kern kennt keine Domäne.

- Backend: Die Registry findet Module per Verzeichnis-Scan, ruft den Schema-Init-Hook (`backend.init`) auf und bindet den Router (`backend.router`) ein. Ein neues Modul = ein neuer Ordner unter `module/`, ohne Änderung am Kern.
- Frontend: Module werden beim Start automatisch entdeckt (jedes `module/<name>/index.ts` exportiert `registriere`). Auch hier bleibt der Kern unverändert.

Erweiterungspunkte im Manifest werden unter `/api/erweiterungen` aggregiert bereitgestellt. Aktiv ausgewertet wird `views` (steuert die Ansichten der Oberfläche). `cardFields`, `mappeTabs` und `commands` sind als Erweiterungspunkte vorgesehen und werden bereits ausgeliefert; die zugehörigen Renderer folgen mit den nächsten Modulen.

## Ansichten

Aktuell: Heute (Was steht an), Board, Zeiten (Wochen-Stundenzettel mit Soll/Ist), Kalender (Heatmap + Monatsansicht), Jahreskalender (12-Monats-Gitter und Team-Matrix mit umschaltbaren Ebenen Anwesenheit/Feiertage/Stunden/Auslastung, direkter Eingabe und Halbtags-Regeln), Serien (wiederkehrende Termine), Suche, Transkripte, Planung (Personen, Bundesland, Wochenstunden, Urlaubsanspruch, Urlaub, Feiertage, Abwesenheits-Arten), Berichte (PDF/CSV/Markdown mit Archiv), Einstellungen (Sicherung, Agenten-Token). Vorgesehen als weitere Module: Tabelle, Zeitachse.
