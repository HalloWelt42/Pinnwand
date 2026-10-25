// Inhalt eines Kalendertags eines Boards: Karten nach Fälligkeit, Termine, Serientage, Abwesenheiten der Mitglieder
// (nur mit Recht und Modul Arbeitszeit) und Feiertage ihrer Bundesländer. Monat und Woche lesen nur hierüber.

import type { Abwesenheit, Board, Karte, Serie, Termin } from "../../modell";
import { abwesenheit, abwesenheitenSichtbar, feiertageAm, serienDesBoards, termineDesBoards, vorkommen } from "./plan.svelte";
import type { Feiertag, Vorkommen } from "./typen";

export interface Zeigen {
  karten: boolean;
  termine: boolean;
  serien: boolean;
  abwesenheiten: boolean;
}

export interface Serientag {
  serie: Serie;
  v: Vorkommen;
}

export interface TagInhalt {
  tag: string;
  karten: Karte[];
  termine: Termin[];
  serien: Serientag[];
  abwesend: Abwesenheit[];
  feiertage: { feiertag: Feiertag; konten: string[] }[];
}

/** Stände eines Serientags, die im Kalender als Termin erscheinen (nicht gelöscht, entfallen, verworfen, pausiert) */
const SICHTBAR: Vorkommen["stand"][] = ["gezaehlt", "wartet", "heute", "vorgebucht", "beruehrt", "geplant"];

/** Inhalte aller Tage eines Zeitraums; Serientage, die schon als Karte dastehen, erscheinen nur als Karte */
export function tageInhalt(b: Board, tage: string[], karten: Karte[], zeigen: Zeigen): Map<string, TagInhalt> {
  const von = tage[0];
  const bis = tage[tage.length - 1];
  const mitglieder = b.mitglieder.map((m) => m.konto);
  const serientage = b.module.serien && zeigen.serien
    ? serienDesBoards(b.id).flatMap((s) => vorkommen(s, von, bis).filter((v) => SICHTBAR.includes(v.stand)).map((v) => ({ serie: s, v })))
    : [];
  const mitAbwesenheit = zeigen.abwesenheiten && abwesenheitenSichtbar(b);
  const termine = b.module.serien && zeigen.termine ? termineDesBoards(b.id) : [];
  const m = new Map<string, TagInhalt>();
  for (const tag of tage) {
    const kartenAmTag = zeigen.karten ? karten.filter((k) => k.faellig === tag) : [];
    m.set(tag, {
      tag,
      karten: kartenAmTag,
      termine: termine.filter((t) => t.datum === tag).sort((a, c) => a.von.localeCompare(c.von)),
      serien: serientage.filter((x) => x.v.tag === tag && !karten.some((k) => k.serie === x.serie.id && k.faellig === tag))
        .sort((a, c) => (a.serie.uhrzeit ?? "").localeCompare(c.serie.uhrzeit ?? "")),
      abwesend: mitAbwesenheit ? mitglieder.map((k) => abwesenheit(k, tag)).filter((a): a is Abwesenheit => a !== undefined) : [],
      feiertage: feiertageAm(tag, mitglieder),
    });
  }
  return m;
}
