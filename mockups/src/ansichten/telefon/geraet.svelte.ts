// Zustand dieses Geräts, nicht des Kontos: was das Telefon sich merkt (gewählte Spalte je Board). Fachliches liegt im
// gemeinsamen Zustand und ändert sich nur über die Anwendungsfälle (beispiel/anwendung/).

import { SPALTE_GEMERKT } from "./daten";

export const geraet = $state({
  /** zuletzt gewählte Spalte je Board */
  spalte: { ...SPALTE_GEMERKT } as Record<string, string>,
});
