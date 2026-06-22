// HTTP-Client zum Pinnwand-Backend.

import type { Board, BoardDetail, ChecklistPunkt, Karte, Prioritaet, Projektmappe, Spalte, Zeiteintrag } from './types'
import { uiAuth, uiToken } from './uiAuth.svelte'

const BASIS = import.meta.env.VITE_API ?? 'http://localhost:8420'

async function hole<T>(pfad: string, init?: RequestInit): Promise<T> {
  const t = uiToken()
  const antwort = await fetch(`${BASIS}${pfad}`, {
    headers: { 'Content-Type': 'application/json', ...(t ? { 'X-Pinnwand-Token': t } : {}) },
    ...init,
  })
  if (antwort.status === 401) {
    uiAuth.noetig = true
    throw new Error('Anmeldung erforderlich')
  }
  if (!antwort.ok) throw new Error(`Anfrage fehlgeschlagen: ${antwort.status} ${antwort.statusText}`)
  if (antwort.status === 204) return undefined as T
  return (await antwort.json()) as T
}

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

export const ladeErweiterungen = (): Promise<Erweiterungen> => hole('/api/erweiterungen')
export const ladeMappen = (): Promise<Projektmappe[]> => hole('/api/kanban/mappen')
export const ladeBoards = (mappeId: string): Promise<Board[]> => hole(`/api/kanban/mappen/${mappeId}/boards`)

export const erstelleMappe = (titel: string, beschreibung?: string): Promise<Projektmappe> =>
  hole('/api/kanban/mappen', { method: 'POST', body: JSON.stringify({ titel, beschreibung }) })

export const benenneMappe = (mappeId: string, titel: string): Promise<Projektmappe> =>
  hole(`/api/kanban/mappen/${mappeId}`, { method: 'PATCH', body: JSON.stringify({ titel }) })

export const loescheMappe = (mappeId: string): Promise<void> =>
  hole(`/api/kanban/mappen/${mappeId}`, { method: 'DELETE' })

// --- Dokumente (Karten- und Mappen-Dokumente) ---
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

export const ladeDokumente = (kontext: DokumentKontext, kontextId: string): Promise<Dokument[]> =>
  hole(`/api/kanban/dokumente?kontext=${kontext}&kontext_id=${encodeURIComponent(kontextId)}`)

export const erstelleDokument = (kontext: DokumentKontext, kontextId: string, titel: string): Promise<Dokument> =>
  hole('/api/kanban/dokumente', { method: 'POST', body: JSON.stringify({ kontext, kontext_id: kontextId, titel }) })

export const aktualisiereDokument = (id: string, daten: { titel?: string; inhalt?: string }): Promise<Dokument> =>
  hole(`/api/kanban/dokumente/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const loescheDokument = (id: string): Promise<void> =>
  hole(`/api/kanban/dokumente/${id}`, { method: 'DELETE' })

// --- Schnell-Erfassung (natuersprachliche Zeitbuchung mit Vorschau) ---
export interface ErfassenErgebnis {
  vorschau: boolean
  aktion: string
  karte?: { id: string; schluessel?: string | null; titel: string }
  sekunden?: number
  datum?: string | null
  kommentar?: string | null
}
export const schnellErfassen = (text: string, dryRun: boolean): Promise<ErfassenErgebnis> =>
  hole('/api/kanban/schnell-erfassen', { method: 'POST', body: JSON.stringify({ text, dry_run: dryRun }) })
export const ladeBoard = (boardId: string): Promise<BoardDetail> => hole(`/api/kanban/boards/${boardId}`)

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
export const ladeHeute = (): Promise<HeuteUebersicht> => hole('/api/kanban/heute')

// --- Karten ---

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
}

export const erstelleKarte = (eingabe: KarteEingabe): Promise<Karte> =>
  hole('/api/kanban/karten', { method: 'POST', body: JSON.stringify(eingabe) })

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
}

export const aktualisiereKarte = (id: string, daten: KarteAenderung): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const verschiebeKarte = (id: string, spalte: string, reihenfolge: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/move`, { method: 'POST', body: JSON.stringify({ spalte, reihenfolge }) })

export const setzeErfasst = (id: string, sekunden: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/erfasst`, { method: 'PATCH', body: JSON.stringify({ sekunden }) })

export const anhaengenKommentar = (id: string, autor: string, text: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/kommentare`, { method: 'POST', body: JSON.stringify({ autor, text }) })

