// Meldung und Rückgängig für alle Anwendungsfälle: ein Weg. aendern() schickt die Änderung an den Server, übernimmt die
// neuen Stände aus der Antwort und meldet ihr Ergebnis; Rückgängig ruft den Rückweg des Servers. Lehnt der Server ab,
// steht sein Grund in der Meldung. Wo die Oberfläche vorab zeigen muss, was gleich gilt (Ziehen einer Karte), tut
// `vorab` das lokal; die Antwort ersetzt es, eine Ablehnung lädt den Stand neu.

import { ApiFehler, hole, json } from "appkern-oberflaeche";
import { laden, stand, uebernehmen, type Geaendert } from "../stand.svelte";

/** Antwort jeder Änderung des Servers */
export interface Antwort {
  meldung: string | null;
  rueckgaengig: string | null;
  geaendert: Geaendert[];
}

export interface Aenderung {
  /** lokal vorab anwenden, was der Server gleich bestätigt */
  vorab?: () => void;
  /** der Server lehnt ab, weil inzwischen jemand anders dasselbe geändert hat (409); ohne: nur die Meldung */
  beiKonflikt?: () => void;
}

/** Meldung ohne Rückgängig (Ereignisse von außen, etwa eine Änderung durch eine andere Person) */
export function melden(text: string): void {
  stand.meldung = { text };
}

export function meldungSchliessen(): void {
  stand.meldung = null;
}

/** POST an einen Weg der Pinnwand (unter /api/v1) */
export function senden(pfad: string, daten: unknown = {}): Promise<Antwort> {
  return hole<Antwort>(pfad, { method: "POST", ...json(daten) });
}

/** PATCH an einen Weg der Pinnwand (unter /api/v1): nur die genannten Teile ändern, null leert einen Teil */
export function teilweiseAn(pfad: string, daten: Record<string, unknown>): Promise<Antwort> {
  return hole<Antwort>(pfad, { method: "PATCH", ...json(daten) });
}

/** DELETE an einen Weg der Pinnwand (unter /api/v1), ohne Inhalt */
export function loeschenAn(pfad: string): Promise<Antwort> {
  return hole<Antwort>(pfad, { method: "DELETE" });
}

function grund(f: unknown): string {
  return f instanceof ApiFehler || f instanceof Error ? f.message : "Das ging nicht";
}

async function rueckgaengig(journal: string): Promise<void> {
  stand.meldung = null;
  await aendern(() => senden(`/rueckgaengig/${journal}`));
}

/** Ändert über den Server. Getrennt wirkt nichts: Schreibendes ist gesperrt, die Meldung sagt es. Ergebnis: die Antwort,
 *  oder null, wenn es nicht wirkte. Ohne Meldung des Servers (nichts geschah oder Kleines) bleibt die alte stehen. */
export async function aendern(anfrage: () => Promise<Antwort>, { vorab, beiKonflikt }: Aenderung = {}): Promise<Antwort | null> {
  if (stand.verbindung === "getrennt") {
    stand.meldung = { text: "Keine Verbindung: Änderungen sind gesperrt, bis die Verbindung wieder steht" };
    return null;
  }
  vorab?.();
  try {
    const a = await anfrage();
    uebernehmen(a.geaendert);
    if (a.meldung) {
      const journal = a.rueckgaengig;
      stand.meldung = { text: a.meldung, rueckgaengig: journal ? () => void rueckgaengig(journal) : undefined };
    }
    return a;
  } catch (f) {
    if (vorab) void laden();
    if (beiKonflikt && f instanceof ApiFehler && f.status === 409) beiKonflikt();
    else stand.meldung = { text: grund(f) };
    return null;
  }
}
