// Was sich aus dem Zustand ergibt, an einem Ort gerechnet: Zeit einer Karte, Timer einer Person, Ist und Soll, Urlaub,
// Hinweise, sichtbare Karten einer Spalte. In der App liefert das die Schnittstelle (dieselben Regeln auf dem Server);
// die Ansichten fragen nur hier, nie mit eigener Rechnung.

import type { Board, Karte, Spalte, Timer, Zeitfenster } from "../modell";
import { fassungAm, sollAm, urlaubstage, type TagSoll } from "../regeln/arbeitszeit";
import { hatRecht, imArchiv, imFenster } from "../regeln/board";
import { tageVon } from "../regeln/tage";
import { HEUTE, ICH } from "./daten";
import { MONATSIST, TAGESREST } from "./daten-zeit";
import { laufendSek } from "./format";
import { board, karte, kartenDerSpalte, stand } from "./stand.svelte";

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
export function sichtbareKarten(b: Board, s: Spalte, fenster: Zeitfenster = s.zeitfenster ?? "woche"): Karte[] {
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
