// Anwendungsfälle der Verwaltung: ein Board anlegen und einstellen (Name, Farbe, Ordner, Einstellungen, Spalten,
// Labels, Felder, Rollen und Rechte, Mitglieder, Module), als Vorlage speichern, in den Papierkorb; dazu die eigenen
// Hinweis-Wege und das eigene Kürzel. Jede Änderung läuft über aendern() mit Rückgängig und prüft das Recht wie der
// Server; die Ansichten ändern den Zustand nie selbst.

import { FARBEN, MODULE, ZEITFENSTER_VORGABE } from "../../anzeige";
import type {
  Board, BoardEinstellungen, Farbe, Feld, FeldArt, HinweisArt, HinweisWeg, KellerwolkePerson, Kennung, ModulKennung,
  Spalte, Vorlage, Zeitfenster,
} from "../../modell";
import { personKuerzel } from "../../regeln/kuerzel";
import { darf, kuerzelPruefen } from "../abfragen";
import { EINSTELLUNGEN_VORGABE, HEUTE, ICH, JETZT, startRollen } from "../daten";
import { dauer } from "../format";
import { board, karte, kartenDerSpalte, konto, stand } from "../stand.svelte";
import { sammelVerschieben } from "./karten.svelte";
import { aendern } from "./meldung.svelte";
import { spalteInPapierkorb } from "./papierkorb.svelte";
import { timerBeenden } from "./timer.svelte";
import { neueKennung, sitzungBuchen } from "./zeiten.svelte";

const anzahl = (n: number, eins: string, viele: string) => `${n} ${n === 1 ? eins : viele}`;

/** Ändern nur mit dem Recht in diesem Board (der Server prüft dasselbe; die Oberfläche blendet nur aus) */
function mitRecht(b: Board, recht: string, tun: () => string | null): boolean {
  if (!darf(b, recht)) {
    stand.meldung = { text: `Dafür fehlt dir in ${b.name} das Recht` };
    return false;
  }
  return aendern(tun);
}

function abgelehnt(text: string): false {
  stand.meldung = { text };
  return false;
}

// ═══ Board anlegen und als Vorlage speichern ════════════════════════════════════════════════════════════════

/** Leer anfangen: drei Spalten wie in der alten App (Mechanik 3.2), die letzte ist die Erledigt-Spalte */
export const LEER_VORLAGE: Vorlage = {
  id: "leer", name: "Leer anfangen", beschreibung: "Drei Spalten, ohne Module und Felder; alles Weitere stellst du selbst ein.",
  symbol: "fa-square",
  spalten: [{ name: "Offen", farbe: "stahl", erledigt: false }, { name: "In Arbeit", farbe: "honig", erledigt: false },
    { name: "Erledigt", farbe: "minze", erledigt: true }],
  felder: [], labels: [], module: [],
};


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

/** Board aus einer Vorlage: ihre Spalten, Felder, Labels und Module, die Start-Rollen, die Vorgaben der Einstellungen;
 *  wer anlegt, ist Besitzer. Das Kürzel muss frei sein (der Server prüft über alle Boards). */
export function boardAnlegen(n: NeuesBoard): Board | undefined {
  const name = n.name.trim();
  const pruefung = kuerzelPruefen(n.kuerzel, name);
  if (!name) return void abgelehnt("Ein Board braucht einen Namen");
  if (pruefung.stand !== "frei") return void abgelehnt(pruefung.text);
  let neu: Board | undefined;
  aendern(() => {
    const id = neueKennung("b");
    const spalten: Spalte[] = n.vorlage.spalten.map((s) => ({
      id: neueKennung("s"), name: s.name, farbe: s.farbe, erledigt: s.erledigt,
      ...(s.grenze ? { grenze: s.grenze } : {}), ...(s.erledigt ? { zeitfenster: ZEITFENSTER_VORGABE } : {}),
    }));
    stand.boards.push({
      id, name, kuerzel: n.kuerzel, farbe: neueBoardFarbe(), laufnummer: 0, spalten,
      labels: n.vorlage.labels.map((l) => ({ id: neueKennung("l"), ...structuredClone(l) })),
      felder: n.vorlage.felder.map((f) => ({ id: neueKennung("f"), ...structuredClone(f) })),
      rollen: startRollen(),
      mitglieder: [{ konto: ICH, rolle: "besitzer", seit: HEUTE }],
      module: Object.fromEntries(MODULE.map((m) => [m.id, n.vorlage.module.includes(m.id)])) as Record<ModulKennung, boolean>,
      einstellungen: { ...EINSTELLUNGEN_VORGABE },
    });
    for (const s of spalten) stand.reihen[s.id] = [];
    stand.ordner.find((o) => o.id === n.ordner)?.boards.push(id);
    const b = board(id);
    for (const e of n.einladungen) mitgliedHinzu(b, e.person, e.rolle);
    neu = b;
    return `Board ${name} angelegt, Karten heißen ${n.kuerzel}-1 und so weiter`;
  });
  return neu;
}

