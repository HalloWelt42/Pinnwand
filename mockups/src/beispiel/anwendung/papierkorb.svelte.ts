// Anwendungsfälle des Papierkorbs je Board: Karten und Spalten hineinlegen, an die alte Stelle wiederherstellen,
// endgültig entfernen (nur mit dem Recht "Papierkorb leeren"). Gelöschtes liegt nur im Papierkorb; die gebuchte Zeit
// bleibt in den Zeiteinträgen und zählt weiter, auch nach dem Entfernen (dann mit dem gemerkten Namen der Karte).

import type { Geloescht, Karte, Kennung } from "../../modell";
import { darf } from "../abfragen";
import { ICH, JETZT } from "../daten";
import { dauer } from "../format";
import { board, karte, kartenDerSpalte, stand } from "../stand.svelte";
import { aendern } from "./meldung.svelte";
import { timerBeenden } from "./timer.svelte";
import { neueKennung } from "./zeiten.svelte";

function anzahl(n: number): string {
  return `${n} ${n === 1 ? "Karte" : "Karten"}`;
}

/** Eine gelöschte Serienkarte: ihr Tag kommt nicht wieder (Auslass der Serie, Mechanik M-108) */
function auslassen(k: Karte): void {
  const s = k.serie && k.faellig ? stand.serien.find((x) => x.id === k.serie) : undefined;
  if (s && !s.auslass.some((a) => a.tag === k.faellig)) s.auslass.push({ tag: k.faellig!, von: ICH, am: JETZT });
}

/** Wiederhergestellt: der Tag gehört wieder zur Serie */
function zurueckInSerie(k: Karte): void {
  const s = k.serie && k.faellig ? stand.serien.find((x) => x.id === k.serie) : undefined;
  if (s) s.auslass = s.auslass.filter((a) => a.tag !== k.faellig);
}

export function eintragName(e: Geloescht): string {
  if (e.art === "board") return `Board ${e.inhalt?.board.name ?? ""}`;
  return e.art === "spalte" ? `Spalte ${e.spalte?.name}` : e.karten[0].schluessel;
}

/** Das Board eines Eintrags: das lebende, oder bei einem gelöschten Board sein festgehaltener Stand */
function boardDes(e: Geloescht) {
  return e.inhalt?.board ?? board(e.board);
}

/** Karten in den Papierkorb ihres Boards, mit allem, was daran hängt; laufende Timer buchen vorher */
export function inPapierkorb(ids: Kennung[]): void {
  const da = ids.filter((id) => karte(id));
  if (!da.length) return;
  aendern(() => {
    let gebucht = 0;
    for (const id of da) {
      const k = karte(id)!;
      gebucht += timerBeenden(id);
      const reihe = stand.reihen[k.spalte] ?? [];
      stand.papierkorb.unshift({ id: neueKennung("p"), board: k.board, art: "karte", karten: [$state.snapshot(k)],
                                 stelle: { spalte: k.spalte, platz: reihe.indexOf(id) }, von: ICH, am: JETZT });
      stand.reihen[k.spalte] = reihe.filter((i) => i !== id);
      stand.karten = stand.karten.filter((x) => x.id !== id);
      auslassen(k);
    }
    return `${anzahl(da.length)} im Papierkorb, mit Zeiten, Kommentaren und Anhängen wiederherstellbar`
      + (gebucht ? `; Timer angehalten, ${dauer(gebucht)} gebucht` : "");
  });
}

