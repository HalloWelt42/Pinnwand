// Wege der Telefonansicht: dieselben Pfade wie am Rechner, dazu der Zusatz ?geraet=telefon (in der App wählt das Gerät
// die Ansicht, der Zusatz entfällt dort). Weitere Zusätze tragen, woher man kam oder was vorbelegt ist.

export function telPfad(pfad: string, zusatz: Record<string, string> = {}): string {
  const s = new URLSearchParams(zusatz);
  s.set("geraet", "telefon");
  return `${pfad}?${s}`;
}