/** Aufbau eines Boards als Vorlage: Spalten, Felder, Labels, Module; ohne Karten und Mitglieder */
export function vorlageAus(b: Board, name: string): Vorlage {
  return {
    id: neueKennung("v"), name, beschreibung: `Eigene Vorlage aus ${b.name}`, symbol: "fa-copy", eigen: true,
    spalten: b.spalten.map((s) => ({ name: s.name, farbe: s.farbe, erledigt: s.erledigt, ...(s.grenze ? { grenze: s.grenze } : {}) })),
    felder: b.felder.map(({ id: _, ...f }) => structuredClone($state.snapshot(f))),
    labels: b.labels.map((l) => ({ name: l.name, farbe: l.farbe })),
    module: MODULE.filter((m) => b.module[m.id]).map((m) => m.id),
  };
}

/** Als Vorlage speichern: Spalten, Felder, Labels und Module des Boards; sie steht danach beim Anlegen unter den eigenen */
export function alsVorlageSpeichern(boardId: Kennung, name: string): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Eine Vorlage braucht einen Namen");
  return mitRecht(b, "board.verwalten", () => {
    const v = vorlageAus(b, n);
    stand.vorlagen.push(v);
    return `Vorlage ${v.name} gespeichert: ${anzahl(v.spalten.length, "Spalte", "Spalten")}, ${anzahl(v.felder.length, "Feld", "Felder")}, `
      + `${anzahl(v.labels.length, "Label", "Labels")}; sie steht beim Anlegen unter den eigenen Vorlagen`;
  });
}

/** Board mit allem, was daran hängt, in den Papierkorb der App (Einstellungen, Papierkorb); laufende Timer buchen */
export function boardInPapierkorb(boardId: Kennung): boolean {
  const b = board(boardId);
  if (b.id !== boardId) return false;
  return mitRecht(b, "board.verwalten", () => {
    const karten = stand.karten.filter((k) => k.board === b.id);
    let gebucht = 0;
    for (const k of karten) gebucht += timerBeenden(k.id);
    const reihen = Object.fromEntries(b.spalten.map((sp) => [sp.id, stand.reihen[sp.id] ?? []]));
    const ordner = stand.ordner.find((o) => o.boards.includes(b.id))?.id;
    stand.papierkorb.unshift({
      id: neueKennung("p"), board: b.id, art: "board", karten: karten.map((k) => $state.snapshot(k)),
      stelle: { platz: stand.boards.findIndex((x) => x.id === b.id) }, von: ICH, am: JETZT,
      inhalt: { board: $state.snapshot(b), serien: $state.snapshot(stand.serien.filter((x) => x.board === b.id)),
                termine: $state.snapshot(stand.termine.filter((x) => x.board === b.id)), reihen, ordner },
    });
    for (const sp of b.spalten) delete stand.reihen[sp.id];
    stand.karten = stand.karten.filter((k) => k.board !== b.id);
    stand.serien = stand.serien.filter((x) => x.board !== b.id);
    stand.termine = stand.termine.filter((t) => t.board !== b.id);
    for (const o of stand.ordner) o.boards = o.boards.filter((x) => x !== b.id);
    stand.boards = stand.boards.filter((x) => x.id !== b.id);
    return `${b.name} mit ${anzahl(karten.length, "Karte", "Karten")} im Papierkorb; wiederherstellen unter Einstellungen, Papierkorb`
      + (gebucht ? `; Timer angehalten, ${dauer(gebucht)} gebucht` : "");
  });
}

// ═══ Allgemein ══════════════════════════════════════════════════════════════════════════════════════════

