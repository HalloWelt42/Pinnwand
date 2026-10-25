// Anwendungsfälle an Anhängen einer Karte über den Server (E-15, Mechanik M-63): hochladen legt die Dateien in der
// Kellerwolke ab, in der Ablage der Pinnwand mit einem Ordner je Board; aus der eigenen Kellerwolke wird nur verknüpft,
// die Datei bleibt, wo sie ist. Entfernen nimmt den Anhang von der Karte, mit Rückgängig (die alte App löschte sofort und
// endgültig). Den Verlauf der Karte schreibt der Server. Grenze 25 MB je Datei, leere Dateien bleiben draußen, die
// Meldung sagt es; der Server prüft dasselbe.
//
// Geöffnet wird Hochgeladenes über die Inhaltsadresse der Pinnwand (jedes Mitglied des Boards), Verknüpftes in der
// Kellerwolke der Person, die es verknüpft hat: nur sie sieht die Datei dort.

import { hochladen as mitFortschritt, inKellerwolke } from "appkern-oberflaeche";
import type { Anhang, Karte, KellerwolkeDatei, Kennung } from "../../modell";
import { ICH } from "../ich";
import { karte } from "../stand.svelte";
import { aendern, melden, senden, type Antwort } from "./meldung.svelte";

/** höchstens so groß darf eine Datei sein (wie in der alten App) */
export const GRENZE_MB = 25;
/** so viele Dateien gehen auf einmal */
export const AUF_EINMAL = 20;

/** Ordner einer Datei in der Kellerwolke zum Lesen, ohne den Zweig der Apps und ohne den Namen ("Pinnwand/Haushalt");
 *  gleich ort_zum_lesen in backend/app/anwendung/anhaenge.py */
export function ablageOrt(a: Anhang): string {
  const teile = (a.pfad ?? "").split("/").slice(0, -1);
  return (teile[0] === "Apps" ? teile.slice(1) : teile).join("/");
}

/** Adresse zum Öffnen eines Anhangs; leer, wenn die Datei in der Kellerwolke einer anderen Person liegt */
export function dateiAdresse(k: Karte, a: Anhang): string {
  if (!a.datei) return "";
  if (!a.verknuepft) return `/api/v1/inhalt/anhaenge/${encodeURIComponent(k.id)}/${encodeURIComponent(a.datei)}`;
  return a.von === ICH && a.pfad ? inKellerwolke(a.pfad) : "";
}

function anzahl(n: number): string {
  return n === 1 ? "1 Datei" : `${n} Dateien`;
}

/** Dateien hochladen (Dateiwahl oder auf die Fläche gezogen), alle in einer Änderung: zu große und leere bleiben
 *  draußen, die Meldung sagt es. Im Körper vorn die Angaben (Namen, Größen, Typen), dahinter die Inhalte */
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
  if (gut.length > AUF_EINMAL) {
    melden(`Höchstens ${AUF_EINMAL} Dateien auf einmal; nichts angehängt`);
    return;
  }
  const angaben = JSON.stringify({ dateien: gut.map((d) => ({ name: d.name, groesse: d.size, typ: d.type })) });
  const koerper = new Blob([`${angaben}\n`, ...gut]);
  const name = gut.length === 1 ? gut[0].name : anzahl(gut.length);
  void aendern(async () => {
    const a = await mitFortschritt<Antwort>(`/api/v1/karten/${karteId}/anhaenge/hochladen`, koerper, name, 200);
    return abgelehnt && a.meldung ? { ...a, meldung: `${a.meldung}; nicht angehängt: ${abgelehnt}` } : a;
  });
}

/** Dateien aus deiner Kellerwolke verknüpfen; schon verknüpfte kommen nicht doppelt */
export function ausKellerwolke(karteId: Kennung, dateien: KellerwolkeDatei[]): void {
  const k = karte(karteId);
  const neu = dateien.filter((d) => d.typ === "datei" && !k?.anhaenge.some((a) => a.datei === d.id));
  if (!k || !neu.length) return;
  void aendern(() => senden(`/karten/${karteId}/anhaenge/aus-kellerwolke`, { dateien: neu.map((d) => ({ ordner: d.ordner, datei: d.id })) }));
}

/** Anhang von der Karte nehmen, mit Rückgängig; die Datei bleibt in der Kellerwolke */
export function entfernen(karteId: Kennung, name: string): void {
  if (karte(karteId)?.anhaenge.some((a) => a.name === name)) void aendern(() => senden(`/karten/${karteId}/anhaenge/entfernen`, { name }));
}
