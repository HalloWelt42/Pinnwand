// Der eine Timer je Person (Modul Zeiterfassung) über den Server: starten, anhalten, fortsetzen, stoppen. Gebucht wird
// im Server, beim Anhalten, Stoppen oder einem Start auf einer anderen Karte (bis jetzt, an Mitternacht zerlegt, über 12
// Stunden gedeckelt); ein Start setzt dort den Starttag der Karte, wenn er fehlt. Erledigen, Idee, Papierkorb und das
// Abschalten der Zeiterfassung beenden Timer ebenfalls im Server. Die Oberfläche schickt nur, was die Person will.

import { timerErlaubt, timerVon } from "../abfragen";
import { karte } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

/** Timer auf einer Karte starten; dein laufender oder angehaltener Timer auf einer anderen Karte endet dabei (gebucht) */
export function starten(karteId: string): void {
  const k = karte(karteId);
  if (!k || !timerErlaubt(k)) return;
  const vorher = timerVon();
  if (vorher?.karte === karteId && vorher.seit) return;
  void aendern(() => senden("/timer/starten", { karte: karteId }));
}

/** Anhalten: die Sitzung wird gebucht, der Timer bleibt auf der Karte und lässt sich fortsetzen */
export function anhalten(): void {
  if (timerVon()?.seit) void aendern(() => senden("/timer/anhalten"));
}

export function fortsetzen(): void {
  const t = timerVon();
  if (t && !t.seit) void aendern(() => senden("/timer/fortsetzen"));
}

/** Stoppen: die Sitzung wird gebucht, der Timer endet */
export function stoppen(): void {
  if (timerVon()) void aendern(() => senden("/timer/stoppen"));
}
