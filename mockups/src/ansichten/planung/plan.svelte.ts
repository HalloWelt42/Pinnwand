// Zustand und Regeln der Planung: Serien, Termine, Karten mit Daten, Vorkommen einer Serie, Nachtrag, Abwesenheiten
// und Feiertage. Ansichten lesen nur hierüber und ändern nur über die Anwendungsfälle unten (wie später die
// Anwendungsschicht des Moduls Serien und Termine); in den Entwürfen wirken Änderungen bis zum Neuladen.

import { ABWESENHEITEN, HEUTE, ICH, JETZT, SERIEN, TERMINE, ZEITKONTEN } from "../../beispiel/daten";
import { datum } from "../../beispiel/format";
import { konto, stand } from "../../beispiel/stand.svelte";
import type { Abwesenheit, AbwesenheitArt, Board, Karte, Kennung, Serie, Termin } from "../../modell";
import { boardPfad } from "../../weg.svelte";
import { BESTAETIGT, BESTAETIGT_BIS, FEIERTAGE, PLAN_KARTEN, PLAN_SERIEN, PLAN_TERMINE, REGELN } from "./daten";
import { istWochenende, minutenAus, plusTage, TAGE_LANG, tageImMonat, tageVon, wochentag } from "./tage";
import type { Feiertag, Nachtragposten, SerienRegel, Vorkommen, VorkommenStand } from "./typen";

export const plan = $state({
  karten: structuredClone(PLAN_KARTEN) as Karte[],
  serien: structuredClone([...SERIEN, ...PLAN_SERIEN]) as Serie[],
  termine: structuredClone([...TERMINE, ...PLAN_TERMINE]) as Termin[],
  regeln: structuredClone(REGELN) as Record<Kennung, SerienRegel>,
});

export const GESTERN = plusTage(HEUTE, -1);
const JETZT_UHR = JETZT.slice(11, 16);

/* ═══ Boards, Rechte, Karten ═══════════════════════════════════════════════════════════════════════════ */

export function boardVon(id: Kennung): Board | undefined {
  return stand.boards.find((b) => b.id === id);
}

export function hatRecht(b: Board, recht: string, kontoId: Kennung = ICH): boolean {
  const rolle = b.mitglieder.find((m) => m.konto === kontoId)?.rolle;
  return b.rollen.find((r) => r.id === rolle)?.rechte.includes(recht) ?? false;
}

/** Boards, in denen du Mitglied bist und das Modul Serien und Termine an ist */
export function boardsMitSerien(): Board[] {
  return stand.boards.filter((b) => b.module.serien && b.mitglieder.some((m) => m.konto === ICH));
}

/** Karten eines Boards: die aus dem Zustand des Boards und die zusätzlichen der Planung */
export function kartenDesBoards(boardId: Kennung): Karte[] {
  return [...stand.karten, ...plan.karten].filter((k) => k.board === boardId);
}

export function istErledigt(b: Board, k: Karte): boolean {
  return b.spalten.find((s) => s.id === k.spalte)?.erledigt ?? false;
}

export function farbeDerSpalte(b: Board, k: Karte): string {
  return b.spalten.find((s) => s.id === k.spalte)?.farbe ?? "stahl";
}

export function kartenPfad(b: Board, k: Karte): string {
  return boardPfad(b.kuerzel, k.schluessel.split("-")[1]);
}

/* ═══ Abwesenheiten und Feiertage ══════════════════════════════════════════════════════════════════════ */

export const ABWESENHEIT_NAME: Record<AbwesenheitArt, string> = {
  urlaub: "Urlaub", krank: "krank", frei: "frei", halbtag: "halber Tag frei", feiertag: "Feiertag", fortbildung: "Fortbildung",
};
export const ABWESENHEIT_SYMBOL: Record<AbwesenheitArt, string> = {
  urlaub: "fa-umbrella-beach", krank: "fa-briefcase-medical", frei: "fa-sun", halbtag: "fa-sun", feiertag: "fa-flag",
  fortbildung: "fa-graduation-cap",
};

/** Abwesenheiten der Mitglieder sieht nur, wer im Board das Recht hat, und nur mit dem Modul Arbeitszeit */
export function abwesenheitenSichtbar(b: Board): boolean {
  return b.module.arbeitszeit && hatRecht(b, "abwesenheit.sehen");
}

