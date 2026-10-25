// Regeln der Kürzel eines Boards als reine Funktionen: 2 bis 6 Zeichen, vorne ein Buchstabe, nur Großbuchstaben und
// Ziffern; der Vorschlag kommt aus dem Namen, Umlaute werden ausgeschrieben statt verworfen. Wem ein Kürzel gehört, weiß
// nur der Server (über alle Boards, auch fremde); die Regeln bekommen es als Funktion.

/** Wem ein Kürzel gehört: Name eines sichtbaren Boards, "" für ein fremdes, undefined für niemanden */
export type Inhaber = (kuerzel: string) => string | undefined;

const UMLAUTE: Record<string, string> = { Ä: "AE", Ö: "OE", Ü: "UE" };
const KUERZEL_LAENGE = 6;
/** 2 bis 6 Zeichen, vorne ein Buchstabe, nur Großbuchstaben und Ziffern */
export const KUERZEL_MUSTER = /^[A-Z][A-Z0-9]{1,5}$/;

/** Großbuchstaben, Umlaute ausgeschrieben statt verworfen (ß wird beim Großschreiben zu SS; die alte App machte aus
 *  "Übersicht" das Kürzel "BER", M-02) */
export function ausschreiben(text: string): string {
  return text.toUpperCase().replace(/[ÄÖÜ]/g, (z) => UMLAUTE[z]);
}

/** Eingabe im Kürzelfeld: nur, was ein Kürzel tragen darf */
export function kuerzelSaeubern(eingabe: string): string {
  return ausschreiben(eingabe).replace(/[^A-Z0-9]/g, "").slice(0, KUERZEL_LAENGE);
}

/** Grundform aus dem Namen: ein Wort gibt seine ersten vier Zeichen, mehrere ihre Anfänge (Zahlen ganz) */
function grundform(name: string): string {
  const w = ausschreiben(name).split(/[^A-Z0-9]+/).filter(Boolean);
  if (!w.length) return "";
  let k = w.length === 1 ? w[0].slice(0, 4) : w.slice(0, 4).map((x) => (/^\d+$/.test(x) ? x : x[0])).join("").slice(0, KUERZEL_LAENGE);
  if (k.length < 2) k = w[0].slice(0, 4);
  return /^\d/.test(k) ? ("B" + k).slice(0, KUERZEL_LAENGE) : k;
}

function abwandlungen(k: string, inhaber: Inhaber): string[] {
  const frei: string[] = [];
  for (let n = 2; n <= 9 && frei.length < 3; n++) {
    const v = k.slice(0, KUERZEL_LAENGE - 1) + n;
    if (inhaber(v) === undefined) frei.push(v);
  }
  return frei;
}

/** Vorschlag aus dem Namen, schon frei */
export function kuerzelVorschlag(name: string, inhaber: Inhaber): string {
  const k = grundform(name);
  if (!k || inhaber(k) === undefined) return k;
  return abwandlungen(k, inhaber)[0] ?? k;
}

export interface KuerzelPruefung {
  stand: "leer" | "form" | "vergeben" | "frei";
  text: string;
  /** freie Kürzel zum Anklicken, wenn das gewählte vergeben ist */
  frei: string[];
}

export function kuerzelPruefen(k: string, name: string, inhaber: Inhaber): KuerzelPruefung {
  if (!k) return { stand: "leer", text: "Ein Kürzel braucht jedes Board, es steht vor jeder Kartennummer.", frei: [] };
  if (!KUERZEL_MUSTER.test(k)) return { stand: "form", text: "2 bis 6 Zeichen, vorne ein Buchstabe.", frei: [] };
  const wer = inhaber(k);
  if (wer === undefined) return { stand: "frei", text: `Frei. Karten heißen ${k}-1, ${k}-2 und so weiter.`, frei: [] };
  const aus = kuerzelVorschlag(name, inhaber);
  const frei = [...new Set([...(aus && aus !== k ? [aus] : []), ...abwandlungen(k, inhaber)])].slice(0, 3);
  return { stand: "vergeben", frei,
           text: wer ? `${k} ist schon vergeben, an das Board ${wer}.` : `${k} ist schon vergeben, an ein Board, das du nicht siehst.` };
}

/** Kürzel einer Person aus ihrem Namen: Anfänge von Vor- und Nachname (Umlaute ausgeschrieben) */
export function personKuerzel(name: string): string {
  const w = ausschreiben(name).split(/[^A-Z]+/).filter(Boolean);
  return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] ?? "?").slice(0, 2)) || "?";
}
