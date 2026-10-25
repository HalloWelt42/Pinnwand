// Regeln des Moduls Arbeitszeit als reine Funktionen: Wirkung jeder Abwesenheit, Soll eines Tags aus dem Zeitkonto,
// Urlaubstage und Brückentage. In der App dieselben Regeln im Modul auf dem Server; die Oberfläche rechnet mit ihnen nur
// Vorschauen (Wirkung eines geplanten Urlaubs).

import type { Abwesenheit, AbwesenheitArt, Halbtagsregel, Zeitkonto } from "../modell";
import { feiertag } from "./feiertage";
import { plusTage, tageVon, wochentag } from "./tage";

export interface ArtWirkung {
  name: string;
  /** Wort für schmale Spaltenköpfe */
  knapp: string;
  kurz: string;
  symbol: string;
  /** Faktor auf das Soll des Tags: 0 Soll entfällt, 1 bleibt (Ausgleich baut Überstunden ab) */
  soll: number;
  /** Anteil, der als Urlaubstag zählt */
  urlaub: number;
  wirkung: string;
}

/** Eine Wahrheit für die Wirkung jeder Art; ein halber Tag (Abwesenheit.anteil) wirkt zur Hälfte */
export const ARTEN: Record<AbwesenheitArt, ArtWirkung> = {
  urlaub: { name: "Urlaub", knapp: "Urlaub", kurz: "U", symbol: "fa-umbrella-beach", soll: 0, urlaub: 1, wirkung: "Soll entfällt, zählt als Urlaubstag" },
  krank: { name: "Krank", knapp: "Krank", kurz: "K", symbol: "fa-house-medical", soll: 0, urlaub: 0, wirkung: "Soll entfällt, kein Urlaubstag" },
  frei: { name: "Frei (Ausgleich)", knapp: "Ausgleich", kurz: "F", symbol: "fa-mug-hot", soll: 1, urlaub: 0, wirkung: "Soll bleibt, baut Überstunden ab" },
  fortbildung: { name: "Fortbildung", knapp: "Fortbildung", kurz: "Fb", symbol: "fa-graduation-cap", soll: 0, urlaub: 0, wirkung: "Soll entfällt, kein Urlaubstag" },
  feiertag: { name: "Betrieblich frei", knapp: "Betrieb frei", kurz: "B", symbol: "fa-star", soll: 0, urlaub: 0, wirkung: "Soll entfällt wie an einem Feiertag" },
};

/** Name einer Abwesenheit mit ihrem Anteil: "Urlaub", "Halber Tag Urlaub" */
export function artName(a: Pick<Abwesenheit, "art" | "anteil">): string {
  return a.anteil === 0.5 ? `Halber Tag ${ARTEN[a.art].knapp}` : ARTEN[a.art].name;
}

/** Die Fassung des Zeitkontos, die an einem Tag gilt: die jüngste mit ab bis zu diesem Tag */
export function fassungAm(fassungen: Zeitkonto[], konto: string, tag: string): Zeitkonto | undefined {
  return fassungen.filter((z) => z.konto === konto && z.ab <= tag).sort((a, b) => b.ab.localeCompare(a.ab))[0]
    ?? fassungen.filter((z) => z.konto === konto).sort((a, b) => a.ab.localeCompare(b.ab))[0];
}

export type SollGrund = "arbeitstag" | "wochenende" | "arbeitsfrei" | "feiertag" | "halbtagsregel" | AbwesenheitArt;

export interface TagSoll {
  tag: string;
  /** Soll ohne Abwesenheit (nach Arbeitstag, Feiertag, Halbtagsregel) */
  basisSek: number;
  sollSek: number;
  grund: SollGrund;
  feiertag?: string;
  regel?: string;
  abwesenheit?: Abwesenheit;
  /** verbrauchte Urlaubstage an diesem Tag */
  urlaubstage: number;
}

export function abwesenheitAm(liste: Abwesenheit[], konto: string, tag: string): Abwesenheit | undefined {
  return liste.find((a) => a.konto === konto && a.von <= tag && tag <= a.bis);
}

/** Soll eines Tags in klarer Reihenfolge: Arbeitstag des Kontos, Feiertag des Bundeslands, Halbtagsregel, Abwesenheit
 *  (wie die Kalenderlogik der alten App, jetzt je Konto) */
