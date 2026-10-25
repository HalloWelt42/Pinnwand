// Anwendungsfälle des Moduls Arbeitszeit: Abwesenheiten eintragen und entfernen, eine neue Fassung des Zeitkontos.
// Eine neue Abwesenheit ersetzt überlappende derselben Person; Serien der Person setzen an diesen Tagen aus.

import type { Abwesenheit, Kennung, Zeitkonto } from "../../modell";
import { artName } from "../../regeln/arbeitszeit";
import { datumJahr, spanne } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { neueKennung } from "./zeiten.svelte";

export function eintragen(a: Omit<Abwesenheit, "id">): void {
  aendern(() => {
    stand.abwesenheiten = [...stand.abwesenheiten.filter((x) => !(x.konto === a.konto && x.von <= a.bis && a.von <= x.bis)),
      { ...a, id: neueKennung("a") }];
    return `${artName(a)} eingetragen: ${spanne(a.von, a.bis)}`;
  });
}

export function entfernen(id: Kennung): void {
  const a = stand.abwesenheiten.find((x) => x.id === id);
  if (!a) return;
  aendern(() => {
    stand.abwesenheiten = stand.abwesenheiten.filter((x) => x.id !== id);
    return `${artName(a)} ${spanne(a.von, a.bis)} entfernt`;
  });
}

/** Neue Fassung des Zeitkontos ab einem Tag; frühere Tage behalten ihr Soll */
export function zeitkontoSpeichern(z: Zeitkonto): void {
  aendern(() => {
    stand.zeitkonten = [...stand.zeitkonten.filter((x) => !(x.konto === z.konto && x.ab === z.ab)), structuredClone(z)];
    return `Zeitkonto gespeichert, gilt ab ${datumJahr(z.ab, true)}; frühere Tage behalten ihr Soll`;
  });
}
