// Die Uhr der Oberfläche: Ortszeit wie der Server sie schreibt ("2026-10-27T10:42:00", Tage "2026-10-27"). Ansichten
// lesen `uhr.jetzt` und `uhr.heute` und rechnen damit neu, wenn die Uhr weiterspringt (auch über Mitternacht). Solange
// dein Timer läuft, springt sie jede Sekunde, damit seine Zeit sichtbar mitläuft (M-85); wann das gilt, sagt die
// Oberfläche über `sekundentakt`.

/** Grundtakt: reicht für "vor 5 Minuten" und den Tageswechsel */
const TAKT_MS = 10_000;
/** Takt, solange dein Timer läuft */
const SEKUNDENTAKT_MS = 1000;

function ortszeit(d = new Date()): string {
  const z = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}T${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
}

const anfang = ortszeit();
export const uhr = $state({ jetzt: anfang, heute: anfang.slice(0, 10) });

/** Der laufende Takt (leer: die Uhr steht) und ob er sekundengenau ist */
let takt: ReturnType<typeof setInterval> | undefined;
let sekundengenau = false;
let gestartet = false;

function stellen(): void {
  const j = ortszeit();
  uhr.jetzt = j;
  if (uhr.heute !== j.slice(0, 10)) uhr.heute = j.slice(0, 10);
}

function taktSetzen(): void {
  clearInterval(takt);
  takt = gestartet ? setInterval(stellen, sekundengenau ? SEKUNDENTAKT_MS : TAKT_MS) : undefined;
}

/** Startet die Uhr. Ergebnis: zum Anhalten (Abmelden, Verlassen der Seite) */
export function uhrStarten(): () => void {
  gestartet = true;
  stellen();
  taktSetzen();
  return () => {
    gestartet = false;
    taktSetzen();
  };
}

/** Sekundentakt an (dein Timer läuft) oder zurück auf den Grundtakt */
export function sekundentakt(an: boolean): void {
  if (sekundengenau === an) return;
  sekundengenau = an;
  stellen();
  taktSetzen();
}
