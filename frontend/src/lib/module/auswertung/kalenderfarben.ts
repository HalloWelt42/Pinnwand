// Gemeinsame Farb- und Aggregationslogik für den Jahreskalender (Gitter + Matrix).

import { formatStd } from '../../zeit'
import type { AbwesenheitTyp, KalenderZelle } from '../../api'

export interface Ebenen {
  anwesenheit: boolean
  feiertage: boolean
  stunden: boolean
  auslastung: boolean
  frei: boolean
}

export type TypMap = Record<string, AbwesenheitTyp>

const FREI_TON = 'color-mix(in srgb, var(--text-3) 24%, transparent)'

const TAG_REF_SEK = 8 * 3600 // Referenz für die Stunden-Heatmap (ein voller Arbeitstag)

/** Hintergrundfarbe einer Zelle (Matrix) je nach aktiven Ebenen. */
export function zellHintergrund(z: KalenderZelle, e: Ebenen, typen: TypMap): string {
  // Frei-Ebene: alle freien Tage hervorheben (Feiertag, Urlaub/Abwesenheit, Wochenende),
  // Arbeitstage bleiben neutral - so sieht man das Frei-Muster auf einen Blick.
  if (e.frei) {
    if (z.feiertag) return 'var(--due-rot-bg)'
    if (z.status === 'abwesend' && z.abw) return typen[z.abw.typ]?.farbe ?? 'var(--due-rot-bg)'
    if (z.status === 'frei' || z.status === 'feiertag') return FREI_TON
    return 'var(--surface-2)'
  }
  if (e.feiertage && z.feiertag) return 'var(--due-rot-bg)'
  // Feiertag und freier Tag gelten nie als anwesend (keine grüne Färbung).
  if (z.status === 'frei' || z.status === 'feiertag') return 'var(--surface-2)'
  if (e.anwesenheit && z.status === 'abwesend' && z.abw) {
    return typen[z.abw.typ]?.farbe ?? 'var(--due-rot-bg)'
  }
  if (e.stunden) {
    if (z.ist_sek <= 0) return 'var(--surface-2)'
    const pct = Math.min(100, Math.max(16, Math.round((z.ist_sek / TAG_REF_SEK) * 100)))
    return `color-mix(in srgb, var(--hl-primary) ${pct}%, transparent)`
  }
  if (e.auslastung && z.soll > 0) {
    if (z.ist_sek <= 0) return 'var(--surface-2)'
    const r = z.ist_sek / 3600 / z.soll
    return r > 1.05 ? 'color-mix(in srgb, var(--gefahr) 38%, transparent)' : 'color-mix(in srgb, var(--ok) 42%, transparent)'
  }
  if (e.anwesenheit) return 'color-mix(in srgb, var(--ok) 15%, transparent)'
  return 'var(--surface-2)'
}

/** Kleiner Eck-Marker (Homeoffice/extern: anwesend trotz Eintrag). */
export function zellMarker(z: KalenderZelle, e: Ebenen, typen: TypMap): string | null {
  if (e.anwesenheit && z.status === 'anwesend' && z.abw) return typen[z.abw.typ]?.farbe ?? null
  return null
}

/** Halber Tag (Abwesenheit oder Regel anteilig)? Für eine diagonale Markierung. */
export function zellHalb(z: KalenderZelle): boolean {
  if (z.abw && z.abw.anteil > 0 && z.abw.anteil < 1) return true
  return z.regel !== null && z.regel > 0 && z.regel < 1
}

export interface TagAggregat {
  zahl: string
  bg: string
  feiertag: string | null
  titel: string
}

/** Verdichtet die Zellen aller Personen eines Tages zu Zahl + Farbe (Monatsgitter). */
export function tagAggregat(zellen: KalenderZelle[], e: Ebenen): TagAggregat {
  const anwesend = zellen.filter((z) => z.status === 'anwesend').length
  const abwesend = zellen.filter((z) => z.status === 'abwesend').length
  // Eingeplant = an dem Tag arbeitende Personen (ohne Feiertag/Wochenende/Teilzeit-frei).
  const eingeplant = anwesend + abwesend
  const feier = zellen.find((z) => z.feiertag)?.feiertag ?? null
  const sumIst = zellen.reduce((s, z) => s + z.ist_sek, 0)
  const sumSoll = zellen.reduce((s, z) => s + z.soll, 0)

  let zahl = ''
  let bg = 'var(--surface-2)'
  if (e.stunden && sumIst > 0) {
    zahl = formatStd(sumIst)
    const pct = Math.min(100, Math.max(16, Math.round((sumIst / (TAG_REF_SEK * Math.max(eingeplant, 1))) * 100)))
    bg = `color-mix(in srgb, var(--hl-primary) ${pct}%, transparent)`
  } else if (e.auslastung && sumSoll > 0 && sumIst > 0) {
    const r = sumIst / 3600 / sumSoll
    zahl = Math.round(r * 100) + '%'
    bg = r > 1.05 ? 'color-mix(in srgb, var(--gefahr) 38%, transparent)' : 'color-mix(in srgb, var(--ok) 42%, transparent)'
  } else if (e.anwesenheit && eingeplant > 0) {
    zahl = `${anwesend}/${eingeplant}`
    const r = anwesend / eingeplant
    bg = `color-mix(in srgb, var(--ok) ${Math.round(10 + r * 40)}%, transparent)`
  }
  if (e.feiertage && feier) bg = 'var(--due-rot-bg)'

  // Frei-Ebene: freie Tage hervorheben (Feiertag, Abwesenheit, oder ganz arbeitsfrei).
  if (e.frei) {
    if (feier) {
      bg = 'var(--due-rot-bg)'
    } else if (eingeplant === 0) {
      bg = FREI_TON
    } else if (abwesend > 0) {
      bg = 'color-mix(in srgb, var(--text-3) 15%, transparent)'
      if (!zahl) zahl = `${abwesend} frei`
    } else {
      bg = 'var(--surface-2)'
    }
  }

  const teile = eingeplant > 0 ? [`anwesend ${anwesend}/${eingeplant}`] : ['arbeitsfrei']
  if (abwesend) teile.push(`abwesend ${abwesend}`)
  if (feier) teile.push(`Feiertag: ${feier}`)
  if (sumIst) teile.push(`${formatStd(sumIst)} h`)
  return { zahl, bg, feiertag: feier, titel: teile.join(', ') }
}
