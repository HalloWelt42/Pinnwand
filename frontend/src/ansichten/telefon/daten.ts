// Eigene Beispieldaten der Telefonansicht: nur, was zum Gerät gehört und nicht zum gemeinsamen Bestand
// (daten/daten.ts). Dieselbe Welt: Dienstag, der 27. Oktober 2026, 10:42 Uhr; angemeldet ist Max Paulsen.

/** Zuletzt genutztes Board beim Erfassen (je Gerät gemerkt) */
export const ZULETZT_BOARD = "b-prod";

/** Zuletzt gewählte Spalte je Board am Telefon (je Gerät gemerkt wie der Ansichtszustand des Boards, M-97) */
export const SPALTE_GEMERKT: Record<string, string> = { "b-prod": "s-arbeit" };

/** Spracheingabe beim Erfassen: was die App Transkription live erkennt */
export const SPRACHE = {
  text: "Angebot für Lindner Möbelbau schreiben. Es geht um 400 Gehäuse in RAL 7035 mit Lieferung Ende November. Vorher die Preise für die Pulverbeschichtung nachfragen.",
  /** im vorgeführten Zustand schon erkannter Anteil der Wörter */
  erkannt: 0.8,
  /** so viele der zuletzt erkannten Wörter sind noch vorläufig und können sich ändern */
  vorlaeufig: 3,
  /** Wörter je Sekunde beim Mitschreiben */
  tempo: 2.4,
};

/** Pegel der Aufnahme je Balken (0 bis 1) */
export const PEGEL = [
  0.22, 0.4, 0.62, 0.48, 0.8, 0.95, 0.7, 0.52, 0.34, 0.58, 0.86, 0.66, 0.42, 0.3, 0.5, 0.74, 0.9, 0.6, 0.38, 0.26, 0.46,
  0.68, 0.84, 0.56, 0.36, 0.24,
];
