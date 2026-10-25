// Das Archiv eines Boards seitenweise vom Server: erledigte Karten jenseits der Archivgrenze, neueste zuerst. Der Stand
// enthält sie nie (reine Ladegrenze); eine Ansicht hält ihre geladenen Seiten selbst und holt die nächste auf Wunsch.

import { hole } from "appkern-oberflaeche";
import type { Karte, Kennung } from "../modell";

/** Eine Seite des Archivs mit der Gesamtzahl des Servers */
interface Seite {
  gesamt: number;
  karten: Karte[];
}

export class Archivseiten {
  karten = $state<Karte[]>([]);
  /** Zahl aller archivierten Karten des Boards (vom Server) */
  gesamt = $state(0);
  /** die erste Seite ist da */
  geladen = $state(false);
  laedt = $state(false);
  fehler = $state("");
  readonly boardId: Kennung;
  /** Karten je Seite (Ladeschritt des Boards) */
  readonly schritt: number;

  constructor(boardId: Kennung, schritt: number) {
    this.boardId = boardId;
    this.schritt = schritt;
  }

  get weitere(): number {
    return Math.max(0, this.gesamt - this.karten.length);
  }

  /** Die nächste Seite holen (die erste, wenn noch keine da ist); läuft schon eine Anfrage, geschieht nichts */
  async weiter(): Promise<void> {
    if (this.laedt || (this.geladen && !this.weitere)) return;
    this.laedt = true;
    try {
      const s = await hole<Seite>(`/boards/${this.boardId}/archiv?versatz=${this.karten.length}&grenze=${this.schritt}`);
      const da = new Set(this.karten.map((k) => k.id));
      this.karten = [...this.karten, ...s.karten.filter((k) => !da.has(k.id))];
      this.gesamt = s.gesamt;
      this.geladen = true;
      this.fehler = "";
    } catch (f) {
      this.fehler = f instanceof Error ? f.message : "Das Archiv ließ sich nicht laden";
    } finally {
      this.laedt = false;
    }
  }
}
