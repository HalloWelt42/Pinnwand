// Veränderlicher Zustand der Zeit-Ansichten: Zeiteinträge und Abwesenheiten wirken in den Entwürfen wie in der App,
// bis zum Neuladen der Seite. Jede Änderung läuft durch genau eine Funktion hier (in der App: ein Anwendungsfall der
// Module Zeiterfassung und Arbeitszeit), mit Meldung und Rückgängig. Der Timer ist der eine Timer je Person aus dem
// gemeinsamen Stand (src/beispiel/stand.svelte.ts); Anhalten und Starten wirken darum auch im Kopf und im Board.

import { ABWESENHEITEN, HEUTE, ICH, JETZT, ZEITEINTRAEGE, ZEITKONTEN } from "../../beispiel/daten";
import { datum, dauer, laufendSek } from "../../beispiel/format";
import { karte as karteImStand, stand } from "../../beispiel/stand.svelte";
import type { Abwesenheit, Karte, Zeitkonto } from "../../modell";
import { HALBTAGSREGELN, MONATSIST, TAGESREST, ZUSATZABWESENHEITEN, ZUSATZEINTRAEGE, ZUSATZKARTEN } from "./daten";
import { ARTEN, sollAm, tageImMonat, tageVonBis, type Halbtagsregel, type TagSoll } from "./regeln";
import type { Eintrag } from "./typen";

export interface Meldung {
  text: string;
  rueckgaengig?: () => void;
}

export const zeit = $state({
  eintraege: structuredClone([...ZEITEINTRAEGE, ...ZUSATZEINTRAEGE]) as Eintrag[],
  abwesenheiten: structuredClone([...ABWESENHEITEN, ...ZUSATZABWESENHEITEN]) as Abwesenheit[],
  meldung: null as Meldung | null,
});

/** Kennung ohne Zähler und ohne randomUUID (das fehlt außerhalb sicherer Kontexte) */
export function neueKennung(): string {
  const b = crypto.getRandomValues(new Uint8Array(8));
  return "z-" + Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}

function melden(text: string, rueckgaengig?: () => void): void {
  zeit.meldung = { text, rueckgaengig };
}

// ═══ Lesen ═══════════════════════════════════════════════════════════════════════════════════════════════

export function karteVon(id: string): Karte | undefined {
  return karteImStand(id) ?? ZUSATZKARTEN.find((k) => k.id === id);
}

export function kontoVon(id: string): Zeitkonto | undefined {
  return ZEITKONTEN.find((k) => k.konto === id);
}

export function halbtage(konto: string): Halbtagsregel[] {
  return HALBTAGSREGELN[konto] ?? [];
}

export function soll(konto: string, tag: string): TagSoll | null {
  const k = kontoVon(konto);
  return k ? sollAm(k, halbtage(konto), zeit.abwesenheiten, tag) : null;
}

/** Der eine laufende Timer einer Person */
export function laufend(konto: string): { karte: Karte; seit: string } | undefined {
  const k = stand.karten.find((x) => x.laeuft?.konto === konto);
  return k ? { karte: k, seit: k.laeuft!.seit } : undefined;
}

/** Laufende Sekunden an einem Tag (der Timer läuft in den Entwürfen nie über Mitternacht) */
export function laufendAm(konto: string, tag: string, karteId?: string): number {
  const l = laufend(konto);
  if (!l || l.seit.slice(0, 10) !== tag || (karteId && l.karte.id !== karteId)) return 0;
  return laufendSek(l.seit);
}

export function eintraegeVon(konto: string, von: string, bis = von): Eintrag[] {
  return zeit.eintraege.filter((e) => e.konto === konto && e.datum >= von && e.datum <= bis);
}

/** Ist eines Tags: Einträge, nicht einzeln geführte Zeit und der laufende Timer */
export function istAm(konto: string, tag: string): number {
  return eintraegeVon(konto, tag).reduce((s, e) => s + e.sekunden, 0) + (TAGESREST[konto]?.[tag] ?? 0) + laufendAm(konto, tag);
}

function monatsSchluessel(tag: string): string {
  return tag.slice(0, 7);
}

/** Ist eines Zeitraums; Monate vor den einzeln geführten Tagen kommen als Monatssumme */
export function istBereich(konto: string, von: string, bis: string): number {
  let summe = 0;
  const gezaehlt = new Set<string>();
  for (const t of tageVonBis(von, bis)) {
    const m = MONATSIST[konto]?.[monatsSchluessel(t)];
    if (m === undefined) summe += istAm(konto, t);
    else if (!gezaehlt.has(monatsSchluessel(t))) { summe += m; gezaehlt.add(monatsSchluessel(t)); }
  }
  return summe;
}

export function sollBereich(konto: string, von: string, bis: string): number {
  return tageVonBis(von, bis).reduce((s, t) => s + (soll(konto, t)?.sollSek ?? 0), 0);
}

