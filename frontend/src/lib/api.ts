// Fassade des HTTP-Clients: bündelt die bereichsbezogenen Module unter
// lib/api/. Bestehende Importe aus './api' funktionieren unverändert;
// neue Aufrufe gehören in das passende Bereichsmodul.

// Datenmodelle bleiben ueber api.ts erreichbar (viele Komponenten importieren von
// hier). EINE Quelle statt einer von Hand gespiegelten Namensliste.
export type * from './types'

// Querschnitts-Helfer: nur der Datei-Download ist Teil der öffentlichen Fläche.
export { ladeDateiHerunter } from './api/basis'

export * from './api/system'
export * from './api/kanban'
export * from './api/suche'
export * from './api/serien'
export * from './api/planung'
export * from './api/termine'
