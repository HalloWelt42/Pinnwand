// Der eine Zustand der Oberfläche: was die angemeldete Person sieht, geladen aus /stand und danach aktuell gehalten über
// die Antworten der Änderungen und den Ereignisstrom. Ändern nur über die Anwendungsfälle in daten/anwendung/, lesen
// über die Hilfen hier und in daten/abfragen.ts. Jede Zeile trägt ihre Fassung; eine ältere überschreibt nie eine neuere.

import { abmelden, ereignisse, hole } from "appkern-oberflaeche";
import type {
  Abwesenheit, Bericht, Board, Entfernt, Geloescht, Gruppe, Hinweis, Karte, Kartenname, Konto, Laufnummer, Hinweiswege, Mitglied, ModulKennung, Ordner, PersonEinstellungen, Terminname,
  Serie, Termin, Timer, Verbindung, Vorlage, Zeiteintrag, Zeitkonto,
} from "../modell";
import { PINNWAND_KONTO } from "./konstanten";
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
  /** Wege der Hinweise, die diese Fassung anbietet, mit ihrer Vorgabe je Art */
  hinweiswege: Hinweiswege;
  einstellungen: PersonEinstellungen;
  papierkorb: Geloescht[];
  entfernt: Entfernt[];
  /** Namen von Karten, auf die sichtbare Zeiteinträge zeigen, die selbst nicht im Stand sind (archiviert, Board verlassen) */
  kartennamen: Kartenname[];
  /** dasselbe für Termine deiner bestätigten Zeit (Board verlassen) */
  terminnamen: Terminname[];
  vorlagen: Vorlage[];
  berichte: Bericht[];
  /** Vorschläge der KI gehen (Leitstelle eingerichtet); sonst zeigt die Oberfläche keine */
  kiBereit: boolean;
  /** wo die Transkription liegt (leer: nicht eingerichtet, keine Transkripte und keine Spracheingabe) */
  transkriptionAdresse: string;
  /** wo die Vertonung liegt (leer: nicht eingerichtet, kein Vorlesen) */
  vertonungAdresse: string;
  /** du bist Besitzer der App: du kannst alle Konten zurücksetzen und löschen */
  appBesitzer: boolean;
  /** Verbindung zum Ereignisstrom; getrennt: letzter Stand sichtbar, Schreibendes gesperrt */
  verbindung: Verbindung;
  meldung: Meldung | null;
}