/** Überstunden: Ist minus Soll über das Jahr bis einschließlich des Tags */
export function saldo(konto: string, bis: string): number {
  const von = `${bis.slice(0, 4)}-01-01`;
  return istBereich(konto, von, bis) - sollBereich(konto, von, bis);
}

export function monatsende(jahr: number, monat: number): string {
  return `${jahr}-${String(monat).padStart(2, "0")}-${String(tageImMonat(jahr, monat)).padStart(2, "0")}`;
}

// ═══ Zeit buchen und ändern ══════════════════════════════════════════════════════════════════════════════

function minuten(hhmm: string): number {
  const [hh, mm] = hhmm.split(":").map(Number);
  return hh * 60 + mm;
}

function hhmm(min: number): string {
  return `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}`;
}

function schluessel(karteId: string): string {
  return karteVon(karteId)?.schluessel ?? "";
}

function sichern(): () => void {
  const vorher = structuredClone($state.snapshot(zeit.eintraege)) as Eintrag[];
  return () => { zeit.eintraege = vorher; zeit.meldung = null; };
}

/** Eintrag kürzen; bei einem Timer-Eintrag rückt das Ende mit, damit von, bis und Dauer zusammenpassen */
function kuerzen(e: Eintrag, sek: number): void {
  e.sekunden -= sek;
  if (e.bis && e.von && e.herkunft === "timer") {
    const ende = Math.max(minuten(e.von), minuten(e.bis) - Math.round(sek / 60));
    e.bis = hhmm(ende);
    if (e.sitzungen?.length) e.sitzungen[e.sitzungen.length - 1].bis = e.bis;
  }
}

/** Zelle des Stundenzettels: setzt deine Zeit auf einer Karte an einem Tag. Mehr bucht die Differenz auf genau diesen
 *  Tag (als Korrektur, wenn schon Zeit da war), weniger kürzt deine jüngsten Einträge dieses Tags; fremde Einträge
 *  bleiben unberührt (Ticketzeit setzen der alten App, jetzt taggenau und nur für die eigene Zeit). */
export function setzeTageszeit(karteId: string, tag: string, sek: number): void {
  const eigene = zeit.eintraege.filter((e) => e.konto === ICH && e.karte === karteId && e.datum === tag);
  const bisher = eigene.reduce((s, e) => s + e.sekunden, 0);
  const diff = sek - bisher;
  if (diff === 0) return;
  const zurueck = sichern();
  if (diff > 0) {
    zeit.eintraege.push({ id: neueKennung(), karte: karteId, konto: ICH, datum: tag, sekunden: diff, herkunft: bisher ? "korrektur" : "hand" });
  } else {
    let rest = -diff;
    const reihe = [...eigene].sort((a, b) => rang(b) - rang(a));
    for (const e of reihe) {
      if (rest <= 0) break;
      if (e.sekunden <= rest) {
        rest -= e.sekunden;
        zeit.eintraege = zeit.eintraege.filter((x) => x.id !== e.id);
      } else {
        kuerzen(zeit.eintraege.find((x) => x.id === e.id)!, rest);
        rest = 0;
      }
    }
  }
  melden(`${schluessel(karteId)} ${datum(tag, true)}: ${dauer(bisher)} auf ${dauer(sek)} gesetzt`, zurueck);
}

/** jüngster zuerst: Korrektur, dann nachgetragen, dann Timer nach Ende */
function rang(e: Eintrag): number {
  const art = { korrektur: 3, hand: 2, serie: 1, timer: 0 }[e.herkunft];
  return art * 10000 + (e.bis ? minuten(e.bis) : 0);
}

/** Zeit nachtragen: ein eigener Eintrag auf diese Karte an diesem Tag */
export function buchen(karteId: string, tag: string, sek: number, notiz = ""): void {
  const zurueck = sichern();
  zeit.eintraege.push({ id: neueKennung(), karte: karteId, konto: ICH, datum: tag, sekunden: sek, herkunft: "hand", notiz: notiz || undefined });
  melden(`${dauer(sek)} auf ${schluessel(karteId)} gebucht (${datum(tag, true)})`, zurueck);
}

export function dauerAendern(id: string, sek: number): void {
  const e = zeit.eintraege.find((x) => x.id === id);
  if (!e || e.sekunden === sek) return;
  const zurueck = sichern();
  const alt = e.sekunden;
  if (sek < alt) kuerzen(e, alt - sek);
  else {
    e.sekunden = sek;
    if (e.herkunft === "timer" && e.von && e.bis && !e.sitzungen) e.bis = hhmm(Math.min(24 * 60, minuten(e.von) + Math.round(sek / 60)));
  }
  melden(`${schluessel(e.karte)} ${datum(e.datum, true)}: ${dauer(alt)} auf ${dauer(sek)} geändert`, zurueck);
}

