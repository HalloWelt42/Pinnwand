// Anwendungsfälle der Hinweise: gelesen gilt am Konto (auf allen Geräten), darum im gemeinsamen Zustand; Glocke,
// Seitenleiste, Heute und Telefon zählen dieselben. Ein einzelner Hinweis meldet sich nicht, "alle gelesen" schon.

import type { HinweisArt, HinweisWeg, Kennung } from "../../modell";
import { baustelle } from "./baustelle";

export function gelesen(id: Kennung, wert = true): void {
  baustelle("Hinweise");
}

export function alleGelesen(): void {
  baustelle("Hinweise");
}

/** Auf welchem Weg welche Hinweise kommen (gilt am Konto, auf allen Geräten) */
export function hinweisWegSetzen(art: HinweisArt, weg: HinweisWeg, an: boolean): boolean {
  return baustelle("Hinweise");
}
