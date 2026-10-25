// Anwendungsfälle des Bereichs Übersicht auf dem veränderlichen Zustand der Entwürfe: erledigen, verschieben, Timer,
// Papierkorb, Hinweise gelesen. Verschieben und Erledigen laufen über ablegen() aus beispiel/stand.svelte.ts, also über
// denselben Weg wie das Ziehen im Board (Gruppe zieht mit, Abschlussdatum, ein laufender Timer hält an und bucht).
// In der App ruft jede dieser Funktionen genau einen Anwendungsfall der Schnittstelle; Erfolg erst nach der Antwort.

import { HEUTE, HINWEISE, ICH, JETZT, ZEITEINTRAEGE } from "../../beispiel/daten";
import { dauer, laufendSek } from "../../beispiel/format";
import { ablegen, board, karte, stand } from "../../beispiel/stand.svelte";
import type { Hinweis, Karte, Prioritaet } from "../../modell";
import { PAPIERKORB } from "./daten";
import type { Geloescht } from "./modell";

/** Eigener Zustand des Bereichs: gelesene Hinweise und der Papierkorb */
export const uebersicht = $state({
  hinweise: structuredClone(HINWEISE) as Hinweis[],
  papierkorb: structuredClone(PAPIERKORB) as Geloescht[],
});

/** Karte in eine andere Spalte ihres Boards, ans Ende (wie Ziehen und die Status-Auswahl im Detail) */
export function verschieben(id: string, nach: string): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.id === nach);
  if (!k || !ziel || k.spalte === nach) return;
  stand.reihen[k.spalte] = (stand.reihen[k.spalte] ?? []).filter((i) => i !== id);
  ablegen(nach, [...(stand.reihen[nach] ?? []), id], ziel.erledigt);
}

/** Abhaken: in die Erledigt-Spalte des Boards */
export function erledigen(id: string): void {
  const k = karte(id);
  const ziel = k && board(k.board).spalten.find((s) => s.erledigt);
  if (!k || !ziel) return;
  stand.meldung = "";
  verschieben(id, ziel.id);
  if (!stand.meldung) stand.meldung = `${k.schluessel} erledigt, liegt jetzt in ${ziel.name}`;
}

/** Mehrere Karten verschieben; über der Grenze der Zielspalte nur eine Warnung, kein harter Halt */
export function sammelVerschieben(ids: string[], nach: string): void {
  stand.meldung = "";
  const k0 = karte(ids[0]);
  const ziel = k0 && board(k0.board).spalten.find((s) => s.id === nach);
  if (!ziel) return;
  for (const id of ids) verschieben(id, nach);
  const offen = (stand.reihen[nach] ?? []).length;
  const ueber = ziel.grenze !== undefined && !ziel.erledigt && offen > ziel.grenze;
  stand.meldung = `${ids.length} ${ids.length === 1 ? "Karte" : "Karten"} nach ${ziel.name} verschoben`
    + (ueber ? `; ${ziel.name} ist über der Grenze (${offen}/${ziel.grenze})` : "");
}

export function sammelZuweisen(ids: string[], konto: string): void {
  for (const id of ids) {
    const k = karte(id);
    if (k && !k.zustaendig.includes(konto)) k.zustaendig.push(konto);
  }
  stand.meldung = `${ids.length} ${ids.length === 1 ? "Karte" : "Karten"} zugewiesen`;
}

export function sammelLabel(ids: string[], label: string): void {
  for (const id of ids) {
    const k = karte(id);
    if (k && !k.labels.includes(label)) k.labels.push(label);
  }
  stand.meldung = `Label an ${ids.length} ${ids.length === 1 ? "Karte" : "Karten"} gesetzt`;
}

export function sammelPrioritaet(ids: string[], p: Prioritaet): void {
  for (const id of ids) {
    const k = karte(id);
    if (k) k.prioritaet = p;
  }
  stand.meldung = `Priorität von ${ids.length} ${ids.length === 1 ? "Karte" : "Karten"} gesetzt`;
}

/** Laufende Sitzung buchen (ganze Sekunden) und den Timer beenden */
function buchen(k: Karte): number {
  if (!k.laeuft) return 0;
  const sek = Math.round(laufendSek(k.laeuft.seit));
  k.erfasstSek += sek;
  k.laeuft = undefined;
  return sek;
}

