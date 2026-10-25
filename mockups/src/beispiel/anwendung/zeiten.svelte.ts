// Anwendungsfälle des Moduls Zeiterfassung: Zeit buchen, eine Tageszeit setzen, Einträge ändern und löschen, die
// Rückfrage nach dem 12-Stunden-Deckel. Jede Änderung meldet sich mit Rückgängig. Gebucht wird immer als Zeiteintrag;
// die Zeit einer Karte ist deren Summe (abfragen.ts), es gibt keinen zweiten Zähler.

import type { Timer, Zeiteintrag } from "../../modell";
import { minutenAus, uhrzeitAus } from "../../regeln/tage";
import { kartenName, zeitDerKarte } from "../abfragen";
import { HEUTE, ICH, JETZT } from "../daten";
import { datum, dauer, laufendSek } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";

/** Kennung ohne Zähler und ohne randomUUID (das fehlt außerhalb sicherer Kontexte) */
export function neueKennung(vorsatz: string): string {
  const b = crypto.getRandomValues(new Uint8Array(8));
  return `${vorsatz}-${Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("")}`;
}

function schluessel(karteId: string): string {
  return kartenName(karteId).schluessel;
}

/** Die laufende Sitzung eines Timers buchen: in den Timer-Eintrag der Karte an diesem Tag (je Karte, Person und Tag
 *  einer, die Sitzungen darin sichtbar). Ergebnis: gebuchte Sekunden. Der Timer selbst bleibt, wie er ist. */
export function sitzungBuchen(t: Timer): number {
  if (!t.seit) return 0;
  const sek = Math.round(laufendSek(t.seit));
  const tag = t.seit.slice(0, 10), von = t.seit.slice(11, 16), bis = JETZT.slice(11, 16);
  const da = stand.zeiteintraege.find((e) => e.konto === t.konto && e.karte === t.karte && e.datum === tag && e.herkunft === "timer");
  if (da) {
    da.sitzungen = [...(da.sitzungen ?? (da.von && da.bis ? [{ von: da.von, bis: da.bis }] : [])), { von, bis }];
    da.sekunden += sek;
    da.bis = bis;
  } else {
    stand.zeiteintraege.push({ id: neueKennung("z"), karte: t.karte, konto: t.konto, datum: tag, von, bis, sekunden: sek, herkunft: "timer" });
  }
  t.seit = undefined;
  return sek;
}

/** Eintrag kürzen; bei einem Timer-Eintrag rückt das Ende mit, damit von, bis und Dauer zusammenpassen */
function kuerzen(e: Zeiteintrag, sek: number): void {
  e.sekunden -= sek;
  if (e.bis && e.von && e.herkunft === "timer") {
    e.bis = uhrzeitAus(Math.max(minutenAus(e.von), minutenAus(e.bis) - Math.round(sek / 60)));
    if (e.sitzungen?.length) e.sitzungen[e.sitzungen.length - 1].bis = e.bis;
  }
}

/** jüngster zuerst: Korrektur, dann nachgetragen, dann Serie, dann Timer nach Ende */
function rang(e: Zeiteintrag): number {
  const art = { korrektur: 3, hand: 2, serie: 1, timer: 0 }[e.herkunft];
  return art * 10000 + (e.bis ? minutenAus(e.bis) : 0);
}

/** Zeit nachtragen: ein eigener Eintrag auf diese Karte an diesem Tag */
export function buchen(karteId: string, tag: string, sek: number, notiz = ""): void {
  if (sek <= 0) return;
  aendern(() => {
    stand.zeiteintraege.push({ id: neueKennung("z"), karte: karteId, konto: ICH, datum: tag, sekunden: sek, herkunft: "hand", notiz: notiz || undefined });
    return `${dauer(sek)} auf ${schluessel(karteId)} gebucht (${datum(tag, true)})`;
  });
}

/** Deine Zeit auf einer Karte an einem Tag setzen (Zelle des Stundenzettels). Mehr bucht die Differenz auf genau diesen
 *  Tag (als Korrektur, wenn schon Zeit da war), weniger kürzt deine jüngsten Einträge dieses Tags; fremde bleiben. */
