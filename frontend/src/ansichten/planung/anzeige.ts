// Darstellung der Serien für Menschen: Stand eines Serientags (immer Wort und Symbol, nie Farbe allein) und der Rhythmus
// als Satz ohne Abkürzungen. Eine Stelle für Liste, Bearbeiten und Kalender.

import type { Serie } from "../../modell";
import type { VorkommenStand } from "../../regeln/serien";
import { TAGE_LANG } from "../../regeln/tage";

export const STAND: Record<VorkommenStand, { text: string; symbol: string; klasse: string; erklaerung: string }> = {
  gezaehlt: { text: "gezählt", symbol: "fa-check", klasse: "fertig", erklaerung: "Vorbei; alle Teilnehmer haben ihre Zeit bestätigt" },
  wartet: { text: "wartet", symbol: "fa-hourglass-half", klasse: "wartet", erklaerung: "Vorbei; mindestens eine vorgebuchte Zeit wartet auf Bestätigung im Nachtrag" },
  verworfen: { text: "fand nicht statt", symbol: "fa-ban", klasse: "aus", erklaerung: "Im Nachtrag verworfen; es zählt keine Zeit" },
  heute: { text: "heute", symbol: "fa-calendar-day", klasse: "", erklaerung: "Die Karte liegt in der Zielspalte; morgen fragt der Nachtrag nach der Zeit" },
  vorgebucht: { text: "vorgebucht", symbol: "fa-thumbtack", klasse: "", erklaerung: "Die Karte liegt unberührt in der Zielspalte; Ändern und Pause passen sie an oder nehmen sie zurück" },
  beruehrt: { text: "angefasst, bleibt", symbol: "fa-hand", klasse: "wartet", erklaerung: "Jemand hat die Karte angefasst; Ändern, Pause und Urlaub lassen sie stehen" },
  geplant: { text: "noch nicht vorgebucht", symbol: "fa-calendar", klasse: "aus", erklaerung: "Jenseits des Vorlaufs; die Karte entsteht, sobald der Tag in den Vorlauf rückt" },
  geloescht: { text: "gelöscht, kommt nicht wieder", symbol: "fa-trash-can", klasse: "fehler", erklaerung: "Der Tag wurde bewusst gelöscht; er bleibt gemerkt und wird nie wieder angelegt" },
  ausgelassen: { text: "entfällt", symbol: "fa-calendar-xmark", klasse: "pausiert", erklaerung: "Alle Teilnehmer fehlen an dem Tag (Abwesenheit oder Feiertag)" },
  pausiert: { text: "pausiert", symbol: "fa-circle-pause", klasse: "pausiert", erklaerung: "Die Serie ist pausiert; an diesem Tag entsteht keine Karte" },
};

/** "werktags", "wöchentlich montags und mittwochs", "monatlich am 30.", "monatlich am letzten Werktag" */
export function rhythmusText(s: Serie): string {
  switch (s.rhythmus) {
    case "taeglich": return s.wochenendenUeberspringen ? "täglich außer am Wochenende" : "täglich";
    case "werktags": return "werktags";
    case "woechentlich": {
      const tage = [...(s.tage ?? [])].sort((a, b) => ((a + 6) % 7) - ((b + 6) % 7)).map((t) => TAGE_LANG[t].toLowerCase() + "s");
      return "wöchentlich " + (tage.length > 1 ? `${tage.slice(0, -1).join(", ")} und ${tage[tage.length - 1]}` : tage[0] ?? "");
    }
    case "monatlich":
      if (s.monatsregel === "erster-werktag") return "monatlich am ersten Werktag";
      if (s.monatsregel === "letzter-werktag") return "monatlich am letzten Werktag";
      return `monatlich am ${s.monatstag ?? Number(s.ab.slice(8, 10))}.`;
  }
}
