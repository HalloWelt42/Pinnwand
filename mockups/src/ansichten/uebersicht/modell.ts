// Typen des Bereichs Übersicht, die das gemeinsame Modell (src/modell.ts) nicht hat: Einträge des Papierkorbs und die
// Gruppen der Ansicht Heute. In der App kommen beide aus der Schnittstelle.

import type { Board, Karte, Kennung, Spalte, Zeiteintrag } from "../../modell";

/** Ein Eintrag im Papierkorb eines Boards: eine Karte oder eine Spalte mit ihren Karten, samt allem, was daran hängt.
 *  Wiederherstellen bringt ihn an seine alte Stelle zurück (Schlüssel, Zeiten, Kommentare, Anhänge, Verknüpfungen). */
export interface Geloescht {
  id: Kennung;
  board: Kennung;
  art: "karte" | "spalte";
  /** die gelöschte Spalte (nur bei art "spalte") */
  spalte?: Spalte;
  /** die Karten des Eintrags: eine bei einer Karte, alle der Spalte bei einer Spalte */
  karten: Karte[];
  /** die Zeiteinträge dieser Karten; sie liegen mit im Papierkorb */
  zeiten: Zeiteintrag[];
  /** alte Stelle: bei einer Karte Spalte und Platz darin, bei einer Spalte ihr Platz in der Spaltenfolge (ab 0) */
  stelle: { spalte?: Kennung; platz: number };
  von: Kennung;
  am: string;
}

/** Eine Karte in Heute mit ihrem Board */
export interface HeuteEintrag {
  karte: Karte;
  board: Board;
}
