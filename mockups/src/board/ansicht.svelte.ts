// Der Ansichtszustand eines Boards (Mechanik M-97): Suche, Filter, Sortierung, eingeklappte Spalten und das Zeitfenster
// der Erledigt-Spalten. Er gehört der Person an diesem Gerät, nicht dem Board: er bleibt beim Wechsel der Seite und liegt
// je Board im Browser, damit er nach dem Neuladen wieder da ist. Jeder Zugriff auf den Speicher ist geschützt; ohne
// Speicher gilt er bis zum Neuladen. Vorgeführte Zustände (?entwurf=) beginnen bei ihrer Vorgabe und merken nichts.

import { PRIORITAETEN, ZEITFENSTER, ZEITFENSTER_VORGABE } from "../anzeige";
import { leererFilter, type Kartenfilter, type Sortierung } from "../beispiel/abfragen";
import type { Board, Kennung, Prioritaet, Spalte, Zeitfenster } from "../modell";

export interface Ansichtszustand {
  filter: Kartenfilter;
  sortierung: Sortierung;
  /** eingeklappt (ja) oder bewusst aufgeklappt (nein); ohne Eintrag gilt die Vorgabe der Spalte */
  eingeklappt: Record<Kennung, boolean>;
  /** eigenes Zeitfenster je Erledigt-Spalte; ohne Eintrag gilt die Vorgabe der Spalte */
  zeitfenster: Record<Kennung, Zeitfenster>;
}

/** Vorgabe eines vorgeführten Zustands: nur die Teile, die er setzt */
export interface AnsichtVorgabe {
  filter?: Partial<Kartenfilter>;
  sortierung?: Sortierung;
  eingeklappt?: Record<Kennung, boolean>;
  zeitfenster?: Record<Kennung, Zeitfenster>;
}

const SORTIERUNGEN: Sortierung[] = ["manuell", "faellig", "prioritaet"];

function leer(): Ansichtszustand {
  return { filter: leererFilter(), sortierung: "manuell", eingeklappt: {}, zeitfenster: {} };
}

/** bis eine Ansicht eingerichtet ist (erster Durchlauf), gilt die Vorgabe */
const VORGABE: Ansichtszustand = leer();

const zustaende = $state<Record<string, Ansichtszustand>>({});

/** Schlüssel des Zustands: das Board, im vorgeführten Zustand dazu der Entwurf (getrennt vom gemerkten) */
export function ansichtSchluessel(boardId: Kennung, entwurf: string): string {
  return entwurf ? `${boardId}?entwurf=${entwurf}` : boardId;
}

const gemerkt = (schluessel: string) => !schluessel.includes("?");
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
  if (SORTIERUNGEN.includes(r.sortierung as Sortierung)) a.sortierung = r.sortierung as Sortierung;
  for (const [id, an] of Object.entries(objekt(r.eingeklappt))) if (b.spalten.some((s) => s.id === id) && typeof an === "boolean") a.eingeklappt[id] = an;
  for (const [id, z] of Object.entries(objekt(r.zeitfenster))) {
    if (b.spalten.some((s) => s.id === id && s.erledigt) && typeof z === "string" && z in ZEITFENSTER) a.zeitfenster[id] = z as Zeitfenster;
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

/** Richtet den Zustand eines Boards ein: gemerkt aus dieser Sitzung oder dem Browser; vorgeführt immer frisch aus der
 *  Vorgabe des Entwurfs */
export function ansichtEinrichten(b: Board, entwurf: string, vorgabe: AnsichtVorgabe = {}): void {
  const s = ansichtSchluessel(b.id, entwurf);
  if (!gemerkt(s)) {
    const a = leer();
    zustaende[s] = { ...a, ...structuredClone(vorgabe), filter: { ...a.filter, ...structuredClone(vorgabe.filter ?? {}) } };
  } else {
    zustaende[s] ??= bereinigt(lesen(b.id), b);
  }
}

export function ansichtVon(schluessel: string): Ansichtszustand {
  return zustaende[schluessel] ?? VORGABE;
}

/** Ändert den Zustand und merkt ihn im Browser (nicht im vorgeführten Zustand) */
function aendern(schluessel: string, tun: (a: Ansichtszustand) => void): void {
  const a = zustaende[schluessel];
  if (!a) return;
  tun(a);
  if (gemerkt(schluessel)) schreiben(schluessel, $state.snapshot(a));
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

export function sortierungSetzen(schluessel: string, s: Sortierung): void {
  aendern(schluessel, (a) => { a.sortierung = s; });
}

/** Suche, Filter, Personen und Sortierung zurück (M-69); eingeklappte Spalten und Zeitfenster bleiben */
export function allesZuruecksetzen(schluessel: string): void {
  aendern(schluessel, (a) => { a.filter = leererFilter(); a.sortierung = "manuell"; });
}

/** Nur die Filter der Tafel zurück (Personen, Prioritäten, Labels, Felder); Suche und Sortierung bleiben */
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
