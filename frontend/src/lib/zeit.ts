// Datums-/Zeit-Hilfsfunktionen für die Auswertung (lokale Zeit, ISO-Wochen).

export function ymd(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const t = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${t}`
}

export function parseTag(s: string): Date {
  return new Date(s + 'T00:00:00')
}

export function addTage(d: Date, n: number): Date {
  const x = new Date(d)
  x.setDate(x.getDate() + n)
  return x
}

// Montag der Woche, in der d liegt (lokal).
export function montagDer(d: Date): Date {
  const x = new Date(d)
  const wd = (x.getDay() + 6) % 7 // 0 = Montag
  x.setDate(x.getDate() - wd)
  x.setHours(0, 0, 0, 0)
  return x
}

// ISO-8601-Kalenderwoche.
export function isoWoche(d: Date): number {
  const x = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  const wd = (x.getUTCDay() + 6) % 7
  x.setUTCDate(x.getUTCDate() - wd + 3) // Donnerstag dieser Woche
  const ersterDonnerstag = new Date(Date.UTC(x.getUTCFullYear(), 0, 4))
  const wdE = (ersterDonnerstag.getUTCDay() + 6) % 7
  ersterDonnerstag.setUTCDate(ersterDonnerstag.getUTCDate() - wdE + 3)
  return 1 + Math.round((x.getTime() - ersterDonnerstag.getTime()) / (7 * 86400000))
}

// Sekunden -> "H:MM" (Stunden:Minuten, gerundet auf Minuten).
export function formatStd(sek: number): string {
  const m = Math.round(sek / 60)
  return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`
}

export function stdDezimal(sek: number): number {
  return Math.round((sek / 3600) * 100) / 100
}

const WOCHENTAGE = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
export function wochentag(d: Date): string {
  return WOCHENTAGE[(d.getDay() + 6) % 7]
}

export function tagKurz(d: Date): string {
  return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.`
}

const MONATE_LANG = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

// Deutsche Datumsformate aus einem ISO-String ("2026-06-20" oder "2026-06-20T14:30:00").
// Eine Quelle der Wahrheit, damit Datumsangaben ueberall einheitlich deutsch erscheinen.

// -> "20.06."
export function isoKurz(iso: string): string {
  const [, m, t] = iso.slice(0, 10).split('-')
  return `${t}.${m}.`
}

// -> "20.06.2026"
export function isoLang(iso: string): string {
  const [j, m, t] = iso.slice(0, 10).split('-')
  return `${t}.${m}.${j}`
}

// -> "20.06.2026 14:30" (Uhrzeit nur, wenn im String vorhanden)
export function isoDatumZeit(iso: string): string {
  const tag = isoLang(iso)
  const zeit = iso.slice(11, 16)
  return zeit ? `${tag} ${zeit}` : tag
}

// -> "20. Juni 2026" (ausgeschrieben, z.B. zum Vorlesen)
export function isoGesprochen(iso: string): string {
  const [j, m, t] = iso.slice(0, 10).split('-')
  return `${Number(t)}. ${MONATE_LANG[Number(m) - 1]} ${j}`
}

// Kurze Wochentags-Kuerzel (Mo..So) - zentral statt in Komponenten kopiert.
export const WOCHENTAGE_KURZ = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'] as const

// ISO-Datum (YYYY-MM-DD) als deutsches Kurzdatum TT.MM.JJJJ.
export function dmy(iso: string): string {
  const [j, m, t] = iso.slice(0, 10).split('-')
  return `${t}.${m}.${j}`
}

// Wochentags-Kuerzel eines ISO-Datums.
export function wtagKurz(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return WOCHENTAGE_KURZ[(d.getDay() + 6) % 7]
}
