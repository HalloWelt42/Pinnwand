// HTTP-Client zum Pinnwand-Backend. Reine Aufrufe; alle Datenmodelle leben in types.ts.

import type {
  Board,
  BoardDetail,
  Karte,
  Projektmappe,
  Spalte,
  Zeiteintrag,
  LabelDefinition,
  Erweiterungen,
  Dokument,
  DokumentKontext,
  ErfassenErgebnis,
  HeuteUebersicht,
  KarteEingabe,
  KarteAenderung,
  SuchErgebnis,
  SuchStatus,
  Dienst,
  Stimmen,
  TranskriptTreffer,
  TranskriptDetail,
  TranskriptMarke,
  MarkeEingabe,
  MarkeAenderung,
  Serie,
  SerienNachtrag,
  Person,
  Urlaubskonto,
  Urlaubstag,
  Feiertag,
  PlanTag,
  WochenOverride,
  Region,
  AbwesenheitTyp,
  Tagesregel,
  KalenderAntwort,
  StundenUebersicht,
  BerichtTyp,
  ArchivEintrag,
  BerichtAnfrage,
  SnapshotInfo,
  BackupZustand,
  BackupVorschau,
  WiederherstellenErgebnis,
  AgentToken,
  TerminSerie,
  TerminInstanz,
  KiStatusAntwort,
  KiAntwort,
  AuthStatus,
} from './types'
import { uiAuth, uiToken } from './uiAuth.svelte'
import { auth, authToken, setzeAuthToken } from './auth.svelte'

// Datenmodelle bleiben ueber api.ts erreichbar (viele Komponenten importieren von hier).
export type {
  AnsichtMeta,
  Erweiterungen,
  DokumentKontext,
  Dokument,
  ErfassenErgebnis,
  HeuteEintrag,
  HeuteUebersicht,
  KarteEingabe,
  KarteAenderung,
  SuchTreffer,
  SuchErgebnis,
  SuchStatus,
  Dienst,
  Stimmen,
  TranskriptTreffer,
  TranskriptDetail,
  TranskriptSegment,
  TranskriptMarke,
  MarkeEingabe,
  MarkeAenderung,
  Serie,
  SerienNachtrag,
  Person,
  Urlaubskonto,
  Urlaubstag,
  Feiertag,
  PlanTag,
  WochenOverride,
  Region,
  AbwesenheitTyp,
  Tagesregel,
  KalenderZelle,
  KalenderAntwort,
  StundenSumme,
  StundenUebersicht,
  BerichtTyp,
  ArchivEintrag,
  BerichtAnfrage,
  SnapshotInfo,
  BackupZustand,
  SchemaTabelle,
  BackupVorschau,
  WiederherstellenErgebnis,
  AgentToken,
  TerminSerie,
  TerminInstanz,
  KiStatusAntwort,
  KiVorschlag,
  KiAntwort,
  LabelDefinition,
  AuthStatus,
} from './types'

const BASIS = import.meta.env.VITE_API ?? 'http://localhost:8420'

async function hole<T>(pfad: string, init?: RequestInit): Promise<T> {
  const t = uiToken()
  const s = authToken()
  const antwort = await fetch(`${BASIS}${pfad}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(t ? { 'X-Pinnwand-Token': t } : {}),
      ...(s ? { 'X-Pinnwand-Sitzung': s } : {}),
    },
    ...init,
  })
  if (antwort.status === 401) {
    // Zwei Quellen einer 401 unterscheiden: optionales UI-Token vs. echte Anmeldung.
    let detail = ''
    try { detail = (await antwort.clone().json()).detail } catch { /* kein JSON */ }
    if (detail === 'UI-Token erforderlich') uiAuth.noetig = true
    else auth.angemeldet = false
    throw new Error(detail || 'nicht autorisiert')
  }
  if (!antwort.ok) {
    // Server-Begruendung (detail) mitliefern, damit die Oberflaeche sie anzeigen kann.
    let detail = ''
    try { detail = (await antwort.clone().json()).detail } catch { /* kein JSON */ }
    throw new Error(detail || `Anfrage fehlgeschlagen: ${antwort.status} ${antwort.statusText}`)
  }
  if (antwort.status === 204) return undefined as T
  return (await antwort.json()) as T
}

// --- Anmeldung (echtes Login mit Name/Kuerzel + Passwort) ---
export async function ladeAuthStatus(): Promise<void> {
  try {
    const s = await hole<AuthStatus>('/api/auth/status')
    auth.erforderlich = s.erforderlich
    auth.angemeldet = s.angemeldet
    auth.personId = s.person_id ?? null
    auth.name = s.name ?? null
    auth.kuerzel = s.kuerzel ?? null
    auth.rolle = (s.rolle as 'admin' | 'mitarbeiter' | null) ?? null
  } catch {
    /* offline o.ae.: Login bleibt inaktiv, App laeuft wie bisher */
  } finally {
    auth.geladen = true
  }
}

export async function anmelden(kennung: string, passwort: string): Promise<boolean> {
  const r = await fetch(`${BASIS}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kennung, passwort }),
  })
  if (!r.ok) return false
  const d = await r.json()
  setzeAuthToken(d.token)
  await ladeAuthStatus()
  return true
}

