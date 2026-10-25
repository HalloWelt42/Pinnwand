// Was sich aus dem Zustand ergibt, an einem Ort gerechnet: Zeit einer Karte, Timer einer Person, Ist und Soll, Urlaub,
// Hinweise, sichtbare Karten einer Spalte. In der App liefert das die Schnittstelle (dieselben Regeln auf dem Server);
// die Ansichten fragen nur hier, nie mit eigener Rechnung.

import { hole } from "appkern-oberflaeche";
import { ZEITFENSTER_VORGABE } from "../anzeige";
import type { Board, Karte, KellerwolkeOrdner, KellerwolkePerson, Kennung, ModulKennung, Ordner, Prioritaet, Serie, Spalte, Termin, Timer, Zeitfenster } from "../modell";
import { abwesenheitAm, artName, fassungAm, sollAm, urlaubstage, type TagSoll } from "../regeln/arbeitszeit";
import { feiertag } from "../regeln/feiertage";
import { vorkommen, type Nachtragposten, type SerienUmfeld } from "../regeln/serien";
import { hatRecht, imArchiv, imFenster, liegengeblieben, modulAn } from "../regeln/board";
import { kuerzelPruefen as regelKuerzelPruefen, kuerzelVorschlag as regelKuerzelVorschlag, type KuerzelPruefung } from "../regeln/kuerzel";
import { minutenAus, plusTage, tageVon, tageZwischen } from "../regeln/tage";
import { uhr } from "./uhr.svelte";
import { ICH } from "./ich";
import { alterTage, laufendSek } from "./format";
import { board, karte, kartenDerSpalte, konto, stand } from "./stand.svelte";

// ═══ Timer ═══════════════════════════════════════════════════════════════════════════════════════════════

/** Der eine Timer einer Person (läuft oder angehalten) */
export function timerVon(konto = ICH): Timer | undefined {
  return stand.timer.find((t) => t.konto === konto);
}

/** Laufende Timer auf einer Karte (jede Person hat höchstens einen; die anderer nur mit dem Recht "Zeiten anderer sehen") */
export function laufendAuf(karteId: string): Timer[] {
  return stand.timer.filter((t) => t.karte === karteId && t.seit);
}

/** Sekunden der laufenden Sitzung eines Timers (0, wenn angehalten) */
export function sitzungSek(t: Timer | undefined): number {
  return t?.seit ? laufendSek(t.seit) : 0;
}

/** Sekunden der laufenden Sitzung, die auf einen Tag fallen: über Mitternacht zählt jeder Tag seinen Teil, wie der
 *  Server beim Anhalten bucht */
export function sitzungAm(t: Timer | undefined, tag: string): number {
  if (!t?.seit) return 0;
  const von = Math.max(new Date(t.seit).getTime(), new Date(`${tag}T00:00:00`).getTime());
  const bis = Math.min(new Date(uhr.jetzt).getTime(), new Date(`${plusTage(tag, 1)}T00:00:00`).getTime());
  return Math.max(0, (bis - von) / 1000);
}

/** Darf auf dieser Karte ein Timer laufen? Nur Arbeit, nicht erledigt, Board mit Zeiterfassung, Recht zum Buchen */
export function timerErlaubt(k: Karte, konto = ICH): boolean {
  const b = board(k.board);
  const spalte = b.spalten.find((s) => s.id === k.spalte);
  return k.art === "arbeit" && !spalte?.erledigt && b.module.zeiterfassung && hatRecht(b, "zeit.buchen", konto, stand.moduleDa);
}

// ═══ Zeit einer Karte ════════════════════════════════════════════════════════════════════════════════════

/** Gebuchte Zeit einer Karte: Summe ihrer Einträge, mit den laufenden Sitzungen. Der Stand hat nur, was du siehst: ohne
 *  das Recht "Zeiten anderer sehen" im Board der Karte ist das deine Zeit auf ihr */
export function zeitDerKarte(karteId: string, mitLaufend = true): number {
  const gebucht = stand.zeiteintraege.filter((e) => e.karte === karteId).reduce((s, e) => s + e.sekunden, 0);
  return gebucht + (mitLaufend ? laufendAuf(karteId).reduce((s, t) => s + sitzungSek(t), 0) : 0);
}

