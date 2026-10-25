// Vorschläge der KI an der Karte über den Server (Modul ki): Holen schreibt nichts; übernommen wird über die gewohnten
// Anwendungsfälle mit Rückgängig (bearbeiten, mehrereAnlegen). Ein Vorschlagslauf hält den Zustand einer Anfrage für die
// Vorschau: läuft, Grund der Ablehnung (Leitstelle kann nicht, Recht fehlt) oder das Ergebnis. Abbrechen beendet nur
// das Warten hier; ein neuer Lauf ersetzt den alten.

import { hole, json } from "appkern-oberflaeche";
import type { Board, Kartenentwurf, Kennung } from "../../modell";
import { modulAn } from "../../regeln/board";
import { stand } from "../stand.svelte";

/** Gibt es in diesem Board Vorschläge? Modul an und die Leitstelle eingerichtet */
export function kiDa(b: Board): boolean {
  return stand.kiBereit && modulAn(b, "ki", stand.moduleDa);
}

/** Ein Modell rechnet oft länger als die übliche Zeitgrenze einer Anfrage (beim ersten Laden Minuten): ohne Grenze;
 *  abbrechen kann die Person im Kasten des Vorschlags */
function fragen<T>(pfad: string, signal: AbortSignal, daten: unknown = {}): Promise<T> {
  return hole<T>(pfad, { method: "POST", ...json(daten), signal, zeitgrenzeMs: 0 });
}

export const zusammenfassungHolen = (karteId: Kennung) => (signal: AbortSignal) =>
  fragen<{ text: string }>(`/karten/${karteId}/ki/zusammenfassung`, signal);

export const punkteHolen = (karteId: Kennung) => (signal: AbortSignal) =>
  fragen<{ punkte: string[] }>(`/karten/${karteId}/ki/checkliste`, signal);

export const labelsHolen = (karteId: Kennung) => (signal: AbortSignal) =>
  fragen<{ labels: Kennung[] }>(`/karten/${karteId}/ki/labels`, signal);

export const kartenAusTextHolen = (boardId: Kennung, text: string) => (signal: AbortSignal) =>
  fragen<{ karten: Kartenentwurf[] }>(`/boards/${boardId}/ki/karten`, signal, { text });

export const notizHolen = (karteId: Kennung, markeId: Kennung) => (signal: AbortSignal) =>
  fragen<{ text: string }>(`/karten/${karteId}/transkripte/${markeId}/ki/notiz`, signal);

export class Vorschlagslauf<T> {
  laeuft = $state(false);
  grund = $state("");
  wert = $state<T | null>(null);
  #steuerung: AbortController | null = null;

  /** Ist der Kasten zu sehen (rechnet, abgelehnt oder mit Ergebnis)? */
  get offen(): boolean {
    return this.laeuft || !!this.grund || this.wert !== null;
  }

  /** Fragt neu; Ergebnis: ob ein Vorschlag da ist (nicht abgebrochen, nicht abgelehnt) */
  async holen(frage: (signal: AbortSignal) => Promise<T>): Promise<boolean> {
    this.schliessen();
    const steuerung = new AbortController();
    this.#steuerung = steuerung;
    this.laeuft = true;
    try {
      const wert = await frage(steuerung.signal);
      if (steuerung.signal.aborted) return false;
      this.wert = wert;
      return true;
    } catch (f) {
      if (!steuerung.signal.aborted) this.grund = f instanceof Error ? f.message : "Der Vorschlag ging nicht";
      return false;
    } finally {
      if (this.#steuerung === steuerung) {
        this.#steuerung = null;
        this.laeuft = false;
      }
    }
  }

  /** Warten beenden und den Kasten schließen */
  schliessen(): void {
    this.#steuerung?.abort();
    this.#steuerung = null;
    this.laeuft = false;
    this.grund = "";
    this.wert = null;
  }
}
