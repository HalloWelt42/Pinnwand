// Anwendungsfälle der Verwaltung über den Server: ein Board anlegen (das Kürzel vorher prüfen) und einstellen (Name,
// Farbe, Kartenart, Einstellungen, Spalten, Labels, Felder, Rollen und Rechte, Mitglieder, Module), als Vorlage speichern;
// dazu, was nur der Person gehört: ihre Ordner und ihr Kürzel. Rechte und Regeln prüft der Server und sagt den Grund;
// hier bleibt nur, was ohne Weg zum Server klar ist (nichts geändert, schon Mitglied). Die Ansichten ändern den Zustand
// nie selbst; Antworten und Ereignisse übernimmt der Zustand von selbst.

import { hole } from "appkern-oberflaeche";
import type {
  Board, BoardEinstellungen, Farbe, FeldArt, KellerwolkePerson, Kennung, ModulKennung, Ordner, Spaltensortierung, Vorlage, Zeitfenster,
} from "../../modell";
import type { KuerzelPruefung } from "../../regeln/kuerzel";
import { kuerzelPruefen } from "../abfragen";
import { board, stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

function abgelehnt(text: string): false {
  stand.meldung = { text };
  return false;
}

/** Eine Änderung über ihren Weg; Ergebnis: ob sie wirkte (die Meldung sagt, was geschah oder warum nicht) */
async function schicken(pfad: string, daten: unknown = {}): Promise<boolean> {
  return (await aendern(() => senden(pfad, daten))) !== null;
}

// ═══ Board anlegen und als Vorlage speichern ════════════════════════════════════════════════════════════════

/** Ein neues Board bekommt die erste Farbe, die noch kein Board trägt (unterscheidbar in der Seitenleiste) */
const NEU_FARBEN: Farbe[] = ["tuerkis", "himmel", "honig", "violett", "rose", "sand", "stahl", "koralle", "petrol", "minze", "flieder"];
export function neueBoardFarbe(): Farbe {
  return NEU_FARBEN.find((f) => !stand.boards.some((b) => b.farbe === f)) ?? NEU_FARBEN[0];
}

/** Kontonamen der Kellerwolke, oder Konto/Zugang für einen App-Zugang (HELF-43); gleich KONTONAME in
 *  backend/app/anwendung/boards.py */
const KONTONAME = /^[\p{L}\p{N}_.@-]{1,64}(\/[\p{L}\p{N}_ .@-]{1,64})?$/u;

export function kontonameOk(name: string): boolean {
  return KONTONAME.test(name.trim());
}

/** Eine Person zum Einladen aus dem, was im Textfeld steht: eine bekannte, wenn der Kontoname passt, sonst der Name */
export function personAusText(text: string, bekannte: KellerwolkePerson[]): KellerwolkePerson {
  const name = text.trim();
  return bekannte.find((p) => p.kennung === name) ?? { kennung: name, name };
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

/** Was der Server zu einem Kürzel sagt: wie die Prüfung hier, aber über alle Boards, auch die, die du nicht siehst */
export interface KuerzelAntwort extends KuerzelPruefung {
  kuerzel: string;
}

/** Kürzel am Server prüfen (beim Tippen nach einer Pause); ohne Verbindung keine Antwort, die Prüfung hier gilt weiter */
export async function kuerzelAmServer(kuerzel: string): Promise<KuerzelAntwort | null> {
  try {
    return await hole<KuerzelAntwort>(`/kuerzel/${encodeURIComponent(kuerzel)}`);
  } catch {
    return null;
  }
}

/** Als Vorlage speichern: Spalten, Kartenart, Felder, Labels und Module des Boards; sie steht danach beim Anlegen unter
 *  den eigenen (nur für dich) */
export function alsVorlageSpeichern(boardId: Kennung, name: string): Promise<boolean> {
  return schicken(`/boards/${boardId}/vorlage`, { name });
}

// ═══ Allgemein ══════════════════════════════════════════════════════════════════════════════════════════

/** Umbenennen ändert das Kürzel nie (Kartenschlüssel und Adressen bleiben) */
export async function boardUmbenennen(boardId: Kennung, name: string): Promise<boolean> {
  if (name.trim() === board(boardId).name) return false;
  return schicken(`/boards/${boardId}/umbenennen`, { name });
}

export async function boardFarbeSetzen(boardId: Kennung, farbe: Farbe): Promise<boolean> {
  if (board(boardId).farbe === farbe) return false;
  return schicken(`/boards/${boardId}/farbe`, { farbe });
}

/** Art neuer Karten, wenn beim Anlegen keine gewählt ist; bestehende Karten bleiben, wie sie sind */
export async function kartenartSetzen(boardId: Kennung, kartenart: Board["kartenart"]): Promise<boolean> {
  if (board(boardId).kartenart === kartenart) return false;
  return schicken(`/boards/${boardId}/kartenart`, { kartenart });
}

/** Alterung, Ladeschritt und Archiv; ganze Zahlen in ihren Grenzen, 0 schaltet eine Alterungsstufe aus */
export async function einstellungenSetzen(boardId: Kennung, teil: Partial<BoardEinstellungen>): Promise<boolean> {
  const e = board(boardId).einstellungen;
  if ((Object.entries(teil) as [keyof BoardEinstellungen, number][]).every(([k, v]) => e[k] === v)) return false;
  return schicken(`/boards/${boardId}/einstellungen`, teil);
}

// ═══ Spalten ════════════════════════════════════════════════════════════════════════════════════════════

/** Neue Spalte ans Ende, ohne Grenze, offen */
export function spalteAnlegen(boardId: Kennung, name: string, farbe: Farbe): Promise<boolean> {
  return schicken(`/boards/${boardId}/spalten`, { name, farbe });
}

export interface Spaltenaenderung {
  name?: string;
  farbe?: Farbe;
  /** null: keine Grenze; sonst ganze Zahl ab 1 (nur offene Spalten) */
  grenze?: number | null;
  /** Vorgabe des Zeitfensters (nur die Erledigt-Spalte) */
  zeitfenster?: Zeitfenster;
  /** anfangs eingeklappt für alle; jede Person klappt für sich um */
  eingeklappt?: boolean;
  /** Vorgabe der Sortierung für alle; jede Person stellt für sich um */
  sortierung?: Spaltensortierung;
}

/** Name, Farbe, Grenze, Zeitfenster, Sortierung und ob die Spalte anfangs eingeklappt steht */
export function spalteAendern(boardId: Kennung, spalteId: Kennung, a: Spaltenaenderung): Promise<boolean> {
  return schicken(`/boards/${boardId}/spalten/${spalteId}/aendern`, a);
}

/** Genau eine Erledigt-Spalte je Board: die gewählte wird es, die bisherige wird offen. Karten der neuen gelten als
 *  erledigt (Abschluss heute), die der alten sind wieder offen (Alter neu). */
export async function zurErledigtSpalte(boardId: Kennung, spalteId: Kennung): Promise<boolean> {
  if (board(boardId).spalten.find((s) => s.id === spalteId)?.erledigt) return false;
  return schicken(`/boards/${boardId}/spalten/${spalteId}/erledigt`);
}

/** Reihenfolge der Spalten (wie das Ziehen der Spalten im Board); die Liste enthält genau die Spalten des Boards */
export async function spaltenOrdnen(boardId: Kennung, ids: Kennung[]): Promise<boolean> {
  if (ids.join() === board(boardId).spalten.map((s) => s.id).join()) return false;
  return schicken(`/boards/${boardId}/spalten/ordnen`, { ids });
}

// ═══ Labels ═════════════════════════════════════════════════════════════════════════════════════════════

/** Gibt es den Namen schon (ohne Beachtung von Groß und klein)? Zum Hinweis beim Tippen; der Server prüft dasselbe */
export function labelVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.labels.find((l) => l.id !== ausser && l.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

export function labelAnlegen(boardId: Kennung, name: string, farbe: Farbe): Promise<boolean> {
  return schicken(`/boards/${boardId}/labels`, { name, farbe });
}

/** Umbenennen und Umfärben gelten sofort auf allen Karten (sie tragen das Label, nicht seinen Text) */
export function labelAendern(boardId: Kennung, labelId: Kennung, a: { name?: string; farbe?: Farbe }): Promise<boolean> {
  return schicken(`/boards/${boardId}/labels/${labelId}/aendern`, a);
}

/** Label löschen: es fällt an allen Karten weg, sonst ändert sich nichts an ihnen */
export function labelLoeschen(boardId: Kennung, labelId: Kennung): Promise<boolean> {
  return schicken(`/boards/${boardId}/labels/${labelId}/loeschen`);
}

// ═══ Eigene Felder ══════════════════════════════════════════════════════════════════════════════════════

/** Karten des Boards mit einem Wert in diesem Feld */
export function kartenMitWert(boardId: Kennung, feldId: Kennung) {
  return stand.karten.filter((k) => k.board === boardId && k.felder[feldId]);
}

export function feldAnlegen(boardId: Kennung, name: string, art: FeldArt): Promise<boolean> {
  return schicken(`/boards/${boardId}/felder`, { name, art });
}

/** Name, "auf der Karte" und Art eines Feldes; die Art bleibt fest, sobald Karten einen Wert tragen */
export function feldAendern(boardId: Kennung, feldId: Kennung, a: { name?: string; art?: FeldArt; aufKarte?: boolean }): Promise<boolean> {
  return schicken(`/boards/${boardId}/felder/${feldId}/aendern`, a);
}

/** Optionen einer Auswahl: hinzufügen (ohne Dublette in anderer Schreibweise) oder entfernen (Karten mit dieser Option
 *  verlieren den Wert) */
export async function feldOption(boardId: Kennung, feldId: Kennung, option: string, dazu: boolean): Promise<boolean> {
  if (!option.trim()) return false;
  return schicken(`/boards/${boardId}/felder/${feldId}/option`, { option, dazu });
}

/** Reihenfolge der Felder (so stehen sie im Kartendetail und auf der Karte) */
export async function felderOrdnen(boardId: Kennung, ids: Kennung[]): Promise<boolean> {
  if (ids.join() === board(boardId).felder.map((f) => f.id).join()) return false;
  return schicken(`/boards/${boardId}/felder/ordnen`, { ids });
}

/** Feld löschen: die Werte an den Karten fallen mit weg */
export function feldLoeschen(boardId: Kennung, feldId: Kennung): Promise<boolean> {
  return schicken(`/boards/${boardId}/felder/${feldId}/loeschen`);
}

// ═══ Rollen und Rechte ══════════════════════════════════════════════════════════════════════════════════

/** Rechte, die Besitzer immer behalten, damit jemand das Board führen kann (gleich BESITZER_FEST im Server) */
export const BESITZER_FEST = ["board.verwalten", "mitglieder.verwalten"];

export function rolleVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.rollen.find((r) => r.id !== ausser && r.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

/** Neue Rolle mit den Rechten einer bestehenden */
export function rolleAnlegen(boardId: Kennung, name: string, kopieVon: Kennung): Promise<boolean> {
  return schicken(`/boards/${boardId}/rollen`, { name, kopieVon });
}

export async function rolleUmbenennen(boardId: Kennung, rolleId: Kennung, name: string): Promise<boolean> {
  if (board(boardId).rollen.find((r) => r.id === rolleId)?.name === name.trim()) return false;
  return schicken(`/boards/${boardId}/rollen/${rolleId}/umbenennen`, { name });
}

/** Ein Recht einer Rolle an oder aus; wirkt sofort für alle Mitglieder mit dieser Rolle */
export function rechtSetzen(boardId: Kennung, rolleId: Kennung, recht: Kennung, an: boolean): Promise<boolean> {
  return schicken(`/boards/${boardId}/rollen/${rolleId}/recht`, { recht, an });
}

/** Eigene Rolle löschen (Start-Rollen bleiben); wer sie hat, bekommt die Ersatzrolle */
export function rolleLoeschen(boardId: Kennung, rolleId: Kennung, ersatz: Kennung): Promise<boolean> {
  return schicken(`/boards/${boardId}/rollen/${rolleId}/loeschen`, { ersatz });
}

// ═══ Mitglieder (je Kontoname der Kellerwolke, auch wer noch auf die erste Anmeldung wartet) ═══════════════════

/** Einladen per Kontoname der Kellerwolke: die Person sieht das Board sofort (oder ab ihrer ersten Anmeldung) */
export async function einladen(boardId: Kennung, p: KellerwolkePerson, rolle: Kennung): Promise<boolean> {
  if (board(boardId).mitglieder.some((m) => m.kellerwolke === p.kennung)) return abgelehnt(`${p.name} ist schon im Board`);
  return schicken(`/boards/${boardId}/mitglieder`, { kellerwolke: p.kennung, rolle });
}

/** Rolle einer Person; der einzige Besitzer gibt seine Rolle erst ab, wenn er den Besitz überträgt */
export async function rolleSetzen(boardId: Kennung, kellerwolke: string, rolle: Kennung): Promise<boolean> {
  if (board(boardId).mitglieder.find((m) => m.kellerwolke === kellerwolke)?.rolle === rolle) return false;
  return schicken(`/boards/${boardId}/mitglieder/rolle`, { kellerwolke, rolle });
}

/** Person entfernen (eine wartende Einladung zurücknehmen): das Board verschwindet aus ihrer Seitenleiste, an offenen
 *  Karten fällt ihre Zuständigkeit weg */
export function mitgliedEntfernen(boardId: Kennung, kellerwolke: string): Promise<boolean> {
  return schicken(`/boards/${boardId}/mitglieder/entfernen`, { kellerwolke });
}

/** Besitz übertragen: die andere Person (schon einmal angemeldet) wird Besitzer, du bekommst die gewählte Rolle */
export function besitzUebertragen(boardId: Kennung, an: string, ichWerde: Kennung): Promise<boolean> {
  return schicken(`/boards/${boardId}/besitz`, { an, ichWerde });
}

// ═══ Module ═════════════════════════════════════════════════════════════════════════════════════════════

/** Modul an oder aus: aus blendet es in Board, Karten und Rollen aus, seine Daten bleiben (nur angebotene Module) */
export async function modulSchalten(boardId: Kennung, modul: ModulKennung, an: boolean): Promise<boolean> {
  if (board(boardId).module[modul] === an) return false;
  return schicken(`/boards/${boardId}/module/${modul}`, { an });
}

// ═══ Persönlich: Ordner und Kürzel ═══════════════════════════════════════════════════════════════════════

/** Ein Ordner, wie der Server ihn hält: mit seinem Platz in der Seitenleiste */
type OrdnerZeile = Ordner & { reihe?: number };

/** Ordner in der Reihenfolge der Seitenleiste (nach ihrem Platz, den der Server vergibt) */
function ordnerSortieren(): void {
  const platz = (o: Ordner) => (o as OrdnerZeile).reihe ?? 0;
  stand.ordner = [...stand.ordner].sort((a, b) => platz(a) - platz(b));
}

export function ordnerAnlegen(name: string): Promise<boolean> {
  return schicken("/ordner", { name });
}

export async function ordnerUmbenennen(ordnerId: Kennung, name: string): Promise<boolean> {
  if (stand.ordner.find((o) => o.id === ordnerId)?.name === name.trim()) return false;
  return schicken(`/ordner/${ordnerId}/umbenennen`, { name });
}

/** Ordner löschen: seine Boards stehen danach ohne Ordner, an ihnen ändert sich nichts */
export function ordnerLoeschen(ordnerId: Kennung): Promise<boolean> {
  return schicken(`/ordner/${ordnerId}/loeschen`);
}

/** Reihenfolge deiner Ordner in der Seitenleiste */
export async function ordnerOrdnen(ids: Kennung[]): Promise<boolean> {
  if (ids.join() === stand.ordner.map((o) => o.id).join()) return false;
  const ok = await schicken("/ordner/ordnen", { ids });
  ordnerSortieren();
  return ok;
}

/** Ordner sind persönlich: das Board hängt nur in deiner Seitenleiste um, Rechte ändern sich nicht. Leer: ohne Ordner;
 *  die Stelle im Ordner ab 0, ohne Angabe ans Ende */
export function ordnerSetzen(boardId: Kennung, ordnerId: Kennung, stelle?: number): Promise<boolean> {
  return schicken(`/boards/${boardId}/ordner`, { ordner: ordnerId || null, stelle: ordnerId ? stelle ?? null : null });
}

/** Eigenes Kürzel (nur Anzeige auf Karten; Zeiten, Kommentare und Rechte hängen am Konto) */
export function eigenesKuerzelSetzen(kuerzel: string): Promise<boolean> {
  return schicken("/ich/kuerzel", { kuerzel });
}