/** Zeit einer Gruppe verknüpfter Karten: jede Sekunde zählt einmal */
export function zeitDerGruppe(k: Karte): number {
  const ids = k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe).map((x) => x.id) : [k.id];
  return ids.reduce((s, id) => s + zeitDerKarte(id), 0);
}

/** Name und Board einer Karte für Zeiteinträge, auch wenn sie im Papierkorb liegt, entfernt ist oder nicht im Stand
 *  steht (archiviert, Board verlassen: dann kommt der Name aus den Kartennamen des Stands, die Karte gibt es noch) */
export function kartenName(karteId: string): { schluessel: string; titel: string; board: string; zustand: "da" | "papierkorb" | "entfernt" } {
  const k = karte(karteId);
  if (k) return { schluessel: k.schluessel, titel: k.titel, board: k.board, zustand: "da" };
  const p = stand.papierkorb.flatMap((e) => e.karten).find((x) => x.id === karteId);
  if (p) return { schluessel: p.schluessel, titel: p.titel, board: p.board, zustand: "papierkorb" };
  const e = stand.entfernt.find((x) => x.karte === karteId);
  if (e) return { schluessel: e.schluessel, titel: e.titel, board: e.board, zustand: "entfernt" };
  const n = stand.kartennamen.find((x) => x.karte === karteId);
  if (n) return { schluessel: n.schluessel, titel: n.titel, board: n.board, zustand: "da" };
  return { schluessel: "", titel: "Entfernte Karte", board: "", zustand: "entfernt" };
}

/** Zeiteinträge einer Person von bis (einschließlich) */
export function eintraegeVon(kontoId: string, von: string, bis = von) {
  return stand.zeiteintraege.filter((e) => e.konto === kontoId && e.datum >= von && e.datum <= bis);
}

// ═══ Ist und Soll einer Person ═══════════════════════════════════════════════════════════════════════════

/** Ist eines Tags: Einträge und der Teil der laufenden Sitzung an diesem Tag */
export function istAm(konto: string, tag: string): number {
  const eintraege = stand.zeiteintraege.filter((e) => e.konto === konto && e.datum === tag).reduce((s, e) => s + e.sekunden, 0);
  return eintraege + sitzungAm(timerVon(konto), tag);
}

/** Ist eines Zeitraums: die Summe der Tage */
export function istBereich(konto: string, von: string, bis: string): number {
  return tageVon(von, bis).reduce((s, t) => s + istAm(konto, t), 0);
}

/** Soll eines Tags aus der dann gültigen Fassung des Zeitkontos; ohne Zeitkonto nichts, auch nicht vor seiner ersten
 *  Fassung (fassungAm nimmt dort die erste, damit Kalender und Vorschau ein Bundesland haben) */
export function sollTag(konto: string, tag: string): TagSoll | null {
  const k = fassungAm(stand.zeitkonten, konto, tag);
  return k && k.ab <= tag ? sollAm(k, stand.abwesenheiten, tag) : null;
}

export function sollBereich(konto: string, von: string, bis: string): number {
  return tageVon(von, bis).reduce((s, t) => s + (sollTag(konto, t)?.sollSek ?? 0), 0);
}

/** Überstunden: Ist minus Soll über das Jahr bis einschließlich des Tags */
export function saldo(konto: string, bis = uhr.heute): number {
  const von = `${bis.slice(0, 4)}-01-01`;
  return istBereich(konto, von, bis) - sollBereich(konto, von, bis);
}

/** Urlaub eines Jahres: Anspruch mit Rest aus dem Vorjahr, genommen bis heute, geplant danach, übrig */
export function urlaub(konto: string, jahr = Number(uhr.heute.slice(0, 4))): { anspruch: number; genommen: number; geplant: number; rest: number } | null {
  const k = fassungAm(stand.zeitkonten, konto, uhr.heute);
  if (!k) return null;
  const anspruch = k.urlaubsanspruch + k.resturlaubVorjahr;
  const genommen = urlaubstage(k, stand.abwesenheiten, jahr, uhr.heute);
  const geplant = urlaubstage(k, stand.abwesenheiten, jahr, uhr.heute, true);
  return { anspruch, genommen, geplant, rest: anspruch - genommen - geplant };
}