export function abwesenheit(kontoId: Kennung, tag: string): Abwesenheit | undefined {
  return ABWESENHEITEN.find((a) => a.konto === kontoId && a.von <= tag && tag <= a.bis);
}

function bundesland(kontoId: Kennung): string {
  return ZEITKONTEN.find((z) => z.konto === kontoId)?.bundesland ?? "";
}

function giltFuer(f: Feiertag, kontoId: Kennung): boolean {
  return f.laender.length === 0 || f.laender.includes(bundesland(kontoId));
}

/** Feiertage eines Tages, die für mindestens eine der Personen gelten, mit den betroffenen Personen */
export function feiertageAm(tag: string, konten: Kennung[]): { feiertag: Feiertag; konten: Kennung[] }[] {
  return FEIERTAGE.filter((f) => f.tag === tag)
    .map((f) => ({ feiertag: f, konten: konten.filter((k) => giltFuer(f, k)) }))
    .filter((x) => x.konten.length > 0);
}

/** "Allerheiligen: Feiertag in Nordrhein-Westfalen (Max Paulsen, Anna Berger)" */
export function feiertagTitel(f: Feiertag, konten: Kennung[]): string {
  if (f.laender.length === 0) return `${f.name}: bundesweit`;
  const laender = [...new Set(konten.map(bundesland))].join(" und ");
  return `${f.name}: Feiertag in ${laender} (${konten.map((k) => konto(k).name).join(", ")})`;
}

function istWerktag(tag: string): boolean {
  return !istWochenende(tag) && !FEIERTAGE.some((f) => f.tag === tag && f.laender.length === 0);
}

/* ═══ Rhythmus und Vorkommen einer Serie ═══════════════════════════════════════════════════════════════ */

/** pausiert an diesem Tag; ohne Tag: jetzt */
export function istPausiert(r: SerienRegel, tag: string = HEUTE): boolean {
  return !!r.pausiertSeit && tag >= r.pausiertSeit && !(r.fortgesetzt && tag >= r.fortgesetzt);
}

export function regel(s: Serie): SerienRegel {
  return plan.regeln[s.id] ?? { serie: s.id, labels: [], ab: HEUTE, vorlaufTage: 14, wochenendenUeberspringen: false,
                                feiertageUeberspringen: true, auslass: [], beruehrt: [], verworfen: [] };
}

/** der Tag der Serie im Monat eines Tages */
function monatstagDer(r: SerienRegel, tag: string): string {
  const monat = tag.slice(0, 8);
  const n = tageImMonat(tag);
  const t = (d: number): string => monat + String(d).padStart(2, "0");
  if (r.monatsregel === "erster-werktag") {
    for (let d = 1; d <= n; d++) if (istWerktag(t(d))) return t(d);
  }
  if (r.monatsregel === "letzter-werktag") {
    for (let d = n; d >= 1; d--) if (istWerktag(t(d))) return t(d);
  }
  return t(Math.min(r.monatstag ?? Number(r.ab.slice(8, 10)), n));
}

function trifft(s: Serie, r: SerienRegel, tag: string): boolean {
  const w = wochentag(tag);
  switch (s.rhythmus) {
    case "taeglich": return !(r.wochenendenUeberspringen && istWochenende(tag));
    case "werktags": return w >= 1 && w <= 5;
    case "woechentlich": return (s.tage?.length ? s.tage : [wochentag(r.ab)]).includes(w);
    case "monatlich": return tag === monatstagDer(r, tag);
  }
}

/** Tage, an denen der Rhythmus greift (vor Abwesenheiten, Auslass und Pause) */
function rhythmusTage(s: Serie, r: SerienRegel, von: string, bis: string): string[] {
  const a = von < r.ab ? r.ab : von;
  const e = r.bis && r.bis < bis ? r.bis : bis;
  return tageVon(a, e).filter((t) => trifft(s, r, t));
}

/** Stand eines Tages der Serie: wer fehlt, ob gelöscht, pausiert, bestätigt, vorgebucht oder erst geplant. Pause,
 *  Ändern und Urlaub räumen nur unberührte Vorbuchungen; angefasste Karten bleiben stehen. */
