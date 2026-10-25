// Inhalt eines Berichts aus der Auswahl, unabhängig vom Format (PDF, Tabelle, Markdown): Abschnitte mit Spalten, Zeilen
// und Summe. Zeiten kommen aus den Zeiteinträgen (jede Sekunde zählt einmal), Soll und Abwesenheit aus dem Zeitkonto.
// In der App rechnet das der Dienst des Moduls Berichte; die Vorschau zeigt genau, was die Datei enthält.

import { darf, istAm, kartenName, sollTag, zeitDerKarte } from "../../beispiel/abfragen";
import { HEUTE, ICH } from "../../beispiel/daten";
import { datum, dauer, differenz, spanne } from "../../beispiel/format";
import { board, karte, konto, stand } from "../../beispiel/stand.svelte";
import type { BerichtArt, BerichtFormat } from "../../modell";
import { artName, fassungAm } from "../../regeln/arbeitszeit";
import { tageVon } from "../../regeln/tage";

/** Inhalt eines Berichts unabhängig vom Format: Abschnitte mit Spalten, Zeilen und Summe (wie der Dienst der alten App) */
export interface BerichtInhalt {
  titel: string;
  zeitraum: string;
  abschnitte: { titel: string; spalten: string[]; zeilen: string[][]; summe?: string[]; fuss?: string }[];
}

export interface Auswahl {
  art: BerichtArt;
  von: string;
  bis: string;
  boards: string[];
  personen: string[];
  format: BerichtFormat;
}

export const ARTNAMEN: Record<BerichtArt, string> = {
  stundennachweis: "Stundennachweis je Person",
  board: "Zeiten je Board und Karte",
  erledigt: "Erledigte Karten",
};

function nachweis(a: Auswahl): BerichtInhalt {
  const abschnitte = a.personen.map((p) => {
    const zeilen: string[][] = [];
    let s = 0, i = 0;
    for (const t of tageVon(a.von, a.bis)) {
      const sl = sollTag(p, t);
      if (!sl) continue;
      const ist = istAm(p, t);
      if (!sl.sollSek && !ist && !sl.feiertag && !sl.abwesenheit) continue;
      s += sl.sollSek; i += ist;
      const karten = [...new Set(stand.zeiteintraege.filter((e) => e.konto === p && e.datum === t).map((e) => kartenName(e.karte).schluessel))].join(", ");
      const hinweis = sl.feiertag ?? (sl.abwesenheit ? artName(sl.abwesenheit) : sl.regel ?? "");
      zeilen.push([datum(t, true), dauer(sl.sollSek), dauer(ist), differenz(ist - sl.sollSek), karten, hinweis]);
    }
    return { titel: konto(p).name, spalten: ["Tag", "Soll", "Ist", "Differenz", "Karten", "Hinweis"], zeilen,
             summe: ["Summe", dauer(s), dauer(i), differenz(i - s), "", ""],
             fuss: "Ist ist die gebuchte Zeit aus allen Boards; Soll aus dem Zeitkonto mit Feiertagen und Abwesenheiten." };
  });
  return { titel: ARTNAMEN.stundennachweis, zeitraum: spanne(a.von, a.bis), abschnitte };
}

function jeKarte(a: Auswahl): BerichtInhalt {
  const abschnitte = a.boards.map((bid) => {
    const b = board(bid);
    const je = new Map<string, { sek: number; wer: Set<string> }>();
    for (const p of b.mitglieder.map((m) => m.konto)) {
      if (a.personen.length && !a.personen.includes(p)) continue;
      for (const e of stand.zeiteintraege.filter((x) => x.konto === p && x.datum >= a.von && x.datum <= a.bis)) {
        if (karte(e.karte)?.board !== bid) continue;
        const x = je.get(e.karte) ?? { sek: 0, wer: new Set<string>() };
        x.sek += e.sekunden; x.wer.add(konto(p).kuerzel);
        je.set(e.karte, x);
      }
    }
    const zeilen = [...je.entries()].sort((x, y) => y[1].sek - x[1].sek).map(([id, x]) => {
      const k = karte(id)!;
      return [k.schluessel, k.titel, [...x.wer].join(", "), dauer(x.sek), k.schaetzungMin ? dauer(k.schaetzungMin * 60) : ""];
    });
    const summe = [...je.values()].reduce((s, x) => s + x.sek, 0);
    return { titel: b.name, spalten: ["Schlüssel", "Karte", "Personen", "Zeit", "Schätzung"], zeilen, summe: ["", "Summe", "", dauer(summe), ""],
             fuss: "Zeiten aus den Einträgen im Zeitraum; verknüpfte Karten zählen jede Sekunde einmal." };
  });
  return { titel: ARTNAMEN.board, zeitraum: spanne(a.von, a.bis), abschnitte };
}