/** Tagessummen der Mitglieder eines Boards für die Ansicht Team: wen du dort siehst (mit dem Recht "Abwesenheiten
 *  sehen" alle, sonst dich) und je Person und Tag die gebuchten Sekunden aus allen Boards, ohne Einträge */
export interface TeamTage {
  personen: Kennung[];
  ist: Record<Kennung, Record<string, number>>;
}

/** Kommt vom Server, nicht aus dem Zustand: Zeiten anderer in fremden Boards stehen nie im Stand */
export function teamTage(boardId: Kennung, von: string, bis: string, signal?: AbortSignal): Promise<TeamTage> {
  return hole<TeamTage>(`/team/${encodeURIComponent(boardId)}?von=${von}&bis=${bis}`, { signal });
}

// ═══ Board ═══════════════════════════════════════════════════════════════════════════════════════════════

/** Karten, die eine Spalte zeigt: offene alle, erledigte nur im Zeitfenster (nie die archivierten) */
export function sichtbareKarten(b: Board, s: Spalte, fenster: Zeitfenster = s.zeitfenster ?? ZEITFENSTER_VORGABE): Karte[] {
  const alle = kartenDerSpalte(s.id);
  return s.erledigt ? alle.filter((k) => imFenster(k, fenster, b.einstellungen, uhr.heute)) : alle;
}

/** Erledigte Karten einer Spalte, die nicht im Archiv liegen (Zahl hinter "von" im Kopf der Spalte) */
export function erledigteOhneArchiv(b: Board, s: Spalte): Karte[] {
  return kartenDerSpalte(s.id).filter((k) => !imArchiv(k, b.einstellungen, uhr.heute));
}

export function archivVon(b: Board): Karte[] {
  return stand.karten.filter((k) => k.board === b.id && imArchiv(k, b.einstellungen, uhr.heute))
    .sort((x, y) => (y.abgeschlossen ?? "").localeCompare(x.abgeschlossen ?? ""));
}

/** Papierkorb eines Boards: gelöschte Karten und Spalten (gelöschte Boards liegen im Papierkorb der App) */
export function papierkorbVon(boardId: string) {
  return stand.papierkorb.filter((e) => e.board === boardId && e.art !== "board");
}

/** Papierkorb der App: gelöschte Boards mit allem, was daran hing */
export function boardsImPapierkorb() {
  return stand.papierkorb.filter((e) => e.art === "board");
}

/** Deine Boards nach deinen Ordnern (in deren Reihenfolge, auch leere Ordner), Boards ohne Ordner zuletzt in einer Gruppe
 *  ohne Ordner (M-01); Seitenleiste und Telefon zeigen dieselbe Ordnung */
export function boardGruppen(): { ordner: Ordner | null; boards: Board[] }[] {
  const meine = stand.boards.filter((b) => b.mitglieder.some((m) => m.konto === ICH));
  const gruppen = stand.ordner.map((o) => ({
    ordner: o as Ordner | null, boards: o.boards.map((id) => meine.find((b) => b.id === id)).filter((b): b is Board => !!b),
  }));
  const einsortiert = new Set(gruppen.flatMap((g) => g.boards.map((b) => b.id)));
  const ohne = meine.filter((b) => !einsortiert.has(b.id)).sort((a, b) => a.name.localeCompare(b.name, "de"));
  return ohne.length ? [...gruppen, { ordner: null, boards: ohne }] : gruppen;
}

/** Hat eines deiner Boards dieses Modul an? Dann zeigen Kopf, Seitenleiste und Heute seine Teile */
export function modulIrgendwo(m: ModulKennung): boolean {
  return stand.boards.some((b) => b.mitglieder.some((x) => x.konto === ICH) && modulAn(b, m, stand.moduleDa));
}

/** Rechte der angemeldeten Person in einem Board */
export function darf(b: Board, recht: string): boolean {
  return hatRecht(b, recht, ICH, stand.moduleDa);
}

/** Boards, in die eine Karte ziehen kann: im eigenen Board das Recht "Karten löschen" (sie geht dort weg), im Ziel
 *  "Karten anlegen" */
export function umzugsziele(k: Karte): Board[] {
  const von = stand.boards.find((b) => b.id === k.board);
  if (!von || !darf(von, "karten.loeschen")) return [];
  return stand.boards.filter((b) => b.id !== k.board && darf(b, "karten.anlegen"));
}

