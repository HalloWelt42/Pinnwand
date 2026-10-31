// Anwendungsfälle an Karten über den Server: verschieben (Ziehen, Status im Detail, Telefon, Liste: ein Weg), erledigen,
// in ein anderes Board ziehen, anlegen (auch mehrere auf einmal), duplizieren, bearbeiten, kommentieren, verknüpfen, Sammelaktionen. Die Regeln (Alter, Abschluss, Mitziehen,
// Grenze, Verlauf) rechnet der Server; die Oberfläche zeigt beim Ziehen vorab, wohin die Karte kommt.

import type { Karte, Kartenentwurf, Kennung, Prioritaet, Spalte } from "../../modell";
import { bewegteKarte, reihenFuer } from "../../regeln/reihe";
import { darf } from "../abfragen";
import { board, karte, kartenDerSpalte } from "../stand.svelte";
import { uhr } from "../uhr.svelte";
import { aendern, melden, senden, type Antwort } from "./meldung.svelte";

/** Darf die angemeldete Person Karten dieses Boards verschieben? Sonst gleich mit Grund ablehnen (die Oberfläche sperrt
 *  das Ziehen schon vorher; der Server prüft dasselbe) */
function verschiebenErlaubt(boardId: Kennung): boolean {
  if (darf(board(boardId), "karten.verschieben")) return true;
  melden("Verschieben abgelehnt: dir fehlt in diesem Board das Recht Karten verschieben");
  return false;
}

/** Vorschau eines Verschiebens: Spalte, Platz, Alter und Abschluss, bis die Antwort des Servers sie ersetzt */
function vorab(id: Kennung, ziel: Spalte, platz?: number): () => void {
  return () => {
    const k = karte(id);
    if (!k) return;
    const andere = kartenDerSpalte(ziel.id).filter((x) => x.id !== id).map((x) => x.reihe);
    if (k.spalte !== ziel.id) {
      k.spalte = ziel.id;
      k.bewegtAm = uhr.jetzt;
      k.abgeschlossen = ziel.erledigt ? (k.serie && k.faellig ? k.faellig : uhr.heute) : undefined;
    }
    k.reihe = reihenFuer(andere, platz, 1)[0];
  };
}

/** Die erste neue oder geänderte Karte aus einer Antwort (anlegen, duplizieren, umziehen) */
function neueKarte(a: Antwort | null): Karte | undefined {
  const g = a?.geaendert.find((x) => x.tabelle === "karten" && x.daten);
  return g ? karte(g.id) : undefined;
}

/** Ergebnis des Ziehens in eine Spalte: ihre neue Reihenfolge (mit den neu hineingezogenen Karten) */
export function ablegen(spalteId: Kennung, ids: Kennung[]): void {
  const k0 = karte(ids[0] ?? "");
  const ziel = k0 && board(k0.board).spalten.find((s) => s.id === spalteId);
  if (!k0 || !ziel || !verschiebenErlaubt(k0.board)) return;
  const neu = ids.filter((id) => karte(id)?.spalte !== spalteId);
  if (neu.length > 1) return sammelVerschieben(neu, spalteId);
  const vorher = kartenDerSpalte(spalteId).map((k) => k.id);
  const bewegt = neu[0] ?? bewegteKarte(vorher, ids);
  if (!bewegt) return;
  const platz = ids.indexOf(bewegt);                          // so viele übrige Karten stehen davor
  void aendern(() => senden(`/karten/${bewegt}/verschieben`, { nach: spalteId, platz: ziel.erledigt ? undefined : platz }),
               { vorab: vorab(bewegt, ziel, ziel.erledigt ? undefined : platz) });
}

/** Karte in eine andere Spalte ihres Boards, oben hinein (Status im Detail, Telefon, Liste) */
export function verschieben(id: Kennung, nach: Kennung): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.id === nach);
  if (!k || !ziel || k.spalte === nach || !verschiebenErlaubt(k.board)) return;
  void aendern(() => senden(`/karten/${id}/verschieben`, { nach }), { vorab: vorab(id, ziel) });
}

/** Mehrere Karten eines Boards in eine Spalte */
export function sammelVerschieben(ids: Kennung[], nach: Kennung): void {
  const k = karte(ids[0] ?? "");
  if (!k || !verschiebenErlaubt(k.board)) return;
  void aendern(() => senden("/karten/sammel/verschieben", { ids, nach }));
}

/** Abhaken: in die Erledigt-Spalte des Boards */
export function erledigen(id: Kennung): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.erledigt);
  if (k && ziel) verschieben(id, ziel.id);
}

/** Neue Karte ans Ende der Spalte; der Server vergibt den Schlüssel (nie wiederverwendet), du bist zuständig. Die
 *  Beschreibung ist Markdown-Text, wie getippt oder gesprochen. Ergebnis: die neue Karte */
export async function anlegen(boardId: Kennung, spalteId: Kennung,
                              felder: { titel: string; art?: "arbeit" | "idee"; faellig?: string; beschreibung?: string }): Promise<Karte | undefined> {
  if (!felder.titel.trim()) return undefined;
  return neueKarte(await aendern(() => senden(`/boards/${boardId}/karten`, { ...felder, spalte: spalteId })));
}

