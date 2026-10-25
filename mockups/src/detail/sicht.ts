// Einen Teil des Kartendetails in Sicht bringen: nur im eigenen Rollfeld des Details, die Seite drumherum bleibt stehen
// (scrollIntoView verschöbe auch Rahmen, die nicht rollen sollen).

const RAND = 16;

/** "anfang": der Teil steht oben; sonst so wenig wie nötig, damit er ganz zu sehen ist */
export function inSicht(teil: HTMLElement | undefined, wo: "anfang" | "nah" = "nah"): void {
  const feld = teil?.closest<HTMLElement>(".pw-detail-inhalt");
  if (!teil || !feld) return;
  const oben = teil.getBoundingClientRect().top - feld.getBoundingClientRect().top + feld.scrollTop - RAND;
  const unten = oben + teil.offsetHeight + 2 * RAND;
  if (wo === "anfang" || oben < feld.scrollTop) feld.scrollTop = oben;
  else if (unten > feld.scrollTop + feld.clientHeight) feld.scrollTop = Math.min(oben, unten - feld.clientHeight);
}
