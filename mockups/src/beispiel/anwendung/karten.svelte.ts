// Anwendungsfälle an Karten: verschieben (Ziehen, Status im Detail, Telefon, Liste: ein Weg), erledigen, anlegen,
// duplizieren, bearbeiten, kommentieren, verknüpfen, Sammelaktionen. Beim Spaltenwechsel beginnt das Alter neu,
// verknüpfte Karten desselben Boards ziehen mit, in einer Erledigt-Spalte gibt es das Abschlussdatum und laufende Timer
// halten an und buchen (wie verschiebe_karte der alten App, jetzt ohne Nebenwege). Über der Grenze einer Spalte nur
// eine Warnung, nie ein harter Halt. Was zählt, steht im Verlauf der Karte (verlauf.ts).

import type { Karte, Kennung, Prioritaet, Spalte } from "../../modell";
import { HEUTE, ICH, JETZT } from "../daten";
import { dauer } from "../format";
import { board, gruppenmitglieder, karte, kartenDerSpalte, konto, stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { timerBeenden } from "./timer.svelte";
import { vermerken } from "./verlauf";

function spalteVon(k: Karte): Spalte | undefined {
  return board(k.board).spalten.find((s) => s.id === k.spalte);
}

/** Abschlussdatum in einer Erledigt-Spalte: eine Serienkarte hat fest ihren Termintag, alle anderen den Tag des
 *  Ablegens (Mechanik M-23) */
function abschluss(k: Karte): string {
  return k.serie && k.faellig ? k.faellig : HEUTE;
}

/** Eine Karte wechselt in eine Spalte (Reihen sind schon gesetzt): Alter, Abschluss, Timer, Verlauf. Ergebnis: eigene
 *  gebuchte Zeit */
function wechseln(k: Karte, ziel: Spalte, mitgezogen: boolean): number {
  const alt = spalteVon(k);
  k.spalte = ziel.id;
  k.bewegtAm = JETZT;
  k.abgeschlossen = ziel.erledigt ? abschluss(k) : undefined;
  vermerken(k, mitgezogen ? `mit verknüpfter Karte verschoben nach ${ziel.name}`
    : ziel.erledigt ? "hat sie erledigt" : `hat sie von ${alt?.name ?? "?"} nach ${ziel.name} verschoben`);
  return ziel.erledigt ? timerBeenden(k.id) : 0;
}

/** Hinweis, wenn eine Spalte über ihrer Grenze liegt (nur Warnung) */
function ueberGrenze(ziel: Spalte): string {
  const offen = kartenDerSpalte(ziel.id).length;
  return !ziel.erledigt && ziel.grenze !== undefined && offen > ziel.grenze ? `${ziel.name} über der Grenze (${offen}/${ziel.grenze})` : "";
}

/** Karten in eine Spalte bringen: an den Platz (oder ans Ende), verknüpfte ziehen mit ans Ende. Ergebnis: Meldung */
function hinein(ids: Kennung[], ziel: Spalte, platz?: number): string {
  const erste = karte(ids[0]);
  if (!erste) return "";
  // Mitglieder desselben Boards ziehen mit; Mitglieder auf anderen Boards bleiben stehen (M-76)
  const mit = ids.flatMap((id) => gruppenmitglieder(karte(id)!))
    .filter((m) => m.board === erste.board && m.spalte !== ziel.id && !ids.includes(m.id));
  const alle = [...ids, ...new Set(mit.map((m) => m.id))];
  for (const id of alle) for (const sp of Object.keys(stand.reihen)) stand.reihen[sp] = stand.reihen[sp].filter((x) => x !== id);
  const reihe = [...(stand.reihen[ziel.id] ?? [])];
  reihe.splice(platz ?? reihe.length, 0, ...ids);
  reihe.push(...alle.slice(ids.length));
  stand.reihen[ziel.id] = reihe;
  let gebucht = 0;
  alle.forEach((id, i) => {
    const k = karte(id)!;
    if (k.spalte !== ziel.id) gebucht += wechseln(k, ziel, i >= ids.length);
  });
  const teile = [ids.length === 1 ? (ziel.erledigt ? `${erste.schluessel} erledigt` : `${erste.schluessel} nach ${ziel.name}`)
    : `${ids.length} Karten nach ${ziel.name}`];
  if (mit.length) teile.push(`${mit.length} verknüpfte ${mit.length === 1 ? "zieht" : "ziehen"} mit`);
  if (gebucht) teile.push(`Timer angehalten, ${dauer(gebucht)} gebucht`);
  const grenze = ueberGrenze(ziel);
  if (grenze) teile.push(grenze);
  return teile.join("; ");
}

/** Ergebnis des Ziehens in eine Spalte: ihre neue Reihenfolge (mit den neu hineingezogenen Karten) */
export function ablegen(spalteId: Kennung, ids: Kennung[]): void {
  const k0 = karte(ids[0] ?? "");
  const ziel = k0 && board(k0.board).spalten.find((s) => s.id === spalteId);
  if (!ziel) { stand.reihen[spalteId] = ids; return; }
  const neu = ids.filter((id) => karte(id)?.spalte !== spalteId);
  aendern(() => {
    if (!neu.length) {
      stand.reihen[spalteId] = ids;
      return `${ziel.name} neu geordnet`;
    }
    return hinein(neu, ziel, ids.indexOf(neu[0]));
  });
}

/** Karte in eine andere Spalte ihres Boards, ans Ende (Status im Detail, Telefon, Liste) */
export function verschieben(id: Kennung, nach: Kennung): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.id === nach);
  if (!k || !ziel || k.spalte === nach) return;
  aendern(() => hinein([id], ziel));
}