/** Umbenennen ändert das Kürzel nie (Kartenschlüssel und Adressen bleiben) */
export function boardUmbenennen(boardId: Kennung, name: string): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Ein Board braucht einen Namen");
  if (n === b.name) return false;
  return mitRecht(b, "board.verwalten", () => {
    const alt = b.name;
    b.name = n;
    return `${alt} heißt jetzt ${n}; das Kürzel ${b.kuerzel} bleibt`;
  });
}

export function boardFarbeSetzen(boardId: Kennung, farbe: Farbe): boolean {
  const b = board(boardId);
  if (b.farbe === farbe) return false;
  return mitRecht(b, "board.verwalten", () => {
    b.farbe = farbe;
    return `Farbe von ${b.name} geändert`;
  });
}

/** Ordner sind persönlich: das Board hängt nur in deiner Seitenleiste um, Rechte ändern sich nicht */
export function ordnerSetzen(boardId: Kennung, ordnerId: Kennung): boolean {
  const ziel = stand.ordner.find((o) => o.id === ordnerId);
  const b = board(boardId);
  return aendern(() => {
    for (const o of stand.ordner) o.boards = o.boards.filter((x) => x !== boardId);
    ziel?.boards.push(boardId);
    return ziel ? `${b.name} liegt jetzt im Ordner ${ziel.name}` : `${b.name} liegt jetzt ohne Ordner`;
  });
}

/** Alterung und Grenzen der Erledigt-Spalten; ganze Zahlen, 0 schaltet eine Alterungsstufe aus */
export function einstellungenSetzen(boardId: Kennung, teil: Partial<BoardEinstellungen>): boolean {
  const b = board(boardId);
  const werte = Object.entries(teil) as [keyof BoardEinstellungen, number][];
  if (werte.some(([k, v]) => !Number.isInteger(v) || v < (k === "ladeschritt" || k === "archivTage" ? 1 : 0))) {
    return abgelehnt("Nur ganze Zahlen; Ladeschritt und Archiv ab 1, Alterung ab 0");
  }
  if (werte.every(([k, v]) => b.einstellungen[k] === v)) return false;
  return mitRecht(b, "board.verwalten", () => {
    Object.assign(b.einstellungen, teil);
    return `Einstellungen von ${b.name} gespeichert`;
  });
}

// ═══ Spalten ════════════════════════════════════════════════════════════════════════════════════════════

function spalteVon(b: Board, id: Kennung): Spalte | undefined {
  return b.spalten.find((s) => s.id === id);
}

/** Neue Spalte ans Ende, ohne Grenze, nicht erledigt */
export function spalteAnlegen(boardId: Kennung, name: string, farbe: Farbe): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Eine Spalte braucht einen Namen");
  return mitRecht(b, "board.verwalten", () => {
    const id = neueKennung("s");
    b.spalten.push({ id, name: n, farbe, erledigt: false });
    stand.reihen[id] = [];
    return `Spalte ${n} angelegt, am Ende`;
  });
}

/** Name, Farbe, Grenze (null: keine; sonst ganze Zahl ab 1) und Vorgabe des Zeitfensters einer Spalte */
export function spalteAendern(boardId: Kennung, spalteId: Kennung,
                              a: { name?: string; farbe?: Farbe; grenze?: number | null; zeitfenster?: Zeitfenster }): boolean {
  const b = board(boardId);
  const s = spalteVon(b, spalteId);
  if (!s) return false;
  if (a.name !== undefined && !a.name.trim()) return abgelehnt("Eine Spalte braucht einen Namen");
  if (a.grenze != null && (!Number.isInteger(a.grenze) || a.grenze < 1)) return abgelehnt("Grenze: ganze Zahl ab 1, leer heißt keine");
  return mitRecht(b, "board.verwalten", () => {
    const teile: string[] = [];
    if (a.name !== undefined && a.name.trim() !== s.name) { teile.push(`heißt jetzt ${a.name.trim()}`); s.name = a.name.trim(); }
    if (a.farbe && a.farbe !== s.farbe) { s.farbe = a.farbe; teile.push("neue Farbe"); }
    if (a.grenze !== undefined && (a.grenze ?? undefined) !== s.grenze) {
      if (a.grenze === null) delete s.grenze;
      else s.grenze = a.grenze;
      teile.push(a.grenze === null ? "ohne Grenze" : `Grenze ${a.grenze}`);
    }
    if (a.zeitfenster && a.zeitfenster !== s.zeitfenster) { s.zeitfenster = a.zeitfenster; teile.push("neues Zeitfenster"); }
    return teile.length ? `Spalte ${s.name}: ${teile.join(", ")}` : null;
  });
}

