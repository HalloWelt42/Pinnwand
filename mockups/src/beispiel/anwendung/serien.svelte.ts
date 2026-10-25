// Anwendungsfälle der Serien (Modul Serien und Termine): anlegen, ändern, pausieren, fortsetzen, löschen, einen Tag
// auslassen, und der Nachtrag am Folgetag (vorgebuchte Zeit bestätigen oder verwerfen). Alles über aendern(), mit
// Rückgängig. Die Regeln der Tage stehen in regeln/serien.ts; hier steht nur, was sich am Zustand ändert.
//
// Pause, Ändern und Löschen fassen nur unberührte Vorbuchungen an (Karte des Tags in der Zielspalte, ohne Zeit, nicht
// angefasst); bewusst gelöschte Tage kommen nie wieder (M-107 bis M-110). Gezählt wird nach den Regeln: in den
// Entwürfen liegen nicht alle Vorbuchungen als Karte vor, in der App legt sie der Server an.

import type { Karte, Kennung, Serie } from "../../modell";
import { kartenTitel, vorkommen, vorkommenAm, type Nachtragposten } from "../../regeln/serien";
import { karteDesTags, nachtrag, serie, serienUmfeld } from "../abfragen";
import { minutenAus, plusTage, uhrzeitAus } from "../../regeln/tage";
import { HEUTE, ICH, JETZT } from "../daten";
import { datum, dauer } from "../format";
import { board, karte, konto, stand } from "../stand.svelte";
import { verschieben } from "./karten.svelte";
import { aendern } from "./meldung.svelte";
import { inPapierkorb } from "./papierkorb.svelte";
import { zeitBestaetigen, zeitVerwerfen } from "./termine.svelte";
import { neueKennung } from "./zeiten.svelte";

/** Unberührte Vorbuchungen ab einem Tag: Karten der Serie in der Zielspalte, ohne Zeit, nicht angefasst */
function unberuehrte(s: Serie, ab: string): Karte[] {
  return stand.karten.filter((k) => k.serie === s.id && !!k.faellig && k.faellig >= ab && k.spalte === s.zielspalte
    && !stand.zeiteintraege.some((e) => e.karte === k.id) && !s.beruehrt.some((b) => b.tag === k.faellig));
}

/** Zahl der unberührten Vorbuchungen nach den Regeln (Tage im Vorlauf ab morgen) */
function zahlVorgebucht(s: Serie): number {
  const u = serienUmfeld();
  return vorkommen(s, plusTage(HEUTE, 1), plusTage(HEUTE, s.vorlaufTage), u).filter((v) => v.stand === "vorgebucht").length;
}

function vorbuchungen(n: number): string {
  return `${n} unberührte ${n === 1 ? "Vorbuchung" : "Vorbuchungen"}`;
}

/** Karten aus dem Zustand nehmen (zurückgenommene Vorbuchungen; der Server legt sie bei Bedarf neu an) */
function zuruecknehmen(karten: Karte[]): void {
  const ids = new Set(karten.map((k) => k.id));
  for (const sp of Object.keys(stand.reihen)) stand.reihen[sp] = stand.reihen[sp].filter((id) => !ids.has(id));
  stand.karten = stand.karten.filter((k) => !ids.has(k.id));
}

// ═══ Serie anlegen, ändern, pausieren, fortsetzen, löschen ══════════════════════════════════════════════════

/** Neue Serie: legt im Vorlauf ihre Karten in die Zielspalte (in der App der Server). Ergebnis: Kennung */
export function serieAnlegen(neu: Omit<Serie, "id">): Kennung | undefined {
  if (!neu.titel.trim() || !neu.teilnehmer.length) return undefined;
  const id = neueKennung("se");
  const ok = aendern(() => {
    const s: Serie = { ...($state.snapshot(neu) as Omit<Serie, "id">), id, titel: neu.titel.trim() };
    stand.serien.push(s);
    return `Serie ${s.titel} angelegt; ${zahlVorgebucht(s) + (vorkommenAm(s, HEUTE, serienUmfeld()).stand === "heute" ? 1 : 0)} Tage vorgebucht`;
  });
  return ok ? id : undefined;
}