/** Spalte mit ihren Karten in den Papierkorb; die letzte Spalte eines Boards bleibt */
export function spalteInPapierkorb(boardId: Kennung, spalteId: Kennung): void {
  const b = board(boardId);
  const platz = b.spalten.findIndex((s) => s.id === spalteId);
  if (platz < 0 || b.spalten.length < 2) return;
  aendern(() => {
    const spalte = b.spalten[platz];
    const karten = kartenDerSpalte(spalteId);
    for (const k of karten) timerBeenden(k.id);
    stand.papierkorb.unshift({ id: neueKennung("p"), board: b.id, art: "spalte", spalte: $state.snapshot(spalte),
                               karten: karten.map((k) => $state.snapshot(k)), stelle: { platz }, von: ICH, am: JETZT });
    b.spalten.splice(platz, 1);
    delete stand.reihen[spalteId];
    const neuesZiel = b.spalten.find((x) => !x.erledigt) ?? b.spalten[0];
    for (const s of stand.serien.filter((x) => x.board === b.id && x.zielspalte === spalteId)) s.zielspalte = neuesZiel.id;
    stand.karten = stand.karten.filter((k) => k.spalte !== spalteId || k.board !== b.id);
    return `Spalte ${spalte.name} mit ${anzahl(karten.length)} im Papierkorb`;
  });
}

/** Wiederherstellen an die alte Stelle: Spalte samt Karten, oder Karte in ihre Spalte am alten Platz (fehlt die Spalte,
 *  in die erste des Boards); Schlüssel, Kommentare, Anhänge und Verknüpfung bleiben, wie sie waren */
export function wiederherstellen(id: Kennung): void {
  const e = stand.papierkorb.find((x) => x.id === id);
  if (!e) return;
  aendern(() => {
    const ids = e.karten.map((k) => k.id);
    if (e.art === "board" && e.inhalt) {
      const i = structuredClone($state.snapshot(e.inhalt));
      stand.boards.splice(Math.min(e.stelle.platz, stand.boards.length), 0, i.board);
      Object.assign(stand.reihen, i.reihen);
      stand.serien.push(...i.serien);
      stand.termine.push(...i.termine);
      const o = stand.ordner.find((x) => x.id === i.ordner);
      if (o && !o.boards.includes(i.board.id)) o.boards.push(i.board.id);
      stand.karten.push(...e.karten.map((k) => structuredClone($state.snapshot(k))));
      stand.papierkorb = stand.papierkorb.filter((x) => x.id !== id);
      return `Board ${i.board.name} wiederhergestellt, mit ${e.karten.length} ${e.karten.length === 1 ? "Karte" : "Karten"}`;
    }
    const b = board(e.board);
    let ort: string;
    if (e.art === "spalte" && e.spalte) {
      b.spalten.splice(Math.min(e.stelle.platz, b.spalten.length), 0, structuredClone($state.snapshot(e.spalte)));
      stand.reihen[e.spalte.id] = ids;
      ort = b.name;
    } else {
      const sp = b.spalten.find((s) => s.id === e.stelle.spalte) ?? b.spalten[0];
      const reihe = [...(stand.reihen[sp.id] ?? [])];
      reihe.splice(Math.min(e.stelle.platz, reihe.length), 0, ...ids);
      stand.reihen[sp.id] = reihe;
      for (const k of e.karten) k.spalte = sp.id;
      ort = `${sp.name} in ${b.name}`;
    }
    stand.karten.push(...e.karten.map((k) => structuredClone($state.snapshot(k))));
    for (const k of e.karten) zurueckInSerie(k);
    stand.papierkorb = stand.papierkorb.filter((x) => x.id !== id);
    return `${eintragName(e)} wiederhergestellt, an der alten Stelle in ${ort}`;
  });
}

/** Endgültig entfernen (nur mit dem Recht; die Rückfrage steht vorher in der Fläche). Die Zeit bleibt gebucht. */
export function entfernen(ids: Kennung[]): void {
  const weg = stand.papierkorb.filter((x) => ids.includes(x.id) && darf(boardDes(x), "papierkorb.leeren"));
  if (!weg.length) return;
  aendern(() => {
    for (const e of weg) for (const k of e.karten) {
      stand.entfernt.push({ karte: k.id, board: k.board, schluessel: k.schluessel, titel: k.titel, am: JETZT });
    }
    stand.papierkorb = stand.papierkorb.filter((x) => !weg.includes(x));
    return weg.length === 1 ? `${eintragName(weg[0])} endgültig entfernt; gebuchte Zeit bleibt` : `${weg.length} Einträge endgültig entfernt; gebuchte Zeit bleibt`;
  }, { rueckgaengig: false });
}