/** Genau eine Erledigt-Spalte je Board: die gewählte wird es, die bisherige wird offen. Karten der neuen gelten als
 *  erledigt (Abschluss heute, laufende Timer halten an und buchen), die der alten sind wieder offen (Alter neu). */
export function zurErledigtSpalte(boardId: Kennung, spalteId: Kennung): boolean {
  const b = board(boardId);
  const neu = spalteVon(b, spalteId);
  if (!neu || neu.erledigt) return false;
  return mitRecht(b, "board.verwalten", () => {
    const alt = b.spalten.find((s) => s.erledigt);
    let gebucht = 0;
    if (alt) {
      alt.erledigt = false;
      for (const k of kartenDerSpalte(alt.id)) { k.abgeschlossen = undefined; k.bewegtAm = JETZT; }
    }
    neu.erledigt = true;
    neu.zeitfenster ??= ZEITFENSTER_VORGABE;
    delete neu.grenze;
    for (const k of kartenDerSpalte(neu.id)) { k.abgeschlossen ??= HEUTE; gebucht += timerBeenden(k.id); }
    return `${neu.name} ist jetzt die Erledigt-Spalte` + (alt ? `; Karten in ${alt.name} sind wieder offen` : "")
      + (gebucht ? `; Timer angehalten, ${dauer(gebucht)} gebucht` : "");
  });
}

/** Reihenfolge der Spalten (wie das Ziehen der Spalten im Board); die Liste enthält genau die Spalten des Boards */
export function spaltenOrdnen(boardId: Kennung, ids: Kennung[]): boolean {
  const b = board(boardId);
  if (ids.length !== b.spalten.length || ids.some((id) => !spalteVon(b, id))) return false;
  if (ids.every((id, i) => b.spalten[i].id === id)) return false;
  return mitRecht(b, "board.verwalten", () => {
    b.spalten = ids.map((id) => spalteVon(b, id)!);
    return `Spalten von ${b.name} neu geordnet`;
  });
}

/** Spalte löschen: die Karten vorher in eine andere Spalte (derselbe Weg wie Ziehen, die Gruppe zieht mit) oder mit
 *  der Spalte in den Papierkorb (Wiederherstellen an der alten Stelle). Die Erledigt-Spalte und die letzte bleiben. */
export function spalteLoeschen(boardId: Kennung, spalteId: Kennung, kartenNach?: Kennung): boolean {
  const b = board(boardId);
  const s = spalteVon(b, spalteId);
  if (!s) return false;
  if (s.erledigt) return abgelehnt("Die Erledigt-Spalte bleibt; mach erst eine andere Spalte zur Erledigt-Spalte");
  if (b.spalten.length < 2) return abgelehnt("Die letzte Spalte bleibt: ein Board braucht mindestens eine");
  const ziel = kartenNach ? spalteVon(b, kartenNach) : undefined;
  return mitRecht(b, "board.verwalten", () => {
    const ids = kartenDerSpalte(s.id).map((k) => k.id);
    let verschoben = "";
    if (ziel && ids.length) {
      sammelVerschieben(ids, ziel.id);
      verschoben = stand.meldung?.text ?? "";
    }
    // Serien legen künftig dorthin, wohin die Karten gehen (sonst setzt der Papierkorb die erste offene Spalte)
    if (ziel) for (const serie of stand.serien.filter((x) => x.board === b.id && x.zielspalte === s.id)) serie.zielspalte = ziel.id;
    spalteInPapierkorb(b.id, s.id);
    return `Spalte ${s.name} im Papierkorb` + (verschoben ? `; ${verschoben}` : ids.length ? ` mit ${anzahl(ids.length, "Karte", "Karten")}` : "");
  });
}

// ═══ Labels ═════════════════════════════════════════════════════════════════════════════════════════════

