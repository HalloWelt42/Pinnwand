// Wer angemeldet ist: die Kennung des eigenen Kontos der Pinnwand. Gesetzt beim Laden des Stands, bevor eine Ansicht
// zeichnet; innerhalb einer Sitzung fest (Abmelden baut die Oberfläche neu auf).

export let ICH = "";

export function ichSetzen(id: string): void {
  ICH = id;
}
