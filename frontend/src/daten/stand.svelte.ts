// Der eine Zustand der Oberfläche: was die angemeldete Person sieht, geladen aus /stand und danach aktuell gehalten über
// die Antworten der Änderungen und den Ereignisstrom. Ändern nur über die Anwendungsfälle in daten/anwendung/, lesen
// über die Hilfen hier und in daten/abfragen.ts. Jede Zeile trägt ihre Fassung; eine ältere überschreibt nie eine neuere.

import { ereignisse, hole } from "appkern-oberflaeche";
import type {
  Abwesenheit, Bericht, Board, Entfernt, Geloescht, Gruppe, Hinweis, Karte, Konto, Laufnummer, ModulKennung, Ordner, PersonEinstellungen, Serie, Termin,
  Timer, Verbindung, Vorlage, Zeiteintrag, Zeitkonto,
} from "../modell";
import { ICH, ichSetzen } from "./ich";

/** Meldung unten: was eben geschah, mit Rückgängig, solange sie steht */
export interface Meldung {
  text: string;
  rueckgaengig?: () => void;
}

export interface Zustand {
  /** der erste Stand ist da (vorher zeichnet keine Ansicht) */
  geladen: boolean;
  /** Module, die diese Fassung der Pinnwand anbietet; die übrigen lassen sich nicht einschalten */
  moduleDa: ModulKennung[];
  konten: Konto[];
  boards: Board[];
  karten: Karte[];
  gruppen: Gruppe[];
  laufnummern: Laufnummer[];
  ordner: Ordner[];
  timer: Timer[];
  zeiteintraege: Zeiteintrag[];
  zeitkonten: Zeitkonto[];
  abwesenheiten: Abwesenheit[];
  serien: Serie[];
  termine: Termin[];
  hinweise: Hinweis[];
  einstellungen: PersonEinstellungen;
  papierkorb: Geloescht[];
  entfernt: Entfernt[];
  vorlagen: Vorlage[];
  berichte: Bericht[];
  /** Verbindung zum Ereignisstrom; getrennt: letzter Stand sichtbar, Schreibendes gesperrt */
  verbindung: Verbindung;
  meldung: Meldung | null;
}

export const stand = $state<Zustand>({
  geladen: false, moduleDa: [], konten: [], boards: [], karten: [], gruppen: [], laufnummern: [], ordner: [], timer: [], zeiteintraege: [],
  zeitkonten: [], abwesenheiten: [], serien: [], termine: [], hinweise: [], einstellungen: { hinweise: {} } as PersonEinstellungen, papierkorb: [],
  entfernt: [], vorlagen: [], berichte: [], verbindung: "getrennt", meldung: null,
});

/** Antwort von /stand: die Teile, die der Server schon kennt (die übrigen kommen mit ihren Stufen) */
interface Serverstand {
  jetzt: string;
  ich: string;
  moduleDa: ModulKennung[];
  konten: Konto[];
  boards: Board[];
  karten: Karte[];
  gruppen: Gruppe[];
  laufnummern: Laufnummer[];
  ordner: Ordner[];
  hinweise: Hinweis[];
  vorlagen: Vorlage[];
  papierkorb: Geloescht[];
  entfernt: Entfernt[];
  einstellungen: PersonEinstellungen;
}

/** Eine Änderung aus Antwort oder Ereignis: der neue Stand einer Zeile oder ihr Wegfall (ohne daten) */
export interface Geaendert {
  tabelle: string;
  id: string;
  daten?: { id: string; fassung?: number } & Record<string, unknown>;
}

/** Tabelle des Servers und Teil des Zustands (je Zeile ein Eintrag mit Kennung) */
const TEILE = {
  konten: "konten", boards: "boards", karten: "karten", gruppen: "gruppen", laufnummern: "laufnummern", ordner: "ordner",
  hinweise: "hinweise", vorlagen: "vorlagen", papierkorb: "papierkorb", entfernt: "entfernt",
} as const satisfies Record<string, keyof Zustand>;

type Zeile = { id: string; fassung?: number };

export async function laden(): Promise<void> {
  const s = await hole<Serverstand>("/stand");
  ichSetzen(s.ich);
  Object.assign(stand, {
    moduleDa: s.moduleDa, konten: s.konten, boards: s.boards, karten: s.karten, gruppen: s.gruppen, laufnummern: s.laufnummern, ordner: s.ordner,
    hinweise: s.hinweise, vorlagen: s.vorlagen, papierkorb: s.papierkorb, entfernt: s.entfernt, einstellungen: s.einstellungen,
    geladen: true,
  });
}

