// Meldung und Rückgängig für alle Anwendungsfälle: ein Weg. aendern() merkt sich den Zustand, führt die Änderung aus und
// meldet ihr Ergebnis mit Rückgängig, das genau diesen Stand wiederherstellt. In der App ruft Rückgängig den
// Gegen-Anwendungsfall der Schnittstelle; die Ansichten sehen denselben Knopf.

import { DATEN, stand } from "../stand.svelte";

/** Meldung ohne Rückgängig (etwa nach dem Lesen von Hinweisen) */
export function melden(text: string): void {
  stand.meldung = { text };
}

export function meldungSchliessen(): void {
  stand.meldung = null;
}

/** Ändert den Zustand mit Rückgängig. tun() gibt den Text der Meldung zurück, oder null, wenn nichts geschah (dann
 *  bleibt die alte Meldung stehen). Getrennt wirkt nichts: Schreibendes ist gesperrt, die Meldung sagt es. */
export function aendern(tun: () => string | null): boolean {
  if (stand.verbindung === "getrennt") {
    stand.meldung = { text: "Keine Verbindung: Änderungen sind gesperrt, bis die Verbindung wieder steht" };
    return false;
  }
  const vorher = Object.fromEntries(DATEN.map((teil) => [teil, $state.snapshot(stand[teil])]));
  const text = tun();
  if (text === null) return false;
  stand.meldung = {
    text,
    rueckgaengig: () => {
      Object.assign(stand, structuredClone(vorher));
      stand.meldung = null;
    },
  };
  return true;
}