export function setzeTageszeit(karteId: string, tag: string, sek: number): void {
  const eigene = stand.zeiteintraege.filter((e) => e.konto === ICH && e.karte === karteId && e.datum === tag);
  const bisher = eigene.reduce((s, e) => s + e.sekunden, 0);
  if (sek === bisher) return;
  aendern(() => {
    if (sek > bisher) {
      stand.zeiteintraege.push({ id: neueKennung("z"), karte: karteId, konto: ICH, datum: tag, sekunden: sek - bisher,
                                 herkunft: bisher ? "korrektur" : "hand" });
    } else {
      let rest = bisher - sek;
      for (const e of [...eigene].sort((a, b) => rang(b) - rang(a))) {
        if (rest <= 0) break;
        if (e.sekunden <= rest) {
          rest -= e.sekunden;
          stand.zeiteintraege = stand.zeiteintraege.filter((x) => x.id !== e.id);
        } else {
          kuerzen(stand.zeiteintraege.find((x) => x.id === e.id)!, rest);
          rest = 0;
        }
      }
    }
    return `${schluessel(karteId)} ${datum(tag, true)}: ${dauer(bisher)} auf ${dauer(sek)} gesetzt`;
  });
}

/** Ticketzeit an der Karte direkt setzen: die Differenz zur Summe aller Einträge wird heute bei dir gebucht */
export function ticketzeitSetzen(karteId: string, sek: number): void {
  const bisher = zeitDerKarte(karteId, false);
  const eigeneHeute = stand.zeiteintraege.filter((e) => e.konto === ICH && e.karte === karteId && e.datum === HEUTE)
    .reduce((s, e) => s + e.sekunden, 0);
  const ziel = Math.max(0, eigeneHeute + sek - bisher);
  setzeTageszeit(karteId, HEUTE, ziel);
}

export function dauerAendern(id: string, sek: number): void {
  const e = stand.zeiteintraege.find((x) => x.id === id);
  if (!e || e.sekunden === sek) return;
  aendern(() => {
    const alt = e.sekunden;
    if (sek < alt) kuerzen(e, alt - sek);
    else {
      e.sekunden = sek;
      if (e.herkunft === "timer" && e.von && e.bis && !e.sitzungen) e.bis = uhrzeitAus(Math.min(24 * 60, minutenAus(e.von) + Math.round(sek / 60)));
    }
    return `${schluessel(e.karte)} ${datum(e.datum, true)}: ${dauer(alt)} auf ${dauer(sek)} geändert`;
  });
}

export function notizAendern(id: string, notiz: string): void {
  const e = stand.zeiteintraege.find((x) => x.id === id);
  if (e && (e.notiz ?? "") !== notiz) e.notiz = notiz || undefined;
}

/** Löschen mit Rückgängig: der Eintrag kommt genau so zurück (Person, Zeiten, Herkunft) */
export function loeschen(id: string): void {
  const e = stand.zeiteintraege.find((x) => x.id === id);
  if (!e) return;
  aendern(() => {
    stand.zeiteintraege = stand.zeiteintraege.filter((x) => x.id !== id);
    return `Zeiteintrag (${dauer(e.sekunden)}, ${datum(e.datum, true)}) gelöscht`;
  });
}

/** Rückfrage nach dem Deckel: das tatsächliche Ende der Sitzung übernehmen */
export function deckelKorrigieren(ids: string[], ende: string): void {
  aendern(() => {
    for (const id of ids) {
      const e = stand.zeiteintraege.find((x) => x.id === id);
      if (!e) continue;
      if (e.von === "00:00") { e.bis = ende; e.sekunden = minutenAus(ende) * 60; }
      e.gedeckelt = undefined;
    }
    return `Ende auf ${ende} gesetzt, Rückfrage erledigt`;
  });
}

export function deckelBestaetigen(ids: string[]): void {
  aendern(() => {
    for (const id of ids) {
      const e = stand.zeiteintraege.find((x) => x.id === id);
      if (e) e.gedeckelt = undefined;
    }
    return "12 Stunden bleiben gebucht, Rückfrage erledigt";
  });
}
