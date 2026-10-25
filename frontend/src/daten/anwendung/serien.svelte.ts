// Anwendungsfälle der Serien (Modul Serien und Termine) über den Server: anlegen, ändern, pausieren, fortsetzen, löschen,
// einen Tag auslassen, und der Nachtrag am Folgetag (vorgebuchte Zeit bestätigen oder verwerfen). Die Karten der
// Serientage legt der Server an, passt unberührte an, nimmt sie zurück, legt sie in den Papierkorb oder löst sie von der
// Serie, und beim Bestätigen bucht er und legt die Karte nach Erledigt; die Oberfläche schickt nur, was die Person will.
// Jede Änderung meldet sich mit Rückgängig. Die Regeln der Tage stehen in regeln/serien.ts, die Termine in
// termine.svelte.ts.

import type { Kennung, Serie } from "../../modell";
import type { Nachtragposten } from "../../regeln/serien";
import { nachtrag, serie } from "../abfragen";
import { aendern, loeschenAn, senden, teilweiseAn } from "./meldung.svelte";
import { zeitBestaetigen, zeitVerwerfen } from "./termine.svelte";

/** Was die Person an einer Serie einstellt; Kennung, Board (steht nach dem Anlegen fest), ausgelassene und verworfene
 *  Tage und die Pause führt der Server */
export type SerienFelder = Omit<Serie, "id" | "board" | "auslass" | "verworfen" | "pausiertSeit" | "fortgesetzt">;

/** Felder so, wie der Server sie nimmt: Titel ohne Leerraum am Rand, leere Beschreibung und Uhrzeit als nichts, die
 *  Uhrzeit zweistellig ("7:30" wird "07:30") */
function bereinigt<T extends Partial<SerienFelder>>(f: T): T {
  const uhrzeit = f.uhrzeit?.trim();
  return {
    ...f,
    ...(f.titel !== undefined ? { titel: f.titel.trim() } : {}),
    ...("beschreibung" in f ? { beschreibung: f.beschreibung?.trim() || undefined } : {}),
    ...("uhrzeit" in f ? { uhrzeit: uhrzeit ? uhrzeit.padStart(5, "0") : undefined } : {}),
  };
}

// ═══ Serie anlegen, ändern, pausieren, fortsetzen, löschen ══════════════════════════════════════════════════

/** Neue Serie in einem Board; der Server bucht in derselben Änderung die Tage im Vorlauf als Karten vor. Ergebnis: Kennung */
export async function serieAnlegen(neu: SerienFelder & { board: Kennung }): Promise<Kennung | undefined> {
  if (!neu.titel.trim() || !neu.teilnehmer.length) return undefined;
  const a = await aendern(() => senden("/serien", bereinigt(neu)));
  return a?.geaendert.find((g) => g.tabelle === "serien" && g.daten)?.id;
}

/** Serie ändern: geschickt werden nur die Teile, die sich unterscheiden (null leert einen Teil wie Uhrzeit oder Ende).
 *  Der Server passt unberührte Vorbuchungen ab morgen an oder nimmt sie zurück; angefasste, vergangene und ausgelassene
 *  Tage bleiben. Ergebnis: ob gespeichert ist (auch, wenn nichts zu ändern war) */
export async function serieAendern(id: Kennung, felder: Partial<SerienFelder>): Promise<boolean> {
  const s = serie(id);
  if (!s) return false;
  const gleich = (a: unknown, b: unknown) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
  const teile = Object.fromEntries(Object.entries(bereinigt(felder))
    .filter(([feld, wert]) => !gleich(wert, s[feld as keyof Serie]))
    .map(([feld, wert]) => [feld, wert ?? null]));
  if (!Object.keys(teile).length) return true;
  return (await aendern(() => teilweiseAn(`/serien/${id}`, teile))) !== null;
}

/** Pausieren: keine neuen Vorbuchungen, unberührte Karten ab morgen nimmt der Server zurück, angefasste bleiben (M-109) */
export function pausieren(id: Kennung): void {
  const s = serie(id);
  if (!s || (s.pausiertSeit && !s.fortgesetzt)) return;
  void aendern(() => senden(`/serien/${id}/pausieren`));
}

/** Fortsetzen: ab heute wird wieder vorgebucht; die Tage der Pause bleiben ohne Karte, ausgelassene bleiben ausgelassen */
export function fortsetzen(id: Kennung): void {
  const s = serie(id);
  if (!s?.pausiertSeit || s.fortgesetzt) return;
  void aendern(() => senden(`/serien/${id}/fortsetzen`));
}

/** Serie löschen: unberührte Vorbuchungen gehen in den Papierkorb, Karten mit Zeit, angefasste und erledigte bleiben und
 *  werden von der Serie gelöst (M-110); bestätigte Zeiten zählen weiter */
export function serieLoeschen(id: Kennung): void {
  if (serie(id)) void aendern(() => loeschenAn(`/serien/${id}`));
}

/** Einen Tag bewusst auslassen: er wird gemerkt und nie wieder angelegt (M-108); eine unberührte Karte des Tags legt der
 *  Server in den Papierkorb */
export function tagAuslassen(id: Kennung, tag: string): void {
  const s = serie(id);
  if (!s || s.auslass.some((a) => a.tag === tag)) return;
  void aendern(() => senden(`/serien/${id}/auslassen`, { tag }));
}

// ═══ Nachtrag am Folgetag ══════════════════════════════════════════════════════════════════════════════════

/** Ein Posten des Nachtrags heißt nach seinem Bezug und Tag (Dauer je Posten in der Ansicht und beim Bestätigen aller) */
export function nachtragSchluessel(p: Nachtragposten): string {
  return `${p.bezug}|${p.tag}`;
}

/** Eine vorgebuchte Zeit bestätigen, bei einer Serie mit der angegebenen Dauer (Vorschlag: geplante Dauer). Der Server
 *  bucht einen Zeiteintrag auf die Karte des Tags und legt sie nach Erledigt (Abschluss bleibt der Tag, M-23); beim
 *  Termin zählt die Zeit von Beginn bis Ende */
export function nachtragBestaetigen(p: Nachtragposten, sek = p.geplantMin * 60): void {
  if (p.art === "termin") return zeitBestaetigen(p.bezug);
  if (sek > 0) void aendern(() => senden(`/serien/${p.bezug}/bestaetigen`, { tag: p.tag, sekunden: Math.round(sek) }));
}

/** Verwerfen: fand für dich nicht statt. Waren andere dabei, fällst nur du aus der Karte des Tags; warst du allein, geht
 *  die Karte in den Papierkorb und der Tag gilt als verworfen (es zählt keine Zeit) */
export function nachtragVerwerfen(p: Nachtragposten): void {
  if (p.art === "termin") return zeitVerwerfen(p.bezug);
  void aendern(() => senden(`/serien/${p.bezug}/verwerfen`, { tag: p.tag }));
}

/** Alle offenen Posten auf einmal bestätigen, in einer Änderung mit einem Rückgängig; Serien mit ihrer eingetragenen
 *  Dauer (je Schlüssel, sonst die geplante), Termine mit ihrer Zeit */
export function alleBestaetigen(dauern: Record<string, number> = {}): void {
  const posten = nachtrag().map((p) => p.art === "termin"
    ? { art: p.art, bezug: p.bezug, tag: p.tag }
    : { art: p.art, bezug: p.bezug, tag: p.tag, sekunden: Math.round(dauern[nachtragSchluessel(p)] ?? p.geplantMin * 60) });
  if (posten.length) void aendern(() => senden("/nachtrag", { posten }));
}
