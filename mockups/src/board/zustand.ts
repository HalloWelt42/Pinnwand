// Zustände einer Board-Ansicht, die die Entwürfe vorführen (in der App ergeben sie sich aus Bedienung und Daten).

export interface BoardZustand {
  /** Karte im Detail geöffnet */
  detail?: string;
  detailVoll?: boolean;
  bearbeiten?: "beschreibung";
  /** Schnelleingabe in dieser Spalte offen */
  schnell?: string;
  /** Suche oder Filter aktiv: Ziehen pausiert, Erledigte werden ohne Zeitfenster durchsucht */
  filter?: string;
  /** Ziehen in Aktion: welche Karte, wohin */
  ziehen?: { karte: string; nach: string };
  /** Jemand anderes hat gerade diese Karte geändert */
  fremd?: string;
  /** Speichern auf veralteter Fassung abgelehnt */
  konflikt?: boolean;
  meldung?: string;
}