/** Gibt es den Namen schon (ohne Beachtung von Groß und klein)? */
export function labelVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.labels.find((l) => l.id !== ausser && l.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

export function labelAnlegen(boardId: Kennung, name: string, farbe: Farbe): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Ein Label braucht einen Namen");
  const doppelt = labelVergeben(b, n);
  if (doppelt) return abgelehnt(`Das Label ${doppelt} gibt es schon`);
  return mitRecht(b, "board.verwalten", () => {
    b.labels.push({ id: neueKennung("l"), name: n, farbe });
    return `Label ${n} angelegt`;
  });
}

/** Umbenennen und Umfärben gelten sofort auf allen Karten (sie tragen das Label, nicht seinen Text) */
export function labelAendern(boardId: Kennung, labelId: Kennung, a: { name?: string; farbe?: Farbe }): boolean {
  const b = board(boardId);
  const l = b.labels.find((x) => x.id === labelId);
  if (!l) return false;
  if (a.name !== undefined) {
    if (!a.name.trim()) return abgelehnt("Ein Label braucht einen Namen");
    const doppelt = labelVergeben(b, a.name, l.id);
    if (doppelt) return abgelehnt(`Das Label ${doppelt} gibt es schon`);
  }
  return mitRecht(b, "board.verwalten", () => {
    const alt = l.name;
    if (a.name !== undefined && a.name.trim() !== l.name) l.name = a.name.trim();
    if (a.farbe) l.farbe = a.farbe;
    return alt !== l.name ? `Label ${alt} heißt jetzt ${l.name}, auf allen Karten` : `Farbe des Labels ${l.name} geändert`;
  });
}

/** Label löschen: es fällt an allen Karten weg, sonst ändert sich nichts an ihnen */
export function labelLoeschen(boardId: Kennung, labelId: Kennung): boolean {
  const b = board(boardId);
  const l = b.labels.find((x) => x.id === labelId);
  if (!l) return false;
  return mitRecht(b, "board.verwalten", () => {
    const traeger = stand.karten.filter((k) => k.board === b.id && k.labels.includes(l.id));
    for (const k of traeger) k.labels = k.labels.filter((x) => x !== l.id);
    b.labels = b.labels.filter((x) => x.id !== l.id);
    return `Label ${l.name} gelöscht` + (traeger.length ? `, an ${anzahl(traeger.length, "Karte", "Karten")} entfernt` : "");
  });
}

// ═══ Eigene Felder ══════════════════════════════════════════════════════════════════════════════════════

/** Karten des Boards mit einem Wert in diesem Feld */
export function kartenMitWert(boardId: Kennung, feldId: Kennung) {
  return stand.karten.filter((k) => k.board === boardId && k.felder[feldId]);
}

export function feldAnlegen(boardId: Kennung, name: string, art: FeldArt): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Ein Feld braucht einen Namen");
  return mitRecht(b, "board.verwalten", () => {
    b.felder.push({ id: neueKennung("f"), name: n, art, aufKarte: false, ...(art === "auswahl" ? { optionen: [] } : {}) });
    return `Feld ${n} angelegt`;
  });
}

/** Name, "auf der Karte" und Art eines Feldes; die Art bleibt fest, sobald Karten einen Wert tragen */
export function feldAendern(boardId: Kennung, feldId: Kennung, a: { name?: string; art?: FeldArt; aufKarte?: boolean }): boolean {
  const b = board(boardId);
  const f = b.felder.find((x) => x.id === feldId);
  if (!f) return false;
  if (a.name !== undefined && !a.name.trim()) return abgelehnt("Ein Feld braucht einen Namen");
  if (a.art && a.art !== f.art && kartenMitWert(b.id, f.id).length) return abgelehnt(`Die Art von ${f.name} bleibt fest, solange Karten Werte tragen`);
  return mitRecht(b, "board.verwalten", () => {
    const teile: string[] = [];
    if (a.name !== undefined && a.name.trim() !== f.name) { f.name = a.name.trim(); teile.push(`heißt jetzt ${f.name}`); }
    if (a.art && a.art !== f.art) { f.art = a.art; if (a.art === "auswahl") f.optionen ??= []; teile.push("neue Art"); }
    if (a.aufKarte !== undefined && a.aufKarte !== f.aufKarte) { f.aufKarte = a.aufKarte; teile.push(a.aufKarte ? "auf der Karte" : "nur im Detail"); }
    return teile.length ? `Feld ${f.name}: ${teile.join(", ")}` : null;
  });
}

