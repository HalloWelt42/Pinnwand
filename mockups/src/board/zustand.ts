// Zustände einer Board-Ansicht, die die Entwürfe vorführen (in der App ergeben sie sich aus Bedienung und Daten).

import type { AnsichtVorgabe } from "./ansicht.svelte";

export interface BoardZustand {
  /** Karte im Detail geöffnet */
  detail?: string;
  detailVoll?: boolean;
  bearbeiten?: "beschreibung";
  /** Schnelleingabe in dieser Spalte offen */
  schnell?: string;
  /** Ansichtszustand zum Beginn (Suche, Filter, Sortierung, eingeklappte Spalten, Zeitfenster); gemerkt wird er nicht */
  ansicht?: AnsichtVorgabe;
  /** Filtertafel offen */
  tafel?: boolean;
  /** Menü dieser Spalte offen, mit rueckfrage die Rückfrage zum Löschen */
  menue?: string;
  rueckfrage?: boolean;
  /** Eingabe einer neuen Spalte offen */
  neueSpalte?: boolean;
  /** Kette in Aktion: von dieser Karte auf jene gezogen, der Zeiger über dem Ziel */
  kette?: { quelle: string; ziel: string };
  /** Ziehen in Aktion: welche Karte, wohin */
  ziehen?: { karte: string; nach: string };
  /** Jemand anderes hat gerade diese Karte geändert */
  fremd?: string;
  /** Speichern auf veralteter Fassung abgelehnt */
  konflikt?: boolean;
  /** richtet den Zustand nach dem Ausgangsstand ein, über die Anwendungsfälle (etwa: eine Karte erledigen) */
  vorbereiten?: () => void;
}