export function sollAm(k: Zeitkonto, abwesenheiten: Abwesenheit[], tag: string): TagSoll {
  const wt = wochentag(tag);
  const tagesSek = k.tage.length ? Math.round((k.wochenstunden * 3600) / k.tage.length) : 0;
  const ft = feiertag(tag, k.bundesland);
  const abw = abwesenheitAm(abwesenheiten, k.konto, tag);
  if (!k.tage.includes(wt)) return { tag, basisSek: 0, sollSek: 0, grund: wt === 0 || wt === 6 ? "wochenende" : "arbeitsfrei", feiertag: ft, urlaubstage: 0 };
  if (ft) return { tag, basisSek: 0, sollSek: 0, grund: "feiertag", feiertag: ft, urlaubstage: 0 };
  const regel = k.halbtage.find((r) => Number(tag.slice(5, 7)) === r.monat && Number(tag.slice(8, 10)) === r.tag);
  const basis = regel ? tagesSek / 2 : tagesSek;
  const tagesanteil = tagesSek ? basis / tagesSek : 0;
  if (abw) {
    const w = ARTEN[abw.art];
    const anteil = abw.anteil ?? 1;
    return { tag, basisSek: basis, sollSek: basis * (1 - anteil * (1 - w.soll)), grund: abw.art, regel: regel?.name, abwesenheit: abw,
             urlaubstage: w.urlaub * anteil * tagesanteil };
  }
  return { tag, basisSek: basis, sollSek: basis, grund: regel ? "halbtagsregel" : "arbeitstag", regel: regel?.name, urlaubstage: 0 };
}

/** Wirkung einer (geplanten) Abwesenheit: Arbeitstage, entfallendes Soll, Urlaubstage */
export function wirkung(k: Zeitkonto, a: Abwesenheit): { arbeitstage: number; sollSek: number; urlaubstage: number; tage: TagSoll[] } {
  const tage = tageVon(a.von, a.bis).map((t) => sollAm(k, [a], t));
  const arbeit = tage.filter((t) => t.basisSek > 0);
  return {
    tage,
    arbeitstage: arbeit.reduce((s, t) => s + (t.regel ? 0.5 : 1), 0),
    sollSek: arbeit.reduce((s, t) => s + (t.basisSek - t.sollSek), 0),
    urlaubstage: arbeit.reduce((s, t) => s + t.urlaubstage, 0),
  };
}

/** Urlaubstage eines Jahres bis einschließlich bis (oder danach), gewichtet mit der echten Wirkung des Tags */
export function urlaubstage(k: Zeitkonto, abwesenheiten: Abwesenheit[], jahr: number, bis: string, danach = false): number {
  let summe = 0;
  for (const a of abwesenheiten.filter((x) => x.konto === k.konto && ARTEN[x.art].urlaub > 0)) {
    for (const t of tageVon(a.von, a.bis)) {
      if (Number(t.slice(0, 4)) !== jahr || (danach ? t <= bis : t > bis)) continue;
      summe += sollAm(k, [a], t).urlaubstage;
    }
  }
  return summe;
}

export interface Brueckentag {
  tag: string;
  /** der Feiertag, an den er grenzt */
  feiertag: string;
  /** freie Tage am Stück, wenn man ihn nimmt */
  frei: number;
}

/** Arbeitstage, deren beide Nachbartage frei sind (Feiertag oder kein Arbeitstag), mit einem Feiertag daneben */
export function brueckentage(k: Zeitkonto, von: string, bis: string): Brueckentag[] {
  const frei = (t: string) => !k.tage.includes(wochentag(t)) || !!feiertag(t, k.bundesland);
  const out: Brueckentag[] = [];
  for (const t of tageVon(von, bis)) {
    if (frei(t)) continue;
    const vor = plusTage(t, -1), nach = plusTage(t, 1);
    if (!frei(vor) || !frei(nach)) continue;
    const ft = feiertag(vor, k.bundesland) ?? feiertag(nach, k.bundesland);
    if (!ft) continue;
    let a = vor, b = nach;
    while (frei(plusTage(a, -1))) a = plusTage(a, -1);
    while (frei(plusTage(b, 1))) b = plusTage(b, 1);
    out.push({ tag: t, feiertag: ft, frei: tageVon(a, b).length });
  }
  return out;
}