function erledigt(a: Auswahl): BerichtInhalt {
  const alle = stand.karten;
  const abschnitte = a.boards.map((bid) => {
    const b = board(bid);
    const karten = alle.filter((k) => k.board === bid && k.abgeschlossen && k.abgeschlossen >= a.von && k.abgeschlossen <= a.bis
      && (!a.personen.length || k.zustaendig.some((p) => a.personen.includes(p))))
      .sort((x, y) => x.abgeschlossen!.localeCompare(y.abgeschlossen!));
    return { titel: b.name, spalten: ["Schlüssel", "Karte", "Erledigt", "Zuständig", "Zeit"],
             zeilen: karten.map((k) => [k.schluessel, k.titel, datum(k.abgeschlossen!, true), k.zustaendig.map((p) => konto(p).kuerzel).join(", "), dauer(zeitDerKarte(k.id, false))]),
             summe: ["", `${karten.length} Karten`, "", "", dauer(karten.reduce((s, k) => s + zeitDerKarte(k.id, false), 0))] };
  });
  return { titel: ARTNAMEN.erledigt, zeitraum: spanne(a.von, a.bis), abschnitte };
}

export function inhalt(a: Auswahl): BerichtInhalt {
  return a.art === "stundennachweis" ? nachweis(a) : a.art === "board" ? jeKarte(a) : erledigt(a);
}

/** Der Bericht als Markdown, genau so, wie die Datei ihn enthält */
export function alsMarkdown(b: BerichtInhalt): string {
  const teile = [`# ${b.titel}`, "", `Zeitraum: ${b.zeitraum}`, ""];
  for (const s of b.abschnitte) {
    teile.push(`## ${s.titel}`, "", `| ${s.spalten.join(" | ")} |`, `| ${s.spalten.map(() => "---").join(" | ")} |`);
    for (const z of s.zeilen) teile.push(`| ${z.join(" | ")} |`);
    if (s.summe) teile.push(`| ${s.summe.map((x) => (x ? `**${x}**` : "")).join(" | ")} |`);
    if (s.fuss) teile.push("", s.fuss);
    teile.push("");
  }
  return teile.join("\n");
}

const ENDUNG: Record<BerichtFormat, string> = { pdf: "pdf", tabelle: "csv", markdown: "md" };

export function dateiname(a: Auswahl): string {
  const wer = a.art === "stundennachweis" ? (a.personen.length === 1 ? konto(a.personen[0]).name.replace(/\s+/g, "_") : "Team")
    : a.boards.map((b) => board(b).kuerzel).join("_");
  const art = { stundennachweis: "Stundennachweis", board: "Zeiten", erledigt: "Erledigt" }[a.art];
  return `${art}_${wer}_${a.von}_${a.bis}.${ENDUNG[a.format]}`;
}

export function titelVon(a: Auswahl): string {
  if (a.art === "stundennachweis") return `Stundennachweis ${a.personen.map((p) => konto(p).name).join(", ")}`;
  return `${a.art === "board" ? "Zeiten je Karte" : "Erledigte Karten"}: ${a.boards.map((b) => board(b).name).join(", ")}`;
}

/** Wer im Bericht vorkommen darf: du immer, andere nur mit dem Recht "Zeiten anderer sehen" in einem gemeinsamen Board;
 *  im Stundennachweis nur Personen mit Zeitkonto */
export function sichtbarePersonen(boardIds: string[], mitZeitkonto: boolean): string[] {
  const out = new Set<string>([ICH]);
  for (const b of stand.boards) {
    if (boardIds.length && !boardIds.includes(b.id)) continue;
    if (!darf(b, "zeit.andere.sehen")) continue;
    for (const m of b.mitglieder) out.add(m.konto);
  }
  return [...out].filter((p) => !mitZeitkonto || !!fassungAm(stand.zeitkonten, p, HEUTE));
}