function fassung(z: unknown): number {
  return (z as Zeile | undefined)?.fassung ?? 0;
}

/** Übernimmt neue Stände; gibt zurück, ob der ganze Stand neu zu laden ist (ein Board kam neu hinzu oder fiel weg) */
function einspielen(g: Geaendert): boolean {
  if (g.tabelle === "person_einstellungen") {
    if (g.daten && fassung(g.daten) >= fassung(stand.einstellungen)) stand.einstellungen = g.daten as unknown as PersonEinstellungen;
    return false;
  }
  const teil = TEILE[g.tabelle as keyof typeof TEILE];
  if (!teil) return false;
  const liste = stand[teil] as Zeile[];
  const i = liste.findIndex((z) => z.id === g.id);
  if (teil === "boards") {
    const mitglied = !!g.daten && (g.daten as unknown as Board).mitglieder.some((m) => m.konto === ICH);
    if ((i < 0) === mitglied) return true;                     // neu sichtbar oder nicht mehr: den ganzen Stand holen
  }
  if (!g.daten) {
    if (i >= 0) liste.splice(i, 1);
  } else if (i < 0) {
    liste.push(g.daten);
  } else if (fassung(g.daten) > fassung(liste[i])) {
    liste[i] = g.daten;
  }
  return false;
}

export function uebernehmen(geaendert: Geaendert[]): void {
  let neu = false;
  for (const g of geaendert) neu = einspielen(g) || neu;
  if (neu) void laden();
}

/** Hält den Zustand über den Ereignisstrom aktuell; nach einem Abbruch neu verbinden und den ganzen Stand holen.
 *  Ergebnis: zum Beenden (Abmelden, Verlassen der Seite). */
export function verbinden(): () => void {
  const halt = new AbortController();
  void (async () => {
    let warten = 1000;
    while (!halt.signal.aborted) {
      try {
        for await (const e of ereignisse("/ereignisse", halt.signal)) {
          if (e.art === "bereit") {
            await laden();
            stand.verbindung = "verbunden";
            warten = 1000;
          } else if (e.art === "geaendert") {
            uebernehmen(JSON.parse(e.daten) as Geaendert[]);
          }
        }
      } catch {
        // getrennt: unten neu verbinden
      }
      if (halt.signal.aborted) break;
      stand.verbindung = "getrennt";
      await new Promise((r) => setTimeout(r, warten));
      warten = Math.min(warten * 2, 30_000);
    }
  })();
  return () => halt.abort();
}

export function board(id: string): Board {
  return stand.boards.find((b) => b.id === id) ?? stand.boards[0];
}

/** Board aus dem Kürzel im Pfad (klein oder groß geschrieben) */
export function boardAusKuerzel(kuerzel: string): Board | undefined {
  return stand.boards.find((b) => b.kuerzel.toLowerCase() === kuerzel.toLowerCase());
}

/** Zuletzt vergebene Kartennummer eines Boards (die nächste Karte bekommt eine mehr) */
export function laufnummer(boardId: string): number {
  return stand.laufnummern.find((l) => l.board === boardId)?.zahl ?? 0;
}

export function karte(id: string): Karte | undefined {
  return stand.karten.find((k) => k.id === id);
}

/** Karte aus ihrem Schlüssel im Pfad (/board/prod/131) */
export function karteAusNummer(b: Board, nr: string): Karte | undefined {
  return stand.karten.find((k) => k.board === b.id && k.schluessel === `${b.kuerzel}-${nr}`);
}

/** Alle Karten einer Spalte in ihrer Reihenfolge (ohne Zeitfenster) */
export function kartenDerSpalte(spalte: string): Karte[] {
  return stand.karten.filter((k) => k.spalte === spalte).sort((a, b) => a.reihe - b.reihe);
}

/** Konto einer Person; eine unbekannte Kennung ergibt einen Platzhalter statt einer fremden Person */
export function konto(id: string): Konto {
  return stand.konten.find((k) => k.id === id) ?? { id, name: "Unbekannte Person", kuerzel: "?", farbe: "stahl", kellerwolke: "" };
}

/** Verknüpfte Karten (ohne sie selbst) */
export function gruppenmitglieder(k: Karte): Karte[] {
  return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id) : [];
}

/** Der persönliche Ordner, in dem ein Board liegt */
export function ordnerVon(boardId: string): Ordner | undefined {
  return stand.ordner.find((o) => o.boards.includes(boardId));
}