/** Pfad einer Karte im Detail: /board/prod/131 (auch aus dem Namen einer Karte außerhalb des Stands) */
export function kartenNummer(k: Pick<Karte, "schluessel">): string {
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

// ═══ Filter und Sortierung der Werkzeugleiste (Board, Liste, Kalender, Zeitachse) ═══════════════════════════

/** Suche und Filter der Werkzeugleiste eines Boards. Ein leerer Teil filtert nicht; innerhalb eines Teils reicht ein
 *  Treffer (oder), über die Teile muss alles passen (und). Mechanik M-91 bis M-93. */
export interface Kartenfilter {
  /** Volltext wie passt(): jedes Wort muss vorkommen */
  suche: string;
  /** zuständig ist eine dieser Personen */
  personen: Kennung[];
  prioritaeten: Prioritaet[];
  labels: Kennung[];
  /** eigene Felder mit Auswahl: je Feld einer dieser Werte */
  felder: Record<Kennung, string[]>;
}

export function leererFilter(): Kartenfilter {
  return { suche: "", personen: [], prioritaeten: [], labels: [], felder: {} };
}

/** Gilt eine Suche oder ein Filter? Dann ist Ziehen gesperrt und Erledigte zeigen alle außerhalb des Archivs (M-25) */
export function filterAktiv(f: Kartenfilter): boolean {
  return woerter(f.suche).length > 0 || f.personen.length > 0 || f.prioritaeten.length > 0 || f.labels.length > 0
    || Object.values(f.felder).some((w) => w.length > 0);
}

/** Die eine Abfrage für Suche und Filter in jeder Ansicht eines Boards */
export function kartePasst(k: Karte, b: Board, f: Kartenfilter): boolean {
  return (!f.personen.length || k.zustaendig.some((p) => f.personen.includes(p)))
    && (!f.prioritaeten.length || f.prioritaeten.includes(k.prioritaet))
    && (!f.labels.length || k.labels.some((l) => f.labels.includes(l)))
    && Object.entries(f.felder).every(([feld, werte]) => !werte.length || werte.includes(k.felder[feld] ?? ""))
    && passt(k, b, f.suche);
}

/** Ordnung offener Spalten (M-94): von Hand, nach Fälligkeit (früheste zuerst, ohne Datum am Ende) oder nach Priorität */
export type Sortierung = "manuell" | "faellig" | "prioritaet";

/** Offene Karten nach der Sortierung; bei Gleichstand bleibt die Reihenfolge von Hand */
export function kartenOrdnen(karten: Karte[], s: Sortierung): Karte[] {
  if (s === "manuell") return karten;
  return [...karten].sort(s === "faellig" ? (a, b) => (a.faellig ?? "9999").localeCompare(b.faellig ?? "9999")
    : (a, b) => RANG[a.prioritaet] - RANG[b.prioritaet]);
}

/** Erledigte neueste zuerst nach Abschluss, am selben Tag die zuletzt abgelegte zuerst (M-28); die Ordnung steht fest */
function neuesteZuerst(karten: Karte[]): Karte[] {
  const am = (k: Karte) => k.abgeschlossen ?? k.bewegtAm.slice(0, 10);
  return [...karten].sort((a, b) => am(b).localeCompare(am(a)) || b.bewegtAm.localeCompare(a.bewegtAm));
}

/** Was eine Spalte im Board zeigt */
export interface Spalteninhalt {
  /** alle Karten der Spalte (Erledigt: außerhalb des Archivs), nie nur die Treffer: daran hängen Zahl und Grenze (M-14) */
  alle: number;
  /** die gezeigten Karten in ihrer Ordnung: offene von Hand oder nach der Sortierung, erledigte neueste zuerst */
  karten: Karte[];
  /** Erledigt bei Suche, Filter oder Sortierung: ohne Zeitfenster, alle passenden außerhalb des Archivs (M-25) */
  ohneFenster: boolean;
}

export function spalteninhalt(b: Board, s: Spalte, f: Kartenfilter, sortierung: Sortierung, fenster: Zeitfenster): Spalteninhalt {
  if (!s.erledigt) {
    const alle = kartenDerSpalte(s.id);
    return { alle: alle.length, karten: kartenOrdnen(alle.filter((k) => kartePasst(k, b, f)), sortierung), ohneFenster: false };
  }
  const ausserhalb = erledigteOhneArchiv(b, s);
  const ohneFenster = filterAktiv(f) || sortierung !== "manuell";
  const grund = ohneFenster ? ausserhalb : sichtbareKarten(b, s, fenster);
  return { alle: ausserhalb.length, karten: neuesteZuerst(grund.filter((k) => kartePasst(k, b, f))), ohneFenster };
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
      if (e.karte.abgeschlossen === uhr.heute) tag.erledigt.push(e);
      continue;
    }
    const t = e.karte.faellig ? tageZwischen(uhr.heute, e.karte.faellig) : null;
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
    .filter((t) => { const d = tageZwischen(uhr.heute, t.datum); return d >= 0 && d <= WOCHE_TAGE; })
    .sort((a, b) => (a.datum + a.von).localeCompare(b.datum + b.von));
  tag.termine = { heute: termine.filter((t) => t.datum === uhr.heute), woche: termine.filter((t) => t.datum !== uhr.heute) };
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

/** Warum die Karte eines Serientags als angefasst gilt, in Worten; nichts: unberührt. Unberührt ist sie, solange sie in
 *  der Zielspalte liegt, nicht erledigt ist, keine Zeit hat und ihr Verlauf nur die Zeile ihres Anlegens hat (dieselbe
 *  Regel, nach der der Server Vorbuchungen anpasst oder zurücknimmt) */
export function angefasstWeil(k: Karte, s: Serie): string | undefined {
  const spalte = stand.boards.find((b) => b.id === k.board)?.spalten.find((x) => x.id === k.spalte);
  if (spalte?.erledigt || k.abgeschlossen) return "erledigt";
  if (k.spalte !== s.zielspalte) return `liegt in ${spalte?.name ?? "einer anderen Spalte"}`;
  if (stand.zeiteintraege.some((e) => e.karte === k.id)) return "mit erfasster Zeit";
  const zuletzt = k.verlauf.length > 1 ? k.verlauf[k.verlauf.length - 1] : undefined;
  return zuletzt ? `${konto(zuletzt.von).name} ${zuletzt.text}` : undefined;
}

/** Bis so viele Tage zurück fragt der Nachtrag nach (M-111); ältere Serientage gelten als bestätigt */
const NACHTRAG_TAGE = 31;

/** Was die Regeln der Serien aus dem Zustand brauchen: Abwesenheiten (ganze Tage), Feiertage im Bundesland des
 *  Zeitkontos, die Karte jedes Tags mit den Personen, die darauf Zeit gebucht haben, und ob jemand sie angefasst hat */
export function serienUmfeld(): SerienUmfeld {
  return {
    heute: uhr.heute,
    jetzt: uhr.jetzt.slice(11, 16),
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
      const s = serie(serieId);
      if (!k || !s) return undefined;
      const gebucht = [...new Set(stand.zeiteintraege.filter((e) => e.karte === k.id && e.datum === tag).map((e) => e.konto))];
      return { id: k.id, zustaendig: k.zustaendig, gebucht, angefasst: angefasstWeil(k, s) !== undefined };
    },
    bestaetigtBis: plusTage(uhr.heute, -NACHTRAG_TAGE - 1),
  };
}

