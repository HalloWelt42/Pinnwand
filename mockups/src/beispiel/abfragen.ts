// Was sich aus dem Zustand ergibt, an einem Ort gerechnet: Zeit einer Karte, Timer einer Person, Ist und Soll, Urlaub,
// Hinweise, sichtbare Karten einer Spalte. In der App liefert das die Schnittstelle (dieselben Regeln auf dem Server);
// die Ansichten fragen nur hier, nie mit eigener Rechnung.

import { ZEITFENSTER_VORGABE } from "../anzeige";
import type { Board, Karte, Kennung, Prioritaet, Serie, Spalte, Termin, Timer, Zeitfenster } from "../modell";
import { abwesenheitAm, artName, fassungAm, sollAm, urlaubstage, type TagSoll } from "../regeln/arbeitszeit";
import { feiertag } from "../regeln/feiertage";
import { vorkommen, type Nachtragposten, type SerienUmfeld } from "../regeln/serien";
import { hatRecht, imArchiv, imFenster, liegengeblieben } from "../regeln/board";
import { minutenAus, plusTage, tageVon, tageZwischen } from "../regeln/tage";
import { HEUTE, ICH, JETZT } from "./daten";
import { BESTAETIGT_BIS } from "./daten-planung";
import { MONATSIST, TAGESREST } from "./daten-zeit";
import { alterTage, laufendSek } from "./format";
import { board, karte, kartenDerSpalte, konto, stand } from "./stand.svelte";

// ═══ Timer ═══════════════════════════════════════════════════════════════════════════════════════════════

/** Der eine Timer einer Person (läuft oder angehalten) */
export function timerVon(konto = ICH): Timer | undefined {
  return stand.timer.find((t) => t.konto === konto);
}

/** Laufende Timer auf einer Karte (jede Person hat höchstens einen) */
export function laufendAuf(karteId: string): Timer[] {
  return stand.timer.filter((t) => t.karte === karteId && t.seit);
}

/** Sekunden der laufenden Sitzung eines Timers (0, wenn angehalten) */
export function sitzungSek(t: Timer | undefined): number {
  return t?.seit ? laufendSek(t.seit) : 0;
}

/** Darf auf dieser Karte ein Timer laufen? Nur Arbeit, nicht erledigt, Board mit Zeiterfassung, Recht zum Buchen */
export function timerErlaubt(k: Karte, konto = ICH): boolean {
  const b = board(k.board);
  const spalte = b.spalten.find((s) => s.id === k.spalte);
  return k.art === "arbeit" && !spalte?.erledigt && b.module.zeiterfassung && hatRecht(b, "zeit.buchen", konto);
}

// ═══ Zeit einer Karte ════════════════════════════════════════════════════════════════════════════════════

/** Gebuchte Zeit einer Karte: Summe ihrer Einträge, mit den laufenden Sitzungen */
export function zeitDerKarte(karteId: string, mitLaufend = true): number {
  const gebucht = stand.zeiteintraege.filter((e) => e.karte === karteId).reduce((s, e) => s + e.sekunden, 0);
  return gebucht + (mitLaufend ? laufendAuf(karteId).reduce((s, t) => s + sitzungSek(t), 0) : 0);
}

/** Zeit einer Gruppe verknüpfter Karten: jede Sekunde zählt einmal */
export function zeitDerGruppe(k: Karte): number {
  const ids = k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe).map((x) => x.id) : [k.id];
  return ids.reduce((s, id) => s + zeitDerKarte(id), 0);
}

/** Name einer Karte für Zeiteinträge, auch wenn sie im Papierkorb liegt oder entfernt ist */
export function kartenName(karteId: string): { schluessel: string; titel: string; zustand: "da" | "papierkorb" | "entfernt" } {
  const k = karte(karteId);
  if (k) return { schluessel: k.schluessel, titel: k.titel, zustand: "da" };
  const p = stand.papierkorb.flatMap((e) => e.karten).find((x) => x.id === karteId);
  if (p) return { schluessel: p.schluessel, titel: p.titel, zustand: "papierkorb" };
  const e = stand.entfernt.find((x) => x.karte === karteId);
  return { schluessel: e?.schluessel ?? "", titel: e?.titel ?? "Entfernte Karte", zustand: "entfernt" };
}

// ═══ Ist und Soll einer Person ═══════════════════════════════════════════════════════════════════════════