export function vorkommenAm(s: Serie, tag: string, r: SerienRegel = regel(s)): Vorkommen {
  const ohne = s.teilnehmer.flatMap((k) => {
    const a = abwesenheit(k, tag);
    if (a) return [{ konto: k, grund: ABWESENHEIT_NAME[a.art] }];
    const f = r.feiertageUeberspringen ? FEIERTAGE.find((x) => x.tag === tag && giltFuer(x, k)) : undefined;
    return f ? [{ konto: k, grund: f.name }] : [];
  });
  const da = s.teilnehmer.filter((k) => !ohne.some((o) => o.konto === k));
  const v = (stand: VorkommenStand, rest: Partial<Vorkommen> = {}): Vorkommen => ({ serie: s.id, tag, stand, ohne, offen: [], ...rest });
  const pausiert = istPausiert(r, tag);

  const geloescht = r.auslass.find((a) => a.tag === tag);
  if (geloescht) return v("geloescht", { notiz: `gelöscht von ${konto(geloescht.von).name} am ${datum(geloescht.am)}` });
  const beruehrt = tag > HEUTE ? r.beruehrt.find((b) => b.tag === tag) : undefined;
  if (beruehrt) return v("beruehrt", { notiz: beruehrt.grund });
  if (da.length === 0) return v("ausgelassen", { notiz: [...new Set(ohne.map((o) => o.grund))].join(", ") });
  if (tag < HEUTE) {
    if (pausiert) return v("pausiert");
    if (r.verworfen.includes(tag)) return v("verworfen");
    const bestaetigt = tag <= BESTAETIGT_BIS ? da : (BESTAETIGT.find((b) => b.serie === s.id && b.tag === tag)?.konten ?? []);
    const offen = da.filter((k) => !bestaetigt.includes(k));
    return v(offen.length ? "wartet" : "gezaehlt", { offen });
  }
  if (pausiert) return v("pausiert");
  if (tag === HEUTE) return v("heute");
  return v(tag <= plusTage(HEUTE, r.vorlaufTage) ? "vorgebucht" : "geplant");
}

export function vorkommen(s: Serie, von: string, bis: string, r: SerienRegel = regel(s)): Vorkommen[] {
  return rhythmusTage(s, r, von, bis).map((t) => vorkommenAm(s, t, r));
}

/** nächster Tag, an dem die Serie stattfindet; heute nur, solange die Uhrzeit noch kommt */
export function naechstes(s: Serie, r: SerienRegel = regel(s)): Vorkommen | undefined {
  return vorkommen(s, HEUTE, plusTage(HEUTE, 400), r).find((v) =>
    ["heute", "vorgebucht", "beruehrt", "geplant"].includes(v.stand) && !(v.tag === HEUTE && s.uhrzeit && s.uhrzeit < JETZT_UHR));
}

/** Tage für die Liste einer Serie: die letzten Tage, alles im Vorlauf, danach drei geplante */
export function vorkommenListe(s: Serie, r: SerienRegel = regel(s)): Vorkommen[] {
  const zurueck = s.rhythmus === "monatlich" ? 62 : s.rhythmus === "woechentlich" ? 22 : 8;
  const ende = plusTage(HEUTE, r.vorlaufTage);
  const alle = vorkommen(s, plusTage(HEUTE, -zurueck), plusTage(HEUTE, 400), r);
  return [...alle.filter((v) => v.tag <= ende), ...alle.filter((v) => v.tag > ende).slice(0, 3)];
}

/** Text des Rhythmus ohne Abkürzungen: "werktags", "wöchentlich montags", "monatlich am 30." */
export function rhythmusText(s: Serie, r: SerienRegel = regel(s)): string {
  switch (s.rhythmus) {
    case "taeglich": return r.wochenendenUeberspringen ? "täglich außer am Wochenende" : "täglich";
    case "werktags": return "werktags";
    case "woechentlich": {
      const tage = [...(s.tage ?? [])].sort((a, b) => ((a + 6) % 7) - ((b + 6) % 7)).map((t) => TAGE_LANG[t].toLowerCase() + "s");
      return "wöchentlich " + (tage.length > 1 ? `${tage.slice(0, -1).join(", ")} und ${tage[tage.length - 1]}` : tage[0] ?? "");
    }
    case "monatlich":
      if (r.monatsregel === "erster-werktag") return "monatlich am ersten Werktag";
      if (r.monatsregel === "letzter-werktag") return "monatlich am letzten Werktag";
      return `monatlich am ${r.monatstag ?? Number(r.ab.slice(8, 10))}.`;
  }
}

