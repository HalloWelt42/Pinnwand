// Anwendungsfälle der Verwaltung: ein Board anlegen und einstellen (Name, Farbe, Ordner, Einstellungen, Spalten,
// Labels, Felder, Rollen und Rechte, Mitglieder, Module), als Vorlage speichern, in den Papierkorb; dazu die eigenen
// Hinweis-Wege und das eigene Kürzel. Jede Änderung läuft über aendern() mit Rückgängig und prüft das Recht wie der
// Server; die Ansichten ändern den Zustand nie selbst.

import { MODULE } from "../../anzeige";
import type {
  Board, BoardEinstellungen, Farbe, FeldArt, KellerwolkePerson, Kennung, ModulKennung, Vorlage, Zeitfenster } from "../../modell";

import { darf, kuerzelPruefen } from "../abfragen";
import { board, stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";
import { baustelle } from "./baustelle";

function abgelehnt(text: string): false {
  stand.meldung = { text };
  return false;
}

// ═══ Board anlegen und als Vorlage speichern ════════════════════════════════════════════════════════════════


/** Ein neues Board bekommt die erste Farbe, die noch kein Board trägt (unterscheidbar in der Seitenleiste) */
const NEU_FARBEN: Farbe[] = ["tuerkis", "himmel", "honig", "violett", "rose", "sand", "stahl", "koralle", "petrol", "minze", "flieder"];
export function neueBoardFarbe(): Farbe {
  return NEU_FARBEN.find((f) => !stand.boards.some((b) => b.farbe === f)) ?? NEU_FARBEN[0];
}

export interface Einladung {
  person: KellerwolkePerson;
  rolle: Kennung;
}

export interface NeuesBoard {
  vorlage: Vorlage;
  name: string;
  kuerzel: string;
  /** persönlicher Ordner, leer: ohne Ordner */
  ordner: Kennung;
  einladungen: Einladung[];
}

/** Board aus einer Vorlage: ihre Spalten, Felder, Labels, die Start-Rollen, die Vorgaben der Einstellungen; wer anlegt,
 *  ist Besitzer. Das Kürzel prüft der Server über alle Boards (auch fremde). Ergebnis: das neue Board */
export async function boardAnlegen(n: NeuesBoard): Promise<Board | undefined> {
  const name = n.name.trim();
  const pruefung = kuerzelPruefen(n.kuerzel, name);
  if (!name) return void abgelehnt("Ein Board braucht einen Namen");
  if (pruefung.stand !== "frei") return void abgelehnt(pruefung.text);
  const a = await aendern(() => senden("/boards", {
    vorlage: n.vorlage.id, name, kuerzel: n.kuerzel, ordner: n.ordner || undefined,
    einladungen: n.einladungen.map((e) => ({ kellerwolke: e.person.kennung, rolle: e.rolle })),
  }));
  const g = a?.geaendert.find((x) => x.tabelle === "boards" && x.daten);
  return g ? (g.daten as unknown as Board) : undefined;
}

/** Aufbau eines Boards als Vorlage: Spalten, Felder, Labels, Module; ohne Karten und Mitglieder */
export function vorlageAus(b: Board, name: string): Vorlage {
  return {
    id: "vorschau", name, beschreibung: `Eigene Vorlage aus ${b.name}`, symbol: "fa-copy", eigen: true, kartenart: b.kartenart,
    spalten: b.spalten.map((s) => ({ name: s.name, farbe: s.farbe, erledigt: s.erledigt, ...(s.grenze ? { grenze: s.grenze } : {}) })),
    felder: b.felder.map(({ id: _, ...f }) => structuredClone($state.snapshot(f))),
    labels: b.labels.map((l) => ({ name: l.name, farbe: l.farbe })),
    module: MODULE.filter((m) => b.module[m.id]).map((m) => m.id),
  };
}

/** Als Vorlage speichern: Spalten, Felder, Labels und Module des Boards; sie steht danach beim Anlegen unter den eigenen */
export function alsVorlageSpeichern(boardId: Kennung, name: string): boolean {
  return baustelle("Verwaltung");
}

// ═══ Allgemein ══════════════════════════════════════════════════════════════════════════════════════════

/** Umbenennen ändert das Kürzel nie (Kartenschlüssel und Adressen bleiben) */
export function boardUmbenennen(boardId: Kennung, name: string): boolean {
  return baustelle("Verwaltung");
}

export function boardFarbeSetzen(boardId: Kennung, farbe: Farbe): boolean {
  return baustelle("Verwaltung");
}

/** Ordner sind persönlich: das Board hängt nur in deiner Seitenleiste um, Rechte ändern sich nicht */
export function ordnerSetzen(boardId: Kennung, ordnerId: Kennung): boolean {
  return baustelle("Verwaltung");
}

/** Alterung und Grenzen der Erledigt-Spalten; ganze Zahlen, 0 schaltet eine Alterungsstufe aus */
export function einstellungenSetzen(boardId: Kennung, teil: Partial<BoardEinstellungen>): boolean {
  return baustelle("Verwaltung");
}

// ═══ Spalten ════════════════════════════════════════════════════════════════════════════════════════════

/** Neue Spalte ans Ende, ohne Grenze, nicht erledigt */
export function spalteAnlegen(boardId: Kennung, name: string, farbe: Farbe): boolean {
  return baustelle("Verwaltung");
}

/** Name, Farbe, Grenze (null: keine; sonst ganze Zahl ab 1) und Vorgabe des Zeitfensters einer Spalte */
export function spalteAendern(boardId: Kennung, spalteId: Kennung,
                              a: { name?: string; farbe?: Farbe; grenze?: number | null; zeitfenster?: Zeitfenster }): boolean {
  return baustelle("Verwaltung");
}

/** Genau eine Erledigt-Spalte je Board: die gewählte wird es, die bisherige wird offen. Karten der neuen gelten als
 *  erledigt (Abschluss heute, laufende Timer halten an und buchen), die der alten sind wieder offen (Alter neu). */
export function zurErledigtSpalte(boardId: Kennung, spalteId: Kennung): boolean {
  return baustelle("Verwaltung");
}

/** Reihenfolge der Spalten (wie das Ziehen der Spalten im Board); die Liste enthält genau die Spalten des Boards */
export function spaltenOrdnen(boardId: Kennung, ids: Kennung[]): boolean {
  return baustelle("Verwaltung");
}

// ═══ Labels ═════════════════════════════════════════════════════════════════════════════════════════════

/** Gibt es den Namen schon (ohne Beachtung von Groß und klein)? */
export function labelVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.labels.find((l) => l.id !== ausser && l.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

export function labelAnlegen(boardId: Kennung, name: string, farbe: Farbe): boolean {
  return baustelle("Verwaltung");
}

/** Umbenennen und Umfärben gelten sofort auf allen Karten (sie tragen das Label, nicht seinen Text) */
export function labelAendern(boardId: Kennung, labelId: Kennung, a: { name?: string; farbe?: Farbe }): boolean {
  return baustelle("Verwaltung");
}

/** Label löschen: es fällt an allen Karten weg, sonst ändert sich nichts an ihnen */
export function labelLoeschen(boardId: Kennung, labelId: Kennung): boolean {
  return baustelle("Verwaltung");
}

// ═══ Eigene Felder ══════════════════════════════════════════════════════════════════════════════════════

/** Karten des Boards mit einem Wert in diesem Feld */
export function kartenMitWert(boardId: Kennung, feldId: Kennung) {
  return stand.karten.filter((k) => k.board === boardId && k.felder[feldId]);
}

export function feldAnlegen(boardId: Kennung, name: string, art: FeldArt): boolean {
  return baustelle("Verwaltung");
}

/** Name, "auf der Karte" und Art eines Feldes; die Art bleibt fest, sobald Karten einen Wert tragen */
export function feldAendern(boardId: Kennung, feldId: Kennung, a: { name?: string; art?: FeldArt; aufKarte?: boolean }): boolean {
  return baustelle("Verwaltung");
}

/** Optionen einer Auswahl: hinzufügen (ohne Dublette in anderer Schreibweise) oder entfernen */
export function feldOption(boardId: Kennung, feldId: Kennung, option: string, dazu: boolean): boolean {
  return baustelle("Verwaltung");
}

/** Reihenfolge der Felder (so stehen sie im Kartendetail und auf der Karte) */
export function felderOrdnen(boardId: Kennung, ids: Kennung[]): boolean {
  return baustelle("Verwaltung");
}

/** Feld löschen: die Werte an den Karten fallen mit weg */
export function feldLoeschen(boardId: Kennung, feldId: Kennung): boolean {
  return baustelle("Verwaltung");
}

// ═══ Rollen und Rechte ══════════════════════════════════════════════════════════════════════════════════

/** Rechte, die Besitzer immer behalten, damit jemand das Board führen kann */
export const BESITZER_FEST = ["board.verwalten", "mitglieder.verwalten"];

export function rolleVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.rollen.find((r) => r.id !== ausser && r.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

/** Neue Rolle mit den Rechten einer bestehenden */
export function rolleAnlegen(boardId: Kennung, name: string, kopieVon: Kennung): boolean {
  return baustelle("Verwaltung");
}

export function rolleUmbenennen(boardId: Kennung, rolleId: Kennung, name: string): boolean {
  return baustelle("Verwaltung");
}

/** Ein Recht einer Rolle an oder aus; wirkt sofort für alle Mitglieder mit dieser Rolle */
export function rechtSetzen(boardId: Kennung, rolleId: Kennung, recht: Kennung, an: boolean): boolean {
  return baustelle("Verwaltung");
}

/** Eigene Rolle löschen (Start-Rollen bleiben); wer sie hat, bekommt die Ersatzrolle */
export function rolleLoeschen(boardId: Kennung, rolleId: Kennung, ersatz: Kennung): boolean {
  return baustelle("Verwaltung");
}

// ═══ Mitglieder ═════════════════════════════════════════════════════════════════════════════════════════

/** Einladen per Name eines Kellerwolke-Kontos: die Person sieht das Board sofort (oder ab ihrer ersten Anmeldung) */
export async function einladen(boardId: Kennung, p: KellerwolkePerson, rolle: Kennung): Promise<boolean> {
  const b = board(boardId);
  if (b.mitglieder.some((m) => m.kellerwolke === p.kennung)) return abgelehnt(`${p.name} ist schon im Board`);
  if (!darf(b, "mitglieder.verwalten")) return abgelehnt(`Dafür fehlt dir in ${b.name} das Recht`);
  return (await aendern(() => senden(`/boards/${boardId}/mitglieder`, { kellerwolke: p.kennung, rolle }))) !== null;
}

/** Rolle einer Person; der einzige Besitzer gibt seine Rolle erst ab, wenn er den Besitz überträgt */
export function rolleSetzen(boardId: Kennung, kontoId: Kennung, rolle: Kennung): boolean {
  return baustelle("Verwaltung");
}

/** Person entfernen: das Board verschwindet aus ihrer Seitenleiste, an offenen Karten fällt ihre Zuständigkeit weg,
 *  ihr laufender Timer auf einer Karte dieses Boards hält an und bucht; gebuchte Zeiten bleiben */
export function mitgliedEntfernen(boardId: Kennung, kontoId: Kennung): boolean {
  return baustelle("Verwaltung");
}

/** Besitz übertragen: die andere Person wird Besitzer, du bekommst die gewählte Rolle */
export function besitzUebertragen(boardId: Kennung, an: Kennung, ichWerde: Kennung): boolean {
  return baustelle("Verwaltung");
}

// ═══ Module ═════════════════════════════════════════════════════════════════════════════════════════════

/** Modul an oder aus: aus blendet es in Board, Karten und Rollen aus, seine Daten bleiben */
export function modulSchalten(boardId: Kennung, modul: ModulKennung, an: boolean): boolean {
  return baustelle("Verwaltung");
}

// ═══ Persönlich ═════════════════════════════════════════════════════════════════════════════════════════

/** Eigenes Kürzel (nur Anzeige auf Karten; Zeiten, Kommentare und Rechte hängen am Konto) */
export function eigenesKuerzelSetzen(kuerzel: string): boolean {
  return baustelle("Verwaltung");
}