export const stand = $state<Zustand>({
  geladen: false, moduleDa: [], konten: [], boards: [], karten: [], gruppen: [], laufnummern: [], ordner: [], timer: [], zeiteintraege: [],
  zeitkonten: [], abwesenheiten: [], serien: [], termine: [], hinweise: [], hinweiswege: { da: ["pinnwand"], vorgabe: {} }, einstellungen: { hinweise: {} } as PersonEinstellungen, papierkorb: [],
  entfernt: [], kartennamen: [], terminnamen: [], vorlagen: [], berichte: [], kiBereit: false, transkriptionAdresse: "", vertonungAdresse: "", appBesitzer: false, verbindung: "getrennt", meldung: null,
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
  timer: Timer[];
  zeiteintraege: Zeiteintrag[];
  zeitkonten: Zeitkonto[];
  abwesenheiten: Abwesenheit[];
  serien: Serie[];
  termine: Termin[];
  hinweise: Hinweis[];
  vorlagen: Vorlage[];
  papierkorb: Geloescht[];
  entfernt: Entfernt[];
  kartennamen: Kartenname[];
  terminnamen: Terminname[];
  berichte: Bericht[];
  hinweiswege: Hinweiswege;
  kiBereit: boolean;
  transkriptionAdresse: string;
  vertonungAdresse: string;
  appBesitzer: boolean;
  einstellungen: PersonEinstellungen;
}

/** Eine Änderung aus Antwort oder Ereignis: der neue Stand einer Zeile oder ihr Wegfall (ohne daten) */
export interface Geaendert {
  tabelle: string;
  id: string;
  daten?: { id: string; fassung?: number } & Record<string, unknown>;
}

/** Ein Ereignis des Stroms: wer änderte, die Meldung (ohne: still) und die neuen Stände */
interface Neuigkeit {
  von: string;
  text?: string;
  geaendert: Geaendert[];
}

/** So lange zeigt eine Karte, dass jemand anders sie gerade geändert hat (M-06) */
const FRISCH_MS = 5000;

/** Karten, die gerade jemand anders geändert hat, mit der Kennung der Person */
export const frisch = $state<Record<string, string>>({});

/** Tabelle des Servers und Teil des Zustands (je Zeile ein Eintrag mit Kennung) */
const TEILE = {
  konten: "konten", boards: "boards", karten: "karten", gruppen: "gruppen", laufnummern: "laufnummern", ordner: "ordner",
  timer: "timer", zeiteintraege: "zeiteintraege", zeitkonten: "zeitkonten", abwesenheiten: "abwesenheiten",
  serien: "serien", termine: "termine", hinweise: "hinweise", vorlagen: "vorlagen", papierkorb: "papierkorb", entfernt: "entfernt",
  berichte: "berichte",
} as const satisfies Record<string, keyof Zustand>;

type Zeile = { id: string; fassung?: number };

/** Änderungen, die eintreffen, während der ganze Stand unterwegs ist: je laufendem Laden eine Liste. Der geholte Stand
 *  kann älter sein als sie (sonst käme etwa ein eben gelöschtes Board zurück); darum kommen sie danach noch einmal
 *  darüber, in ihrer Reihenfolge. Das ist ohne Schaden, weil ein Stand nur mit höherer Fassung ersetzt wird. */
const unterwegs = new Set<Geaendert[]>();

export async function laden(): Promise<void> {
  const danach: Geaendert[] = [];
  unterwegs.add(danach);
  let s: Serverstand;
  try {
    s = await hole<Serverstand>("/stand");
  } finally {
    unterwegs.delete(danach);
  }
  ichSetzen(s.ich);
  Object.assign(stand, {
    moduleDa: s.moduleDa, konten: s.konten, boards: s.boards, karten: s.karten, gruppen: s.gruppen, laufnummern: s.laufnummern, ordner: s.ordner,
    timer: s.timer, zeiteintraege: s.zeiteintraege, zeitkonten: s.zeitkonten, abwesenheiten: s.abwesenheiten,
    serien: s.serien, termine: s.termine, hinweise: s.hinweise, vorlagen: s.vorlagen, papierkorb: s.papierkorb, entfernt: s.entfernt, kartennamen: s.kartennamen, terminnamen: s.terminnamen, berichte: s.berichte, hinweiswege: s.hinweiswege,
    kiBereit: s.kiBereit, transkriptionAdresse: s.transkriptionAdresse, vertonungAdresse: s.vertonungAdresse, appBesitzer: s.appBesitzer,
    einstellungen: s.einstellungen, geladen: true,
  });
  let nochmal = false;
  for (const g of danach) nochmal = einspielen(g) || nochmal;
  if (!eigenesKontoPruefen()) return;
  if (nochmal) void laden();
}

function fassung(z: unknown): number {
  return (z as Zeile | undefined)?.fassung ?? 0;
}

/** Hängt an diesen Teilen eines Boards, was du siehst? Module, Rollen und Mitglieder entscheiden, welche Zeiten,
 *  Timer, Zeitkonten und Abwesenheiten anderer im Stand stehen */
function sichtGeaendert(alt: Board, neu: Board): boolean {
  const teile = (b: Board) => JSON.stringify([b.module, b.rollen, b.mitglieder]);
  return teile(alt) !== teile(neu);
}

/** Übernimmt neue Stände; gibt zurück, ob der ganze Stand neu zu laden ist (ein Board kam neu hinzu oder fiel weg, oder
 *  an einem Board änderte sich, was du siehst) */
function einspielen(g: Geaendert): boolean {
  if (g.tabelle === "person_einstellungen") {
    if (g.daten && fassung(g.daten) >= fassung(stand.einstellungen)) stand.einstellungen = g.daten as unknown as PersonEinstellungen;
    return false;
  }
  const teil = TEILE[g.tabelle as keyof typeof TEILE];
  if (!teil) return false;
  const liste = stand[teil] as Zeile[];
  const i = liste.findIndex((z) => z.id === g.id);
  let neuLaden = false;
  if (teil === "boards") {
    const mitglied = !!g.daten && (g.daten as unknown as Board).mitglieder.some((m) => m.konto === ICH);
    // nicht mehr sichtbar: sofort heraus, dann den ganzen Stand holen (Karten, Papierkorb); neu sichtbar: seine Karten fehlen
    if (!mitglied) {
      if (i >= 0) liste.splice(i, 1);
      return i >= 0;
    }
    if (i < 0) {
      liste.push(g.daten!);
      return true;
    }
    // Module, Rollen oder Mitglieder geändert: was du siehst, folgt daraus, also den ganzen Stand holen
    neuLaden = fassung(g.daten) > fassung(liste[i]) && sichtGeaendert(liste[i] as unknown as Board, g.daten as unknown as Board);
  }
  if (!g.daten) {
    if (i >= 0) liste.splice(i, 1);
  } else if (i < 0) {
    liste.push(g.daten);
  } else if (fassung(g.daten) > fassung(liste[i])) {
    liste[i] = g.daten;
  }
  // Ordner stehen in ihrer Reihenfolge, auch wenn sie auf einem anderen Gerät umgeordnet wurden; Berichte neueste zuerst
  if (teil === "ordner") liste.sort((a, b) => reihe(a) - reihe(b));
  if (teil === "berichte") (liste as Bericht[]).sort((a, b) => b.erstellt.localeCompare(a.erstellt));
  return neuLaden;
}

function reihe(z: unknown): number {
  return (z as { reihe?: number }).reihe ?? 0;
}

/** Eine Änderung einer anderen Person: die Karten zeigen es kurz, die Meldung sagt es, ohne eine eigene Meldung mit
 *  Rückgängig zu verdrängen */
function fremdGeaendert(n: Neuigkeit): void {
  for (const g of n.geaendert) {
    if (g.tabelle !== "karten" || !g.daten) continue;
    frisch[g.id] = n.von;
    setTimeout(() => { if (frisch[g.id] === n.von) delete frisch[g.id]; }, FRISCH_MS);
  }
  if (n.text && !stand.meldung?.rueckgaengig) stand.meldung = { text: `${konto(n.von).name}: ${n.text}` };
}

export function uebernehmen(geaendert: Geaendert[]): void {
  for (const liste of unterwegs) liste.push(...geaendert);
  let neu = false;
  for (const g of geaendert) neu = einspielen(g) || neu;
  if (!eigenesKontoPruefen()) return;
  if (neu) void laden();
}

/** Merker dieser Oberfläche, die an Boards und Konto hängen (Ansicht je Board, Telefon); Thema, Schrift und Seitenleiste
 *  gehören dem Gerät und bleiben */
const MERKER = /^pinnwand_(ansicht_|telefon$)/;
const ANLAGE = "pinnwand_anlage";

/** Das eigene Konto im Stand: gelöscht, dann abmelden; neu angelegt (zurückgesetzt), dann die Merker vergessen und neu
 *  laden, wie bei der ersten Anmeldung. Ergebnis: ob die Oberfläche so weiterläuft. */
function eigenesKontoPruefen(): boolean {
  const ich = stand.konten.find((k) => k.id === ICH);
  if (!ich) {
    void abmelden();
    return false;
  }
  try {
    // gemerkt wird auch "ohne Kennung" (Konten von vor der Kennung), damit schon das erste Zurücksetzen erkannt wird
    const jetzt = ich.anlage ?? "";
    const gemerkt = localStorage.getItem(ANLAGE);
    if (gemerkt !== jetzt) {
      localStorage.setItem(ANLAGE, jetzt);
      if (gemerkt !== null) {
        for (const schluessel of Object.keys(localStorage)) if (MERKER.test(schluessel)) localStorage.removeItem(schluessel);
        location.reload();
        return false;
      }
    }
  } catch {
    // ohne Speicher gibt es auch nichts zu vergessen
  }
  return true;
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
            const n = JSON.parse(e.daten) as Neuigkeit;
            uebernehmen(n.geaendert);
            if (n.von !== ICH) fremdGeaendert(n);
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

/** Eine Karte einzeln vom Server in den Zustand holen (etwa eine archivierte über ihren Pfad, M-09, auch über einen
 *  früheren Schlüssel); Ergebnis: die Karte, wenn es sie gibt und du sie sehen darfst */
export async function karteHolen(schluessel: string): Promise<Karte | undefined> {
  try {
    const d = await hole<Geaendert["daten"]>(`/karten/${encodeURIComponent(schluessel)}`);
    if (!d) return undefined;
    uebernehmen([{ tabelle: "karten", id: d.id, daten: d }]);
    return karte(d.id);
  } catch {
    return undefined;
  }
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

/** Konto einer Person, auch der Pinnwand selbst (Vorbuchung der Serien); eine unbekannte Kennung ergibt einen Platzhalter
 *  statt einer fremden Person */
export function konto(id: string): Konto {
  if (id === PINNWAND_KONTO.id) return PINNWAND_KONTO;
  return stand.konten.find((k) => k.id === id) ?? { id, name: "Unbekannte Person", kuerzel: "?", farbe: "stahl", kellerwolke: "" };
}

/** Mitglieder mit Konto: wer sich schon einmal angemeldet hat. Wer auf die erste Anmeldung wartet, steht nur in der
 *  Mitgliederverwaltung, nicht in Personenauswahl, Filter oder Zeitachse */
export function mitKonto(b: Board): Mitglied[] {
  return b.mitglieder.filter((m) => m.konto);
}

/** Verknüpfte Karten (ohne sie selbst) */
export function gruppenmitglieder(k: Karte): Karte[] {
  return k.gruppe ? stand.karten.filter((x) => x.gruppe === k.gruppe && x.id !== k.id) : [];
}

/** Der persönliche Ordner, in dem ein Board liegt */
export function ordnerVon(boardId: string): Ordner | undefined {
  return stand.ordner.find((o) => o.boards.includes(boardId));
}
