// Zentrale Datenmodelle des Frontends (spiegeln backend/module/*/models.py).
// api.ts enthaelt nur HTTP-Aufrufe und re-exportiert die hier definierten Typen.

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

export interface Projektmappe {
  id: string
  titel: string
  beschreibung?: string | null
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
  karte_titel?: string | null
  karte_schluessel?: string | null
  karte_zustaendig?: string | null
}

// === Weitere Module (aus api.ts hierher zentralisiert; api.ts re-exportiert sie) ===

// -- Modul-Erweiterungen / Manifest --
export interface AnsichtMeta {
  id: string
  titel: string
  icon: string
}
export interface Erweiterungen {
  views: { modul: string; wert: AnsichtMeta }[]
  cardFields: { modul: string; wert: unknown }[]
  mappeTabs: { modul: string; wert: unknown }[]
  commands: { modul: string; wert: unknown }[]
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

// -- Suche --
export interface SuchTreffer {
  karte_id: string
  schluessel: string | null
  titel: string
  board_id?: string
  spalte?: string
  score?: number
  quelle: string
}
export interface SuchErgebnis {
  treffer: SuchTreffer[]
  anzahl: number
  modus: string
}
export interface SuchStatus {
  embeddings: boolean
  vektor_konfiguriert: boolean
  vektor_erreichbar: boolean
  mikrofon: boolean
  modus: string
}

// -- Dienste / TTS --
export interface Dienst {
  schluessel: string
  name: string
  konfiguriert: boolean
  erreichbar: boolean
}
export interface Stimmen {
  model?: string
  speakers?: string[]
  custom?: { id: string; name: string }[]
}

// -- Transkripte --
export interface TranskriptTreffer {
  id: string
  name: string
  snippet: string
  speaker_names: string[]
  language?: string
  start?: number | null
}
export interface TranskriptDetail {
  id: string
  name: string
  full_text: string
  speaker_names: string[]
  language?: string
  audio_url?: string | null
  segment_count?: number
  segmente?: TranskriptSegment[]
}
export interface TranskriptSegment {
  start: number
  text: string
  speaker?: string | null
}
// Transkript-Marke: verbindet eine Karte mit einer Stelle im Transkript.
export interface TranskriptMarke {
  id: string
  karte_id: string
  transkript_id: string
  transkript_name?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
  titel?: string | null
  zusammenfassung?: string | null
  reihenfolge: number
  erstellt_am?: string | null
  // nur bei marken-je-Transkript mitgeliefert:
  karte_schluessel?: string | null
  karte_titel?: string | null
  karte_board?: string | null
}
export interface MarkeEingabe {
  karte_id: string
  transkript_id: string
  transkript_name?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
  titel?: string | null
  zusammenfassung?: string | null
}
export interface MarkeAenderung {
  titel?: string | null
  zusammenfassung?: string | null
  position_sek?: number | null
  segment_text?: string | null
  sprecher?: string | null
}

// -- Serien (wiederkehrende Termine/Aufgaben) --
export interface Serie {
  id: string
  board_id: string
  spalte_id?: string | null
  titel: string
  beschreibung?: string | null
  labels: string[]
  zustaendig?: string | null
  typ: 'taeglich' | 'woechentlich' | 'monatlich'
  intervall: number
  wochentage: number[]
  monatstag?: number | null
  monatsregel?: 'tag' | 'erster_werktag' | 'letzter_werktag'
  uhrzeit?: string | null
  dauer_min?: number | null
  wochenenden_ueberspringen: boolean
  feiertage_ueberspringen?: boolean
  vorlauf_tage: number
  start?: string | null
  ende?: string | null
  aktiv: boolean
}
export interface SerienNachtrag {
  karte_id: string
  schluessel: string | null
  titel: string
  datum: string
  serie_titel: string
  soll_min: number | null
}

// -- Planung (Personen, Urlaub, Feiertage) --
export interface Person {
  id: string
  name: string
  kuerzel?: string | null
  farbe?: string | null
  wochenstunden: number[]
  bundesland?: string | null
  urlaubsanspruch: number
  resturlaub_vorjahr: number
  aktiv: boolean
  rolle: 'admin' | 'mitarbeiter'
  hat_passwort?: boolean
}

export interface AuthStatus {
  erforderlich: boolean
  angemeldet: boolean
  person_id?: string | null
  name?: string | null
  kuerzel?: string | null
  rolle?: 'admin' | 'mitarbeiter' | null
}
export interface Urlaubskonto {
  person_id: string
  jahr: number
  anspruch: number
  uebertrag: number
  verfuegbar: number
  genommen: number
  verbleibend: number
  genommen_vorjahr: number
}
export interface Urlaubstag {
  id: string
  person_id: string
  datum: string
  anteil: number
  typ: string
  notiz?: string | null
}
export interface Feiertag {
  datum: string
  name: string
  region?: string | null
}
export interface PlanTag {
  datum: string
  wochenende: boolean
  feiertag: string | null
  urlaub: number
}
export interface WochenOverride { jahr: number; kw: number; wochenstunden: number[] }
export interface Region {
  code: string
  name: string
}
export interface AbwesenheitTyp {
  code: string
  name: string
  farbe: string
  reduziert_soll: boolean
  anrechnen: boolean
  anwesend: boolean
  reihenfolge: number
}
export interface Tagesregel {
  id: string
  person_id: string | null
  art: 'jahrestag' | 'wochentag' | 'brueckentag'
  monat?: number | null
  tag?: number | null
  wochentag?: number | null
  anteil: number
  notiz?: string | null
  aktiv: boolean
}
export interface KalenderZelle {
  soll: number
  ist_sek: number
  abw: { typ: string; anteil: number } | null
  feiertag: string | null
  regel: number | null
  status: 'anwesend' | 'abwesend' | 'frei' | 'feiertag'
}
export interface KalenderAntwort {
  jahr: number
  personen: { id: string; name: string; kuerzel: string | null; farbe: string | null }[]
  tage: string[]
  zellen: Record<string, Record<string, KalenderZelle>>
}
export interface StundenSumme {
  ist_sek: number
  soll_sek: number
}
export interface StundenUebersicht {
  heute: StundenSumme
  woche: StundenSumme
  monat: StundenSumme
  jahr: StundenSumme
}

// -- Berichte --
export interface BerichtTyp { id: string; titel: string }
export interface ArchivEintrag {
  id: string
  typ: string
  titel: string
  zeitraum: string
  format: string
  person?: string | null
  erstellt_am: string
  groesse: number
}
export interface BerichtAnfrage {
  typ: string
  format: string
  von?: string
  bis?: string
  person?: string | null
  board_id?: string | null
  archivieren?: boolean
}

// -- Sicherung (Backup/Restore) --
export interface SnapshotInfo {
  id: string
  dateiname: string
  erstellt_am: string
  groesse: number
  version: string
  art: 'manuell' | 'automatisch' | 'vor_wiederherstellung'
  notiz: string
}
export interface BackupZustand {
  version: string
  zaehler: Record<string, number>
  berichte: number
}
export interface SchemaTabelle {
  tabelle: string
  spalten: string[]
}
export interface BackupVorschau {
  info: SnapshotInfo
  snapshot: BackupZustand
  aktuell: BackupZustand
  schema: SchemaTabelle[]
  warnungen: string[]
}
export interface WiederherstellenErgebnis {
  ok: boolean
  vorher_gesichert: string
  wiederhergestellt: BackupZustand
}

// -- Agenten-Zugriff (Token-Verwaltung) --
export interface AgentToken {
  id: string
  name: string
  scopes: string[]
  erstellt_am: string
  zuletzt_genutzt: string | null
  aktiv: boolean
}

// -- Termine (leichte Meeting-Zeiterfassung) --
export interface TerminSerie {
  id: string
  titel: string
  beschreibung?: string | null
  kuerzel?: string | null
  typ: 'taeglich' | 'woechentlich' | 'monatlich'
  intervall: number
  wochentage: number[]
  monatstag?: number | null
  monatsregel?: 'tag' | 'erster_werktag' | 'letzter_werktag'
  uhrzeit?: string | null
  dauer_min: number
  wochenenden_ueberspringen: boolean
  feiertage_ueberspringen: boolean
  urlaub_ueberspringen: boolean
  rueckblick_tage: number
  start?: string | null
  ende?: string | null
  aktiv: boolean
}
export interface TerminInstanz {
  id: string
  serie_id: string
  datum: string
  kuerzel?: string | null
  titel: string
  uhrzeit?: string | null
  geplant_min: number
  status: 'schwebend' | 'bestaetigt' | 'abgelehnt'
  effektiv_min?: number | null
  bestaetigt_am?: string | null
}

// -- KI-Assistent --
export interface KiStatusAntwort {
  verfuegbar: boolean
  modell: string | null
  automatisch: boolean
}
export interface KiVorschlag {
  id: string
  text: string
  begruendung: string
  vorgewaehlt: boolean
}
export interface KiAntwort {
  ok: boolean
  modell: string | null
  vorschlaege: KiVorschlag[]
  fehler: string | null
}
