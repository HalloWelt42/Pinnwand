// Anwendungsfälle der Telefonansicht in den Entwürfen: Timer, Zeit buchen, erledigen, verschieben, anlegen,
// kommentieren, Hinweise lesen. Sie ändern den gemeinsamen Zustand (stand) so, wie es die App über ihre Schnittstelle
// täte; Verschieben und Erledigen laufen über ablegen, denselben Weg wie das Ziehen im Board (Gruppe zieht mit,
// Abschlussdatum, Alter beginnt neu). Der Zustand des Telefons selbst (angehaltener Timer, gelesene Hinweise, gemerkte
// Spalte) steht in telefon.

import { HEUTE, ICH, JETZT, ZEITKONTEN } from "../../beispiel/daten";
import { datum, dauer, laufendSek } from "../../beispiel/format";
import { board, gruppenmitglieder, karte, kartenDerSpalte, stand } from "../../beispiel/stand.svelte";
import { ablegen } from "../../beispiel/anwendung/karten.svelte";
import type { Karte, Spalte } from "../../modell";
import { SPALTE_GEMERKT, TAGESSTAND } from "./daten";
import { wochenanfang } from "./eingabe";

export const telefon = $state({
  /** Karte mit angehaltenem Timer: Pause bucht die Sitzung, Fortsetzen geht weiter (M-79) */
  pausiert: "",
  /** Rückgängig zur letzten Meldung, solange sie steht (M-104) */
  rueckgaengig: null as (() => void) | null,
  /** am Telefon gelesene Hinweise */
  gelesen: [] as string[],
  /** eigene gebuchte Sekunden je Tag */
  tage: { ...TAGESSTAND } as Record<string, number>,
  /** zuletzt gewählte Spalte je Board */
  spalte: { ...SPALTE_GEMERKT } as Record<string, string>,
});

export function melden(text: string, rueckgaengig: (() => void) | null = null): void {
  stand.meldung = text;
  telefon.rueckgaengig = rueckgaengig;
}

export function meldungSchliessen(): void {
  stand.meldung = "";
  telefon.rueckgaengig = null;
}

// ═══ Timer: einer je Person (M-80) ═══════════════════════════════════════════════════════════════════════

export function laufende(): Karte | undefined {
  return stand.karten.find((k) => k.laeuft?.konto === ICH);
}

export function pausierte(): Karte | undefined {
  return telefon.pausiert ? karte(telefon.pausiert) : undefined;
}

/** Gesamtzeit einer Karte mit laufender Sitzung */
export function kartenzeit(k: Karte): number {
  return k.erfasstSek + (k.laeuft ? laufendSek(k.laeuft.seit) : 0);
}

function buchen(k: Karte, tag: string, sek: number): void {
  k.erfasstSek += sek;
  telefon.tage[tag] = (telefon.tage[tag] ?? 0) + sek;
}

/** Laufenden Timer beenden und die Sitzung auf heute buchen (M-81); pausieren lässt die Karte zum Fortsetzen stehen.
 *  Ergebnis: die gebuchte Sitzung, oder nichts, wenn kein Timer lief */
function beenden(pausieren: boolean): { karte: Karte; sek: number } | null {
  const k = laufende();
  if (!k) return null;
  const sek = Math.round(laufendSek(k.laeuft!.seit));
  buchen(k, HEUTE, sek);
  k.laeuft = undefined;
  telefon.pausiert = pausieren ? k.id : "";
  return { karte: k, sek };
}

export function anhalten(): void {
  const s = beenden(true);
  if (s) melden(`${s.karte.schluessel} angehalten, ${dauer(s.sek)} gebucht`);
}

export function stoppen(): void {
  const s = beenden(false);
  if (s) melden(`${s.karte.schluessel} gestoppt, ${dauer(s.sek)} gebucht`);
  else if (telefon.pausiert) {
    melden(`${karte(telefon.pausiert)?.schluessel ?? ""}: Timer beendet`);
    telefon.pausiert = "";
  }
}

/** Start auf einer Karte: ein laufender Timer hält dabei an und bucht; das Startdatum wird gesetzt, wenn es fehlt */
export function starten(id: string): void {
  const k = karte(id);
  if (!k || k.art !== "arbeit") return;
  const vorher = beenden(false);
  k.laeuft = { seit: JETZT, konto: ICH };
  k.start ??= HEUTE;
  telefon.pausiert = "";
  melden(vorher ? `Timer auf ${k.schluessel}; ${vorher.karte.schluessel} angehalten, ${dauer(vorher.sek)} gebucht`
    : `Timer auf ${k.schluessel} gestartet`);
}

// ═══ Zeit nachbuchen (M-86) und Stand ═══════════════════════════════════════════════════════════════════

export function zeitBuchen(id: string, tag: string, sek: number): void {
  const k = karte(id);
  if (!k) return;
  buchen(k, tag, sek);
  melden(`${dauer(sek)} auf ${k.schluessel} gebucht, ${datum(tag, true)}`, () => {
    buchen(k, tag, -sek);
    meldungSchliessen();
  });
}

/** Soll eines Arbeitstags aus dem eigenen Zeitkonto */
export function tagesSoll(): number {
  const z = ZEITKONTEN.find((x) => x.konto === ICH);
  return z ? (z.wochenstunden * 3600) / z.tage.length : 0;
}

