// Meldung und Rückgängig für alle Anwendungsfälle: ein Weg. aendern() merkt sich den Zustand, führt die Änderung aus und
// meldet ihr Ergebnis mit Rückgängig, das genau diesen Stand wiederherstellt. In der App ruft Rückgängig den
// Gegen-Anwendungsfall der Schnittstelle; die Ansichten sehen denselben Knopf.

import { DATEN, stand } from "../stand.svelte";

export interface Aenderung {
  /** Rückgängig anbieten (nein bei Endgültigem wie dem Leeren des Papierkorbs) */
  rueckgaengig?: boolean;
  /** eine Meldung zeigen (nein bei Kleinem wie einem gelesenen Hinweis) */
  melden?: boolean;
}

/** Meldung ohne Rückgängig (Ereignisse von außen, etwa eine Änderung durch eine andere Person) */
export function melden(text: string): void {
  stand.meldung = { text };
}

export function meldungSchliessen(): void {
  stand.meldung = null;
}

/** Ändert den Zustand. tun() gibt den Text der Meldung zurück, oder null, wenn nichts geschah (dann bleibt die alte
 *  Meldung stehen). Getrennt wirkt nichts: Schreibendes ist gesperrt, die Meldung sagt es. Ergebnis: ob es wirkte. */
export function aendern(tun: () => string | null, { rueckgaengig = true, melden = true }: Aenderung = {}): boolean {
  if (stand.verbindung === "getrennt") {
    stand.meldung = { text: "Keine Verbindung: Änderungen sind gesperrt, bis die Verbindung wieder steht" };
    return false;
  }
  const vorher = rueckgaengig ? Object.fromEntries(DATEN.map((teil) => [teil, $state.snapshot(stand[teil])])) : null;
  const text = tun();
  if (text === null) return false;
  if (!melden) return true;
  stand.meldung = {
    text,
    rueckgaengig: vorher ? () => {
      Object.assign(stand, structuredClone(vorher));
      stand.meldung = null;
    } : undefined,
  };
  return true;
}
