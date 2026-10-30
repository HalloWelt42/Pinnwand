// Der eine Timer je Person (Modul Zeiterfassung) über den Server: starten, anhalten, fortsetzen, stoppen. Gebucht wird
// im Server, beim Anhalten, Stoppen oder einem Start auf einer anderen Karte (bis jetzt, an Mitternacht zerlegt, über 12
// Stunden gedeckelt); ein Start setzt dort den Starttag der Karte, wenn er fehlt. Erledigen, Idee, Papierkorb und das
// Abschalten der Zeiterfassung beenden Timer ebenfalls im Server. Die Oberfläche schickt nur, was die Person will.

import { timerErlaubt, timerVon } from "../abfragen";
import { karte, stand } from "../stand.svelte";
import { aendern, senden } from "./meldung.svelte";

/** Timer auf einer Karte starten. Läuft deiner auf einer anderen Karte, ist das ein Wechsel (HELF-42, Nutzer: "Menschen
 *  arbeiten nicht parallel"): die alte Karte pausiert (ihre Zeit ist gebucht), die Meldung nennt den Wechsel und bietet
 *  "Zurück zu ..." an, ein Klick startet den Timer dort wieder */
export async function starten(karteId: string): Promise<void> {
  const k = karte(karteId);
  if (!k || !timerErlaubt(k)) return;
  const vorher = timerVon();
  if (vorher?.karte === karteId && vorher.seit) return;
  const alt = vorher && vorher.karte !== karteId ? karte(vorher.karte) : undefined;
  const a = await aendern(() => senden("/timer/starten", { karte: karteId }));
  if (a && alt && stand.meldung && timerErlaubt(alt)) {
    stand.meldung = { ...stand.meldung, weiter: { text: `Zurück zu ${alt.schluessel}`, symbol: "fa-arrow-rotate-left", tun: () => void starten(alt.id) } };
  }
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
