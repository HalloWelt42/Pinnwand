// Darstellung der Stände eines Serientags, immer mit Wort und Symbol (nie Farbe allein); eine Stelle für Liste,
// Bearbeiten und Kalender.

import type { VorkommenStand } from "./typen";

export const STAND: Record<VorkommenStand, { text: string; symbol: string; klasse: string; erklaerung: string }> = {
  gezaehlt: { text: "gezählt", symbol: "fa-check", klasse: "fertig", erklaerung: "Vorbei; alle Teilnehmer haben ihre Zeit bestätigt" },
  wartet: { text: "wartet", symbol: "fa-hourglass-half", klasse: "wartet", erklaerung: "Vorbei; mindestens eine vorgebuchte Zeit wartet auf Bestätigung im Nachtrag" },
  verworfen: { text: "fand nicht statt", symbol: "fa-ban", klasse: "aus", erklaerung: "Im Nachtrag verworfen; es zählt keine Zeit" },
  heute: { text: "heute", symbol: "fa-calendar-day", klasse: "", erklaerung: "Die Karte liegt in der Zielspalte; morgen fragt der Nachtrag nach der Zeit" },
  vorgebucht: { text: "vorgebucht", symbol: "fa-thumbtack", klasse: "", erklaerung: "Die Karte liegt unberührt in der Zielspalte; Ändern und Pause passen sie an oder räumen sie" },
  beruehrt: { text: "angefasst, bleibt", symbol: "fa-hand", klasse: "wartet", erklaerung: "Jemand hat die Karte angefasst; Ändern, Pause und Urlaub lassen sie stehen" },
  geplant: { text: "noch nicht vorgebucht", symbol: "fa-calendar", klasse: "aus", erklaerung: "Jenseits des Vorlaufs; die Karte entsteht, sobald der Tag in den Vorlauf rückt" },
  geloescht: { text: "gelöscht, kommt nicht wieder", symbol: "fa-trash-can", klasse: "fehler", erklaerung: "Die Karte wurde bewusst gelöscht; der Tag bleibt gemerkt und wird nie wieder angelegt" },
  ausgelassen: { text: "entfällt", symbol: "fa-calendar-xmark", klasse: "pausiert", erklaerung: "Alle Teilnehmer fehlen an dem Tag (Urlaub, Abwesenheit oder Feiertag)" },
  pausiert: { text: "pausiert", symbol: "fa-circle-pause", klasse: "pausiert", erklaerung: "Die Serie ist pausiert; an diesem Tag entsteht keine Karte" },
};
