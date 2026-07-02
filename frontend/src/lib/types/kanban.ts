// Datenmodelle rund um das Kanban-Brett: Mappen/Projekte, Boards, Spalten,
// Karten, Zeiteinträge, Labels, Dokumente, Heute/Fällig, Anhänge und
// Aktivitäten (spiegeln backend/module/*/models.py).

export type Prioritaet = 'hoch' | 'mittel' | 'niedrig'
export type KartenTyp = 'arbeit' | 'idee'

export interface ChecklistPunkt {
  text: string
  erledigt: boolean
}

export interface GruppenMitglied {
  id: string
  schluessel?: string | null
  titel: string
}

export interface Kommentar {
  autor: string
  text: string
  zeit: string
}

export interface Karte {
  id: string
  board_id: string
  spalte: string
  titel: string
  schluessel?: string | null
  beschreibung?: string | null
  notizen?: string | null
  blockiert_grund?: string | null
  labels: string[]
  prioritaet?: Prioritaet | null
  checkliste: ChecklistPunkt[]
  kommentare: Kommentar[]
  cover?: string | null
  reihenfolge: number
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
  erstellt_am?: string | null
  bewegt_am?: string | null
  schaetzung_min?: number | null
  erfasst_sek?: number
  laeuft_seit?: string | null
  transkript_id?: string | null
  transkript_name?: string | null
  abschluss_am?: string | null
  typ?: KartenTyp
  gruppe_id?: string | null
  gruppe_sek?: number | null
  gruppe_mitglieder?: GruppenMitglied[]
  gruppe_zeit_geteilt?: boolean
}

export interface Spalte {
  id: string
  titel: string
  wip_limit?: number | null
  reihenfolge: number
  erledigt?: boolean
}

export interface Board {
  id: string
  mappe_id: string
  titel: string
  kuerzel?: string | null
  spalten: Spalte[]
}

export interface BoardDetail extends Board {
  karten: Karte[]
}

// Eine gefensterte Seite Karten (fertige Spalte oder Archiv) mit Nachlade-Info.
export interface KartenSeite {
  karten: Karte[]
  gesamt: number
  hat_mehr: boolean
}

// In der UI einstellbare Grenzen fuer fertige Karten (Deckel + Archiv-Schwelle).
export interface KanbanEinstellungen {
  fertig_seitengroesse: number
  archiv_tage: number
  aging_amber_tage: number
  aging_rot_tage: number
}

export type ProjektStatus = 'aktiv' | 'pausiert' | 'abgeschlossen'

// Eine Mappe ist zugleich ein Projekt (Board = Phase).
export interface Projektmappe {
  id: string
  titel: string
  beschreibung?: string | null
  owner?: string | null
  budget_min?: number | null
  status?: ProjektStatus
}

// Aufwand je Projekt: Ist (erfasste Sekunden), Soll (geschaetzte Minuten) und
// Budget (Planungsobergrenze in Minuten) bleiben getrennt.
export interface ProjektAufwand {
  mappe_id: string
  titel: string
  status: ProjektStatus
  owner?: string | null
  budget_min?: number | null
  ist_sekunden: number
  soll_minuten: number
  karten: number
  boards: number
}

export interface ProjektBoardAufwand {
  board_id: string
  titel: string
  ist_sekunden: number
  soll_minuten: number
  karten: number
}

export interface ProjektPersonAufwand {
  kuerzel?: string | null
  ist_sekunden: number
}

export interface ProjektDetail {
  mappe_id: string
  titel: string
  status: ProjektStatus
  owner?: string | null
  budget_min?: number | null
  ist_sekunden: number
  soll_minuten: number
  boards: ProjektBoardAufwand[]
  personen: ProjektPersonAufwand[]
}

// Zentrale Farbzuweisung je Label-Name (Verwaltung). karte.labels bleibt eine
// Liste freier Strings; diese Definition liefert nur die Material-Farbe.
export interface LabelDefinition {
  id: string
  name: string
  familie: string
}

export interface Zeiteintrag {
  id: string
  karte_id: string
  board_id?: string | null
  mappe_id?: string | null
  datum: string
  start?: string | null
  ende?: string | null
  sekunden: number
  kommentar?: string | null
  manuell: boolean
  kuerzel?: string | null  // Person des Eintrags (Snapshot beim Buchen)
  karte_titel?: string | null
  karte_schluessel?: string | null
  karte_zustaendig?: string | null
}

// -- Dokumente --
export type DokumentKontext = 'karte' | 'mappe'
export interface Dokument {
  id: string
  kontext: DokumentKontext
  kontext_id: string
  titel: string
  inhalt: string
  erstellt_am?: string | null
  bewegt_am?: string | null
}

// -- Schnell-Erfassung --
export interface ErfassenErgebnis {
  vorschau: boolean
  aktion: string
  karte?: { id: string; schluessel?: string | null; titel: string }
  sekunden?: number
  datum?: string | null
  kommentar?: string | null
}

// -- Heute-Uebersicht --
export interface HeuteEintrag {
  id: string
  board_id: string
  schluessel: string | null
  titel: string
  faellig: string | null
}
export interface HeuteUebersicht {
  datum: string
  ueberfaellig: HeuteEintrag[]
  heute: HeuteEintrag[]
  diese_woche: HeuteEintrag[]
  laufend: HeuteEintrag[]
  liegengeblieben: HeuteEintrag[]
  blockiert: HeuteEintrag[]
}

// -- Faelligkeits-Kalender --
export interface FaelligEintrag {
  id: string
  board_id: string
  schluessel: string | null
  titel: string
  faellig: string
  zustaendig: string | null
  erledigt: boolean
}

// -- Datei-Anhaenge an Karten --
export interface Anhang {
  id: string
  karte_id: string
  name: string
  groesse: number
  typ: string | null
  erstellt_am: string | null
}

// -- Aktivitaetsprotokoll (Verlauf je Karte + Benachrichtigungs-Glocke) --
export interface Aktivitaet {
  id: string
  karte_id: string
  zeit: string
  kuerzel: string | null
  art: string
  text: string
  // Nur in der Glocken-Sicht gefuellt:
  karte_titel: string | null
  karte_schluessel: string | null
  board_id: string | null
}

// -- Karten-Eingaben --
export interface KarteEingabe {
  board_id: string
  spalte: string
  titel: string
  beschreibung?: string | null
  labels?: string[]
  prioritaet?: Prioritaet | null
  cover?: string | null
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
  typ?: KartenTyp
}
export interface KarteAenderung {
  titel?: string
  beschreibung?: string | null
  notizen?: string | null
  blockiert_grund?: string | null
  labels?: string[]
  prioritaet?: Prioritaet | null
  checkliste?: ChecklistPunkt[]
  cover?: string | null
  spalte?: string
  start?: string | null
  faellig?: string | null
  zustaendig?: string | null
  schaetzung_min?: number | null
  transkript_id?: string | null
  transkript_name?: string | null
  typ?: KartenTyp
}