/** Serie ändern: unberührte Vorbuchungen ziehen nach (Titel, Beschreibung, Labels, Teilnehmer, Dauer, Zielspalte; ein
 *  Tag, der nach dem neuen Rhythmus entfällt, wird zurückgenommen); angefasste, vergangene und gelöschte Tage bleiben */
export function serieAendern(id: Kennung, aenderung: Partial<Omit<Serie, "id" | "board">>): void {
  const s = serie(id);
  if (!s) return;
  aendern(() => {
    const vorher = unberuehrte(s, plusTage(HEUTE, 1));
    Object.assign(s, $state.snapshot(aenderung));
    const u = serienUmfeld();
    const weg = vorher.filter((k) => vorkommenAm(s, k.faellig!, u).stand !== "vorgebucht");
    for (const k of vorher.filter((x) => !weg.includes(x))) {
      Object.assign(k, { titel: kartenTitel(s), beschreibung: s.beschreibung, labels: [...s.labels], zustaendig: [...s.teilnehmer], schaetzungMin: s.dauerMin });
      if (k.spalte !== s.zielspalte) {
        stand.reihen[k.spalte] = (stand.reihen[k.spalte] ?? []).filter((x) => x !== k.id);
        (stand.reihen[s.zielspalte] ??= []).push(k.id);
        k.spalte = s.zielspalte;
      }
    }
    zuruecknehmen(weg);
    return `Serie ${s.titel} gespeichert; ${vorbuchungen(zahlVorgebucht(s))} angepasst, angefasste und vergangene Tage bleiben`;
  });
}

/** Pausieren: keine neuen Vorbuchungen, unberührte Zukunftskarten werden zurückgenommen, angefasste bleiben (M-109) */
export function pausieren(id: Kennung): void {
  const s = serie(id);
  if (!s || (s.pausiertSeit && !s.fortgesetzt)) return;
  aendern(() => {
    const n = zahlVorgebucht(s);
    zuruecknehmen(unberuehrte(s, plusTage(HEUTE, 1)));
    s.pausiertSeit = HEUTE;
    s.fortgesetzt = undefined;
    return `Serie ${s.titel} pausiert; ${vorbuchungen(n)} zurückgenommen, angefasste Karten bleiben`;
  });
}

/** Fortsetzen: ab heute wird wieder vorgebucht; die Tage der Pause bleiben ohne Karte, gelöschte bleiben gelöscht */
export function fortsetzen(id: Kennung): void {
  const s = serie(id);
  if (!s?.pausiertSeit || s.fortgesetzt) return;
  aendern(() => {
    s.fortgesetzt = HEUTE;
    return `Serie ${s.titel} fortgesetzt; ${vorbuchungen(zahlVorgebucht(s)).replace("unberührte ", "")} ab heute`;
  });
}

/** Serie löschen: unberührte Vorbuchungen werden zurückgenommen; Karten mit Zeit und erledigte bleiben als Verlauf und
 *  werden von der Serie gelöst (M-110); bestätigte Zeiten zählen weiter */
export function serieLoeschen(id: Kennung): void {
  const s = serie(id);
  if (!s) return;
  aendern(() => {
    const n = zahlVorgebucht(s);
    zuruecknehmen(unberuehrte(s, plusTage(HEUTE, 1)));
    const geloest = stand.karten.filter((k) => k.serie === s.id);
    for (const k of geloest) k.serie = undefined;
    stand.serien = stand.serien.filter((x) => x.id !== s.id);
    return `Serie ${s.titel} gelöscht; ${vorbuchungen(n)} zurückgenommen, ${geloest.length} ${geloest.length === 1 ? "Karte bleibt" : "Karten bleiben"} als Verlauf`;
  });
}

/** Einen Tag bewusst auslassen: er wird gemerkt und nie wieder angelegt (M-108); eine unberührte Karte des Tags geht in
 *  den Papierkorb */