/** Mehrere Karten mit Inhalt in einer Änderung am Ende der Spalte (ein Rückgängig für alle); Ergebnis: ob es wirkte */
export async function mehrereAnlegen(boardId: Kennung, spalteId: Kennung, art: "arbeit" | "idee", karten: Kartenentwurf[]): Promise<boolean> {
  return !!(await aendern(() => senden(`/boards/${boardId}/karten/mehrere`, { karten, spalte: spalteId, art })));
}

/** undefined heißt im Formular "entfernen"; über die Leitung als null */
function mitNull<T extends object>(o: T): Record<string, unknown> {
  return Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v === undefined ? null : v]));
}

export type Kartenaenderung = Partial<Omit<Karte, "id" | "board" | "schluessel" | "spalte">>;

export interface Bearbeiten {
  /** inzwischen hat jemand anders eines der Felder geändert; ohne: nur die Meldung */
  beiKonflikt?: () => void;
  /** bewusst über den jetzigen Stand schreiben (nach "Meine übernehmen") */
  ueberschreiben?: boolean;
  /** wie die Oberfläche die geänderten Felder kannte, als die Bearbeitung begann (ein Formular, das erst später
   *  speichert); ohne: der jetzige Stand */
  gekannt?: Kartenaenderung;
}

/** Felder einer Karte ändern (Titel, Beschreibung, Fällig, Priorität, Checkliste und weitere Grundfelder). Mit dabei,
 *  wie die Oberfläche die Felder kannte: hat sie inzwischen jemand anders geändert, lehnt der Server ab (M-55). */
export async function bearbeiten(id: Kennung, aenderung: Kartenaenderung, text = "Gespeichert",
                                 { beiKonflikt, ueberschreiben = false, gekannt }: Bearbeiten = {}): Promise<boolean> {
  const k = karte(id);
  if (!k) return false;
  const vorher = ueberschreiben ? undefined
    : mitNull(gekannt ?? Object.fromEntries(Object.keys(aenderung).map((f) => [f, $state.snapshot(k[f as keyof Karte])])));
  return (await aendern(() => senden(`/karten/${id}/bearbeiten`, { felder: mitNull(aenderung), vorher, text }), { beiKonflikt })) !== null;
}

/** Kopie in derselben Spalte (am Ende), Mechanik M-36. Ergebnis: die Kopie */
export async function duplizieren(id: Kennung): Promise<Karte | undefined> {
  return neueKarte(await aendern(() => senden(`/karten/${id}/duplizieren`)));
}

/** Arbeit oder Idee: eine Idee hat keine Zeiterfassung */
/** Karte in ein anderes Board (ans Ende der Spalte, ohne: der ersten offenen); Ergebnis: die Karte mit ihrem neuen
 *  Schlüssel. Nummer, Kartenart, Labels und Felder gleicht der Server an. */
export async function umziehen(id: Kennung, boardId: Kennung, spalteId?: Kennung): Promise<Karte | undefined> {
  return neueKarte(await aendern(() => senden(`/karten/${id}/umziehen`, { board: boardId, spalte: spalteId })));
}

export function artSetzen(id: Kennung, art: "arbeit" | "idee"): void {
  if (karte(id)?.art !== art) void aendern(() => senden(`/karten/${id}/art`, { art }));
}

export async function kommentieren(id: Kennung, text: string): Promise<boolean> {
  if (!text.trim()) return false;
  return (await aendern(() => senden(`/karten/${id}/kommentieren`, { text }))) !== null;
}

/** eigenen Kommentar ändern (HELF-94); `nr` zählt die Kommentare der Karte ab 1 in der Reihenfolge ihres Entstehens */
export async function kommentarBearbeiten(id: Kennung, nr: number, text: string): Promise<boolean> {
  if (!text.trim()) return false;
  return (await aendern(() => senden(`/karten/${id}/kommentare/${nr}/bearbeiten`, { text }))) !== null;
}

export function sammelZuweisen(ids: Kennung[], kontoId: Kennung): void {
  void aendern(() => senden("/karten/sammel/zuweisen", { ids, konto: kontoId }));
}

export function sammelLabel(ids: Kennung[], label: Kennung): void {
  void aendern(() => senden("/karten/sammel/label", { ids, label }));
}

export function sammelPrioritaet(ids: Kennung[], p: Prioritaet): void {
  void aendern(() => senden("/karten/sammel/prioritaet", { ids, prioritaet: p }));
}

/** Gemeinsame Zeit einer Gruppe verknüpfter Karten zeigen oder nicht (gebucht wird immer je Karte) */
export function zeitTeilen(gruppeId: Kennung, an: boolean): void {
  void aendern(() => senden(`/gruppen/${gruppeId}/zeit-teilen`, { an }));
}

/** Zwei Arbeitskarten desselben Boards verknüpfen (Mechanik M-74) */
export function verknuepfen(aId: Kennung, bId: Kennung): void {
  void aendern(() => senden(`/karten/${aId}/verknuepfen`, { mit: bId }));
}

/** Karte aus ihrer Gruppe lösen; bleibt nur eine übrig, endet die Gruppe */
export function gruppeLoesen(id: Kennung): void {
  if (karte(id)?.gruppe) void aendern(() => senden(`/karten/${id}/loesen`));
}
