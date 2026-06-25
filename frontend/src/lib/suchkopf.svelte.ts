// Zentrale Kopf-Suche: ein Suchbegriff, der von der Kopfleiste gesetzt und von der
// Suche-Ansicht gelesen wird. So liegt die Suche (samt Spracheingabe) gebuendelt im
// Kopf der App und nicht verstreut in einzelnen Ansichten. stand steigt bei jeder
// neuen Anfrage und triggert die Ausfuehrung in der Suche-Ansicht.
export const kopfSuche = $state<{ q: string; stand: number }>({ q: '', stand: 0 })

export function sucheSetzen(q: string): void {
  kopfSuche.q = q
  kopfSuche.stand++
}
