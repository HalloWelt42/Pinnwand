// Anwendungsfälle an Karten: verschieben (Ziehen, Status im Detail, Telefon, Liste: ein Weg), erledigen, anlegen,
// bearbeiten, kommentieren, Sammelaktionen. Beim Spaltenwechsel beginnt das Alter neu, verknüpfte Karten ziehen mit, in
// einer Erledigt-Spalte gibt es das Abschlussdatum und laufende Timer halten an und buchen (wie verschiebe_karte der
// alten App, jetzt ohne Nebenwege). Über der Grenze einer Spalte nur eine Warnung, nie ein harter Halt.

import type { Karte, Kennung, Prioritaet, Spalte } from "../../modell";
import { HEUTE, ICH, JETZT } from "../daten";
import { dauer } from "../format";
import { board, gruppenmitglieder, karte, kartenDerSpalte, konto, stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { timerBeenden } from "./timer.svelte";

function spalteVon(k: Karte): Spalte | undefined {
  return board(k.board).spalten.find((s) => s.id === k.spalte);
}

/** Eine Karte wechselt in eine Spalte (Reihen sind schon gesetzt): Alter, Abschluss, Timer. Ergebnis: eigene gebuchte Zeit */
function wechseln(k: Karte, ziel: Spalte): number {
  const alt = spalteVon(k);
  k.spalte = ziel.id;
  k.bewegtAm = JETZT;
  k.abgeschlossen = ziel.erledigt ? HEUTE : undefined;
  k.verlauf.push({ zeit: JETZT, von: ICH, text: ziel.erledigt ? "hat sie erledigt" : `hat sie von ${alt?.name ?? "?"} nach ${ziel.name} verschoben` });
  return ziel.erledigt ? timerBeenden(k.id) : 0;
}

/** Karten in eine Spalte bringen: an den Platz (oder ans Ende), verknüpfte ziehen mit ans Ende. Ergebnis: Meldung */
function hinein(ids: Kennung[], ziel: Spalte, platz?: number): string {
  const erste = karte(ids[0]);
  if (!erste) return "";
  const mit = ids.flatMap((id) => gruppenmitglieder(karte(id)!)).filter((m) => m.spalte !== ziel.id && !ids.includes(m.id));
  const alle = [...ids, ...new Set(mit.map((m) => m.id))];
  for (const id of alle) for (const sp of Object.keys(stand.reihen)) stand.reihen[sp] = stand.reihen[sp].filter((x) => x !== id);
  const reihe = [...(stand.reihen[ziel.id] ?? [])];
  reihe.splice(platz ?? reihe.length, 0, ...ids);
  reihe.push(...alle.slice(ids.length));
  stand.reihen[ziel.id] = reihe;
  let gebucht = 0;
  for (const id of alle) {
    const k = karte(id)!;
    if (k.spalte !== ziel.id) gebucht += wechseln(k, ziel);
  }
  const teile = [ids.length === 1 ? (ziel.erledigt ? `${erste.schluessel} erledigt` : `${erste.schluessel} nach ${ziel.name}`)
    : `${ids.length} Karten nach ${ziel.name}`];
  if (mit.length) teile.push(`${mit.length} verknüpfte ${mit.length === 1 ? "zieht" : "ziehen"} mit`);
  if (gebucht) teile.push(`Timer angehalten, ${dauer(gebucht)} gebucht`);
  const offen = kartenDerSpalte(ziel.id).length;
  if (!ziel.erledigt && ziel.grenze !== undefined && offen > ziel.grenze) teile.push(`${ziel.name} über der Grenze (${offen}/${ziel.grenze})`);
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

/** Neue Karte ans Ende der Spalte: Schlüssel aus der Laufnummer des Boards (nie wiederverwendet), du bist zuständig */
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
      art: felder.art ?? (b.module.zeiterfassung ? "arbeit" : "idee"), beschreibung: felder.beschreibung, zustaendig: [ICH],
      prioritaet: "keine", faellig: felder.faellig, labels: [], checkliste: [], kommentare: [], bewegtAm: JETZT, erstelltAm: JETZT,
      felder: {}, anhaenge: [], transkripte: [], verlauf: [{ zeit: JETZT, von: ICH, text: "hat die Karte angelegt" }],
    });
    (stand.reihen[spalte.id] ??= []).push(id);
    neu = karte(id);
    return `${b.kuerzel}-${b.laufnummer} in ${spalte.name} angelegt`;
  });
  return neu;
}

/** Felder einer Karte ändern (Titel, Beschreibung, Fällig, Priorität, Checkliste und weitere Grundfelder) */
export function bearbeiten(id: Kennung, aenderung: Partial<Omit<Karte, "id" | "board" | "schluessel" | "spalte">>, text = "Gespeichert"): void {
  const k = karte(id);
  if (!k) return;
  aendern(() => {
    Object.assign(k, aenderung);
    return `${k.schluessel}: ${text}`;
  });
}

/** Arbeit oder Idee: eine Idee hat keine Zeiterfassung, laufende Timer halten an und buchen */
export function artSetzen(id: Kennung, art: "arbeit" | "idee"): void {
  const k = karte(id);
  if (!k || k.art === art) return;
  aendern(() => {
    const sek = art === "idee" ? timerBeenden(id) : 0;
    k.art = art;
    return `${k.schluessel} ist jetzt ${art === "idee" ? "eine Idee" : "Arbeit"}` + (sek ? `; Timer angehalten, ${dauer(sek)} gebucht` : "");
  });
}

export function kommentieren(id: Kennung, text: string): void {
  const k = karte(id);
  const t = text.trim();
  if (!k || !t) return;
  aendern(() => {
    k.kommentare.push({ von: ICH, zeit: JETZT, text: t });
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
      if (k && !k.zustaendig.includes(kontoId)) k.zustaendig.push(kontoId);
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
      if (k) k.prioritaet = p;
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
