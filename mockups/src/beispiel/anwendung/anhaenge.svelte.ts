// Anwendungsfälle an Anhängen einer Karte (E-15, Mechanik M-63): hochladen legt die Datei in der Kellerwolke ab, in der
// Ablage der Pinnwand mit einem Ordner je Board; aus der eigenen Kellerwolke wird nur verknüpft, die Datei bleibt, wo
// sie ist. Entfernen nimmt den Anhang von der Karte, mit Rückgängig (die alte App löschte sofort und endgültig). Jede
// Änderung steht im Verlauf der Karte. Grenze 25 MB je Datei, leere Dateien werden abgelehnt.
//
// In der App liefert die Kellerwolke die Liste deiner Dateien und öffnet Dateien selbst; in den Entwürfen steht dafür
// eine kleine Ablage im Speicher: Hochgeladenes lässt sich öffnen, solange die Seite steht, für die Beispieldateien
// entsteht beim Öffnen ein schlichter Ersatz.

import type { Anhang, Board, Karte, Kennung } from "../../modell";
import { board, karte } from "../stand.svelte";
import { aendern, melden } from "./meldung.svelte";
import { vermerken } from "./verlauf";

/** höchstens so groß darf eine Datei sein (wie in der alten App) */
export const GRENZE_MB = 25;

/** Eine Datei in deiner Kellerwolke, wie die Dateiwahl sie zeigt */
export interface KellerwolkeDatei {
  pfad: string;
  name: string;
  groesse: string;
  art: Anhang["art"];
}

/** Deine Kellerwolke (Max Paulsen): eine kleine Auswahl erfundener Dateien */
export const KELLERWOLKE: KellerwolkeDatei[] = [
  { pfad: "Dokumente/Angebote", name: "Kalkulation 2026.ods", groesse: "88 KB", art: "tabelle" },
  { pfad: "Dokumente/Angebote", name: "Angebotsvorlage Gehäuse.odt", groesse: "46 KB", art: "text" },
  { pfad: "Dokumente/Lieferanten", name: "Preisliste Pulverbeschichtung.pdf", groesse: "204 KB", art: "pdf" },
  { pfad: "Dokumente/Prüfung", name: "Prüfplan Biegeteile.pdf", groesse: "1,1 MB", art: "pdf" },
  { pfad: "Bilder/Werkstatt", name: "Musterteil K5 Oberfläche.jpg", groesse: "2,3 MB", art: "bild" },
  { pfad: "Bilder/Werkstatt", name: "Laser Düsenwechsel.png", groesse: "940 KB", art: "bild" },
  { pfad: "Aufnahmen", name: "Telefonat Kunde Brandt.m4a", groesse: "6,1 MB", art: "ton" },
];

/** Ort einer hochgeladenen Datei in der Kellerwolke: Ablage der Pinnwand, ein Ordner je Board */
export function ablageOrt(b: Board): string {
  return `Pinnwand/${b.name}`;
}

/** Größe wie in der alten App: B, KB, MB */
function groesse(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`;
}

function artVon(name: string, typ: string): Anhang["art"] {
  const endung = name.split(".").pop()?.toLowerCase() ?? "";
  if (typ.startsWith("image/") || ["png", "jpg", "jpeg", "gif", "webp", "svg", "heic"].includes(endung)) return "bild";
  if (typ === "application/pdf" || endung === "pdf") return "pdf";
  if (typ.startsWith("audio/") || ["mp3", "wav", "ogg", "m4a", "flac"].includes(endung)) return "ton";
  if (["ods", "xlsx", "xls", "csv"].includes(endung)) return "tabelle";
  return "text";
}

/** gleicher Name an derselben Karte: wie in der Kellerwolke mit Zähler, "Skizze (2).png" */
function freierName(liste: Anhang[], name: string): string {
  if (!liste.some((a) => a.name === name)) return name;
  const punkt = name.lastIndexOf(".");
  const stamm = punkt > 0 ? name.slice(0, punkt) : name;
  const endung = punkt > 0 ? name.slice(punkt) : "";
  let n = 2;
  while (liste.some((a) => a.name === `${stamm} (${n})${endung}`)) n++;
  return `${stamm} (${n})${endung}`;
}

function anzahl(n: number): string {
  return n === 1 ? "1 Datei" : `${n} Dateien`;
}

// ═══ Ablage in der Kellerwolke (in den Entwürfen im Speicher) ═══════════════════════════════════════════

const inhalte = new Map<string, Blob>();
const adressen = new Map<string, string>();

function ablageSchluessel(karteId: Kennung, name: string): string {
  return `${karteId}/${name}`;
}

function svgText(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Ersatz für eine Beispieldatei ohne Inhalt: eine Skizze für Bilder, sonst die Angaben der Datei als Text */
function ersatz(a: Anhang, ort: string): Blob {
  if (a.art === "bild") {
    return new Blob([`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"><rect x="8" y="8" width="784" height="484" rx="8" ` +
      `fill="none" stroke="currentColor" stroke-width="4"/><text x="400" y="260" text-anchor="middle" font-family="sans-serif" ` +
      `font-size="32">${svgText(a.name)}</text></svg>`], { type: "image/svg+xml" });
  }
  return new Blob([`${a.name}\n\n${a.groesse}, ${ort}\n`], { type: "text/plain;charset=utf-8" });
}