/** Optionen einer Auswahl: hinzufügen (ohne Dublette in anderer Schreibweise) oder entfernen */
export function feldOption(boardId: Kennung, feldId: Kennung, option: string, dazu: boolean): boolean {
  const b = board(boardId);
  const f = b.felder.find((x) => x.id === feldId);
  const o = option.trim();
  if (!f || !o) return false;
  const da = (f.optionen ?? []).some((x) => x.toLowerCase() === o.toLowerCase());
  if (dazu && da) return abgelehnt(`Die Option ${o} gibt es schon`);
  return mitRecht(b, "board.verwalten", () => {
    f.optionen = dazu ? [...(f.optionen ?? []), o] : (f.optionen ?? []).filter((x) => x !== o);
    return dazu ? `Option ${o} in ${f.name} hinzugefügt` : `Option ${o} aus ${f.name} entfernt`;
  });
}

/** Reihenfolge der Felder (so stehen sie im Kartendetail und auf der Karte) */
export function felderOrdnen(boardId: Kennung, ids: Kennung[]): boolean {
  const b = board(boardId);
  if (ids.length !== b.felder.length || ids.every((id, i) => b.felder[i].id === id)) return false;
  return mitRecht(b, "board.verwalten", () => {
    b.felder = ids.map((id) => b.felder.find((f) => f.id === id)).filter((f): f is Feld => f !== undefined);
    return "Felder neu geordnet";
  });
}

/** Feld löschen: die Werte an den Karten fallen mit weg */
export function feldLoeschen(boardId: Kennung, feldId: Kennung): boolean {
  const b = board(boardId);
  const f = b.felder.find((x) => x.id === feldId);
  if (!f) return false;
  return mitRecht(b, "board.verwalten", () => {
    const mit = kartenMitWert(b.id, f.id);
    for (const k of mit) delete k.felder[f.id];
    b.felder = b.felder.filter((x) => x.id !== f.id);
    return `Feld ${f.name} gelöscht` + (mit.length ? `, Werte an ${anzahl(mit.length, "Karte", "Karten")} entfernt` : "");
  });
}

// ═══ Rollen und Rechte ══════════════════════════════════════════════════════════════════════════════════

/** Rechte, die Besitzer immer behalten, damit jemand das Board führen kann */
export const BESITZER_FEST = ["board.verwalten", "mitglieder.verwalten"];

export function rolleVergeben(b: Board, name: string, ausser = ""): string | undefined {
  return b.rollen.find((r) => r.id !== ausser && r.name.toLowerCase() === name.trim().toLowerCase())?.name;
}

/** Neue Rolle mit den Rechten einer bestehenden */
export function rolleAnlegen(boardId: Kennung, name: string, kopieVon: Kennung): boolean {
  const b = board(boardId);
  const n = name.trim();
  if (!n) return abgelehnt("Eine Rolle braucht einen Namen");
  const doppelt = rolleVergeben(b, n);
  if (doppelt) return abgelehnt(`Die Rolle ${doppelt} gibt es schon`);
  const vorlage = b.rollen.find((r) => r.id === kopieVon);
  return mitRecht(b, "mitglieder.verwalten", () => {
    b.rollen.push({ id: neueKennung("r"), name: n, rechte: [...(vorlage?.rechte ?? [])] });
    return `Rolle ${n} angelegt` + (vorlage ? `, mit den Rechten von ${vorlage.name}` : "");
  });
}

export function rolleUmbenennen(boardId: Kennung, rolleId: Kennung, name: string): boolean {
  const b = board(boardId);
  const r = b.rollen.find((x) => x.id === rolleId);
  const n = name.trim();
  if (!r || n === r.name) return false;
  if (!n) return abgelehnt("Eine Rolle braucht einen Namen");
  const doppelt = rolleVergeben(b, n, r.id);
  if (doppelt) return abgelehnt(`Die Rolle ${doppelt} gibt es schon`);
  return mitRecht(b, "mitglieder.verwalten", () => {
    const alt = r.name;
    r.name = n;
    return `Rolle ${alt} heißt jetzt ${n}`;
  });
}

