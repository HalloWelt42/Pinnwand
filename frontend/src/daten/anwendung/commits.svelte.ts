// Commits an Karten über den Server (HELF-35): die Commits einer Karte, suchen, von Hand verknüpfen und lösen (mit
// Rückgängig). Eingespielt werden sie vom Commitsammler, einem eigenen kleinen Programm; die Pinnwand hängt jeden Commit
// an die Karte, deren Schlüssel in seiner Nachricht steht.

import { hole } from "appkern-oberflaeche";
import type { Board, Commit, CommitBezug, Kennung } from "../../modell";
import { stand } from "../stand.svelte";
import { aendern, loeschenAn, senden } from "./meldung.svelte";

function bezuegeDer(karteId: Kennung, vorschlag: boolean): CommitBezug[] {
  return stand.commitbezuege.filter((c) => c.karte === karteId && !c.geloest && (c.art === "vorschlag") === vorschlag)
    .sort((a, b) => b.zeit.localeCompare(a.zeit));
}

/** Die Commits einer Karte, neueste zuerst (ohne gelöste und ohne Vorschläge) */
export function commitsDer(karteId: Kennung): CommitBezug[] {
  return bezuegeDer(karteId, false);
}

/** Vorschläge für eine Karte zum Übernehmen oder Verwerfen, neueste zuerst */
export function vorschlaegeDer(karteId: Kennung): CommitBezug[] {
  return bezuegeDer(karteId, true);
}

/** Gibt es in diesem Board Commits? Dann bietet jede Karte das Verknüpfen von Hand an */
export function commitsImBoard(b: Board): boolean {
  return stand.commitbezuege.some((c) => c.board === b.id);
}

/** Die erste Zeile der Nachricht */
export function betreff(c: Commit): string {
  return c.nachricht.split("\n")[0] ?? "";
}

export function suchen(karteId: Kennung, text: string, signal: AbortSignal): Promise<Commit[]> {
  return hole<Commit[]>(`/karten/${karteId}/commits/suche?text=${encodeURIComponent(text)}`, { signal });
}

export async function verknuepfen(karteId: Kennung, commit: Kennung): Promise<boolean> {
  return !!(await aendern(() => senden(`/karten/${karteId}/commits`, { commit })));
}

/** Einen Vorschlag übernehmen (wie von Hand verknüpft) */
export async function bestaetigen(karteId: Kennung, bezugId: Kennung): Promise<boolean> {
  return !!(await aendern(() => senden(`/karten/${karteId}/commits/${bezugId}/bestaetigen`, {})));
}

/** Lösen, bei einem Vorschlag: verwerfen (kommt nicht wieder) */
export async function loesen(karteId: Kennung, bezugId: Kennung): Promise<boolean> {
  return !!(await aendern(() => loeschenAn(`/karten/${karteId}/commits/${bezugId}`)));
}
