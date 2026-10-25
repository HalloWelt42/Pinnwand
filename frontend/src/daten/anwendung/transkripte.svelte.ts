// Transkripte an der Karte über den Server (Modul transkripte): suchen und verknüpfen, Notiz, lösen (mit Rückgängig),
// der Ton einer Stelle und der Weg in die Transkription; dazu die Spracheingabe beim Erfassen. Der Server fragt die
// Transkription im Auftrag der Person; wer sie nicht nutzen darf, bekommt den Grund als Meldung oder als Fehler.

import { hole } from "appkern-oberflaeche";
import type { Board, Kennung, TranskriptMarke } from "../../modell";
import { modulAn } from "../../regeln/board";
import { stand } from "../stand.svelte";
import { aendern, loeschenAn, senden } from "./meldung.svelte";

export interface Fundstelle {
  zeit: number;
  ausschnitt: string;
}

export interface Treffer {
  transkript: string;
  name: string;
  dauerS: number;
  fundstellen: Fundstelle[];
}

export interface Trefferseite {
  gesamt: number;
  ab: number;
  treffer: Treffer[];
}

/** Gibt es in diesem Board Transkripte? Modul an und die Transkription eingetragen */
export function transkripteDa(b: Board): boolean {
  return !!stand.transkriptionAdresse && modulAn(b, "transkripte", stand.moduleDa);
}

/** Eine Stelle wie im Spieler: "4:12", ab einer Stunde "1:04:12" */
export function stelleText(sekunde: number): string {
  const s = Math.floor(sekunde);
  const mm = String(Math.floor((s % 3600) / 60)).padStart(s >= 3600 ? 2 : 1, "0");
  return `${s >= 3600 ? `${Math.floor(s / 3600)}:` : ""}${mm}:${String(s % 60).padStart(2, "0")}`;
}

export function suchen(karteId: Kennung, text: string, signal: AbortSignal): Promise<Trefferseite> {
  return hole<Trefferseite>(`/karten/${karteId}/transkripte/suche?text=${encodeURIComponent(text)}`, { signal });
}

/** Eine Stelle (ohne Sekunde: das ganze Transkript) an die Karte; Ergebnis: ob es wirkte */
export async function verknuepfen(karteId: Kennung, transkript: string, sekunde: number | null): Promise<boolean> {
  return !!(await aendern(() => senden(`/karten/${karteId}/transkripte`, { transkript, sekunde })));
}

export async function notizSetzen(karteId: Kennung, markeId: Kennung, notiz: string): Promise<boolean> {
  return !!(await aendern(() => senden(`/karten/${karteId}/transkripte/${markeId}/notiz`, { notiz })));
}

export async function loesen(karteId: Kennung, markeId: Kennung): Promise<boolean> {
  return !!(await aendern(() => loeschenAn(`/karten/${karteId}/transkripte/${markeId}`)));
}

/** Der Ton einer Stelle für den Spieler (über das Inhalts-Cookie der Anmeldung, mit Bereichen zum Springen) */
export function tonAdresse(karteId: Kennung, markeId: Kennung): string {
  return `/api/v1/inhalt/transkripte/${encodeURIComponent(karteId)}/${encodeURIComponent(markeId)}/ton`;
}

/** Dieselbe Stelle in der Transkription */
export function inTranskription(m: TranskriptMarke): string {
  return `${stand.transkriptionAdresse}/transkripte/${m.transkript}${m.sekunde != null ? `/${Math.floor(m.sekunde)}` : ""}`;
}

/** Spracheingabe: die Aufnahme zu Text (bis zwei Minuten). Das Umsetzen dauert, darum ohne Zeitgrenze; abbrechen
 *  kann die Person. */
export async function sprechen(boardId: Kennung, ton: Blob, signal: AbortSignal): Promise<string> {
  const typ = ton.type.split(";")[0] || "application/octet-stream";
  const antwort = await hole<{ text: string }>(`/boards/${boardId}/sprache`,
                                                { method: "POST", body: ton, headers: { "Content-Type": typ }, signal, zeitgrenzeMs: 0 });
  return antwort.text;
}