/** Adresse zum Öffnen eines Anhangs (die Datei aus der Kellerwolke) */
export function dateiAdresse(k: Karte, a: Anhang): string {
  const schluessel = ablageSchluessel(k.id, a.name);
  const da = adressen.get(schluessel);
  if (da) return da;
  const ort = a.verknuepft ? "aus deiner Kellerwolke verknüpft" : `Kellerwolke, ${ablageOrt(board(k.board))}`;
  const adresse = URL.createObjectURL(inhalte.get(schluessel) ?? ersatz(a, ort));
  adressen.set(schluessel, adresse);
  return adresse;
}

// ═══ Anwendungsfälle ═════════════════════════════════════════════════════════════════════════════════════

/** Dateien hochladen (Dateiwahl oder auf die Fläche gezogen): zu große und leere bleiben draußen, die Meldung sagt es */
export function hochladen(karteId: Kennung, dateien: File[]): void {
  const k = karte(karteId);
  if (!k || !dateien.length) return;
  const zuGross = dateien.filter((d) => d.size > GRENZE_MB * 1024 * 1024).map((d) => d.name);
  const leer = dateien.filter((d) => d.size === 0).map((d) => d.name);
  const gut = dateien.filter((d) => d.size > 0 && d.size <= GRENZE_MB * 1024 * 1024);
  const abgelehnt = [
    zuGross.length ? `${zuGross.join(", ")} ${zuGross.length === 1 ? "ist" : "sind"} größer als ${GRENZE_MB} MB` : "",
    leer.length ? `${leer.join(", ")} ${leer.length === 1 ? "ist" : "sind"} leer` : "",
  ].filter(Boolean).join("; ");
  if (!gut.length) {
    melden(`Nicht angehängt: ${abgelehnt}`);
    return;
  }
  const b = board(k.board);
  aendern(() => {
    const namen = gut.map((d) => {
      const name = freierName(k.anhaenge, d.name);
      k.anhaenge.push({ name, groesse: groesse(d.size), art: artVon(d.name, d.type) });
      inhalte.set(ablageSchluessel(k.id, name), d);
      adressen.delete(ablageSchluessel(k.id, name));
      vermerken(k, `hat den Anhang ${name} hochgeladen`);
      return name;
    });
    const was = namen.length === 1 ? namen[0] : anzahl(namen.length);
    return `${was} an ${k.schluessel} angehängt, abgelegt in der Kellerwolke unter ${ablageOrt(b)}` + (abgelehnt ? `; nicht angehängt: ${abgelehnt}` : "");
  });
}

/** Dateien aus deiner Kellerwolke verknüpfen; schon verknüpfte kommen nicht doppelt */
export function ausKellerwolke(karteId: Kennung, dateien: KellerwolkeDatei[]): void {
  const k = karte(karteId);
  const neu = dateien.filter((d) => !k?.anhaenge.some((a) => a.verknuepft && a.name === d.name));
  if (!k || !neu.length) return;
  aendern(() => {
    for (const d of neu) {
      k.anhaenge.push({ name: freierName(k.anhaenge, d.name), groesse: d.groesse, art: d.art, verknuepft: true });
      vermerken(k, `hat ${d.name} aus der Kellerwolke verknüpft`);
    }
    const was = neu.length === 1 ? neu[0].name : anzahl(neu.length);
    return `${was} an ${k.schluessel} verknüpft; ${neu.length === 1 ? "die Datei bleibt" : "die Dateien bleiben"} in deiner Kellerwolke`;
  });
}

/** Anhang von der Karte nehmen, mit Rückgängig; eine verknüpfte Datei bleibt in deiner Kellerwolke */
export function entfernen(karteId: Kennung, name: string): void {
  const k = karte(karteId);
  const a = k?.anhaenge.find((x) => x.name === name);
  if (!k || !a) return;
  aendern(() => {
    k.anhaenge = k.anhaenge.filter((x) => x.name !== name);
    vermerken(k, `hat den Anhang ${name} entfernt`);
    return a.verknuepft ? `Verknüpfung zu ${name} gelöst; die Datei bleibt in deiner Kellerwolke` : `${name} von ${k.schluessel} entfernt`;
  });
}