/** Ein Recht einer Rolle an oder aus; wirkt sofort für alle Mitglieder mit dieser Rolle */
export function rechtSetzen(boardId: Kennung, rolleId: Kennung, recht: Kennung, an: boolean): boolean {
  const b = board(boardId);
  const r = b.rollen.find((x) => x.id === rolleId);
  if (!r || r.rechte.includes(recht) === an) return false;
  if (r.id === "besitzer" && !an && BESITZER_FEST.includes(recht)) return abgelehnt("Besitzer behalten Board und Mitglieder verwalten");
  return mitRecht(b, "mitglieder.verwalten", () => {
    r.rechte = an ? [...r.rechte, recht] : r.rechte.filter((x) => x !== recht);
    const leute = b.mitglieder.filter((m) => m.rolle === r.id).length;
    return `${r.name}: Recht ${an ? "erteilt" : "entzogen"}, gilt sofort für ${anzahl(leute, "Person", "Personen")}`;
  });
}

/** Eigene Rolle löschen (Start-Rollen bleiben); wer sie hat, bekommt die Ersatzrolle */
export function rolleLoeschen(boardId: Kennung, rolleId: Kennung, ersatz: Kennung): boolean {
  const b = board(boardId);
  const r = b.rollen.find((x) => x.id === rolleId);
  const neu = b.rollen.find((x) => x.id === ersatz && x.id !== rolleId);
  if (!r) return false;
  if (r.vorgabe) return abgelehnt("Besitzer, Mitglied und Leser bleiben; umbenennen geht");
  const leute = b.mitglieder.filter((m) => m.rolle === r.id);
  if (leute.length && !neu) return abgelehnt("Wähle die Rolle für die Personen, die sie haben");
  return mitRecht(b, "mitglieder.verwalten", () => {
    for (const m of leute) m.rolle = neu!.id;
    b.rollen = b.rollen.filter((x) => x.id !== r.id);
    return `Rolle ${r.name} gelöscht` + (leute.length ? `; ${anzahl(leute.length, "Person hat", "Personen haben")} jetzt ${neu!.name}` : "");
  });
}

// ═══ Mitglieder ═════════════════════════════════════════════════════════════════════════════════════════

/** Person ins Board: wer noch kein Konto in der Pinnwand hat, bekommt es jetzt (Kürzel und Farbe), aus der Kellerwolke */
function mitgliedHinzu(b: Board, p: KellerwolkePerson, rolle: Kennung): string {
  let id = p.konto ?? stand.konten.find((k) => k.kellerwolke === p.kennung)?.id;
  if (!id) {
    id = neueKennung("k");
    const farbe = FARBEN.find((f) => !stand.konten.some((k) => k.farbe === f)) ?? "stahl";
    stand.konten.push({ id, name: p.name, kuerzel: personKuerzel(p.name), farbe, kellerwolke: p.kennung });
  }
  if (!b.mitglieder.some((m) => m.konto === id)) b.mitglieder.push({ konto: id, rolle, seit: HEUTE });
  return id;
}

/** Einladen per Name eines Kellerwolke-Kontos: die Person sieht das Board sofort und bekommt einen Hinweis */
export function einladen(boardId: Kennung, p: KellerwolkePerson, rolle: Kennung): boolean {
  const b = board(boardId);
  if (p.konto && b.mitglieder.some((m) => m.konto === p.konto)) return abgelehnt(`${p.name} ist schon im Board`);
  if (!b.rollen.some((r) => r.id === rolle)) return false;
  return mitRecht(b, "mitglieder.verwalten", () => {
    mitgliedHinzu(b, p, rolle);
    return `${p.name} ist eingeladen und sieht ${b.name} ab sofort in der Seitenleiste`;
  });
}

const besitzer = (b: Board) => b.mitglieder.filter((m) => m.rolle === "besitzer");

/** Rolle einer Person; der einzige Besitzer gibt seine Rolle erst ab, wenn er den Besitz überträgt */
export function rolleSetzen(boardId: Kennung, kontoId: Kennung, rolle: Kennung): boolean {
  const b = board(boardId);
  const m = b.mitglieder.find((x) => x.konto === kontoId);
  const r = b.rollen.find((x) => x.id === rolle);
  if (!m || !r || m.rolle === rolle) return false;
  if (m.rolle === "besitzer" && besitzer(b).length === 1) return abgelehnt("Ein Board hat immer einen Besitzer: erst den Besitz übertragen");
  return mitRecht(b, "mitglieder.verwalten", () => {
    m.rolle = rolle;
    return `${konto(kontoId).name} ist jetzt ${r.name}`;
  });
}

