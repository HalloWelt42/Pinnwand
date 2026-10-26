// Konten zurücksetzen und löschen, ohne Rückweg: das eigene, als Besitzer der App jedes. Bestätigt wird mit dem Namen
// des Kontos (der Server prüft ihn). Was danach mit dieser Oberfläche geschieht (Merker vergessen, neu laden oder
// abmelden), entscheidet stand.svelte.ts am eigenen Konto im Stand, gleich, wer es angestoßen hat.
import type { Kennung } from "../../modell";
import { aendern, senden } from "./meldung.svelte";

/** Alles des Kontos weg, danach wie bei der ersten Anmeldung */
export async function kontoZuruecksetzen(kontoId: Kennung, bestaetigung: string): Promise<boolean> {
  return (await aendern(() => senden(`/konten/${kontoId}/zuruecksetzen`, { bestaetigung }))) !== null;
}

/** Alles des Kontos weg, und es verschwindet aus der Pinnwand; meldet es sich wieder an, ist es neu */
export async function kontoLoeschen(kontoId: Kennung, bestaetigung: string): Promise<boolean> {
  return (await aendern(() => senden(`/konten/${kontoId}/entfernen`, { bestaetigung }))) !== null;
}
