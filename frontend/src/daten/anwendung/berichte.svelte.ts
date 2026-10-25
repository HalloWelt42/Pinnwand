// Anwendungsfälle des Moduls Berichte über den Server: die Vorschau genau dessen, was die Datei enthält, und das
// Erstellen der Datei in der Ablage der Pinnwand (Kellerwolke, Ordner Berichte). Den Inhalt rechnet nur der Server.

import { hole, json } from "appkern-oberflaeche";
import type { Bericht, BerichtAuswahl, BerichtVorschau } from "../../modell";
import { stand } from "../stand.svelte";
import { aendern, melden, senden } from "./meldung.svelte";

/** Vorschau der Auswahl; ohne Ergebnis, wenn der Server sie ablehnt (der Grund steht dann in der Meldung) */
export async function berichtVorschau(a: BerichtAuswahl): Promise<BerichtVorschau | null> {
  try {
    return await hole<BerichtVorschau>("/berichte/vorschau", { method: "POST", ...json(a) });
  } catch (f) {
    melden(f instanceof Error ? f.message : "Die Vorschau ging nicht");
    return null;
  }
}

/** Datei erstellen und ablegen; Ergebnis: der neue Eintrag in der Liste */
export async function berichtErstellen(a: BerichtAuswahl): Promise<Bericht | undefined> {
  const antwort = await aendern(() => senden("/berichte", a));
  const neu = antwort?.geaendert.find((g) => g.tabelle === "berichte" && g.daten);
  return neu ? stand.berichte.find((b) => b.id === neu.id) : undefined;
}

/** Adresse zum Herunterladen eines eigenen Berichts (über das Inhalts-Cookie der Anmeldung) */
export function berichtAdresse(b: Bericht): string {
  return `/api/v1/inhalt/berichte/${encodeURIComponent(b.id)}`;
}
