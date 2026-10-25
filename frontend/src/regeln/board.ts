// Regeln eines Boards als reine Funktionen: Rechte aus der Rolle, Alterung der Karten im Status, Zeitfenster der
// Erledigt-Spalten. Der Server prüft dieselben Rechte bei jedem Weg; die Oberfläche blendet nur aus, was nicht geht.

import type { Board, BoardEinstellungen, Karte, Kennung, ModulKennung, Zeitfenster } from "../modell";
import { montagVon, plusTage, tageZwischen } from "./tage";

/** Rechte jedes Moduls, gleich backend/app/regeln/board.py; ein Recht eines abgeschalteten Moduls gilt nicht */
export const RECHTE_DER_MODULE: Record<string, string[]> = {
  kern: ["board.verwalten", "mitglieder.verwalten", "karten.anlegen", "karten.bearbeiten", "karten.verschieben", "karten.loeschen",
         "kommentieren", "papierkorb.leeren"],
  zeiterfassung: ["zeit.buchen", "zeit.andere.sehen", "zeit.andere.bearbeiten"],
  arbeitszeit: ["abwesenheit.sehen"],
  serien: ["serien.verwalten"],
  berichte: ["berichte.erstellen"],
};

export function modulVon(recht: string): string {
  return Object.entries(RECHTE_DER_MODULE).find(([, rechte]) => rechte.includes(recht))?.[0] ?? "kern";
}

/** Ist ein Modul in diesem Board an? Nur, wenn diese Fassung der Pinnwand es anbietet (`moduleDa`) und das Board es
 *  eingeschaltet hat */
export function modulAn(b: Board, modul: ModulKennung, moduleDa: readonly string[]): boolean {
  return moduleDa.includes(modul) && !!b.module[modul];
}

/** Hat die Person in diesem Board das Recht (über ihre Rolle)? Rechte abgeschalteter oder nicht angebotener Module
 *  gelten nicht (wie der Server). */
export function hatRecht(b: Board, recht: string, konto: Kennung, moduleDa: readonly string[]): boolean {
  const modul = modulVon(recht);
  if (modul !== "kern" && !modulAn(b, modul as ModulKennung, moduleDa)) return false;
  const rolle = b.rollen.find((r) => r.id === b.mitglieder.find((m) => m.konto === konto)?.rolle);
  return rolle?.rechte.includes(recht) ?? false;
}

export type Alterung = "flaeche" | "warnung" | "gefahr";

/** Stufe der Sanduhr nach Tagen im Status; 0 schaltet eine Stufe aus, die Stufen sind unabhängig */
export function alterung(tage: number, e: BoardEinstellungen): Alterung {
  if (e.alterungGefahr > 0 && tage >= e.alterungGefahr) return "gefahr";
  if (e.alterungWarnung > 0 && tage >= e.alterungWarnung) return "warnung";
  return "flaeche";
}

/** Liegt eine Karte so lange im Status, dass sie als liegengeblieben gilt (Gefahr, sonst Warnung)? */
export function liegengeblieben(tage: number, e: BoardEinstellungen): boolean {
  return alterung(tage, e) === "gefahr";
}

/** Erster Tag eines Zeitfensters (einschließlich), gezählt von heute; "alle": ohne Grenze */
export function fensterAb(f: Zeitfenster, heute: string): string {
  switch (f) {
    case "heute": return heute;
    case "gestern": return plusTage(heute, -1);
    case "woche": return montagVon(heute);
    case "monat": return heute.slice(0, 8) + "01";
    case "jahr": return heute.slice(0, 5) + "01-01";
    case "alle": return "";
  }
}

/** Steht eine erledigte Karte im Zeitfenster ihrer Spalte? Ältere als die Archivgrenze nie (die liegen im Archiv). */
export function imFenster(k: Karte, f: Zeitfenster, e: BoardEinstellungen, heute: string): boolean {
  const am = k.abgeschlossen ?? k.bewegtAm.slice(0, 10);
  if (tageZwischen(am, heute) > e.archivTage) return false;
  return am >= fensterAb(f, heute) && (f !== "gestern" || am === plusTage(heute, -1));
}

/** Liegt eine erledigte Karte im Archiv (Abschluss älter als die Archivgrenze)? */
export function imArchiv(k: Karte, e: BoardEinstellungen, heute: string): boolean {
  return !!k.abgeschlossen && tageZwischen(k.abgeschlossen, heute) > e.archivTage;
}

/** Erlaubte Werte der Einstellungen eines Boards und der Grenze einer Spalte (ganze Zahlen, einschließlich) */
export const EINSTELLUNG_GRENZEN = {
  alterung: [0, 365],
  ladeschritt: [1, 500],
  archivTage: [1, 100000],
  grenze: [1, 999],
} as const;