export function tagAuslassen(id: Kennung, tag: string): void {
  const s = serie(id);
  if (!s || s.auslass.some((a) => a.tag === tag)) return;
  aendern(() => {
    s.auslass.push({ tag, von: ICH, am: JETZT });
    const k = unberuehrte(s, tag).find((x) => x.faellig === tag);
    if (k) inPapierkorb([k.id]);
    return `${s.titel} am ${datum(tag, true)} ausgelassen; der Tag kommt nicht wieder${k ? `, ${k.schluessel} im Papierkorb` : ""}`;
  });
}

// ═══ Nachtrag am Folgetag ══════════════════════════════════════════════════════════════════════════════════

/** Deine Zeit eines Serientags bestätigen: ein Zeiteintrag mit Herkunft Serie auf der Karte des Tags; die Karte geht
 *  nach Erledigt und behält den Termintag als Abschluss (M-23, M-111). Ergebnis: Text der Meldung */
function serienzeitBuchen(p: Nachtragposten, sek: number): string | null {
  const k = p.karte ? karte(p.karte) : undefined;
  const s = serie(p.bezug);
  if (!k || !s || sek <= 0) return null;
  const von = s.uhrzeit;
  stand.zeiteintraege.push({ id: neueKennung("z"), karte: k.id, konto: ICH, datum: p.tag, von, bis: von ? uhrzeitAus(minutenAus(von) + Math.round(sek / 60)) : undefined,
                             sekunden: sek, herkunft: "serie" });
  const ziel = board(k.board).spalten.find((x) => x.erledigt);
  const verschoben = !!ziel && k.spalte !== ziel.id;
  if (ziel && verschoben) {
    verschieben(k.id, ziel.id);
    k.abgeschlossen = p.tag;
  }
  return `${dauer(sek)} auf ${k.schluessel} gebucht (${datum(p.tag, true)})${verschoben ? ", Karte erledigt" : ""}`;
}

/** Eine vorgebuchte Zeit bestätigen, bei einer Serie mit der angegebenen Dauer (Vorschlag: geplante Dauer) */
export function nachtragBestaetigen(p: Nachtragposten, sek = p.geplantMin * 60): void {
  if (p.art === "termin") { zeitBestaetigen(p.bezug); return; }
  aendern(() => serienzeitBuchen(p, sek));
}

/** Verwerfen: fand für dich nicht statt. Waren andere dabei, fällst nur du aus der Karte des Tags; warst du allein, geht
 *  die Karte in den Papierkorb und der Tag gilt als verworfen (es zählt keine Zeit) */
export function nachtragVerwerfen(p: Nachtragposten): void {
  if (p.art === "termin") { zeitVerwerfen(p.bezug); return; }
  const s = serie(p.bezug);
  const k = p.karte ? karte(p.karte) : undefined;
  if (!s || !k) return;
  aendern(() => {
    const andere = k.zustaendig.filter((x) => x !== ICH);
    if (andere.length) {
      k.zustaendig = andere;
      k.verlauf.push({ zeit: JETZT, von: ICH, text: `war am ${datum(p.tag, true)} nicht dabei` });
      return `${k.schluessel}: für dich verworfen, die Karte bleibt für ${andere.map((x) => konto(x).name).join(", ")}`;
    }
    inPapierkorb([k.id]);
    if (!s.verworfen.includes(p.tag)) s.verworfen.push(p.tag);
    return `${s.titel} am ${datum(p.tag, true)} verworfen; ${k.schluessel} im Papierkorb, es zählt keine Zeit`;
  });
}

/** Alle offenen Posten auf einmal bestätigen, Serien mit ihrer eingetragenen Dauer (je Bezug und Tag) */
export function alleBestaetigen(dauern: Record<string, number> = {}): void {
  const posten = nachtrag();
  if (!posten.length) return;
  aendern(() => {
    for (const p of posten) {
      if (p.art === "termin") zeitBestaetigen(p.bezug);
      else serienzeitBuchen(p, dauern[`${p.bezug}|${p.tag}`] ?? p.geplantMin * 60);
    }
    return `${posten.length} ${posten.length === 1 ? "Zeit" : "Zeiten"} bestätigt`;
  });
}
