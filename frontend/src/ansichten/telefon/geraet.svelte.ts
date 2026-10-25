// Zustand dieses Geräts, nicht des Kontos: was das Telefon sich merkt (zuletzt genutztes Board beim Erfassen, gewählte
// Spalte je Board), im Browser gespeichert. Fachliches liegt im gemeinsamen Zustand und ändert sich nur über die
// Anwendungsfälle (daten/anwendung/). Ohne Speicher gilt das Gemerkte bis zum Neuladen.

const SCHLUESSEL = "pinnwand_telefon";

function gemerkt(): { board?: unknown; spalte?: unknown } {
  try {
    return JSON.parse(localStorage.getItem(SCHLUESSEL) ?? "{}");
  } catch {
    return {};
  }
}

const g = gemerkt();
const spalten = g.spalte && typeof g.spalte === "object" ? g.spalte as Record<string, unknown> : {};

export const geraet = $state({
  /** zuletzt beim Erfassen genutztes Board */
  board: typeof g.board === "string" ? g.board : "",
  /** zuletzt gewählte Spalte je Board */
  spalte: Object.fromEntries(Object.entries(spalten).filter(([, w]) => typeof w === "string")) as Record<string, string>,
});

export function geraetMerken(): void {
  try {
    localStorage.setItem(SCHLUESSEL, JSON.stringify($state.snapshot(geraet)));
  } catch {
    // ohne Speicher (privates Fenster, gesperrt, voll): gilt bis zum Neuladen
  }
}