/** Ist eines Tags: Einträge, nicht einzeln geführte Zeit und die laufende Sitzung von heute */
export function istAm(konto: string, tag: string): number {
  const eintraege = stand.zeiteintraege.filter((e) => e.konto === konto && e.datum === tag).reduce((s, e) => s + e.sekunden, 0);
  const t = timerVon(konto);
  const laufend = t?.seit && t.seit.slice(0, 10) === tag ? sitzungSek(t) : 0;
  return eintraege + (TAGESREST[konto]?.[tag] ?? 0) + laufend;
}

/** Ist eines Zeitraums; Monate vor den einzeln geführten Tagen kommen als Monatssumme */
export function istBereich(konto: string, von: string, bis: string): number {
  let summe = 0;
  const gezaehlt = new Set<string>();
  for (const t of tageVon(von, bis)) {
    const monat = t.slice(0, 7);
    const m = MONATSIST[konto]?.[monat];
    if (m === undefined) summe += istAm(konto, t);
    else if (!gezaehlt.has(monat)) { summe += m; gezaehlt.add(monat); }
  }
  return summe;
}

/** Soll eines Tags aus der dann gültigen Fassung des Zeitkontos; ohne Zeitkonto nichts */
export function sollTag(konto: string, tag: string): TagSoll | null {
  const k = fassungAm(stand.zeitkonten, konto, tag);
  return k ? sollAm(k, stand.abwesenheiten, tag) : null;
}

export function sollBereich(konto: string, von: string, bis: string): number {
  return tageVon(von, bis).reduce((s, t) => s + (sollTag(konto, t)?.sollSek ?? 0), 0);
}

/** Überstunden: Ist minus Soll über das Jahr bis einschließlich des Tags */
export function saldo(konto: string, bis = HEUTE): number {
  const von = `${bis.slice(0, 4)}-01-01`;
  return istBereich(konto, von, bis) - sollBereich(konto, von, bis);
}

/** Urlaub eines Jahres: Anspruch mit Rest aus dem Vorjahr, genommen bis heute, geplant danach, übrig */
export function urlaub(konto: string, jahr = Number(HEUTE.slice(0, 4))): { anspruch: number; genommen: number; geplant: number; rest: number } | null {
  const k = fassungAm(stand.zeitkonten, konto, HEUTE);
  if (!k) return null;
  const anspruch = k.urlaubsanspruch + k.resturlaubVorjahr;
  const genommen = urlaubstage(k, stand.abwesenheiten, jahr, HEUTE);
  const geplant = urlaubstage(k, stand.abwesenheiten, jahr, HEUTE, true);
  return { anspruch, genommen, geplant, rest: anspruch - genommen - geplant };
}

// ═══ Board ═══════════════════════════════════════════════════════════════════════════════════════════════

/** Karten, die eine Spalte zeigt: offene alle, erledigte nur im Zeitfenster (nie die archivierten) */
export function sichtbareKarten(b: Board, s: Spalte, fenster: Zeitfenster = s.zeitfenster ?? ZEITFENSTER_VORGABE): Karte[] {
  const alle = kartenDerSpalte(s.id);
  return s.erledigt ? alle.filter((k) => imFenster(k, fenster, b.einstellungen, HEUTE)) : alle;
}

/** Erledigte Karten einer Spalte, die nicht im Archiv liegen (Zahl hinter "von" im Kopf der Spalte) */
export function erledigteOhneArchiv(b: Board, s: Spalte): Karte[] {
  return kartenDerSpalte(s.id).filter((k) => !imArchiv(k, b.einstellungen, HEUTE));
}

export function archivVon(b: Board): Karte[] {
  return stand.karten.filter((k) => k.board === b.id && imArchiv(k, b.einstellungen, HEUTE))
    .sort((x, y) => (y.abgeschlossen ?? "").localeCompare(x.abgeschlossen ?? ""));
}

export function papierkorbVon(boardId: string) {
  return stand.papierkorb.filter((e) => e.board === boardId);
}

/** Rechte der angemeldeten Person in einem Board */
export function darf(b: Board, recht: string): boolean {
  return hatRecht(b, recht, ICH);
}

/** Pfad einer Karte im Detail: /board/prod/131 */
export function kartenNummer(k: Karte): string {
  return k.schluessel.split("-")[1];
}