export const loescheKarte = (id: string): Promise<void> =>
  hole(`/api/kanban/karten/${id}`, { method: 'DELETE' })

// --- Zeiterfassung ---

export const ladeLaufend = (): Promise<Karte | null> => hole('/api/kanban/laufend')

export const timerStart = (id: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/timer/start`, { method: 'POST' })

export const timerPause = (id: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/timer/pause`, { method: 'POST' })

// --- Zeiteinträge (Auswertung) ---

export const ladeZeiteintraege = (von: string, bis: string): Promise<Zeiteintrag[]> =>
  hole(`/api/kanban/zeiteintraege?von=${von}&bis=${bis}`)

export const erstelleZeiteintrag = (eingabe: { karte_id: string; datum: string; sekunden: number; kommentar?: string | null }): Promise<Zeiteintrag> =>
  hole('/api/kanban/zeiteintraege', { method: 'POST', body: JSON.stringify(eingabe) })

export const aktualisiereZeiteintrag = (id: string, daten: { datum?: string; sekunden?: number; kommentar?: string | null }): Promise<Zeiteintrag> =>
  hole(`/api/kanban/zeiteintraege/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const loescheZeiteintrag = (id: string): Promise<void> =>
  hole(`/api/kanban/zeiteintraege/${id}`, { method: 'DELETE' })

// --- Boards ---

export const erstelleBoard = (mappeId: string, titel: string): Promise<BoardDetail> =>
  hole(`/api/kanban/mappen/${mappeId}/boards`, { method: 'POST', body: JSON.stringify({ titel }) })

export const benenneBoard = (boardId: string, titel: string): Promise<Board> =>
  hole(`/api/kanban/boards/${boardId}`, { method: 'PATCH', body: JSON.stringify({ titel }) })

export const loescheBoard = (boardId: string): Promise<void> =>
  hole(`/api/kanban/boards/${boardId}`, { method: 'DELETE' })

export const setzeSpaltenReihenfolge = (boardId: string, spalten: string[]): Promise<void> =>
  hole(`/api/kanban/boards/${boardId}/spalten-reihenfolge`, { method: 'PATCH', body: JSON.stringify({ spalten }) })

// --- Spalten ---

export const erstelleSpalte = (boardId: string, titel: string, wipLimit: number | null = null): Promise<Spalte> =>
  hole(`/api/kanban/boards/${boardId}/spalten`, { method: 'POST', body: JSON.stringify({ titel, wip_limit: wipLimit }) })

export const aktualisiereSpalte = (spalteId: string, daten: { titel?: string; wip_limit?: number | null }): Promise<Spalte> =>
  hole(`/api/kanban/spalten/${spalteId}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const verschiebeSpalte = (spalteId: string, richtung: -1 | 1): Promise<Spalte> =>
  hole(`/api/kanban/spalten/${spalteId}/move`, { method: 'POST', body: JSON.stringify({ richtung }) })

export const loescheSpalte = (spalteId: string): Promise<void> =>
  hole(`/api/kanban/spalten/${spalteId}`, { method: 'DELETE' })

// --- Suche ---

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

export const sucheInhalte = (q: string, limit = 15): Promise<SuchErgebnis> =>
  hole(`/api/suche?q=${encodeURIComponent(q)}&limit=${limit}`)

export const sucheStatus = (): Promise<SuchStatus> => hole('/api/suche/status')

export async function transkribiere(audio: Blob): Promise<{ text: string }> {
  const daten = new FormData()
  daten.append('datei', audio, 'aufnahme.webm')
  const antwort = await fetch(`${BASIS}/api/suche/sprache`, { method: 'POST', body: daten })
  if (!antwort.ok) throw new Error('Spracheingabe nicht verfügbar')
  return antwort.json()
}

// --- Vorlesen (TTS) ---

export const ttsStatus = (): Promise<{ verfuegbar: boolean }> => hole('/api/tts/status')

export interface Dienst {
  schluessel: string
  name: string
  konfiguriert: boolean
  erreichbar: boolean
}
export const ladeDienste = (): Promise<{ bind: string; dienste: Dienst[] }> => hole('/api/dienste')

export interface Stimmen {
  model?: string
  speakers?: string[]
  custom?: { id: string; name: string }[]
}
export const ttsStimmen = (): Promise<{ stimmen: Stimmen | [] }> => hole('/api/tts/stimmen')

// --- Transkripte ---

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
export const transkripteStatus = (): Promise<{ erreichbar: boolean; konfiguriert: boolean }> =>
  hole('/api/transkripte/status')
export const transkripteSuche = (q: string, limit = 30): Promise<{ treffer: TranskriptTreffer[] }> =>
  hole(`/api/transkripte/suche?q=${encodeURIComponent(q)}&limit=${limit}`)
export const transkriptDetail = (id: string): Promise<TranskriptDetail> =>
  hole(`/api/transkripte/${id}`)

// --- Serien (wiederkehrende Termine/Aufgaben) ---

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
export const ladeSerien = (boardId: string): Promise<Serie[]> => hole(`/api/serien?board_id=${boardId}`)
export const erstelleSerie = (daten: Partial<Serie>): Promise<Serie> =>
  hole('/api/serien', { method: 'POST', body: JSON.stringify(daten) })
export const aktualisiereSerie = (id: string, daten: Partial<Serie>): Promise<Serie> =>
  hole(`/api/serien/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheSerie = (id: string): Promise<void> =>
  hole(`/api/serien/${id}`, { method: 'DELETE' })
export const serieVorschau = (id: string, tage = 30): Promise<{ termine: string[] }> =>
  hole(`/api/serien/${id}/vorschau?tage=${tage}`)
export const serieVorbuchen = (id: string): Promise<{ erzeugt: number }> =>
  hole(`/api/serien/${id}/vorbuchen`, { method: 'POST' })
export const serienVorbuchenAlle = (): Promise<{ erzeugt: number }> =>
  hole('/api/serien/vorbuchen', { method: 'POST' })

export interface SerienNachtrag {
  karte_id: string
  schluessel: string | null
  titel: string
  datum: string
  serie_titel: string
  soll_min: number | null
}
export const ladeSerienNachtraege = (): Promise<SerienNachtrag[]> => hole('/api/serien/nachtraege')
export const serieNachtragen = (karteId: string, dauerMin: number): Promise<Karte> =>
  hole(`/api/serien/nachtraege/${karteId}`, { method: 'POST', body: JSON.stringify({ dauer_min: dauerMin }) })

// --- Planung (Personen, Urlaub, Feiertage) ---

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

export const ladePersonen = (): Promise<Person[]> => hole('/api/planung/personen')
export const ladeUrlaubskonten = (jahr: number): Promise<Urlaubskonto[]> =>
  hole(`/api/planung/urlaubskonten?jahr=${jahr}`)
export const erstellePerson = (d: Partial<Person>): Promise<Person> =>
  hole('/api/planung/personen', { method: 'POST', body: JSON.stringify(d) })
export const aktualisierePerson = (id: string, d: Partial<Person>): Promise<Person> =>
  hole(`/api/planung/personen/${id}`, { method: 'PATCH', body: JSON.stringify(d) })
export const loeschePerson = (id: string): Promise<void> =>
  hole(`/api/planung/personen/${id}`, { method: 'DELETE' })

export interface WochenOverride { jahr: number; kw: number; wochenstunden: number[] }
export const ladeWochenOverride = (personId: string): Promise<WochenOverride[]> =>
  hole(`/api/planung/personen/${personId}/wochen-override`)
export const setzeWochenOverride = (personId: string, jahr: number, kw: number, wochenstunden: number[]): Promise<WochenOverride> =>
  hole(`/api/planung/personen/${personId}/wochen-override`, { method: 'POST', body: JSON.stringify({ jahr, kw, wochenstunden }) })
export const loescheWochenOverride = (personId: string, jahr: number, kw: number): Promise<void> =>
  hole(`/api/planung/personen/${personId}/wochen-override/${jahr}/${kw}`, { method: 'DELETE' })

export const ladeUrlaub = (person: string, von: string, bis: string): Promise<Urlaubstag[]> =>
  hole(`/api/planung/urlaub?person=${person}&von=${von}&bis=${bis}`)
export const setzeUrlaub = (d: { person_id: string; von: string; bis?: string; anteil?: number; typ?: string; notiz?: string; wochenenden_ueberspringen?: boolean; feiertage_ueberspringen?: boolean }): Promise<{ gesetzt: number; uebersprungen: number }> =>
  hole('/api/planung/urlaub', { method: 'POST', body: JSON.stringify(d) })
export const loescheUrlaub = (id: string): Promise<void> =>
  hole(`/api/planung/urlaub/${id}`, { method: 'DELETE' })

export interface Region {
  code: string
  name: string
}
export const ladeLaender = (): Promise<{ verfuegbar: boolean; laender: Record<string, Region[]> }> =>
  hole('/api/planung/laender')
export const ladeFeiertage = (von: string, bis: string): Promise<Feiertag[]> =>
  hole(`/api/planung/feiertage?von=${von}&bis=${bis}`)
export const feiertageVorschau = (land: string, region: string | null, jahr: number): Promise<{ eintraege: Feiertag[] }> =>
  hole(`/api/planung/feiertage/vorschau?land=${land}&jahr=${jahr}${region ? `&region=${region}` : ''}`)
export const feiertageUebernehmen = (land: string, region: string | null, jahr: number): Promise<{ uebernommen: number }> =>
  hole('/api/planung/feiertage/uebernehmen', { method: 'POST', body: JSON.stringify({ land, region, jahr }) })
export const loescheFeiertage = (jahr: number, region: string | null): Promise<{ geloescht: number }> =>
  hole(`/api/planung/feiertage?jahr=${jahr}${region ? `&region=${region}` : ''}`, { method: 'DELETE' })

export const ladePlanungsTage = (von: string, bis: string, person?: string): Promise<PlanTag[]> =>
  hole(`/api/planung/tage?von=${von}&bis=${bis}${person ? `&person=${person}` : ''}`)

// --- Jahreskalender: Abwesenheitsarten, Tagesregeln, Aggregation ---

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

export const ladeKalender = (jahr: number): Promise<KalenderAntwort> =>
  hole(`/api/planung/kalender?jahr=${jahr}`)

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
export const ladeStundenUebersicht = (personId?: string): Promise<StundenUebersicht> =>
  hole(`/api/planung/stunden-uebersicht${personId ? `?person=${encodeURIComponent(personId)}` : ''}`)
export const ladeAbwesenheitstypen = (): Promise<AbwesenheitTyp[]> =>
  hole('/api/planung/abwesenheitstypen')
export const aktualisiereAbwesenheitstyp = (code: string, d: Partial<AbwesenheitTyp>): Promise<AbwesenheitTyp> =>
  hole(`/api/planung/abwesenheitstypen/${code}`, { method: 'PATCH', body: JSON.stringify(d) })
export const ladeTagesregeln = (person?: string): Promise<Tagesregel[]> =>
  hole(`/api/planung/tagesregeln${person ? `?person=${person}` : ''}`)
export const setzeTagesregel = (d: Partial<Tagesregel>): Promise<Tagesregel> =>
  hole('/api/planung/tagesregeln', { method: 'POST', body: JSON.stringify(d) })
export const loescheTagesregel = (id: string): Promise<void> =>
  hole(`/api/planung/tagesregeln/${id}`, { method: 'DELETE' })
export const leereTag = (person_id: string, datum: string): Promise<{ geloescht: number }> =>
  hole('/api/planung/tag-leeren', { method: 'POST', body: JSON.stringify({ person_id, datum }) })

// --- Berichte ---

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
export const ladeBerichtTypen = (): Promise<{ typen: BerichtTyp[] }> => hole('/api/berichte/typen')
export const ladeArchiv = (): Promise<ArchivEintrag[]> => hole('/api/berichte/archiv')
export const archivDownloadUrl = (id: string): string => `${BASIS}/api/berichte/archiv/${id}`

export async function erzeugeBericht(anfrage: BerichtAnfrage): Promise<{ blob: Blob; dateiname: string }> {
  const r = await fetch(`${BASIS}/api/berichte/erzeugen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(anfrage),
  })
  if (!r.ok) throw new Error('Bericht konnte nicht erzeugt werden')
  const cd = r.headers.get('Content-Disposition') || ''
  const m = cd.match(/filename="(.+?)"/)
  return { blob: await r.blob(), dateiname: m ? m[1] : 'bericht' }
}

