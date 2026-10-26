// Regeln des Moduls Serien und Termine als reine Funktionen: an welchen Tagen eine Serie greift, welchen Stand jeder Tag
// hat (vorbei und bestätigt, wartet, heute, vorgebucht, angefasst, geplant, gelöscht, entfällt, pausiert), der nächste
// Tag und der Vorlauf. Was die Regeln über Personen und Karten wissen müssen, gibt der Aufrufer als Umfeld (aus dem
// Zustand oder in der App aus dem Server); hier steht kein Zustand. In der App dieselben Regeln im Modul auf dem Server.

import type { Kennung, Serie } from "../modell";
import { istWochenende, plusTage, tageImMonat, tageVon, wochentag } from "./tage";

/** So viele Tage im Voraus legt eine Serie ihre Karten höchstens an; gleich VORLAUF_HOECHSTENS in
 *  backend/app/anwendung/serien.py */
export const VORLAUF_HOECHSTENS = 60;

/** Was die Regeln über Personen und die Karten der Serientage wissen müssen */
export interface SerienUmfeld {
  heute: string;
  /** Uhrzeit jetzt ("10:42"): ein Tag heute zählt als nächster, solange seine Uhrzeit noch kommt */
  jetzt: string;
  /** ganztägige Abwesenheit einer Person an einem Tag, als Wort (Urlaub, Krank, ...); sonst nichts */
  abwesend: (konto: Kennung, tag: string) => string | undefined;
  /** Feiertag im Bundesland der Person an diesem Tag, als Name; sonst nichts */
  feiertag: (konto: Kennung, tag: string) => string | undefined;
  /** die Karte eines Serientags: wer zuständig ist, wer seine Zeit dafür gebucht hat und ob jemand sie angefasst hat
   *  (nicht mehr in der Zielspalte, erledigt, mit Zeit oder mehr im Verlauf als ihr Anlegen) */
  tagKarte: (serie: Kennung, tag: string) => { id: Kennung; zustaendig: Kennung[]; gebucht: Kennung[]; angefasst: boolean } | undefined;
  /** bis zu diesem Tag gelten Serientage als bestätigt (ältere führt niemand einzeln nach) */
  bestaetigtBis: string;
}

/** Stand eines Tages einer Serie */
export type VorkommenStand =
  | "gezaehlt"     // vorbei, alle Anwesenden haben ihre Zeit bestätigt
  | "wartet"       // vorbei, mindestens eine vorgebuchte Zeit wartet auf Bestätigung
  | "verworfen"    // vorbei, fand nicht statt
  | "heute"
  | "vorgebucht"   // Karte liegt in der Zielspalte, unberührt
  | "beruehrt"     // Karte liegt da und wurde angefasst: bleibt beim Ändern, bei der Pause und im Urlaub
  | "geplant"      // jenseits des Vorlaufs: noch keine Karte
  | "geloescht"    // bewusst gelöscht: kommt nicht wieder
  | "ausgelassen"  // alle Teilnehmer fehlen (Abwesenheit, Feiertag)
  | "pausiert";

export interface Vorkommen {
  serie: Kennung;
  tag: string;
  stand: VorkommenStand;
  /** Teilnehmer, die an diesem Tag fehlen, mit Grund */
  ohne: { konto: Kennung; grund: string }[];
  /** wer seine Zeit noch nicht bestätigt hat (nur vorbei) */
  offen: Kennung[];
  /** Karte des Tags, wenn es sie gibt */
  karte?: Kennung;
  notiz?: string;
}

/** Eine vorgebuchte Zeit eines vergangenen Tages, die auf Bestätigung wartet (Nachtrag am Folgetag) */
export interface Nachtragposten {
  art: "serie" | "termin";
  /** Kennung der Serie oder des Termins */
  bezug: Kennung;
  /** Karte des Serientags (nur Serie) */
  karte?: Kennung;
  board: Kennung;
  titel: string;
  tag: string;
  von?: string;
  geplantMin: number;
  /** wer sonst schon bestätigt hat */
  bestaetigt: Kennung[];
}

/** Pausiert an diesem Tag: ab pausiertSeit, bis fortgesetzt wurde */
export function istPausiert(s: Serie, tag: string): boolean {
  return !!s.pausiertSeit && tag >= s.pausiertSeit && !(s.fortgesetzt && tag >= s.fortgesetzt);
}

/** Letzter Tag, für den die Serie schon eine Karte angelegt hat */
export function vorlaufEnde(s: Serie, heute: string): string {
  return plusTage(heute, s.vorlaufTage);
}

/** Werktag für alle Teilnehmer: Montag bis Freitag und für keinen ein Feiertag */
function werktag(s: Serie, tag: string, u: SerienUmfeld): boolean {
  return !istWochenende(tag) && !s.teilnehmer.some((k) => u.feiertag(k, tag));
}

