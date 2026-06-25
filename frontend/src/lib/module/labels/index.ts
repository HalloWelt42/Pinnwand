// Labels-Modul: meldet die globale Verwaltungs-Ansicht "Labels" an
// (eigene Labels anlegen, umbenennen, Farbe aus der Material-Palette zuweisen).

import { registriereAnsicht } from '../registry'
import Labels from './Labels.svelte'

export function registriere(): void {
  registriereAnsicht({ id: 'labels', titel: 'Labels', icon: 'fa-solid fa-tags', komponente: Labels })
}
