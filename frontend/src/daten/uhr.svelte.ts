// Die Uhr der Oberfläche: Ortszeit wie der Server sie schreibt ("2026-10-27T10:42:00", Tage "2026-10-27"). Ansichten
// lesen `uhr.jetzt` und `uhr.heute` und rechnen damit neu, wenn die Uhr weiterspringt (auch über Mitternacht).

/** So oft springt die Uhr weiter; reicht für "vor 5 Minuten" und den Tageswechsel */
const TAKT_MS = 10_000;

function ortszeit(d = new Date()): string {
  const z = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}T${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
}

const anfang = ortszeit();
export const uhr = $state({ jetzt: anfang, heute: anfang.slice(0, 10) });

function stellen(): void {
  const j = ortszeit();
  uhr.jetzt = j;
  if (uhr.heute !== j.slice(0, 10)) uhr.heute = j.slice(0, 10);
}

export function uhrStarten(): () => void {
  stellen();
  const t = setInterval(stellen, TAKT_MS);
  return () => clearInterval(t);
}
