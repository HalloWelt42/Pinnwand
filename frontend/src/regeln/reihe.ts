// Plätze von Karten in einer Spalte als reine Regel, gleich backend/app/anwendung/karten.py (einreihen): Gleitkomma mit
// Raum dazwischen, eine bewegte Karte bekommt einen Platz zwischen ihren Nachbarn. Die Oberfläche nutzt das nur für die
// Vorschau beim Ziehen; wird der Raum zu eng, nummeriert der Server neu und schickt die neuen Plätze.

export const ABSTAND = 1024;

/** Plätze für `n` Karten an `platz` (ohne: am Ende) zwischen den übrigen Karten der Spalte (ihre Reihen, geordnet) */
export function reihenFuer(andere: number[], platz: number | undefined, n: number): number[] {
  const p = platz === undefined ? andere.length : Math.max(0, Math.min(platz, andere.length));
  const vorher = p > 0 ? andere[p - 1] : undefined;
  const nachher = p < andere.length ? andere[p] : undefined;
  const unten = vorher ?? (nachher !== undefined ? nachher - ABSTAND * (n + 1) : 0);
  const oben = nachher ?? unten + ABSTAND * (n + 1);
  const schritt = (oben - unten) / (n + 1);
  return Array.from({ length: n }, (_, i) => unten + schritt * (i + 1));
}

/** Welche eine Karte hat sich bewegt, wenn aus `vorher` die Reihenfolge `nachher` wurde? Die, ohne die beide gleich sind */
export function bewegteKarte(vorher: string[], nachher: string[]): string | undefined {
  const ohne = (liste: string[], id: string) => liste.filter((x) => x !== id).join("\n");
  return nachher.find((id, i) => vorher[i] !== id && ohne(vorher, id) === ohne(nachher, id));
}