// ═══ Hinweise ════════════════════════════════════════════════════════════════════════════════════════════

export function ungelesen(): number {
  return stand.hinweise.filter((h) => !h.gelesen).length;
}

// ═══ Suche ═══════════════════════════════════════════════════════════════════════════════════════════════

/** Suchwörter aus der Eingabe (ohne Groß und Klein) */
export function woerter(suche: string): string[] {
  return suche.toLowerCase().split(/\s+/).filter(Boolean);
}

function suchtext(k: Karte, b: Board): string {
  return [k.schluessel, k.titel, k.beschreibung?.replace(/<[^>]+>/g, " "), k.notizen?.replace(/<[^>]+>/g, " "),
    ...k.labels.map((l) => b.labels.find((x) => x.id === l)?.name), ...Object.values(k.felder), ...k.kommentare.map((c) => c.text),
    ...k.checkliste.map((p) => p.text), ...k.zustaendig.map((p) => konto(p).name)].filter(Boolean).join(" ").toLowerCase();
}

/** Volltextsuche in Board, Liste und Archiv: jedes Wort muss in den Werten der Karte vorkommen (Schlüssel, Titel,
 *  Beschreibung, Notizen, Labels, eigene Felder, Kommentare, Checkliste, Zuständige), nie in gespeicherten Rohtexten */
export function passt(k: Karte, b: Board, suche: string | string[]): boolean {
  const w = typeof suche === "string" ? woerter(suche) : suche;
  if (!w.length) return true;
  const t = suchtext(k, b);
  return w.every((x) => t.includes(x));
}

// ═══ Mein Tag (Heute am Rechner und am Telefon) ══════════════════════════════════════════════════════════

/** "Diese Woche": fällig in den nächsten sieben Tagen */
export const WOCHE_TAGE = 7;

/** Eine Karte in Heute mit ihrem Board */
export interface TagEintrag {
  karte: Karte;
  board: Board;
}

export interface MeinTag {
  ueberfaellig: TagEintrag[];
  /** heute fällig, ohne Serienkarten */
  heute: TagEintrag[];
  /** heute fällige Serienkarten */
  serien: TagEintrag[];
  woche: TagEintrag[];
  ohneDatum: TagEintrag[];
  /** offen, nicht fällig und seit der Gefahrschwelle des Boards im Status (ohne laufenden Timer) */
  liegengeblieben: TagEintrag[];
  /** offen, nicht fällig und blockiert */
  blockiert: TagEintrag[];
  /** heute erledigt */
  erledigt: TagEintrag[];
  termine: { heute: Termin[]; woche: Termin[] };
}

const RANG: Record<Prioritaet, number> = { dringend: 0, hoch: 1, mittel: 2, niedrig: 3, keine: 4 };

function ordnung(a: TagEintrag, b: TagEintrag): number {
  return (a.karte.faellig ?? "9999").localeCompare(b.karte.faellig ?? "9999") || RANG[a.karte.prioritaet] - RANG[b.karte.prioritaet];
}

/** Dein Tag über alle Boards, in denen du Mitglied bist: jede offene Karte genau einmal nach Fälligkeit; dazu, was
 *  liegt oder blockiert ist, was heute erledigt wurde, und deine Termine von heute und den nächsten sieben Tagen */
export function meinTag(kontoId = ICH): MeinTag {
  const tag: MeinTag = { ueberfaellig: [], heute: [], serien: [], woche: [], ohneDatum: [], liegengeblieben: [], blockiert: [], erledigt: [],
                         termine: { heute: [], woche: [] } };
  const boards = stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === kontoId));
  const meine = stand.karten.flatMap((karte) => {
    const b = boards.find((x) => x.id === karte.board);
    return b && karte.zustaendig.includes(kontoId) ? [{ karte, board: b }] : [];
  }).sort(ordnung);
  for (const e of meine) {
    const spalte = e.board.spalten.find((s) => s.id === e.karte.spalte);
    if (spalte?.erledigt) {
      if (e.karte.abgeschlossen === HEUTE) tag.erledigt.push(e);
      continue;
    }
    const t = e.karte.faellig ? tageZwischen(HEUTE, e.karte.faellig) : null;
    if (t !== null && t < 0) tag.ueberfaellig.push(e);
    else if (t === 0) (e.karte.serie ? tag.serien : tag.heute).push(e);
    else if (t !== null && t <= WOCHE_TAGE) tag.woche.push(e);
    else {
      if (t === null) tag.ohneDatum.push(e);
      if (liegengeblieben(alterTage(e.karte.bewegtAm), e.board.einstellungen) && !laufendAuf(e.karte.id).length) tag.liegengeblieben.push(e);
      if (e.karte.blockiert) tag.blockiert.push(e);
    }
  }
  const termine = stand.termine.filter((t) => t.teilnehmer.includes(kontoId))
    .filter((t) => { const d = tageZwischen(HEUTE, t.datum); return d >= 0 && d <= WOCHE_TAGE; })
    .sort((a, b) => (a.datum + a.von).localeCompare(b.datum + b.von));
  tag.termine = { heute: termine.filter((t) => t.datum === HEUTE), woche: termine.filter((t) => t.datum !== HEUTE) };
  return tag;
}

