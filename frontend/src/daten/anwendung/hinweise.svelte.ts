// Anwendungsfälle der Hinweise über den Server: gelesen gilt am Konto (auf allen Geräten), darum im gemeinsamen Zustand;
// Glocke, Seitenleiste, Heute und Telefon zählen dieselben. Ein einzelner Hinweis meldet sich nicht und hat keinen
// Rückweg, "alle gelesen" schon. Die Hinweise selbst entstehen im Server. Welche Arten und Wege diese Fassung gibt und
// was gilt, solange die Person nichts geschaltet hat, steht hier wie im Server (ARTEN_DA, WEGE_DA, VORGABE).

import { HINWEIS_ARTEN, HINWEIS_WEGE } from "../../anzeige";
import type { HinweisArt, HinweisWeg, Kennung } from "../../modell";
import { stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

/** Wege, die diese Fassung anbietet */
const WEGE_DA: readonly HinweisWeg[] = ["pinnwand"];
/** Vorgabe je Weg, solange die Person ihn für eine Art nicht selbst geschaltet hat */
const VORGABE: Partial<Record<HinweisWeg, boolean>> = { pinnwand: true };

/** Arten, die es gibt: Termine nur mit dem Modul Serien */
export function artenDa(): typeof HINWEIS_ARTEN {
  return HINWEIS_ARTEN.filter((a) => a.art !== "termin" || stand.moduleDa.includes("serien"));
}

export function wegeDa(): typeof HINWEIS_WEGE {
  return HINWEIS_WEGE.filter((w) => WEGE_DA.includes(w.id));
}

/** Ob Hinweise dieser Art auf diesem Weg kommen: die Einstellung am Konto, sonst die Vorgabe des Wegs */
export function wegAn(art: HinweisArt, weg: HinweisWeg): boolean {
  return stand.einstellungen.hinweise[art]?.[weg] ?? VORGABE[weg] ?? false;
}

export function gelesen(id: Kennung, wert = true): void {
  const h = stand.hinweise.find((x) => x.id === id);
  if (!h || h.gelesen === wert) return;
  void aendern(() => senden(`/hinweise/${id}/gelesen`, { gelesen: wert }));
}

export function alleGelesen(): void {
  if (stand.hinweise.some((h) => !h.gelesen)) void aendern(() => senden("/hinweise/alle-gelesen"));
}

/** Auf welchem Weg welche Hinweise kommen (gilt am Konto, auf allen Geräten) */
export function hinweisWegSetzen(art: HinweisArt, weg: HinweisWeg, an: boolean): void {
  if (wegAn(art, weg) !== an) void aendern(() => senden("/hinweise/weg", { art, weg, an }));
}
