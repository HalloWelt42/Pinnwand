// Beispieldaten als veränderlicher Zustand: Ziehen, Abhaken und Umschalten wirken in den Entwürfen wie in der App,
// bis zum Neuladen der Seite. In der App tritt an diese Stelle der Zustand aus der Schnittstelle und dem Ereignisstrom.

import type { Board, Karte, Konto } from "../modell";
import { BOARDS, GRUPPEN, HEUTE, JETZT, KARTEN, KONTEN } from "./daten";

function anfangsreihen(): Record<string, string[]> {
  const r: Record<string, string[]> = {};
  for (const k of KARTEN) (r[k.spalte] ??= []).push(k.id);
  return r;
}

export const stand = $state({
  boards: structuredClone(BOARDS) as Board[],
  karten: structuredClone(KARTEN) as Karte[],
  gruppen: structuredClone(GRUPPEN),
  /** Reihenfolge der Karten je Spalte */
  reihen: anfangsreihen(),
  /** letzte Meldung unten rechts (Rückgängig, gebuchte Zeit) */
  meldung: "" as string,
});

export function board(id: string): Board {
  return stand.boards.find((b) => b.id === id) ?? stand.boards[0];
}

export function karte(id: string): Karte | undefined {
  return stand.karten.find((k) => k.id === id);
}

export function kartenDerSpalte(spalte: string): Karte[] {
  return (stand.reihen[spalte] ?? []).map((id) => karte(id)).filter((k): k is Karte => k !== undefined);
}

export function konto(id: string): Konto {
  return KONTEN.find((k) => k.id === id) ?? KONTEN[0];
}

/** Gruppenmitglieder einer Karte (ohne sie selbst) */
export function gruppenmitglieder(k: Karte): Karte[] {
  return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id) : [];
}

/** Neue Reihenfolge einer Spalte nach dem Ablegen. Karten, die neu hineinkamen, wechseln die Spalte: Alter beginnt
 *  neu, ihre Gruppe zieht mit (ans Ende); in einer Erledigt-Spalte bekommen sie ihr Abschlussdatum, ein laufender Timer
 *  hält an und bucht (wie verschiebe_karte der alten App, jetzt der einzige Weg). */
export function ablegen(spalte: string, ids: string[], erledigt: boolean): void {
  const neu = ids.filter((id) => karte(id)?.spalte !== spalte);
  stand.reihen[spalte] = ids;
  for (const id of neu) {
    const k = karte(id)!;
    const mit = [k, ...gruppenmitglieder(k).filter((m) => m.spalte !== spalte)];
    for (const x of mit) {
      if (x.id !== k.id) {
        stand.reihen[x.spalte] = (stand.reihen[x.spalte] ?? []).filter((i) => i !== x.id);
        stand.reihen[spalte].push(x.id);
      }
      x.spalte = spalte;
      x.bewegtAm = JETZT;
      x.abgeschlossen = erledigt ? HEUTE : undefined;
      if (erledigt && x.laeuft) {
        x.erfasstSek += 44 * 60;
        x.laeuft = undefined;
        stand.meldung = `${x.schluessel} erledigt: Timer angehalten, 0:44 gebucht`;
      }
    }
    if (mit.length > 1 && !stand.meldung) stand.meldung = `${k.schluessel} verschoben, ${mit.length - 1} verknüpfte Karte zieht mit`;
  }
}