// --- Sicherung (Backup/Restore) ---

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

export const ladeSnapshots = (): Promise<SnapshotInfo[]> => hole('/api/backup')
export const backupZustand = (): Promise<BackupZustand> => hole('/api/backup/zustand')
export const erzeugeSnapshot = (notiz: string): Promise<SnapshotInfo> =>
  hole('/api/backup/erzeugen', { method: 'POST', body: JSON.stringify({ notiz }) })
export const snapshotVorschau = (id: string): Promise<BackupVorschau> =>
  hole(`/api/backup/${id}/vorschau`)
export const snapshotDownloadUrl = (id: string): string => `${BASIS}/api/backup/${id}/datei`
export const stelleSnapshotWiederHer = (id: string): Promise<WiederherstellenErgebnis> =>
  hole(`/api/backup/${id}/wiederherstellen`, { method: 'POST' })
export const loescheSnapshot = (id: string): Promise<void> =>
  hole(`/api/backup/${id}`, { method: 'DELETE' })
export const datenZuruecksetzen = (modus: 'beispiel' | 'leer'): Promise<{ ok: boolean; modus: string; vorher_gesichert: string }> =>
  hole('/api/backup/zuruecksetzen', { method: 'POST', body: JSON.stringify({ modus }) })

// --- Agenten-Zugriff (Token-Verwaltung, Scope admin) ---