/** Mehrere Karten eines Boards in eine Spalte */
export function sammelVerschieben(ids: Kennung[], nach: Kennung): void {
  const k = karte(ids[0] ?? "");
  const ziel = k && board(k.board).spalten.find((s) => s.id === nach);
  const weg = ids.filter((id) => karte(id)?.spalte !== nach);
  if (!ziel || !weg.length) return;
  aendern(() => hinein(weg, ziel));
}

/** Abhaken: in die Erledigt-Spalte des Boards */
export function erledigen(id: Kennung): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.erledigt);
  if (ziel) verschieben(id, ziel.id);
}

/** Getippter oder gesprochener Text als Absätze (die Beschreibung einer Karte ist formatierter Text) */
function alsAbsaetze(text: string): string {
  const sicher = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return sicher.split(/\n+/).map((z) => z.trim()).filter(Boolean).map((z) => `<p>${z}</p>`).join("");
}

/** Neue Karte ans Ende der Spalte: Schlüssel aus der Laufnummer des Boards (nie wiederverwendet), du bist zuständig;
 *  die Beschreibung kommt als Text und wird hier zu Absätzen */
export function anlegen(boardId: Kennung, spalteId: Kennung,
                        felder: { titel: string; art?: "arbeit" | "idee"; faellig?: string; beschreibung?: string }): Karte | undefined {
  const b = board(boardId);
  const spalte = b.spalten.find((s) => s.id === spalteId) ?? b.spalten.find((s) => !s.erledigt) ?? b.spalten[0];
  const titel = felder.titel.trim();
  if (!titel) return undefined;
  let neu: Karte | undefined;
  aendern(() => {
    b.laufnummer += 1;
    const id = `c-${b.kuerzel.toLowerCase()}-${b.laufnummer}`;
    stand.karten.push({
      id, board: b.id, schluessel: `${b.kuerzel}-${b.laufnummer}`, spalte: spalte.id, titel,
      art: felder.art ?? (b.module.zeiterfassung ? "arbeit" : "idee"),
      beschreibung: felder.beschreibung?.trim() ? alsAbsaetze(felder.beschreibung) : undefined, zustaendig: [ICH],
      prioritaet: "keine", faellig: felder.faellig, labels: [], checkliste: [], kommentare: [], bewegtAm: JETZT, erstelltAm: JETZT,
      felder: {}, anhaenge: [], transkripte: [], verlauf: [{ zeit: JETZT, von: ICH, text: "hat die Karte angelegt" }],
    });
    (stand.reihen[spalte.id] ??= []).push(id);
    neu = karte(id);
    const grenze = ueberGrenze(spalte);
    return `${b.kuerzel}-${b.laufnummer} in ${spalte.name} angelegt` + (grenze ? `; ${grenze}` : "");
  });
  return neu;
}

