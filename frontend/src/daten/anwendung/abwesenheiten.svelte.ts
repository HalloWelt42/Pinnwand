// Anwendungsfälle des Moduls Arbeitszeit über den Server: eigene Abwesenheiten eintragen und entfernen, eine neue
// Fassung des eigenen Zeitkontos. Beides geht nur für dich selbst und nur, wenn das Modul Arbeitszeit in einem deiner
// Boards an ist; das prüft der Server. Eine neue Abwesenheit ersetzt dort überlappende von dir im neuen Zeitraum;
// ihre übrigen Tage bleiben.

import type { Abwesenheit, Kennung, Zeitkonto } from "../../modell";
import { stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

/** Was die Person für eine Abwesenheit wählt; Kennung und Konto vergibt der Server */
export type NeueAbwesenheit = Omit<Abwesenheit, "id" | "konto">;

/** Was die Person für eine Fassung ihres Zeitkontos wählt; Kennung und Konto vergibt der Server */
export type NeueFassung = Omit<Zeitkonto, "id" | "konto">;

/** Eine Abwesenheit eintragen. Ergebnis: ob sie eingetragen ist */
export async function eintragen(a: NeueAbwesenheit): Promise<boolean> {
  const daten = { von: a.von, bis: a.bis, art: a.art, ...(a.anteil ? { anteil: a.anteil } : {}), ...(a.notiz?.trim() ? { notiz: a.notiz.trim() } : {}) };
  return (await aendern(() => senden("/abwesenheiten", daten))) !== null;
}

/** Eine oder mehrere Abwesenheiten entfernen, mit einem Rückgängig für alle */
export function entfernen(ids: Kennung | Kennung[]): void {
  const liste = (Array.isArray(ids) ? ids : [ids]).filter((id) => stand.abwesenheiten.some((x) => x.id === id));
  if (liste.length) void aendern(() => senden("/abwesenheiten/entfernen", { ids: liste }));
}

/** Neue Fassung des Zeitkontos ab einem Tag; frühere Tage behalten ihr Soll */
export function zeitkontoSpeichern(z: NeueFassung): void {
  void aendern(() => senden("/zeitkonten", {
    ab: z.ab, wochenstunden: z.wochenstunden, tage: z.tage, bundesland: z.bundesland, urlaubsanspruch: z.urlaubsanspruch,
    resturlaubVorjahr: z.resturlaubVorjahr, halbtage: z.halbtage,
  }));
}