export interface AgentToken {
  id: string
  name: string
  scopes: string[]
  erstellt_am: string
  zuletzt_genutzt: string | null
  aktiv: boolean
}

export class AuthFehler extends Error {}

async function adminHole<T>(pfad: string, adminToken: string, init?: RequestInit): Promise<T> {
  const antwort = await fetch(`${BASIS}${pfad}`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${adminToken}` },
    ...init,
  })
  if (antwort.status === 401 || antwort.status === 403) {
    throw new AuthFehler('Verwaltungs-Token ungültig oder ohne Admin-Recht')
  }
  if (!antwort.ok) throw new Error(`Anfrage fehlgeschlagen: ${antwort.status}`)
  if (antwort.status === 204) return undefined as T
  return (await antwort.json()) as T
}

export const ladeAgentTokens = (adminToken: string): Promise<AgentToken[]> =>
  adminHole('/api/agent/token', adminToken)

export const erstelleAgentToken = (adminToken: string, name: string, scopes: string[]): Promise<AgentToken & { token: string }> =>
  adminHole('/api/agent/token', adminToken, { method: 'POST', body: JSON.stringify({ name, scopes }) })

export const widerrufeAgentToken = (adminToken: string, id: string): Promise<void> =>
  adminHole(`/api/agent/token/${id}`, adminToken, { method: 'DELETE' })

export async function vorleseAudio(text: string, stimme?: string): Promise<Blob> {
  const antwort = await fetch(`${BASIS}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, stimme }),
  })
  if (!antwort.ok) throw new Error('Vorlesen nicht verfügbar')
  return antwort.blob()
}