/** Felder, deren Änderung im Verlauf steht (Titel und Beschreibung bewusst nicht) */
const IM_VERLAUF: (keyof Karte)[] = ["zustaendig", "faellig", "start", "prioritaet", "blockiert"];

/** Felder einer Karte ändern (Titel, Beschreibung, Fällig, Priorität, Checkliste und weitere Grundfelder) */
export function bearbeiten(id: Kennung, aenderung: Partial<Omit<Karte, "id" | "board" | "schluessel" | "spalte">>, text = "Gespeichert"): boolean {
  const k = karte(id);
  if (!k) return false;
  return aendern(() => {
    Object.assign(k, aenderung);
    if (Object.keys(aenderung).some((f) => IM_VERLAUF.includes(f as keyof Karte))) vermerken(k, text);
    return `${k.schluessel}: ${text}`;
  });
}

/** Kopie in derselben Spalte (am Ende): Titel mit "(Kopie)", Inhalt und Angaben gleich, Checkliste unerledigt; ohne
 *  Zeiten, Kommentare, Blockade, Transkripte, Gruppe und Anhänge (Mechanik M-36). Ergebnis: die Kopie */
export function duplizieren(id: Kennung): Karte | undefined {
  const k = karte(id);
  if (!k) return undefined;
  const b = board(k.board);
  let kopie: Karte | undefined;
  aendern(() => {
    b.laufnummer += 1;
    const neuId = `c-${b.kuerzel.toLowerCase()}-${b.laufnummer}`;
    const q = structuredClone($state.snapshot(k)) as Karte;
    stand.karten.push({
      ...q, id: neuId, schluessel: `${b.kuerzel}-${b.laufnummer}`, titel: `${k.titel} (Kopie)`,
      checkliste: q.checkliste.map((p) => ({ ...p, erledigt: false })), kommentare: [], blockiert: undefined, transkripte: [],
      gruppe: undefined, serie: undefined, anhaenge: [], abgeschlossen: undefined, bewegtAm: JETZT, erstelltAm: JETZT,
      verlauf: [{ zeit: JETZT, von: ICH, text: `hat die Karte aus ${k.schluessel} dupliziert` }],
    });
    (stand.reihen[k.spalte] ??= []).push(neuId);
    kopie = karte(neuId);
    return `Karte als "${k.titel} (Kopie)" dupliziert`;
  });
  return kopie;
}

/** Arbeit oder Idee: eine Idee hat keine Zeiterfassung, laufende Timer halten an und buchen */
export function artSetzen(id: Kennung, art: "arbeit" | "idee"): void {
  const k = karte(id);
  if (!k || k.art === art) return;
  aendern(() => {
    const sek = art === "idee" ? timerBeenden(id) : 0;
    k.art = art;
    vermerken(k, art === "idee" ? "hat sie zur Idee gemacht" : "hat sie zur Arbeit gemacht");
    return `${k.schluessel} ist jetzt ${art === "idee" ? "eine Idee" : "Arbeit"}` + (sek ? `; Timer angehalten, ${dauer(sek)} gebucht` : "");
  });
}

export function kommentieren(id: Kennung, text: string): boolean {
  const k = karte(id);
  const t = text.trim();
  if (!k || !t) return false;
  return aendern(() => {
    k.kommentare.push({ von: ICH, zeit: JETZT, text: t });
    vermerken(k, "hat kommentiert");
    return `Kommentar an ${k.schluessel} gespeichert`;
  });
}

