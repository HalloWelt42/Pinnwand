// Frontend-Modul-Registry.
// Module werden beim Start automatisch entdeckt (siehe main.ts) und melden
// hier ihre Ansichten an. Welche Ansichten tatsächlich erscheinen, steuert
// das Backend-Manifest (/api/erweiterungen); diese Registry liefert die
// passende Komponente je Ansichts-ID.

import type { Component } from 'svelte'

export interface AnsichtsModul {
  id: string
  titel: string
  icon: string
  komponente: Component<{ boardId: string }>
}

const ANSICHTEN: AnsichtsModul[] = []

export function registriereAnsicht(modul: AnsichtsModul): void {
  if (!ANSICHTEN.some((a) => a.id === modul.id)) {
    ANSICHTEN.push(modul)
  }
}

export function ansichten(): AnsichtsModul[] {
  return ANSICHTEN
}

export function komponenteFuer(id: string): Component<{ boardId: string }> | undefined {
  return ANSICHTEN.find((a) => a.id === id)?.komponente
}
