// Der Ansichtszustand eines Boards (Mechanik M-97): Suche, Filter, eingeklappte Spalten, das Zeitfenster der
// Erledigt-Spalten und die Sortierung je Spalte (HELF-50). Er gehört der Person an diesem Gerät, nicht dem Board: er bleibt beim Wechsel der Seite und liegt
// je Board im Browser, damit er nach dem Neuladen wieder da ist. Jeder Zugriff auf den Speicher ist geschützt; ohne
// Speicher gilt er bis zum Neuladen. Der Schlüssel des Zustands ist das Board.

import { PRIORITAETEN, SPALTENSORTIERUNGEN, ZEITFENSTER, ZEITFENSTER_VORGABE } from "../anzeige";
import { leererFilter, sortierungVorgabe, type Kartenfilter } from "../daten/abfragen";
import type { Board, Kennung, Prioritaet, Spalte, Spaltensortierung, Zeitfenster } from "../modell";

export interface Ansichtszustand {
  filter: Kartenfilter;
  /** eingeklappt (ja) oder bewusst aufgeklappt (nein); ohne Eintrag gilt die Vorgabe der Spalte */
  eingeklappt: Record<Kennung, boolean>;
  /** eigenes Zeitfenster je Erledigt-Spalte; ohne Eintrag gilt die Vorgabe der Spalte */
  zeitfenster: Record<Kennung, Zeitfenster>;
  /** eigene Sortierung je Spalte; ohne Eintrag gilt die Vorgabe der Spalte */
  sortierungen: Record<Kennung, Spaltensortierung>;
}

function leer(): Ansichtszustand {
  return { filter: leererFilter(), eingeklappt: {}, zeitfenster: {}, sortierungen: {} };
}

/** bis eine Ansicht eingerichtet ist (erster Durchlauf), gilt die Vorgabe */
const VORGABE: Ansichtszustand = leer();

const zustaende = $state<Record<string, Ansichtszustand>>({});

const SPEICHER = (boardId: Kennung) => `pinnwand_ansicht_${boardId}`;