export function wochenSoll(): number {
  return (ZEITKONTEN.find((x) => x.konto === ICH)?.wochenstunden ?? 0) * 3600;
}

/** Gebucht an einem Tag, heute mit der laufenden Sitzung */
export function gebucht(tag: string): number {
  const lauf = laufende();
  return (telefon.tage[tag] ?? 0) + (tag === HEUTE && lauf ? laufendSek(lauf.laeuft!.seit) : 0);
}

/** Tage dieser Woche bis heute, mit gebuchter Zeit */
export function wochentage(): { tag: string; sek: number }[] {
  const anfang = wochenanfang(HEUTE);
  return Object.keys(telefon.tage).filter((t) => t >= anfang && t <= HEUTE).sort().map((tag) => ({ tag, sek: gebucht(tag) }));
}

// ═══ Verschieben und Erledigen ══════════════════════════════════════════════════════════════════════════

/** Karte in eine andere Spalte (M-48, M-67): ans Ende, verknüpfte ziehen mit (M-76), in Erledigt hält der eigene Timer
 *  an und bucht (M-68), über der Grenze nur eine Warnung (M-15) */
export function verschieben(id: string, zielId: string, mitRueckgaengig = true): void {
  const k = karte(id);
  if (!k || k.spalte === zielId) return;
  const b = board(k.board);
  const ziel = b.spalten.find((s) => s.id === zielId);
  const alt = b.spalten.find((s) => s.id === k.spalte);
  if (!ziel || !alt) return;
  const sitzung = ziel.erledigt && k.laeuft?.konto === ICH ? beenden(false) : null;
  const mit = gruppenmitglieder(k).filter((m) => m.board === k.board && m.spalte !== zielId).length;
  ablegen(alt.id, (stand.reihen[alt.id] ?? []).filter((x) => x !== id), alt.erledigt);
  ablegen(ziel.id, [...(stand.reihen[ziel.id] ?? []).filter((x) => x !== id), id], ziel.erledigt);
  const offen = ziel.erledigt ? 0 : kartenDerSpalte(ziel.id).length;
  const teile = [ziel.erledigt ? `${k.schluessel} erledigt` : `${k.schluessel} nach ${ziel.name}`];
  if (mit) teile.push(`${mit} verknüpfte ${mit === 1 ? "zieht" : "ziehen"} mit`);
  if (sitzung) teile.push(`Timer angehalten, ${dauer(sitzung.sek)} gebucht`);
  if (ziel.grenze !== undefined && offen > ziel.grenze) teile.push(`${ziel.name} über der Grenze (${offen}/${ziel.grenze})`);
  melden(teile.join("; "), mitRueckgaengig ? () => { verschieben(id, alt.id, false); meldungSchliessen(); } : null);
}

/** Erledigen per Halten: in die Erledigt-Spalte des Boards */
export function erledigen(id: string): void {
  const k = karte(id);
  const ziel = k ? board(k.board).spalten.find((s) => s.erledigt) : undefined;
  if (k && ziel) verschieben(id, ziel.id);
}

// ═══ Anlegen, Kommentieren, Hinweise ════════════════════════════════════════════════════════════════════

function alsHtml(text: string): string {
  const sicher = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return sicher.split(/\n+/).map((z) => `<p>${z}</p>`).join("");
}

/** Spalte, in der eine neue Karte landet: die gewünschte, sonst die erste offene */
export function zielspalte(boardId: string, wunsch = ""): Spalte {
  const b = board(boardId);
  return b.spalten.find((s) => s.id === wunsch) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0];
}

/** Neue Karte ans Ende der Spalte (M-32, M-33): Schlüssel aus der Laufnummer des Boards (M-34), du bist zuständig */
export function anlegen(boardId: string, spalteId: string,
                        felder: { titel: string; art: "arbeit" | "idee"; faellig?: string; beschreibung?: string }): Karte {
  const b = board(boardId);
  const spalte = zielspalte(boardId, spalteId);
  b.laufnummer += 1;
  const id = `c-${b.kuerzel.toLowerCase()}-${b.laufnummer}`;
  stand.karten.push({
    id, board: b.id, schluessel: `${b.kuerzel}-${b.laufnummer}`, spalte: spalte.id, titel: felder.titel.trim(), art: felder.art,
    beschreibung: felder.beschreibung ? alsHtml(felder.beschreibung) : undefined, zustaendig: [ICH], prioritaet: "keine",
    faellig: felder.faellig, labels: [], checkliste: [], kommentare: [], erfasstSek: 0, bewegtAm: JETZT, erstelltAm: JETZT,
    felder: {}, anhaenge: [], transkripte: [], verlauf: [{ zeit: JETZT, von: ICH, text: "hat die Karte angelegt" }],
  });
  (stand.reihen[spalte.id] ??= []).push(id);
  return karte(id)!;
}

export function kommentieren(id: string, text: string): void {
  karte(id)?.kommentare.push({ von: ICH, zeit: JETZT, text: text.trim() });
}

export function gelesen(...ids: string[]): void {
  for (const id of ids) if (!telefon.gelesen.includes(id)) telefon.gelesen.push(id);
}