export async function abmelden(): Promise<void> {
  try { await hole('/api/auth/logout', { method: 'POST' }) } catch { /* egal */ }
  setzeAuthToken('')
}

export const setzeLoginModus = (erforderlich: boolean): Promise<AuthStatus> =>
  hole('/api/auth/login-modus', { method: 'PUT', body: JSON.stringify({ erforderlich }) })

export const setzePersonPasswort = (id: string, passwort: string): Promise<Person> =>
  hole(`/api/planung/personen/${id}/passwort`, { method: 'POST', body: JSON.stringify({ passwort }) })

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
export const ladeDokumente = (kontext: DokumentKontext, kontextId: string): Promise<Dokument[]> =>
  hole(`/api/kanban/dokumente?kontext=${kontext}&kontext_id=${encodeURIComponent(kontextId)}`)

export const erstelleDokument = (kontext: DokumentKontext, kontextId: string, titel: string): Promise<Dokument> =>
  hole('/api/kanban/dokumente', { method: 'POST', body: JSON.stringify({ kontext, kontext_id: kontextId, titel }) })

export const aktualisiereDokument = (id: string, daten: { titel?: string; inhalt?: string }): Promise<Dokument> =>
  hole(`/api/kanban/dokumente/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const loescheDokument = (id: string): Promise<void> =>
  hole(`/api/kanban/dokumente/${id}`, { method: 'DELETE' })

// --- Schnell-Erfassung (natuersprachliche Zeitbuchung mit Vorschau) ---
export const schnellErfassen = (text: string, dryRun: boolean): Promise<ErfassenErgebnis> =>
  hole('/api/kanban/schnell-erfassen', { method: 'POST', body: JSON.stringify({ text, dry_run: dryRun }) })
export const ladeBoard = (boardId: string): Promise<BoardDetail> => hole(`/api/kanban/boards/${boardId}`)

export const ladeHeute = (): Promise<HeuteUebersicht> => hole('/api/kanban/heute')

// --- Karten ---

export const erstelleKarte = (eingabe: KarteEingabe): Promise<Karte> =>
  hole('/api/kanban/karten', { method: 'POST', body: JSON.stringify(eingabe) })

// Verknuepfte Aufgaben (geteilte Zeitgruppe)
export const karteVerknuepfen = (id: string, zielKarteId: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/verknuepfen`, { method: 'POST', body: JSON.stringify({ ziel_karte_id: zielKarteId }) })

export const verknuepfungLoesen = (id: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/verknuepfung-loesen`, { method: 'POST' })

export const gruppeZeitTeilen = (gruppeId: string, geteilt: boolean): Promise<void> =>
  hole(`/api/kanban/gruppen/${gruppeId}`, { method: 'PATCH', body: JSON.stringify({ zeit_geteilt: geteilt }) })

export const aktualisiereKarte = (id: string, daten: KarteAenderung): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const verschiebeKarte = (id: string, spalte: string, reihenfolge: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${id}/move`, { method: 'POST', body: JSON.stringify({ spalte, reihenfolge }) })

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

// Alle Zeiteintraege einer Karte ueber alle Tage (Tages-Aufschluesselung im Ticket).
export const ladeKartenZeiten = (karteId: string): Promise<Zeiteintrag[]> =>
  hole(`/api/kanban/zeiteintraege?karte_id=${encodeURIComponent(karteId)}`)

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
export const setzeErledigtSpalte = (spalteId: string): Promise<Spalte> =>
  hole(`/api/kanban/spalten/${spalteId}/erledigt`, { method: 'POST' })

// --- Label-Verwaltung (zentrale Farbe je Label-Name) ---

export const ladeLabels = (): Promise<LabelDefinition[]> => hole('/api/kanban/labels')
export const erstelleLabel = (name: string, familie: string): Promise<LabelDefinition> =>
  hole('/api/kanban/labels', { method: 'POST', body: JSON.stringify({ name, familie }) })
