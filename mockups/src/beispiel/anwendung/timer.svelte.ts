// Der eine Timer je Person (Modul Zeiterfassung): starten, anhalten, fortsetzen, stoppen. Jede laufende Sitzung wird beim
// Anhalten, Stoppen oder einem Start auf einer anderen Karte als Zeiteintrag gebucht. Ein Start setzt den Starttag der
// Karte, wenn er fehlt. Erledigen und das Umschalten auf Idee halten Timer über timerBeenden an (karten.svelte.ts).

import { kartenName, timerErlaubt, timerVon } from "../abfragen";
import { HEUTE, ICH, JETZT } from "../daten";
import { dauer } from "../format";
import { karte, stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { vermerken } from "./verlauf";
import { sitzungBuchen } from "./zeiten.svelte";

function schluessel(karteId: string): string {
  return kartenName(karteId).schluessel;
}

/** Timer auf einer Karte starten; dein laufender oder angehaltener Timer auf einer anderen Karte endet dabei (gebucht) */
export function starten(karteId: string): void {
  const k = karte(karteId);
  if (!k || !timerErlaubt(k)) return;
  const vorher = timerVon(ICH);
  if (vorher?.karte === karteId && vorher.seit) return;
  aendern(() => {
    let text: string;
    if (vorher && vorher.karte !== karteId) {
      const sek = sitzungBuchen(vorher);
      stand.timer = stand.timer.filter((t) => t.konto !== ICH);
      text = `Timer läuft auf ${k.schluessel}; ${schluessel(vorher.karte)} beendet` + (sek ? `, ${dauer(sek)} gebucht` : "");
    } else {
      text = vorher ? `Timer auf ${k.schluessel} fortgesetzt` : `Timer läuft auf ${k.schluessel}`;
      stand.timer = stand.timer.filter((t) => t.konto !== ICH);
    }
    stand.timer.push({ konto: ICH, karte: karteId, seit: JETZT });
    k.start ??= HEUTE;
    vermerken(k, "hat den Timer gestartet");
    return text;
  });
}

/** Anhalten: die Sitzung wird gebucht, der Timer bleibt auf der Karte und lässt sich fortsetzen */
export function anhalten(): void {
  const t = timerVon(ICH);
  if (!t?.seit) return;
  aendern(() => `${schluessel(t.karte)} angehalten, ${dauer(sitzungBuchen(t))} gebucht`);
}

export function fortsetzen(): void {
  const t = timerVon(ICH);
  if (!t || t.seit) return;
  aendern(() => {
    t.seit = JETZT;
    return `Timer auf ${schluessel(t.karte)} fortgesetzt`;
  });
}

/** Stoppen: die Sitzung wird gebucht, der Timer endet */
export function stoppen(): void {
  const t = timerVon(ICH);
  if (!t) return;
  aendern(() => {
    const sek = sitzungBuchen(t);
    stand.timer = stand.timer.filter((x) => x.konto !== ICH);
    return `${schluessel(t.karte)} gestoppt` + (sek ? `, ${dauer(sek)} gebucht` : "");
  });
}

/** Alle Timer auf einer Karte beenden und ihre Sitzungen buchen (Erledigen, Idee, Papierkorb); ohne eigene Meldung,
 *  Ergebnis: die eigene gebuchte Zeit für die Meldung des Aufrufers */
export function timerBeenden(karteId: string): number {
  let eigene = 0;
  for (const t of stand.timer.filter((x) => x.karte === karteId)) {
    const sek = sitzungBuchen(t);
    if (t.konto === ICH) eigene = sek;
  }
  stand.timer = stand.timer.filter((t) => t.karte !== karteId);
  return eigene;
}
