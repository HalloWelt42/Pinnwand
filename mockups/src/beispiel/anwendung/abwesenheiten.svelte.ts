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

/** Eine oder mehrere Abwesenheiten entfernen, mit einem Rückgängig für alle */
export function entfernen(ids: Kennung | Kennung[]): void {
  const liste = Array.isArray(ids) ? ids : [ids];
  const weg = stand.abwesenheiten.filter((x) => liste.includes(x.id));
  if (!weg.length) return;
  aendern(() => {
    stand.abwesenheiten = stand.abwesenheiten.filter((x) => !liste.includes(x.id));
    return weg.length === 1 ? `${artName(weg[0])} ${spanne(weg[0].von, weg[0].bis)} entfernt` : `${weg.length} Abwesenheiten entfernt`;
  });
}

/** Neue Fassung des Zeitkontos ab einem Tag; frühere Tage behalten ihr Soll */
export function zeitkontoSpeichern(z: Zeitkonto): void {
  aendern(() => {
    stand.zeitkonten = [...stand.zeitkonten.filter((x) => !(x.konto === z.konto && x.ab === z.ab)), structuredClone(z)];
    return `Zeitkonto gespeichert, gilt ab ${datumJahr(z.ab, true)}; frühere Tage behalten ihr Soll`;
  });
}
