// Theme-Engine: hell/dunkel gleichwertig, Auswahl wird gemerkt.
// Reaktiver Zustand via Svelte-5-Runes, ueber Module-Import geteilt.

export type Modus = 'hell' | 'dunkel'

const SPEICHER_SCHLUESSEL = 'pinnwand-theme'

function startModus(): Modus {
  const gespeichert = localStorage.getItem(SPEICHER_SCHLUESSEL)
  if (gespeichert === 'hell' || gespeichert === 'dunkel') return gespeichert
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dunkel' : 'hell'
}

export const theme = $state<{ modus: Modus }>({ modus: 'hell' })

function anwenden(): void {
  document.documentElement.setAttribute('data-theme', theme.modus === 'dunkel' ? 'dark' : 'light')
  localStorage.setItem(SPEICHER_SCHLUESSEL, theme.modus)
}

export function initTheme(): void {
  theme.modus = startModus()
  anwenden()
}

export function wechsleTheme(): void {
  theme.modus = theme.modus === 'hell' ? 'dunkel' : 'hell'
  anwenden()
}