/** Der Tag der Serie im Monat eines Tages */
function monatstagDer(s: Serie, tag: string, u: SerienUmfeld): string {
  const monat = tag.slice(0, 8);
  const n = tageImMonat(Number(tag.slice(0, 4)), Number(tag.slice(5, 7)));
  const t = (d: number): string => monat + String(d).padStart(2, "0");
  if (s.monatsregel === "erster-werktag") {
    for (let d = 1; d <= n; d++) if (werktag(s, t(d), u)) return t(d);
  }
  if (s.monatsregel === "letzter-werktag") {
    for (let d = n; d >= 1; d--) if (werktag(s, t(d), u)) return t(d);
  }
  return t(Math.min(s.monatstag ?? Number(s.ab.slice(8, 10)), n));
}

/** Greift der Rhythmus an diesem Tag (vor Abwesenheiten, Auslass und Pause)? */
function trifft(s: Serie, tag: string, u: SerienUmfeld): boolean {
  const w = wochentag(tag);
  switch (s.rhythmus) {
    case "taeglich": return !(s.wochenendenUeberspringen && istWochenende(tag));
    case "werktags": return w >= 1 && w <= 5;
    case "woechentlich": return (s.tage?.length ? s.tage : [wochentag(s.ab)]).includes(w);
    case "monatlich": return tag === monatstagDer(s, tag, u);
  }
}

function rhythmusTage(s: Serie, von: string, bis: string, u: SerienUmfeld): string[] {
  const a = von < s.ab ? s.ab : von;
  const e = s.bis && s.bis < bis ? s.bis : bis;
  return a > e ? [] : tageVon(a, e).filter((t) => trifft(s, t, u));
}

/** Stand eines Tages: wer fehlt, ob gelöscht, angefasst, pausiert, bestätigt, vorgebucht oder erst geplant. Pause,
 *  Ändern und Urlaub räumen nur unberührte Vorbuchungen; angefasste Karten bleiben stehen. Gibt es die Karte des Tags,
 *  gilt sie: ihre Zuständigen sind die Erwarteten, ihre Zeiteinträge die Bestätigungen. */
export function vorkommenAm(s: Serie, tag: string, u: SerienUmfeld): Vorkommen {
  const ohne = s.teilnehmer.flatMap((k) => {
    const a = u.abwesend(k, tag);
    if (a) return [{ konto: k, grund: a }];
    const f = s.feiertageUeberspringen ? u.feiertag(k, tag) : undefined;
    return f ? [{ konto: k, grund: f }] : [];
  });
  const da = s.teilnehmer.filter((k) => !ohne.some((o) => o.konto === k));
  const karte = u.tagKarte(s.id, tag);
  const v = (stand: VorkommenStand, rest: Partial<Vorkommen> = {}): Vorkommen =>
    ({ serie: s.id, tag, stand, ohne, offen: [], karte: karte?.id, ...rest });
  const pausiert = istPausiert(s, tag);

  const geloescht = s.auslass.find((a) => a.tag === tag);
  if (geloescht) return v("geloescht");
  if (tag > u.heute && karte?.angefasst) return v("beruehrt");
  if (da.length === 0) return v("ausgelassen", { notiz: [...new Set(ohne.map((o) => o.grund))].join(", ") });
  if (tag < u.heute) {
    if (pausiert) return v("pausiert");
    if (s.verworfen.includes(tag)) return v("verworfen");
    if (!karte || tag <= u.bestaetigtBis) return v("gezaehlt");
    const offen = karte.zustaendig.filter((k) => !ohne.some((o) => o.konto === k) && !karte.gebucht.includes(k));
    return v(offen.length ? "wartet" : "gezaehlt", { offen });
  }
  if (pausiert) return v("pausiert");
  if (tag === u.heute) return v("heute");
  return v(tag <= vorlaufEnde(s, u.heute) ? "vorgebucht" : "geplant");
}

/** Alle Tage der Serie in einem Zeitraum mit ihrem Stand */
export function vorkommen(s: Serie, von: string, bis: string, u: SerienUmfeld): Vorkommen[] {
  return rhythmusTage(s, von, bis, u).map((t) => vorkommenAm(s, t, u));
}

/** Nächster Tag, an dem die Serie stattfindet; heute nur, solange die Uhrzeit noch kommt */
export function naechstes(s: Serie, u: SerienUmfeld): Vorkommen | undefined {
  return vorkommen(s, u.heute, plusTage(u.heute, 400), u).find((v) =>
    ["heute", "vorgebucht", "beruehrt", "geplant"].includes(v.stand) && !(v.tag === u.heute && s.uhrzeit && s.uhrzeit < u.jetzt));
}

/** Tage für die Übersicht einer Serie: die letzten Tage, alles im Vorlauf, danach drei geplante */
export function vorkommenListe(s: Serie, u: SerienUmfeld): Vorkommen[] {
  const zurueck = s.rhythmus === "monatlich" ? 62 : s.rhythmus === "woechentlich" ? 22 : 8;
  const ende = vorlaufEnde(s, u.heute);
  const alle = vorkommen(s, plusTage(u.heute, -zurueck), plusTage(u.heute, 400), u);
  return [...alle.filter((v) => v.tag <= ende), ...alle.filter((v) => v.tag > ende).slice(0, 3)];
}

/** Titel der Karte eines Serientags: Uhrzeit vor dem Titel (wie in der alten App) */
export function kartenTitel(s: Pick<Serie, "titel" | "uhrzeit">): string {
  return s.uhrzeit ? `${s.uhrzeit} ${s.titel}` : s.titel;
}
