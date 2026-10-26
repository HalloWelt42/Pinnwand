// Anwendungsfälle des Moduls Zeiterfassung über den Server: Zeit buchen, eine Tageszeit oder die Ticketzeit setzen,
// Einträge ändern und löschen (auch die ganze eigene Zeit auf Karten), die Rückfrage nach dem 12-Stunden-Deckel. Wie
// gebucht wird (Korrektur oder nachgetragen, welche Einträge beim Kürzen zuerst gehen, das Ende einer Sitzung), rechnet
// der Server; die Oberfläche schickt nur, was die Person will. Jede Änderung meldet sich mit Rückgängig, nur die Notiz bleibt still.

import type { Kennung } from "../../modell";
import { zeitDerKarte } from "../abfragen";
import { ICH } from "../ich";
import { stand } from "../stand.svelte";
import { aendern, loeschenAn, senden } from "./meldung.svelte";

function eintrag(id: Kennung) {
  return stand.zeiteintraege.find((x) => x.id === id);
}

/** Zeit nachtragen: ein eigener Eintrag auf diese Karte an diesem Tag. Ergebnis: ob gebucht ist */
export async function buchen(karteId: Kennung, tag: string, sek: number, notiz = ""): Promise<boolean> {
  if (sek <= 0) return false;
  const daten = { karte: karteId, datum: tag, sekunden: sek, ...(notiz.trim() ? { notiz: notiz.trim() } : {}) };
  return (await aendern(() => senden("/zeiten", daten))) !== null;
}

/** Deine Zeit auf einer Karte an einem Tag setzen (Zelle des Stundenzettels). Mehr bucht der Server als Differenz auf
 *  genau diesen Tag, weniger kürzt deine jüngsten Einträge dieses Tags; fremde bleiben. */
export function setzeTageszeit(karteId: Kennung, tag: string, sek: number): void {
  const bisher = stand.zeiteintraege.filter((e) => e.konto === ICH && e.karte === karteId && e.datum === tag).reduce((s, e) => s + e.sekunden, 0);
  if (sek !== bisher) void aendern(() => senden("/zeiten/tag", { karte: karteId, datum: tag, sekunden: sek }));
}

/** Ticketzeit an der Karte setzen: die Summe der Einträge, die du siehst; die Differenz bucht der Server heute bei dir */
export function ticketzeitSetzen(karteId: Kennung, sek: number): void {
  if (sek !== Math.round(zeitDerKarte(karteId, false))) void aendern(() => senden("/zeiten/ticketzeit", { karte: karteId, sekunden: sek }));
}

export function dauerAendern(id: Kennung, sek: number): void {
  const e = eintrag(id);
  if (e && e.sekunden !== sek) void aendern(() => senden(`/zeiten/${id}/dauer`, { sekunden: sek }));
}

/** Tag eines Eintrags ändern (Tagesliste an der Karte, Mechanik M-88): der Eintrag zieht auf den neuen Tag, Dauer,
 *  Uhrzeiten und Herkunft bleiben; war die Sitzung an Mitternacht zerlegt, verlieren beide Teile den Bezug aufeinander */
export function datumAendern(id: Kennung, tag: string): void {
  const e = eintrag(id);
  if (e && e.datum !== tag) void aendern(() => senden(`/zeiten/${id}/datum`, { datum: tag }));
}

/** Notiz eines Eintrags (steht im Stundennachweis); still, ohne Meldung und Rückgängig */
export function notizAendern(id: Kennung, notiz: string): void {
  const e = eintrag(id);
  if (e && (e.notiz ?? "") !== notiz) void aendern(() => senden(`/zeiten/${id}/notiz`, { notiz }));
}

/** Löschen mit Rückgängig: der Eintrag kommt genau so zurück (Person, Zeiten, Herkunft) */
export function loeschen(id: Kennung): void {
  if (eintrag(id)) void aendern(() => loeschenAn(`/zeiten/${id}`));
}

/** Deine ganze Zeit auf diesen Karten löschen, über alle Tage, mit Rückgängig; Einträge anderer bleiben */
export function zeitAufKartenLoeschen(karten: Kennung[]): void {
  if (karten.length) void aendern(() => senden("/zeiten/entfernen", { karten }));
}

/** Rückfrage nach dem Deckel: das echte Ende der Sitzung (JJJJ-MM-TTTHH:MM); der Server bucht die Sitzung neu von ihrem
 *  Anfang bis dahin, ohne Deckel */
export function deckelKorrigieren(ids: Kennung[], ende: string): void {
  if (ids.length) void aendern(() => senden("/zeiten/deckel", { ids, ende }));
}

/** Rückfrage nach dem Deckel: die 12 Stunden stimmen, nur der Vermerk geht */
export function deckelBestaetigen(ids: Kennung[]): void {
  if (ids.length) void aendern(() => senden("/zeiten/deckel/bestaetigen", { ids }));
}