function anzahl(n: number): string {
  return `${n} ${n === 1 ? "Karte" : "Karten"}`;
}

export function sammelZuweisen(ids: Kennung[], kontoId: Kennung): void {
  aendern(() => {
    for (const id of ids) {
      const k = karte(id);
      if (k && !k.zustaendig.includes(kontoId)) { k.zustaendig.push(kontoId); vermerken(k, `hat ${konto(kontoId).name} zugewiesen`); }
    }
    return `${anzahl(ids.length)} ${konto(kontoId).name} zugewiesen`;
  });
}

export function sammelLabel(ids: Kennung[], label: Kennung): void {
  aendern(() => {
    for (const id of ids) {
      const k = karte(id);
      if (k && !k.labels.includes(label)) k.labels.push(label);
    }
    return `Label an ${anzahl(ids.length)} gesetzt`;
  });
}

export function sammelPrioritaet(ids: Kennung[], p: Prioritaet): void {
  aendern(() => {
    for (const id of ids) {
      const k = karte(id);
      if (k && k.prioritaet !== p) { k.prioritaet = p; vermerken(k, "hat die Priorität gesetzt"); }
    }
    return `Priorität von ${anzahl(ids.length)} gesetzt`;
  });
}

/** Gemeinsame Zeit einer Gruppe verknüpfter Karten zeigen oder nicht (gebucht wird immer je Karte) */
export function zeitTeilen(gruppeId: Kennung, an: boolean): void {
  const g = stand.gruppen.find((x) => x.id === gruppeId);
  if (!g || g.zeitTeilen === an) return;
  aendern(() => {
    g.zeitTeilen = an;
    return an ? "Die Gruppe zeigt ihre gemeinsame Zeit" : "Jede Karte zeigt nur ihre eigene Zeit";
  });
}

/** Zwei Arbeitskarten desselben Boards verknüpfen (Mechanik M-74): ohne Gruppe entsteht eine neue mit geteilter Zeit, hat
 *  eine eine Gruppe, tritt die andere bei, haben beide verschiedene, geht die zweite in der ersten auf */
export function verknuepfen(aId: Kennung, bId: Kennung): void {
  const a = karte(aId), b = karte(bId);
  if (!a || !b || a.id === b.id || a.board !== b.board || a.art !== "arbeit" || b.art !== "arbeit") return;
  if (a.gruppe && a.gruppe === b.gruppe) return;
  aendern(() => {
    if (!a.gruppe && !b.gruppe) {
      const id = `g-${a.id}-${b.id}`;
      stand.gruppen.push({ id, zeitTeilen: true });
      a.gruppe = b.gruppe = id;
    } else if (a.gruppe && b.gruppe) {
      const alt = b.gruppe;
      for (const x of stand.karten.filter((k) => k.gruppe === alt)) x.gruppe = a.gruppe;
      stand.gruppen = stand.gruppen.filter((g) => g.id !== alt);
    } else {
      const g = a.gruppe ?? b.gruppe;
      a.gruppe = b.gruppe = g;
    }
    vermerken(a, `hat sie mit ${b.schluessel} verknüpft`);
    vermerken(b, `hat sie mit ${a.schluessel} verknüpft`);
    return `${a.schluessel} und ${b.schluessel} verknüpft: ziehen zusammen, Zeit wird geteilt`;
  });
}

/** Karte aus ihrer Gruppe lösen; bleibt nur eine übrig, endet die Gruppe */
export function gruppeLoesen(id: Kennung): void {
  const k = karte(id);
  const g = k?.gruppe;
  if (!k || !g) return;
  aendern(() => {
    k.gruppe = undefined;
    const rest = stand.karten.filter((x) => x.gruppe === g);
    if (rest.length < 2) {
      for (const x of rest) x.gruppe = undefined;
      stand.gruppen = stand.gruppen.filter((x) => x.id !== g);
    }
    return `${k.schluessel} aus der Verknüpfung gelöst`;
  });
}
