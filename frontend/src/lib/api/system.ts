// Systemnahe HTTP-Aufrufe: Anmeldung, Modul-Erweiterungen, Dienste/TTS,
// Berichte, Sicherung (Backup/Restore), Agenten-Zugriff und KI-Assistent.

import type {
  Erweiterungen,
  Dienst,
  Stimmen,
  Person,
  AuthStatus,
  BerichtTyp,
  ArchivEintrag,
  BerichtAnfrage,
  SnapshotInfo,
  BackupZustand,
  BackupVorschau,
  WiederherstellenErgebnis,
  AgentToken,
  KiStatusAntwort,
  KiAntwort,
} from '../types'
import { auth, setzeAuthToken } from '../auth.svelte'
import { BASIS, hole, authKopf, ladeDateiHerunter } from './basis'

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

// --- Modul-Erweiterungen ---

export const ladeErweiterungen = (): Promise<Erweiterungen> => hole('/api/erweiterungen')

// --- Vorlesen (TTS) ---

export const ttsStatus = (): Promise<{ verfuegbar: boolean }> => hole('/api/tts/status')

export const ladeDienste = (): Promise<{ bind: string; dienste: Dienst[] }> => hole('/api/dienste')

export const ttsStimmen = (): Promise<{ stimmen: Stimmen | [] }> => hole('/api/tts/stimmen')

export async function vorleseAudio(text: string, stimme?: string): Promise<Blob> {
  const antwort = await fetch(`${BASIS}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authKopf() },
    body: JSON.stringify({ text, stimme }),
  })
  if (!antwort.ok) throw new Error('Vorlesen nicht verfügbar')
  return antwort.blob()
}

// --- Berichte ---

export const ladeBerichtTypen = (): Promise<{ typen: BerichtTyp[] }> => hole('/api/berichte/typen')
export const ladeArchiv = (): Promise<ArchivEintrag[]> => hole('/api/berichte/archiv')
export const archivHerunterladen = (id: string): Promise<void> =>
  ladeDateiHerunter(`/api/berichte/archiv/${id}`, 'bericht')

export async function erzeugeBericht(anfrage: BerichtAnfrage): Promise<{ blob: Blob; dateiname: string }> {
  const r = await fetch(`${BASIS}/api/berichte/erzeugen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authKopf() },
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
export const snapshotHerunterladen = (id: string): Promise<void> =>
  ladeDateiHerunter(`/api/backup/${id}/datei`, 'snapshot.zip')
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

// --- KI-Assistent (optionale 2. Option an datenreichen Stellen) ---
export const kiStatus = (): Promise<KiStatusAntwort> => hole('/api/ki/status')

export const kiAufgabe = (
  typ: string,
  kontext: Record<string, unknown>,
  anweisung = '',
): Promise<KiAntwort> =>
  hole('/api/ki/aufgabe', { method: 'POST', body: JSON.stringify({ typ, kontext, anweisung }) })
