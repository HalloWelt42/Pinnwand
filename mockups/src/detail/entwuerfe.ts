// Vorgeführte Zustände des Kartendetails (?entwurf=...): nur Zustand der Oberfläche (offener Editor, Reiter, Suche,
// Wahl aus der Kellerwolke), keine Daten. Die Galerie führt sie unter den Zuständen des Boards (zustaende.ts). Dazu, was
// in der App vom Server käme: die abgelehnte Änderung beim Konflikt und ein Vorschlag der Leitstelle.

export interface DetailZustand {
  /** Speichern auf veralteter Fassung wurde abgelehnt (Rückfrage offen) */
  konflikt?: boolean;
  beschreibung?: "ort" | "vollbild";
  notizen?: "vollbild";
  reiter?: "verlauf";
  /** Text im Suchfeld der verknüpften Aufgaben */
  verknuepfen?: string;
  /** Wahl aus der Kellerwolke offen */
  kellerwolke?: boolean;
}

export const DETAIL_ENTWUERFE: Record<string, DetailZustand> = {
  bearbeiten: { beschreibung: "ort" },
  konflikt: { konflikt: true },
  notizen: { notizen: "vollbild" },
  verlauf: { reiter: "verlauf" },
  verknuepfen: { verknuepfen: "Serie" },
  kellerwolke: { kellerwolke: true },
};

/** Konflikt (?entwurf=konflikt): deine Änderung, die der Server auf veralteter Fassung abgelehnt hat; die Fassung der
 *  anderen Person ist der gespeicherte Stand der Karte */
export const ABGELEHNT = { von: "k-anna", aenderung: { faellig: "2026-10-29" } };

/** Vorschlag der Leitstelle (Modul KI) an einer Karte: Zusammenfassung aus Beschreibung, Notizen und Kommentaren */
export const VORSCHLAG = {
  karte: "c-131",
  text: "120 Gehäuse RAL 7035 für Elektro Brandt, Lieferung KW 50, erste 40 Stück bis KW 48. Offen: Preis der Pulverbeschichtung (Antwort am 28.10.), dann Angebot schreiben.",
};