// --- Termine (leichte Meeting-Zeiterfassung mit Folgetag-Bestaetigung) ---
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
export const ladeTerminSerien = (): Promise<TerminSerie[]> => hole('/api/termine/serien')
export const erstelleTerminSerie = (daten: Partial<TerminSerie>): Promise<TerminSerie> =>
  hole('/api/termine/serien', { method: 'POST', body: JSON.stringify(daten) })
export const aktualisiereTerminSerie = (id: string, daten: Partial<TerminSerie>): Promise<TerminSerie> =>
  hole(`/api/termine/serien/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheTerminSerie = (id: string): Promise<void> =>
  hole(`/api/termine/serien/${id}`, { method: 'DELETE' })
export const ladeTerminInstanzen = (p: { status?: string; von?: string; bis?: string } = {}): Promise<TerminInstanz[]> => {
  const q = new URLSearchParams()
  if (p.status) q.set('status', p.status)
  if (p.von) q.set('von', p.von)
  if (p.bis) q.set('bis', p.bis)
  const s = q.toString()
  return hole(`/api/termine/instanzen${s ? '?' + s : ''}`)
}
export const termineOffenAnzahl = (): Promise<{ anzahl: number }> => hole('/api/termine/offen/anzahl')
export const bestaetigeTermin = (id: string, dauerMin?: number): Promise<TerminInstanz> =>
  hole(`/api/termine/instanzen/${id}/bestaetigen`, { method: 'POST', body: JSON.stringify({ dauer_min: dauerMin ?? null }) })
export const lehneTerminAb = (id: string): Promise<TerminInstanz> =>
  hole(`/api/termine/instanzen/${id}/ablehnen`, { method: 'POST' })
export const bestaetigeAlleTermine = (ids?: string[]): Promise<{ bestaetigt: number }> =>
  hole('/api/termine/instanzen/bestaetigen-alle', { method: 'POST', body: JSON.stringify({ ids: ids ?? null }) })
export const materialisiereTermine = (): Promise<{ erzeugt: number }> =>
  hole('/api/termine/materialisieren', { method: 'POST' })
