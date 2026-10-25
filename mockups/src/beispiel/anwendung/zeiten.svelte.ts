// Anwendungsfälle des Moduls Zeiterfassung: Zeit buchen, eine Tageszeit setzen, Einträge ändern und löschen, die
// Rückfrage nach dem 12-Stunden-Deckel. Jede Änderung meldet sich mit Rückgängig. Gebucht wird immer als Zeiteintrag;
// die Zeit einer Karte ist deren Summe (abfragen.ts), es gibt keinen zweiten Zähler.

import type { Timer, Zeiteintrag } from "../../modell";
import { minutenAus, plusTage, uhrzeitAus } from "../../regeln/tage";
import { kartenName, zeitDerKarte } from "../abfragen";
import { HEUTE, ICH, JETZT } from "../daten";
import { datum, dauer, uhrzeit } from "../format";
import { stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { vermerken } from "./verlauf";

/** Kennung ohne Zähler und ohne randomUUID (das fehlt außerhalb sicherer Kontexte) */
export function neueKennung(vorsatz: string): string {
  const b = crypto.getRandomValues(new Uint8Array(8));
  return `${vorsatz}-${Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("")}`;
}

function schluessel(karteId: string): string {
  return kartenName(karteId).schluessel;
}

/** Ein Timer bucht höchstens so lange am Stück; mehr deckelt der Server und fragt nach dem echten Ende */
export const DECKEL_SEK = 12 * 3600;

/** Ortszeit als ISO ohne Zone (wie JETZT) */
function ortszeit(d: Date): string {
  const z = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}T${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
}

/** Die laufende Sitzung eines Timers buchen, bis jetzt (oder bis zum gegebenen Zeitpunkt). Eine Sitzung an einem Tag
 *  geht in den Timer-Eintrag der Karte an diesem Tag (je Karte, Person und Tag einer, die Sitzungen darin sichtbar).
 *  Über Mitternacht wird sie je Tag zerlegt; über 12 Stunden werden die ersten 12 gebucht und die Einträge tragen den
 *  Vermerk gedeckelt mit der echten Spanne, bis die Person die Rückfrage beantwortet. Der Timer selbst hält an.
 *  Ergebnis: gebuchte Sekunden. */
export function sitzungBuchen(t: Timer, bis = JETZT): number {
  if (!t.seit) return 0;
  const start = new Date(t.seit).getTime();
  const gesamt = Math.max(0, Math.round((new Date(bis).getTime() - start) / 1000));
  const gebucht = Math.min(gesamt, DECKEL_SEK);
  const deckel = gesamt > DECKEL_SEK
    ? { spanne: `von ${datum(t.seit, true)} ${uhrzeit(t.seit)} bis ${datum(bis, true)} ${uhrzeit(bis)}`, sekunden: gesamt } : undefined;
  // in Teile je Tag zerlegen, bis die gebuchte Zeit erreicht ist
  const teile: { tag: string; von: string; bis: string; sek: number }[] = [];
  let von = start, rest = gebucht;
  while (rest > 0) {
    const tag = ortszeit(new Date(von)).slice(0, 10);
    const mitternacht = new Date(`${plusTage(tag, 1)}T00:00:00`).getTime();
    const ende = Math.min(mitternacht, von + rest * 1000);
    const sek = Math.round((ende - von) / 1000);
    teile.push({ tag, von: ortszeit(new Date(von)).slice(11, 16), bis: ende === mitternacht ? "24:00" : ortszeit(new Date(ende)).slice(11, 16), sek });
    rest -= sek;
    von = ende;
  }
  if (teile.length === 1 && !deckel) {
    const [teil] = teile;
    const da = stand.zeiteintraege.find((e) => e.konto === t.konto && e.karte === t.karte && e.datum === teil.tag && e.herkunft === "timer");
    if (da) {
      da.sitzungen = [...(da.sitzungen ?? (da.von && da.bis ? [{ von: da.von, bis: da.bis }] : [])), { von: teil.von, bis: teil.bis }];
      da.sekunden += teil.sek;
      da.bis = teil.bis;
    } else {
      stand.zeiteintraege.push({ id: neueKennung("z"), karte: t.karte, konto: t.konto, datum: teil.tag, von: teil.von, bis: teil.bis,
                                 sekunden: teil.sek, herkunft: "timer" });
    }
  } else {
    teile.forEach((teil, i) => {
      const nachbar = teile[i + 1] ?? teile[i - 1];
      stand.zeiteintraege.push({ id: neueKennung("z"), karte: t.karte, konto: t.konto, datum: teil.tag, von: teil.von, bis: teil.bis,
                                 sekunden: teil.sek, herkunft: "timer", zerlegt: teile.length > 1 ? nachbar.tag : undefined, gedeckelt: deckel });
    });
  }
  t.seit = undefined;
  if (gebucht) vermerken(t.karte, `Timer: ${dauer(gebucht)} gebucht` + (deckel ? " (nach 12 Stunden gedeckelt)" : ""));
  return gebucht;
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
    vermerken(karteId, `hat ${dauer(sek)} nachgetragen (${datum(tag, true)})`);
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
    vermerken(karteId, `hat die Zeit am ${datum(tag, true)} von ${dauer(bisher)} auf ${dauer(sek)} gesetzt`);
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

/** Tag eines Eintrags ändern (Tagesliste an der Karte, Mechanik M-88): der Eintrag zieht auf den neuen Tag, Dauer,
 *  Uhrzeiten und Herkunft bleiben. War die Sitzung an Mitternacht zerlegt, verlieren beide Teile den Bezug aufeinander. */
export function datumAendern(id: string, tag: string): void {
  const e = stand.zeiteintraege.find((x) => x.id === id);
  if (!e || e.datum === tag) return;
  aendern(() => {
    const alt = e.datum;
    if (e.zerlegt) {
      const teil = stand.zeiteintraege.find((x) => x.karte === e.karte && x.konto === e.konto && x.datum === e.zerlegt && x.zerlegt === alt);
      if (teil) teil.zerlegt = undefined;
      e.zerlegt = undefined;
    }
    e.datum = tag;
    vermerken(e.karte, `hat einen Zeiteintrag (${dauer(e.sekunden)}) von ${datum(alt, true)} auf ${datum(tag, true)} gelegt`);
    return `${schluessel(e.karte)}: Eintrag (${dauer(e.sekunden)}) von ${datum(alt, true)} auf ${datum(tag, true)} gelegt`;
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
    vermerken(e.karte, `hat einen Zeiteintrag gelöscht (${dauer(e.sekunden)}, ${datum(e.datum, true)})`);
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