/** Kann die Person in diesem Board ihre Zeit bestätigen? Nur mit Zeiterfassung und dem Recht "Eigene Zeit buchen" */
function zeitBestaetigbar(boardId: Kennung, kontoId: Kennung): boolean {
  const b = stand.boards.find((x) => x.id === boardId);
  return !!b && hatRecht(b, "zeit.buchen", kontoId, stand.moduleDa);
}

/** Deine vorgebuchten Zeiten vergangener Tage (höchstens 31 Tage zurück), die auf deine Bestätigung warten: Serientage
 *  und Termine, nur deine (in der alten App fehlte die Grenze, M-111), nur in Boards, in denen du Zeit buchst */
export function nachtrag(kontoId: Kennung = ICH): Nachtragposten[] {
  const u = serienUmfeld();
  const ab = plusTage(uhr.heute, -NACHTRAG_TAGE);
  const gestern = plusTage(uhr.heute, -1);
  const posten: Nachtragposten[] = [];
  for (const s of stand.serien.filter((x) => x.teilnehmer.includes(kontoId) && zeitBestaetigbar(x.board, kontoId))) {
    for (const v of vorkommen(s, ab, gestern, u)) {
      if (v.stand !== "wartet" || !v.offen.includes(kontoId)) continue;
      const k = karteDesTags(s.id, v.tag);
      posten.push({ art: "serie", bezug: s.id, karte: v.karte, board: s.board, titel: s.titel, tag: v.tag, von: s.uhrzeit, geplantMin: s.dauerMin,
                    bestaetigt: (k?.zustaendig ?? []).filter((x) => !v.offen.includes(x) && !v.ohne.some((o) => o.konto === x)) });
    }
  }
  for (const t of stand.termine.filter((x) => x.datum >= ab && x.datum < uhr.heute && x.teilnehmer.includes(kontoId) && !x.bestaetigt.includes(kontoId)
                                         && zeitBestaetigbar(x.board, kontoId))) {
    if (u.abwesend(kontoId, t.datum)) continue;
    posten.push({ art: "termin", bezug: t.id, board: t.board, titel: t.titel, tag: t.datum, von: t.von,
                  geplantMin: minutenAus(t.bis) - minutenAus(t.von), bestaetigt: t.bestaetigt });
  }
  return posten.sort((a, b) => (a.tag + (a.von ?? "")).localeCompare(b.tag + (b.von ?? "")));
}