/** Person entfernen: das Board verschwindet aus ihrer Seitenleiste, an offenen Karten fällt ihre Zuständigkeit weg,
 *  ihr laufender Timer auf einer Karte dieses Boards hält an und bucht; gebuchte Zeiten bleiben */
export function mitgliedEntfernen(boardId: Kennung, kontoId: Kennung): boolean {
  const b = board(boardId);
  const m = b.mitglieder.find((x) => x.konto === kontoId);
  if (!m) return false;
  if (m.rolle === "besitzer" && besitzer(b).length === 1) return abgelehnt("Der einzige Besitzer bleibt, bis er den Besitz überträgt");
  return mitRecht(b, "mitglieder.verwalten", () => {
    const t = stand.timer.find((x) => x.konto === kontoId && karte(x.karte)?.board === b.id);
    const gebucht = t ? sitzungBuchen(t) : 0;
    if (t) stand.timer = stand.timer.filter((x) => x !== t);
    const offen = stand.karten.filter((k) => k.board === b.id && k.zustaendig.includes(kontoId) && !spalteVon(b, k.spalte)?.erledigt);
    for (const k of offen) k.zustaendig = k.zustaendig.filter((x) => x !== kontoId);
    b.mitglieder = b.mitglieder.filter((x) => x.konto !== kontoId);
    return `${konto(kontoId).name} aus ${b.name} entfernt` + (offen.length ? `; Zuständigkeit an ${anzahl(offen.length, "Karte", "Karten")} frei` : "")
      + (gebucht ? `; Timer angehalten, ${dauer(gebucht)} gebucht` : "");
  });
}

/** Besitz übertragen: die andere Person wird Besitzer, du bekommst die gewählte Rolle */
export function besitzUebertragen(boardId: Kennung, an: Kennung, ichWerde: Kennung): boolean {
  const b = board(boardId);
  const ziel = b.mitglieder.find((m) => m.konto === an && m.konto !== ICH);
  const ich = b.mitglieder.find((m) => m.konto === ICH);
  const rolle = b.rollen.find((r) => r.id === ichWerde);
  if (!ziel || !ich || !rolle) return false;
  return mitRecht(b, "mitglieder.verwalten", () => {
    ziel.rolle = "besitzer";
    ich.rolle = rolle.id;
    return `${konto(an).name} besitzt jetzt ${b.name}; du bist ${rolle.name}`;
  });
}

// ═══ Module ═════════════════════════════════════════════════════════════════════════════════════════════

/** Modul an oder aus: aus blendet es in Board, Karten und Rollen aus, seine Daten bleiben */
export function modulSchalten(boardId: Kennung, modul: ModulKennung, an: boolean): boolean {
  const b = board(boardId);
  if (b.module[modul] === an) return false;
  return mitRecht(b, "board.verwalten", () => {
    b.module[modul] = an;
    const name = MODULE.find((m) => m.id === modul)?.name ?? modul;
    return an ? `${name} in ${b.name} eingeschaltet` : `${name} in ${b.name} ausgeblendet; die Daten bleiben`;
  });
}

// ═══ Persönlich ═════════════════════════════════════════════════════════════════════════════════════════

/** Auf welchem Weg welche Hinweise kommen (gilt am Konto, auf allen Geräten) */
export function hinweisWegSetzen(art: HinweisArt, weg: HinweisWeg, an: boolean): boolean {
  if (stand.einstellungen.hinweise[art][weg] === an) return false;
  return aendern(() => {
    stand.einstellungen.hinweise[art][weg] = an;
    return "Hinweise gespeichert";
  });
}

/** Eigenes Kürzel (nur Anzeige auf Karten; Zeiten, Kommentare und Rechte hängen am Konto) */
export function eigenesKuerzelSetzen(kuerzel: string): boolean {
  const k = kuerzel.trim().toUpperCase();
  if (!/^[A-ZÄÖÜ]{1,3}$/.test(k)) return abgelehnt("Ein Kürzel hat ein bis drei Buchstaben");
  const ich = stand.konten.find((x) => x.id === ICH);
  if (!ich || ich.kuerzel === k) return false;
  return aendern(() => {
    ich.kuerzel = k;
    return `Dein Kürzel ist jetzt ${k}`;
  });
}
