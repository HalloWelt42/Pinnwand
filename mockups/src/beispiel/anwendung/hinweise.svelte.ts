// Anwendungsfälle der Hinweise: gelesen gilt am Konto (auf allen Geräten), darum im gemeinsamen Zustand; Glocke,
// Seitenleiste, Heute und Telefon zählen dieselben. Ein einzelner Hinweis meldet sich nicht, "alle gelesen" schon.

import type { Kennung } from "../../modell";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";

export function gelesen(id: Kennung, wert = true): void {
  const h = stand.hinweise.find((x) => x.id === id);
  if (!h || h.gelesen === wert) return;
  aendern(() => {
    h.gelesen = wert;
    return wert ? "gelesen" : "ungelesen";
  }, { rueckgaengig: false, melden: false });
}

export function alleGelesen(): void {
  const offen = stand.hinweise.filter((h) => !h.gelesen);
  if (!offen.length) return;
  aendern(() => {
    for (const h of offen) h.gelesen = true;
    return `${offen.length} ${offen.length === 1 ? "Hinweis" : "Hinweise"} als gelesen markiert`;
  });
}
