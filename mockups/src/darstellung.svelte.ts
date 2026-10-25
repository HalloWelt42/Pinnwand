// Darstellung auf diesem Gerät: Thema und Schriftstufe, eine Wahrheit für die Einstellung "Darstellung" und die Leiste
// der Entwürfe. Gemerkt im Browser unter dem Schlüssel der Anzeige des Appkerns (den setzt auch die Ansichtsprüfung);
// ohne Speicher gilt die Vorgabe: dunkel, Schrift Klein.

const SCHLUESSEL = "appkern_anzeige";

export type Thema = "hell" | "dunkel" | "system";
export type Schrift = "klein" | "mittel" | "gross";

function gemerkt(): Partial<{ thema: Thema; schrift: Schrift }> {
  try {
    return JSON.parse(localStorage.getItem(SCHLUESSEL) ?? "{}");
  } catch {
    return {};
  }
}

const g = gemerkt();
export const darstellung = $state<{ thema: Thema; schrift: Schrift }>({ thema: g.thema ?? "dunkel", schrift: g.schrift ?? "klein" });

function dunkel(): boolean {
  return darstellung.thema === "dunkel" || (darstellung.thema === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
}

export function darstellungAnwenden(): void {
  const h = document.documentElement;
  h.dataset.theme = dunkel() ? "dunkel" : "hell";
  h.dataset.schrift = darstellung.schrift;
}

export function darstellungSetzen(wert: Partial<{ thema: Thema; schrift: Schrift }>): void {
  Object.assign(darstellung, wert);
  try {
    localStorage.setItem(SCHLUESSEL, JSON.stringify({ ...gemerkt(), ...darstellung }));
  } catch {
    // gilt dann nur bis zum Neuladen
  }
  darstellungAnwenden();
}

matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (darstellung.thema === "system") darstellungAnwenden();
});