/** Ein Timer je Person: der Start hält deinen laufenden an und bucht ihn; der erste Start setzt den Starttag */
export function timerStarten(id: string): void {
  const k = karte(id);
  if (!k || k.laeuft) return;
  const vorher = stand.karten.find((x) => x.laeuft?.konto === ICH);
  const gebucht = vorher ? buchen(vorher) : 0;
  k.laeuft = { seit: JETZT, konto: ICH };
  k.start ??= HEUTE;
  stand.meldung = vorher ? `Timer läuft auf ${k.schluessel}; ${vorher.schluessel} angehalten, ${dauer(gebucht)} gebucht`
    : `Timer läuft auf ${k.schluessel}`;
}

export function timerAnhalten(id: string): void {
  const k = karte(id);
  if (!k || k.laeuft?.konto !== ICH) return;
  stand.meldung = `${k.schluessel} angehalten, ${dauer(buchen(k))} gebucht`;
}

/** Karten in den Papierkorb ihres Boards, mit allem, was dranhängt; ein laufender Timer bucht vorher */
export function inPapierkorb(ids: string[]): void {
  for (const id of ids) {
    const k = karte(id);
    if (!k) continue;
    buchen(k);
    const reihe = stand.reihen[k.spalte] ?? [];
    uebersicht.papierkorb.unshift({ id: `p-${id}`, board: k.board, art: "karte", karten: [$state.snapshot(k)],
      zeiten: ZEITEINTRAEGE.filter((z) => z.karte === id), stelle: { spalte: k.spalte, platz: reihe.indexOf(id) }, von: ICH, am: JETZT });
    stand.reihen[k.spalte] = reihe.filter((i) => i !== id);
    stand.karten = stand.karten.filter((x) => x.id !== id);
  }
  stand.meldung = `${ids.length} ${ids.length === 1 ? "Karte" : "Karten"} im Papierkorb, mit Zeiten, Kommentaren und Anhängen wiederherstellbar`;
}

/** Wiederherstellen an die alte Stelle: Spalte samt Karten, oder Karte in ihre Spalte am alten Platz (fehlt die Spalte,
 *  in die erste des Boards); Schlüssel, Zeiten, Kommentare, Anhänge und Verknüpfung bleiben, wie sie waren */
export function wiederherstellen(id: string): void {
  const e = uebersicht.papierkorb.find((x) => x.id === id);
  if (!e) return;
  const b = board(e.board);
  const ids = e.karten.map((k) => k.id);
  if (e.art === "spalte" && e.spalte) {
    b.spalten.splice(Math.min(e.stelle.platz, b.spalten.length), 0, $state.snapshot(e.spalte));
    stand.reihen[e.spalte.id] = ids;
  } else {
    const sp = b.spalten.some((s) => s.id === e.stelle.spalte) ? e.stelle.spalte! : b.spalten[0].id;
    const reihe = [...(stand.reihen[sp] ?? [])];
    reihe.splice(Math.min(e.stelle.platz, reihe.length), 0, ...ids);
    stand.reihen[sp] = reihe;
    for (const k of e.karten) k.spalte = sp;
  }
  stand.karten.push(...e.karten.map((k) => $state.snapshot(k)));
  uebersicht.papierkorb = uebersicht.papierkorb.filter((x) => x.id !== id);
  stand.meldung = `${eintragName(e)} wiederhergestellt, an der alten Stelle in ${b.name}`;
}

/** Endgültig entfernen (nur mit dem Recht "Papierkorb leeren"; die Rückfrage steht vorher in der Fläche) */
export function entfernen(ids: string[]): void {
  const weg = uebersicht.papierkorb.filter((x) => ids.includes(x.id));
  uebersicht.papierkorb = uebersicht.papierkorb.filter((x) => !ids.includes(x.id));
  stand.meldung = weg.length === 1 ? `${eintragName(weg[0])} endgültig entfernt` : `${weg.length} Einträge endgültig entfernt`;
}

export function eintragName(e: Geloescht): string {
  return e.art === "spalte" ? `Spalte ${e.spalte?.name}` : e.karten[0].schluessel;
}

/** Eine Karte außerhalb des Boards (Archiv) einzeln nachladen, damit ihr Pfad sie im Detail öffnet */
export function einzelnLaden(k: Karte): void {
  if (!karte(k.id)) stand.karten.push(structuredClone(k));
}

export function gelesen(id: string, wert = true): void {
  const h = uebersicht.hinweise.find((x) => x.id === id);
  if (h) h.gelesen = wert;
}

export function alleGelesen(): void {
  for (const h of uebersicht.hinweise) h.gelesen = true;
}
