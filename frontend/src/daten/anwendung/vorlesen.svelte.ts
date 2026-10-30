// Vorlesen (Modul vorlesen, M-114): der Text, den die Oberfläche zeigt, geht über den Server an die App Vorlesen und kommt
// Satz für Satz zurück; gespielt wird mit dem Vorleser des Appkerns (im Tippen gestartet, ein zweites Tippen hält an,
// immer nur ein Ton). Markdown wird vorher zu Klartext. Jede Stelle vergibt eine Kennung, damit ihr Knopf weiß, ob er
// gerade liest.

import { vorleser } from "appkern-oberflaeche";
import type { Bericht, BerichtInhalt, Board, Karte, Kennung } from "../../modell";
import { modulAn } from "../../regeln/board";
import { markdownText } from "../../teile/markdown";
import { wochentag } from "../../regeln/tage";
import { modulIrgendwo, type MeinTag, type TagEintrag } from "../abfragen";
import { datumJahr, wann } from "../format";
import { berichtAdresse } from "./berichte.svelte";
import { konto, stand } from "../stand.svelte";

const TAGE = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];

/** Gibt es Vorlesen (in diesem Board; ohne Board: in einem deiner Boards)? Dazu muss die App Vorlesen eingetragen sein. */
export function vorlesenDa(b?: Board): boolean {
  if (!stand.vorlesenAdresse) return false;
  return b ? modulAn(b, "vorlesen", stand.moduleDa) : modulIrgendwo("vorlesen");
}

/** Liest `text` unter `kennung` vor; liest dieselbe Kennung schon, hält es an. Im Klick aufrufen. */
export function vorlesen(kennung: string, text: string, boardId?: Kennung): void {
  vorleser.umschalten(kennung, "/vorlesen", { text, board: boardId ?? null });
}

/** Liest diese Stelle gerade (oder wartet auf ihren ersten Satz)? */
export function liest(kennung: string): boolean {
  return vorleser.kennung === kennung;
}

/** Die ganze Karte zum Vorlesen: Schlüssel und Titel, Beschreibung, offene Punkte der Checkliste */
export function karteText(k: Karte): string {
  const teile = [`${k.schluessel}: ${k.titel}.`];
  if (k.beschreibung) teile.push(markdownText(k.beschreibung));
  const offen = k.checkliste.filter((p) => !p.erledigt).map((p) => p.text);
  if (offen.length) teile.push(`Offene Punkte: ${offen.join("; ")}.`);
  return teile.join("\n");
}

/** Die Checkliste zum Vorlesen: erst die offenen, dann die erledigten Punkte */
export function checklisteText(k: Karte): string {
  const offen = k.checkliste.filter((p) => !p.erledigt).map((p) => p.text);
  const fertig = k.checkliste.filter((p) => p.erledigt).map((p) => p.text);
  const teile = [`Checkliste von ${k.schluessel}.`];
  if (offen.length) teile.push(`Offen: ${offen.join("; ")}.`);
  if (fertig.length) teile.push(`Erledigt: ${fertig.join("; ")}.`);
  return teile.join("\n");
}

/** Alle Kommentare zum Vorlesen, wie die Karte sie zeigt: der neueste zuerst, je mit Person und Zeit */
export function kommentareText(k: Karte): string {
  return [`Kommentare zu ${k.schluessel}.`,
    ...[...k.kommentare].reverse().map((c) => `${konto(c.von).name}, ${wann(c.zeit)}: ${markdownText(c.text)}`)].join("\n");
}

/** Der Verlauf zum Vorlesen, der neueste Eintrag zuerst */
export function verlaufText(k: Karte): string {
  const zeilen = [...k.verlauf].reverse().sort((a, b) => b.zeit.localeCompare(a.zeit));
  return [`Verlauf von ${k.schluessel}.`, ...zeilen.map((e) => `${wann(e.zeit)}: ${konto(e.von).name} ${e.text}.`)].join("\n");
}

function karten(liste: TagEintrag[], seit: boolean): string {
  return liste.map((e) => (seit && e.karte.faellig ? `${e.karte.titel}, fällig seit ${datumJahr(e.karte.faellig)}` : e.karte.titel)).join("; ");
}

/** "ist eine Karte" oder "sind 3 Karten" */
function anzahl(n: number): string {
  return n === 1 ? "ist eine Karte" : `sind ${n} Karten`;
}

/** Eine Serienkarte mit ihrer Uhrzeit, wenn der Titel sie nicht schon nennt */
function serienkarte(e: TagEintrag, uhrzeit: string): string {
  return uhrzeit && !e.karte.titel.startsWith(uhrzeit) ? `${uhrzeit} Uhr ${e.karte.titel}` : e.karte.titel;
}

/** Der Tagesplan aus Heute zum Vorlesen: Überfälliges, heute Fälliges, Serien und Termine von heute (M-114) */
export function tagesplanText(g: MeinTag, heute: string, uhrzeit: (e: TagEintrag) => string): string {
  const zeilen = [`Dein Tag am ${TAGE[wochentag(heute)]}, ${datumJahr(heute)}.`];
  if (g.ueberfaellig.length) zeilen.push(`Überfällig ${anzahl(g.ueberfaellig.length)}: ${karten(g.ueberfaellig, true)}.`);
  if (g.heute.length) zeilen.push(`Heute fällig ${anzahl(g.heute.length)}: ${karten(g.heute, false)}.`);
  if (g.serien.length) zeilen.push(`Aus Serien heute: ${g.serien.map((e) => serienkarte(e, uhrzeit(e))).join("; ")}.`);
  if (g.termine.heute.length) {
    zeilen.push(`Termine heute: ${g.termine.heute.map((t) => `${t.von} bis ${t.bis} Uhr ${t.titel}${t.ort ? ` in ${t.ort}` : ""}`).join("; ")}.`);
  }
  if (zeilen.length === 1) zeilen.push("Heute ist nichts fällig und nichts überfällig.");
  return zeilen.join("\n");
}

/** Ein Bericht zum Vorlesen aus dem Inhalt der Vorschau: Titel und Zeitraum, je Abschnitt die Zeilen als "Spalte Wert" */
export function berichtText(titel: string, inhalt: BerichtInhalt): string {
  const zeilen = [`${titel}, ${inhalt.zeitraum}.`];
  for (const a of inhalt.abschnitte) {
    zeilen.push(`${a.titel}.`);
    for (const z of a.zeilen) zeilen.push(`${a.spalten.map((s, i) => (z[i] ? `${s} ${z[i]}` : "")).filter(Boolean).join(", ")}.`);
    if (a.summe?.some(Boolean)) zeilen.push(`Summe: ${a.summe.filter(Boolean).join(", ")}.`);
  }
  return zeilen.join("\n");
}

/** Einen erstellten Bericht (Markdown) vorlesen: der Ton wird im Tippen freigeschaltet, dann die Datei geladen */
export async function berichtVorlesen(b: Bericht): Promise<void> {
  const kennung = `bericht-${b.id}`;
  if (liest(kennung)) {
    vorleser.anhalten();
    return;
  }
  vorleser.entsperren();
  try {
    const antwort = await fetch(berichtAdresse(b));
    if (!antwort.ok) throw new Error(String(antwort.status));
    vorlesen(kennung, markdownText(await antwort.text()));
  } catch {
    vorleser.fehler = "Der Bericht ließ sich nicht laden";
  }
}
