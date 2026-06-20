// Label-Farben aus der Material-Palette.
// Bekannte Bezeichnungen haben eine feste (semantische) Farbe; alle anderen
// bekommen über einen Hash eine stabile, eindeutige Farbe - kein Zufall, kein Grau.
// Hell: Stufe 100 Hintergrund + dunkelste lesbare Stufe als Text (Kontrast >= 4.5:1).
// Dunkel: getönter Hintergrund aus Stufe 200 + Stufe 200 als Text.

import { material, type Familie } from './theme/palette'

export interface LabelFarbe {
  bg: string
  fg: string
}

const SEMANTISCH: Record<string, Familie> = {
  mechanik: 'teal',
  software: 'blue',
  design: 'deepPurple',
  doku: 'amber',
  blocker: 'red',
  risiko: 'red',
  bug: 'red',
  test: 'green',
  abnahme: 'green',
  infra: 'green',
  meilenstein: 'indigo',
}

// Auswahl gut unterscheidbarer, farbiger Familien (kein Grau/Braun).
const FAMILIEN: Familie[] = [
  'teal', 'blue', 'deepPurple', 'amber', 'red', 'green', 'indigo',
  'cyan', 'pink', 'orange', 'lightGreen', 'lightBlue', 'purple', 'deepOrange',
]

function hashFamilie(label: string): Familie {
  let h = 0
  for (let i = 0; i < label.length; i++) h = (h * 31 + label.charCodeAt(i)) >>> 0
  return FAMILIEN[h % FAMILIEN.length]
}

function familieFuer(label: string): Familie {
  const k = label.trim().toLowerCase()
  return SEMANTISCH[k] ?? hashFamilie(k)
}

function rgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function kanal(c: number): number {
  const s = c / 255
  return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
}

function luminanz(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)
}

function kontrast(a: string, b: string): number {
  const la = luminanz(a)
  const lb = luminanz(b)
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}

function lesbarerText(bg: string, kandidaten: string[]): string {
  for (const c of kandidaten) {
    if (kontrast(bg, c) >= 4.5) return c
  }
  return kandidaten[kandidaten.length - 1]
}

export function labelFarbe(label: string, dunkel: boolean): LabelFarbe {
  const familie = material[familieFuer(label)]
  if (dunkel) {
    return { bg: rgba(familie[200], 0.2), fg: familie[200] }
  }
  return { bg: familie[100], fg: lesbarerText(familie[100], [familie[800], familie[900], '#212121']) }
}