// ═══ Boards anlegen und einladen ═════════════════════════════════════════════════════════════════════════

/** Wem ein Kürzel unter deinen Boards gehört; ein Kürzel eines fremden Boards meldet der Server beim Anlegen */
export function kuerzelInhaber(k: string): string | undefined {
  return stand.boards.find((x) => x.kuerzel === k)?.name;
}

export function kuerzelVorschlag(name: string): string {
  return regelKuerzelVorschlag(name, kuerzelInhaber);
}

export function kuerzelPruefen(k: string, name: string): KuerzelPruefung {
  return regelKuerzelPruefen(k, name, kuerzelInhaber);
}

/** Bekannte Personen zum Einladen (wer schon ein Konto in der Pinnwand hat); andere lädt man über ihren Kontonamen der
 *  Kellerwolke ein */
export function kellerwolkePersonen(): KellerwolkePerson[] {
  return stand.konten.map((k) => ({ kennung: k.kellerwolke, name: k.name, konto: k.id }));
}

// ═══ Verknüpfen ══════════════════════════════════════════════════════════════════════════════════════════

/** Können zwei Karten verknüpft werden? Eine andere Arbeitskarte desselben Boards, noch nicht in derselben Gruppe (M-74) */
export function verknuepfbar(a: Karte | undefined, b: Karte | undefined): boolean {
  return !!a && !!b && a.id !== b.id && a.board === b.board && a.art === "arbeit" && b.art === "arbeit" && !(a.gruppe && a.gruppe === b.gruppe);
}

/** Treffer zum Verknüpfen im Detail: offene Arbeitskarten desselben Boards nach Titel oder Schlüssel, ohne bisherige
 *  Mitglieder, höchstens acht (M-73) */
export function verknuepfTreffer(k: Karte, suche: string, hoechstens = 8): Karte[] {
  const s = suche.trim().toLowerCase();
  if (!s) return [];
  const b = board(k.board);
  const offen = new Set(b.spalten.filter((x) => !x.erledigt).map((x) => x.id));
  return stand.karten.filter((x) => offen.has(x.spalte) && verknuepfbar(k, x)
    && (x.titel.toLowerCase().includes(s) || x.schluessel.toLowerCase().includes(s))).slice(0, hoechstens);
}

/** Ein Ordner deiner Kellerwolke zum Anhängen (null: Meine Dateien): was die Kellerwolke dir dort zeigt, Ordner zuerst.
 *  Kommt vom Server, nicht aus dem Zustand: die Pinnwand sieht deine Dateien nur mit deiner Anmeldung */
export function kellerwolkeDateien(ordner: string | null, signal?: AbortSignal): Promise<KellerwolkeOrdner> {
  return hole<KellerwolkeOrdner>(`/anhaenge/kellerwolke${ordner ? `?ordner=${encodeURIComponent(ordner)}` : ""}`, { signal });
}
