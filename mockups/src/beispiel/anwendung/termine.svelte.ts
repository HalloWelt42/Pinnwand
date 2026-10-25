// Anwendungsfälle der Termine (Modul Serien und Termine): einen Termin anlegen, vorher zusagen oder absagen, nach dem
// Termin die eigene Zeit bestätigen oder verwerfen (fand für dich nicht statt). Ein Termin hat keine Karte; seine Zeit
// zählt erst, wenn du sie bestätigst. Die Serien und der Nachtrag stehen in serien.svelte.ts.

import type { Kennung, Termin } from "../../modell";
import { ICH } from "../daten";
import { datum } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { neueKennung } from "./zeiten.svelte";

function termin(id: Kennung): Termin | undefined {
  return stand.termine.find((x) => x.id === id);
}

/** Neuer Termin; wer ihn anlegt und teilnimmt, hat zugesagt, die anderen sagen selbst zu. Ergebnis: Kennung */
export function terminAnlegen(neu: Omit<Termin, "id" | "zugesagt" | "bestaetigt">): Kennung | undefined {
  if (!neu.titel.trim() || !neu.teilnehmer.length || neu.bis <= neu.von) return undefined;
  const id = neueKennung("t");
  const ok = aendern(() => {
    const t: Termin = { ...($state.snapshot(neu) as typeof neu), id, titel: neu.titel.trim(), ort: neu.ort?.trim() || undefined,
                        zugesagt: neu.teilnehmer.includes(ICH) ? [ICH] : [], bestaetigt: [] };
    stand.termine.push(t);
    return `Termin ${t.titel} am ${datum(t.datum, true)} ${t.von} angelegt`;
  });
  return ok ? id : undefined;
}

/** Zusage vor dem Termin: ja nimmt dich in die Zusagen auf, nein nimmt dich heraus */
export function zusagen(id: Kennung, ja = true): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH) || t.zugesagt.includes(ICH) === ja) return;
  aendern(() => {
    t.zugesagt = ja ? [...t.zugesagt, ICH] : t.zugesagt.filter((k) => k !== ICH);
    return ja ? `Zugesagt: ${t.titel}, ${datum(t.datum, true)} ${t.von}` : `Abgesagt: ${t.titel}`;
  });
}

/** Nach dem Termin: deine Zeit bestätigen, erst dann zählt sie */
export function zeitBestaetigen(id: Kennung): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH) || t.bestaetigt.includes(ICH)) return;
  aendern(() => {
    t.bestaetigt = [...t.bestaetigt, ICH];
    return `Zeit bestätigt: ${t.titel}, ${datum(t.datum, true)} ${t.von} bis ${t.bis}`;
  });
}

/** Nach dem Termin: fand für dich nicht statt; du bist nicht mehr Teilnehmer, es zählt keine Zeit */
export function zeitVerwerfen(id: Kennung): void {
  const t = termin(id);
  if (!t || !t.teilnehmer.includes(ICH)) return;
  aendern(() => {
    t.teilnehmer = t.teilnehmer.filter((k) => k !== ICH);
    t.zugesagt = t.zugesagt.filter((k) => k !== ICH);
    t.bestaetigt = t.bestaetigt.filter((k) => k !== ICH);
    return `${t.titel} am ${datum(t.datum, true)}: fand für dich nicht statt, es zählt keine Zeit`;
  });
}