/** Serien eines Boards */
export function serienDesBoards(boardId: Kennung): Serie[] {
  return plan.serien.filter((s) => s.board === boardId);
}

export function termineDesBoards(boardId: Kennung): Termin[] {
  return plan.termine.filter((t) => t.board === boardId);
}

/* ═══ Termine und Nachtrag ═════════════════════════════════════════════════════════════════════════════ */

/** Stand einer Person bei einem Termin, immer mit Wort: vorher zugesagt oder offen, danach bestätigt oder wartet */
export function terminStand(t: Termin, k: Kennung): { text: string; symbol: string; klasse: string } {
  const b = boardVon(t.board);
  const a = b && abwesenheitenSichtbar(b) ? abwesenheit(k, t.datum) : undefined;
  if (a) return { text: ABWESENHEIT_NAME[a.art], symbol: ABWESENHEIT_SYMBOL[a.art], klasse: "warnung" };
  const vorbei = t.datum < HEUTE;
  if (t.bestaetigt.includes(k)) return { text: vorbei ? "bestätigt" : "zugesagt", symbol: "fa-circle-check", klasse: "gut" };
  return { text: vorbei ? "wartet" : "offen", symbol: "fa-circle-question", klasse: "offen" };
}

export function terminDauerMin(t: Termin): number {
  return minutenAus(t.bis) - minutenAus(t.von);
}

/** Deine vorgebuchten Zeiten vergangener Tage (höchstens 31 Tage zurück), die auf Bestätigung warten; nur deine */
export function nachtrag(kontoId: Kennung = ICH): Nachtragposten[] {
  const ab = plusTage(HEUTE, -31);
  const posten: Nachtragposten[] = [];
  for (const s of plan.serien.filter((x) => x.teilnehmer.includes(kontoId))) {
    for (const v of vorkommen(s, ab, GESTERN)) {
      if (v.stand !== "wartet" || !v.offen.includes(kontoId)) continue;
      posten.push({ art: "serie", bezug: s.id, board: s.board, titel: s.titel, tag: v.tag, von: s.uhrzeit, geplantMin: s.dauerMin,
                    bestaetigt: s.teilnehmer.filter((k) => !v.offen.includes(k) && !v.ohne.some((o) => o.konto === k)) });
    }
  }
  for (const t of plan.termine.filter((x) => x.datum >= ab && x.datum < HEUTE && x.teilnehmer.includes(kontoId) && !x.bestaetigt.includes(kontoId))) {
    posten.push({ art: "termin", bezug: t.id, board: t.board, titel: t.titel, tag: t.datum, von: t.von, geplantMin: terminDauerMin(t),
                  bestaetigt: t.bestaetigt });
  }
  return posten.sort((a, b) => (a.tag + (a.von ?? "")).localeCompare(b.tag + (b.von ?? "")));
}

/* ═══ Anwendungsfälle: Fällig, Start und Zeitraum einer Karte ═══════════════════════════════════════════ */

export function faelligSetzen(k: Karte, tag: string): void {
  if (k.faellig === tag) return;
  k.faellig = tag;
  if (k.start && k.start > tag) k.start = tag;
  stand.meldung = `${k.schluessel} fällig ${datum(tag, true)}`;
}

export function faelligEntfernen(k: Karte): void {
  if (!k.faellig) return;
  k.faellig = undefined;
  stand.meldung = `${k.schluessel}: Fälligkeit entfernt`;
}

/** Start und Fällig zusammen (Zeitachse); was leer bleibt, bleibt leer */
export function zeitraumSetzen(k: Karte, start: string | undefined, faellig: string | undefined): void {
  if (k.start === start && k.faellig === faellig) return;
  k.start = start;
  k.faellig = faellig;
  const teile = [start ? `Start ${datum(start, true)}` : "", faellig ? `fällig ${datum(faellig, true)}` : ""].filter((x) => x);
  stand.meldung = `${k.schluessel}: ${teile.join(", ")}`;
}

export function datumEntfernen(k: Karte): void {
  if (!k.start && !k.faellig) return;
  k.start = undefined;
  k.faellig = undefined;
  stand.meldung = `${k.schluessel}: Start und Fälligkeit entfernt`;
}