function lesen(boardId: Kennung): unknown {
  try {
    const text = localStorage.getItem(SPEICHER(boardId));
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

function schreiben(boardId: Kennung, a: Ansichtszustand): void {
  try {
    localStorage.setItem(SPEICHER(boardId), JSON.stringify(a));
  } catch {
    // ohne Speicher (privates Fenster, gesperrt, voll): der Zustand gilt bis zum Neuladen
  }
}

const liste = (x: unknown): string[] => (Array.isArray(x) ? x.filter((w): w is string => typeof w === "string") : []);
const objekt = (x: unknown): Record<string, unknown> => (x && typeof x === "object" && !Array.isArray(x) ? x as Record<string, unknown> : {});

/** Was im Browser lag, gegen das Board geprüft: nur bekannte Werte, nur Personen, Labels, Felder und Spalten, die es
 *  im Board noch gibt (ein Filter auf ein gelöschtes Label würde sonst still alles ausblenden) */
function bereinigt(roh: unknown, b: Board): Ansichtszustand {
  const r = objekt(roh);
  const f = objekt(r.filter);
  const a = leer();
  a.filter = wirksamerFilter({
    suche: typeof f.suche === "string" ? f.suche : "",
    personen: liste(f.personen), prioritaeten: liste(f.prioritaeten) as Prioritaet[], labels: liste(f.labels),
    felder: Object.fromEntries(Object.entries(objekt(f.felder)).map(([k, w]) => [k, liste(w)])),
  }, b);
  for (const [id, an] of Object.entries(objekt(r.eingeklappt))) if (b.spalten.some((s) => s.id === id) && typeof an === "boolean") a.eingeklappt[id] = an;
  for (const [id, z] of Object.entries(objekt(r.zeitfenster))) {
    if (b.spalten.some((s) => s.id === id && s.erledigt) && typeof z === "string" && z in ZEITFENSTER) a.zeitfenster[id] = z as Zeitfenster;
  }
  for (const [id, art] of Object.entries(objekt(r.sortierungen))) {
    if (b.spalten.some((s) => s.id === id) && typeof art === "string" && art in SPALTENSORTIERUNGEN) a.sortierungen[id] = art as Spaltensortierung;
  }
  return a;
}

/** Der Filter, wie er wirkt: ohne Personen, Labels, Felder und Werte, die es im Board nicht (mehr) gibt */
export function wirksamerFilter(f: Kartenfilter, b: Board): Kartenfilter {
  const felder: Record<Kennung, string[]> = {};
  for (const [id, werte] of Object.entries(f.felder)) {
    const feld = b.felder.find((x) => x.id === id && x.art === "auswahl");
    const gueltig = werte.filter((w) => feld?.optionen?.includes(w));
    if (gueltig.length) felder[id] = gueltig;
  }
  return {
    suche: f.suche,
    personen: f.personen.filter((p) => b.mitglieder.some((m) => m.konto === p)),
    prioritaeten: f.prioritaeten.filter((p) => PRIORITAETEN.some(([w]) => w === p)),
    labels: f.labels.filter((l) => b.labels.some((x) => x.id === l)),
    felder,
  };
}

/** Richtet den Zustand eines Boards ein: gemerkt aus dieser Sitzung oder dem Browser */
export function ansichtEinrichten(b: Board): void {
  zustaende[b.id] ??= bereinigt(lesen(b.id), b);
}

export function ansichtVon(schluessel: string): Ansichtszustand {
  return zustaende[schluessel] ?? VORGABE;
}

/** Ändert den Zustand und merkt ihn im Browser */
function aendern(schluessel: string, tun: (a: Ansichtszustand) => void): void {
  const a = zustaende[schluessel];
  if (!a) return;
  tun(a);
  schreiben(schluessel, $state.snapshot(a));
}

export function sucheSetzen(schluessel: string, suche: string): void {
  aendern(schluessel, (a) => { a.filter.suche = suche; });
}

/** Einen Wert eines Filters an- oder abwählen (Personen, Prioritäten, Labels) */
export function filterUmschalten<T extends "personen" | "prioritaeten" | "labels">(schluessel: string, teil: T, wert: Kartenfilter[T][number]): void {
  aendern(schluessel, (a) => {
    const werte = a.filter[teil] as string[];
    a.filter[teil] = (werte.includes(wert) ? werte.filter((w) => w !== wert) : [...werte, wert]) as Kartenfilter[T];
  });
}

/** Einen Wert eines eigenen Auswahlfelds an- oder abwählen */
export function feldUmschalten(schluessel: string, feld: Kennung, wert: string): void {
  aendern(schluessel, (a) => {
    const werte = a.filter.felder[feld] ?? [];
    a.filter.felder[feld] = werte.includes(wert) ? werte.filter((w) => w !== wert) : [...werte, wert];
  });
}

/** Suche, Filter und Personen zurück (M-69); eingeklappte Spalten, Zeitfenster und Sortierungen bleiben */
export function allesZuruecksetzen(schluessel: string): void {
  aendern(schluessel, (a) => { a.filter = leererFilter(); });
}

/** Nur die Filter der Tafel zurück (Personen, Prioritäten, Labels, Felder); die Suche bleibt */
export function filterZuruecksetzen(schluessel: string): void {
  aendern(schluessel, (a) => { a.filter = { ...leererFilter(), suche: a.filter.suche }; });
}

export function istEingeklappt(a: Ansichtszustand, s: Spalte): boolean {
  return a.eingeklappt[s.id] ?? s.eingeklappt ?? false;
}

export function einklappen(schluessel: string, spalteId: Kennung, an: boolean): void {
  aendern(schluessel, (a) => { a.eingeklappt[spalteId] = an; });
}

export function fensterVon(a: Ansichtszustand, s: Spalte): Zeitfenster {
  return a.zeitfenster[s.id] ?? s.zeitfenster ?? ZEITFENSTER_VORGABE;
}

export function fensterSetzen(schluessel: string, spalteId: Kennung, f: Zeitfenster): void {
  aendern(schluessel, (a) => { a.zeitfenster[spalteId] = f; });
}

/** Die Sortierung, nach der diese Person die Spalte an diesem Gerät sieht: die eigene, sonst die Vorgabe der Spalte */
export function sortierungVon(a: Ansichtszustand, s: Spalte): Spaltensortierung {
  return a.sortierungen[s.id] ?? sortierungVorgabe(s);
}

/** Eigene Sortierung einer Spalte an diesem Gerät; gleich der Vorgabe der Spalte: kein eigener Eintrag mehr */
export function sortierungSetzen(schluessel: string, s: Spalte, art: Spaltensortierung): void {
  aendern(schluessel, (a) => {
    if (art === sortierungVorgabe(s)) delete a.sortierungen[s.id];
    else a.sortierungen[s.id] = art;
  });
}