export const aktualisiereLabel = (id: string, daten: { name?: string; familie?: string }): Promise<LabelDefinition> =>
  hole(`/api/kanban/labels/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheLabel = (id: string): Promise<void> =>
  hole(`/api/kanban/labels/${id}`, { method: 'DELETE' })

// --- Suche ---

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

export const ladeDienste = (): Promise<{ bind: string; dienste: Dienst[] }> => hole('/api/dienste')

export const ttsStimmen = (): Promise<{ stimmen: Stimmen | [] }> => hole('/api/tts/stimmen')

// --- Transkripte ---

export const transkripteStatus = (): Promise<{ erreichbar: boolean; konfiguriert: boolean }> =>
  hole('/api/transkripte/status')
export const transkripteSuche = (q: string, limit = 30): Promise<{ treffer: TranskriptTreffer[] }> =>
  hole(`/api/transkripte/suche?q=${encodeURIComponent(q)}&limit=${limit}`)
export const transkriptDetail = (id: string): Promise<TranskriptDetail> =>
  hole(`/api/transkripte/${id}`)

export const ladeMarken = (karteId: string): Promise<{ marken: TranskriptMarke[] }> =>
  hole(`/api/transkripte/marken?karte_id=${encodeURIComponent(karteId)}`)
export const markenJeTranskript = (tid: string): Promise<{ marken: TranskriptMarke[] }> =>
  hole(`/api/transkripte/${tid}/marken`)
export const erstelleMarke = (eingabe: MarkeEingabe): Promise<TranskriptMarke> =>
  hole('/api/transkripte/marken', { method: 'POST', body: JSON.stringify(eingabe) })
export const aktualisiereMarke = (id: string, daten: MarkeAenderung): Promise<TranskriptMarke> =>
  hole(`/api/transkripte/marken/${id}`, { method: 'PATCH', body: JSON.stringify(daten) })
export const loescheMarke = (id: string): Promise<void> =>
  hole(`/api/transkripte/marken/${id}`, { method: 'DELETE' })
export const zusammenfassungVorschlag = (transkriptId: string, positionSek: number | null): Promise<{ zusammenfassung: string }> =>
  hole('/api/transkripte/zusammenfassung-vorschlag', { method: 'POST', body: JSON.stringify({ transkript_id: transkriptId, position_sek: positionSek }) })

// Arbeitspool: ausgewaehlte, fuer die Arbeit relevante Transkripte (Vorfilter).
export const ladePool = (): Promise<{ pool: { transkript_id: string; transkript_name?: string | null }[] }> =>
  hole('/api/transkripte/pool')
export const poolAufnehmen = (transkriptId: string, name: string | null): Promise<{ ok: boolean }> =>
  hole('/api/transkripte/pool', { method: 'POST', body: JSON.stringify({ transkript_id: transkriptId, transkript_name: name }) })
export const poolEntfernen = (transkriptId: string): Promise<void> =>
  hole(`/api/transkripte/pool/${encodeURIComponent(transkriptId)}`, { method: 'DELETE' })

// --- Serien (wiederkehrende Termine/Aufgaben) ---

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

export const ladeSerienNachtraege = (): Promise<SerienNachtrag[]> => hole('/api/serien/nachtraege')
export const serieNachtragen = (karteId: string, dauerMin: number): Promise<Karte> =>
  hole(`/api/serien/nachtraege/${karteId}`, { method: 'POST', body: JSON.stringify({ dauer_min: dauerMin }) })

// --- Planung (Personen, Urlaub, Feiertage) ---

export const ladePersonen = (): Promise<Person[]> => hole('/api/planung/personen')
export const ladeUrlaubskonten = (jahr: number): Promise<Urlaubskonto[]> =>
  hole(`/api/planung/urlaubskonten?jahr=${jahr}`)
export const erstellePerson = (d: Partial<Person>): Promise<Person> =>
  hole('/api/planung/personen', { method: 'POST', body: JSON.stringify(d) })
export const aktualisierePerson = (id: string, d: Partial<Person>): Promise<Person> =>
  hole(`/api/planung/personen/${id}`, { method: 'PATCH', body: JSON.stringify(d) })
export const loeschePerson = (id: string): Promise<void> =>
  hole(`/api/planung/personen/${id}`, { method: 'DELETE' })

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

export const ladeKalender = (jahr: number): Promise<KalenderAntwort> =>
  hole(`/api/planung/kalender?jahr=${jahr}`)

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

// --- KI-Assistent (optionale 2. Option an datenreichen Stellen) ---
export const kiStatus = (): Promise<KiStatusAntwort> => hole('/api/ki/status')

export const kiAufgabe = (
  typ: string,
  kontext: Record<string, unknown>,
  anweisung = '',
): Promise<KiAntwort> =>
  hole('/api/ki/aufgabe', { method: 'POST', body: JSON.stringify({ typ, kontext, anweisung }) })