export function notizAendern(id: string, notiz: string): void {
  const e = zeit.eintraege.find((x) => x.id === id);
  if (e && (e.notiz ?? "") !== notiz) e.notiz = notiz || undefined;
}

/** Löschen mit Rückgängig: der Eintrag kommt genau so zurück (Person, Zeiten, Herkunft) */
export function loeschen(id: string): void {
  const e = zeit.eintraege.find((x) => x.id === id);
  if (!e) return;
  const zurueck = sichern();
  zeit.eintraege = zeit.eintraege.filter((x) => x.id !== id);
  melden(`Zeiteintrag (${dauer(e.sekunden)}, ${datum(e.datum, true)}) gelöscht`, zurueck);
}

/** Rückfrage nach dem Deckel: das tatsächliche Ende der Sitzung übernehmen */
export function deckelKorrigieren(ids: string[], ende: string): void {
  const zurueck = sichern();
  for (const id of ids) {
    const e = zeit.eintraege.find((x) => x.id === id);
    if (!e) continue;
    if (e.von === "00:00") { e.bis = ende; e.sekunden = minuten(ende) * 60; }
    e.gedeckelt = undefined;
  }
  melden(`Ende auf ${ende} gesetzt, Rückfrage erledigt`, zurueck);
}

export function deckelBestaetigen(ids: string[]): void {
  for (const id of ids) {
    const e = zeit.eintraege.find((x) => x.id === id);
    if (e) e.gedeckelt = undefined;
  }
  melden("12 Stunden bleiben gebucht, Rückfrage erledigt");
}

// ═══ Der eine Timer je Person ════════════════════════════════════════════════════════════════════════════

/** Anhalten bucht die Sitzung in den Timer-Eintrag der Karte an diesem Tag (je Karte und Tag einer) */
function sitzungBuchen(k: Karte): number {
  const seit = k.laeuft!.seit;
  const sek = Math.round(laufendSek(seit));
  const tag = seit.slice(0, 10), von = seit.slice(11, 16), bis = JETZT.slice(11, 16);
  const vorhanden = zeit.eintraege.find((e) => e.konto === ICH && e.karte === k.id && e.datum === tag && e.herkunft === "timer");
  if (vorhanden) {
    vorhanden.sitzungen = [...(vorhanden.sitzungen ?? [{ von: vorhanden.von!, bis: vorhanden.bis! }]), { von, bis }];
    vorhanden.sekunden += sek;
    vorhanden.bis = bis;
  } else {
    zeit.eintraege.push({ id: neueKennung(), karte: k.id, konto: ICH, datum: tag, von, bis, sekunden: sek, herkunft: "timer" });
  }
  k.erfasstSek += sek;
  k.laeuft = undefined;
  return sek;
}

export function anhalten(): void {
  const l = laufend(ICH);
  if (!l) return;
  const sek = sitzungBuchen(l.karte);
  melden(`Timer angehalten: ${dauer(sek)} auf ${l.karte.schluessel} gebucht`);
}

/** Start auf einer Karte hält einen laufenden Timer derselben Person an und bucht ihn; fremde Timer laufen weiter */
export function starten(karteId: string): void {
  const k = karteImStand(karteId);
  if (!k || k.art !== "arbeit") return;
  const l = laufend(ICH);
  const gebucht = l ? sitzungBuchen(l.karte) : 0;
  k.laeuft = { seit: JETZT, konto: ICH };
  if (!k.start) k.start = HEUTE;
  melden(l ? `${l.karte.schluessel} angehalten (${dauer(gebucht)} gebucht), Timer läuft auf ${k.schluessel}` : `Timer läuft auf ${k.schluessel}`);
}

// ═══ Abwesenheiten ═══════════════════════════════════════════════════════════════════════════════════════

export function abwesenheitEintragen(a: Abwesenheit): void {
  const vorher = [...zeit.abwesenheiten];
  zeit.abwesenheiten = [...zeit.abwesenheiten.filter((x) => !(x.konto === a.konto && x.von <= a.bis && a.von <= x.bis)), a];
  const spanne = a.von === a.bis ? datum(a.von, true) : `${datum(a.von, true)} bis ${datum(a.bis, true)}`;
  melden(`${ARTEN[a.art].name} eingetragen: ${spanne}`, () => { zeit.abwesenheiten = vorher; zeit.meldung = null; });
}

export function abwesenheitEntfernen(a: Abwesenheit): void {
  const vorher = [...zeit.abwesenheiten];
  zeit.abwesenheiten = zeit.abwesenheiten.filter((x) => x !== a && !(x.konto === a.konto && x.von === a.von && x.bis === a.bis));
  melden(`${ARTEN[a.art].name} ${datum(a.von, true)} entfernt`, () => { zeit.abwesenheiten = vorher; zeit.meldung = null; });
}