// ═══ Serien: Umfeld der Regeln, Karte eines Tags, Nachtrag ═════════════════════════════════════════════════

export function serie(id: Kennung): Serie | undefined {
  return stand.serien.find((s) => s.id === id);
}

/** Die Karte eines Serientags: die Karte der Serie, fällig an diesem Tag (auch erledigt) */
export function karteDesTags(serieId: Kennung, tag: string): Karte | undefined {
  return stand.karten.find((k) => k.serie === serieId && k.faellig === tag);
}

/** Was die Regeln der Serien aus dem Zustand brauchen: Abwesenheiten (ganze Tage), Feiertage im Bundesland des
 *  Zeitkontos, die Karte jedes Tags mit den Personen, die darauf Zeit gebucht haben */
export function serienUmfeld(): SerienUmfeld {
  return {
    heute: HEUTE,
    jetzt: JETZT.slice(11, 16),
    abwesend: (k, tag) => {
      const a = abwesenheitAm(stand.abwesenheiten, k, tag);
      return a && (a.anteil ?? 1) >= 1 ? artName(a) : undefined;
    },
    feiertag: (k, tag) => {
      const z = fassungAm(stand.zeitkonten, k, tag);
      return z ? feiertag(tag, z.bundesland) : undefined;
    },
    tagKarte: (serieId, tag) => {
      const k = karteDesTags(serieId, tag);
      if (!k) return undefined;
      const gebucht = [...new Set(stand.zeiteintraege.filter((e) => e.karte === k.id && e.datum === tag).map((e) => e.konto))];
      return { id: k.id, zustaendig: k.zustaendig, gebucht };
    },
    bestaetigtBis: BESTAETIGT_BIS,
  };
}

/** Deine vorgebuchten Zeiten vergangener Tage (höchstens 31 Tage zurück), die auf deine Bestätigung warten: Serientage
 *  und Termine, nur deine (in der alten App fehlte die Grenze, M-111) */
export function nachtrag(kontoId: Kennung = ICH): Nachtragposten[] {
  const u = serienUmfeld();
  const ab = plusTage(HEUTE, -31);
  const gestern = plusTage(HEUTE, -1);
  const posten: Nachtragposten[] = [];
  for (const s of stand.serien.filter((x) => x.teilnehmer.includes(kontoId))) {
    for (const v of vorkommen(s, ab, gestern, u)) {
      if (v.stand !== "wartet" || !v.offen.includes(kontoId)) continue;
      const k = karteDesTags(s.id, v.tag);
      posten.push({ art: "serie", bezug: s.id, karte: v.karte, board: s.board, titel: s.titel, tag: v.tag, von: s.uhrzeit, geplantMin: s.dauerMin,
                    bestaetigt: (k?.zustaendig ?? []).filter((x) => !v.offen.includes(x) && !v.ohne.some((o) => o.konto === x)) });
    }
  }
  for (const t of stand.termine.filter((x) => x.datum >= ab && x.datum < HEUTE && x.teilnehmer.includes(kontoId) && !x.bestaetigt.includes(kontoId))) {
    if (u.abwesend(kontoId, t.datum)) continue;
    posten.push({ art: "termin", bezug: t.id, board: t.board, titel: t.titel, tag: t.datum, von: t.von,
                  geplantMin: minutenAus(t.bis) - minutenAus(t.von), bestaetigt: t.bestaetigt });
  }
  return posten.sort((a, b) => (a.tag + (a.von ?? "")).localeCompare(b.tag + (b.von ?? "")));
}
