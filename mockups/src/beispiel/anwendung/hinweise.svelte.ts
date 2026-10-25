// Anwendungsfälle der Hinweise: gelesen gilt am Konto (auf allen Geräten), darum im gemeinsamen Zustand; Glocke,
// Seitenleiste, Heute und Telefon zählen dieselben.

import type { Kennung } from "../../modell";
import { stand } from "../stand.svelte";

export function gelesen(id: Kennung, wert = true): void {
  const h = stand.hinweise.find((x) => x.id === id);
  if (h) h.gelesen = wert;
}

export function alleGelesen(): void {
  for (const h of stand.hinweise) h.gelesen = true;
}
