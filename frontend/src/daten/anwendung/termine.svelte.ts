// Anwendungsfälle der Termine (Modul Serien und Termine) über den Server: einen Termin anlegen, vorher zusagen oder
// absagen, nach dem Termin die eigene Zeit bestätigen oder verwerfen (fand für dich nicht statt). Ein Termin hat keine
// Karte; seine Zeit zählt erst, wenn du sie bestätigst: dann bucht der Server sie als Zeiteintrag des Termins. Den
// übrigen Teilnehmern eines neuen Termins schickt der Server einen Hinweis. Die Serien und der Nachtrag stehen in
// serien.svelte.ts.

import type { Kennung, Termin } from "../../modell";
import { ICH } from "../ich";
import { stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

/** Was die Person für einen neuen Termin wählt; Kennung, Zusagen und Bestätigungen führt der Server */
export type NeuerTermin = Omit<Termin, "id" | "zugesagt" | "bestaetigt">;

function termin(id: Kennung): Termin | undefined {
  return stand.termine.find((x) => x.id === id);
}

/** Neuer Termin; wer ihn anlegt und teilnimmt, hat zugesagt, die anderen sagen selbst zu. Ergebnis: Kennung */
export async function terminAnlegen(neu: NeuerTermin): Promise<Kennung | undefined> {
  if (!neu.titel.trim() || !neu.teilnehmer.length || neu.bis <= neu.von) return undefined;
  const daten = { board: neu.board, titel: neu.titel.trim(), datum: neu.datum, von: neu.von, bis: neu.bis,
                  ...(neu.ort?.trim() ? { ort: neu.ort.trim() } : {}), teilnehmer: [...neu.teilnehmer] };
  const a = await aendern(() => senden("/termine", daten));
  return a?.geaendert.find((g) => g.tabelle === "termine" && g.daten)?.id;
}

/** Zusage vor dem Termin: ja nimmt dich in die Zusagen auf, nein nimmt dich heraus */
export function zusagen(id: Kennung, ja = true): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH) || t.zugesagt.includes(ICH) === ja) return;
  void aendern(() => senden(`/termine/${id}/zusagen`, { ja }));
}

/** Nach dem Termin: deine Zeit bestätigen (von Beginn bis Ende des Termins), erst dann zählt sie */
export function zeitBestaetigen(id: Kennung): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH) || t.bestaetigt.includes(ICH)) return;
  void aendern(() => senden(`/termine/${id}/bestaetigen`));
}

/** Nach dem Termin: fand für dich nicht statt; du bist nicht mehr Teilnehmer, es zählt keine Zeit */
export function zeitVerwerfen(id: Kennung): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH)) return;
  void aendern(() => senden(`/termine/${id}/verwerfen`));
}
