// Anwendungsfälle der Termine (Modul Serien und Termine): vorher zusagen oder absagen, nach dem Termin die eigene Zeit
// bestätigen. Weitere Anwendungsfälle des Moduls (Termin anlegen, Serien, Nachtrag) stehen ebenfalls hier und in
// serien.svelte.ts.

import type { Kennung } from "../../modell";
import { ICH } from "../daten";
import { datum } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";

/** Zusage vor dem Termin: ja nimmt dich in die Zusagen auf, nein nimmt dich heraus */
export function zusagen(id: Kennung, ja = true): void {
  const t = stand.termine.find((x) => x.id === id);
  if (!t || !t.teilnehmer.includes(ICH) || t.zugesagt.includes(ICH) === ja) return;
  aendern(() => {
    t.zugesagt = ja ? [...t.zugesagt, ICH] : t.zugesagt.filter((k) => k !== ICH);
    return ja ? `Zugesagt: ${t.titel}, ${datum(t.datum, true)} ${t.von}` : `Abgesagt: ${t.titel}`;
  });
}
