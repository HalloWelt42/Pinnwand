// Anwendungsfälle des Moduls Arbeitszeit: Abwesenheiten eintragen und entfernen, eine neue Fassung des Zeitkontos.
// Eine neue Abwesenheit ersetzt überlappende derselben Person; Serien der Person setzen an diesen Tagen aus.

import type { Abwesenheit, Kennung, Zeitkonto } from "../../modell";
import { artName } from "../../regeln/arbeitszeit";
import { datumJahr, spanne } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { neueKennung } from "./zeiten.svelte";

/** Unberührte Vorbuchungen von Serien an ganzen Abwesenheitstagen zurücknehmen (Mechanik M-109): die Person fällt aus
 *  den Zuständigen; bleibt niemand, geht die Karte. Angefasste Karten (Zeit, andere Spalte, erledigt) bleiben stehen. */
function vorbuchungenZuruecknehmen(a: Omit<Abwesenheit, "id">): number {
  if ((a.anteil ?? 1) < 1) return 0;
  let n = 0;
  for (const k of [...stand.karten]) {
    const s = k.serie ? stand.serien.find((x) => x.id === k.serie) : undefined;
    if (!s || !k.faellig || k.faellig < a.von || k.faellig > a.bis || !k.zustaendig.includes(a.konto)) continue;
    const unberuehrt = k.spalte === s.zielspalte && !k.abgeschlossen && !stand.zeiteintraege.some((e) => e.karte === k.id);
    if (!unberuehrt) continue;
    k.zustaendig = k.zustaendig.filter((x) => x !== a.konto);
    if (!k.zustaendig.length) {
      stand.reihen[k.spalte] = (stand.reihen[k.spalte] ?? []).filter((id) => id !== k.id);
      stand.karten = stand.karten.filter((x) => x.id !== k.id);
    }
    n++;
  }
  return n;
}

export function eintragen(a: Omit<Abwesenheit, "id">): void {
  aendern(() => {
    stand.abwesenheiten = [...stand.abwesenheiten.filter((x) => !(x.konto === a.konto && x.von <= a.bis && a.von <= x.bis)),
      { ...a, id: neueKennung("a") }];
    const n = vorbuchungenZuruecknehmen(a);
    return `${artName(a)} eingetragen: ${spanne(a.von, a.bis)}` + (n ? `; ${n} ${n === 1 ? "Vorbuchung" : "Vorbuchungen"} einer Serie zurückgenommen` : "");
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
