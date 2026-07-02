// Systemnahe Datenmodelle: Modul-Erweiterungen, Anmeldung, Dienste/TTS,
// Berichte, Sicherung (Backup/Restore), Agenten-Zugriff und KI-Assistent.

// -- Modul-Erweiterungen / Manifest --
export interface AnsichtMeta {
  id: string
  titel: string
  icon: string
  // Aus dem Modul-Manifest: Sortierung, board-unabhaengig, nur fuer Admins.
  reihenfolge?: number
  global?: boolean
  adminOnly?: boolean
}
export interface Erweiterungen {
  views: { modul: string; wert: AnsichtMeta }[]
  cardFields: { modul: string; wert: unknown }[]
  mappeTabs: { modul: string; wert: unknown }[]
  commands: { modul: string; wert: unknown }[]
}

// -- Anmeldung --
export interface AuthStatus {
  erforderlich: boolean
  angemeldet: boolean
  person_id?: string | null
  name?: string | null
  kuerzel?: string | null
  rolle?: 'admin' | 'mitarbeiter' | null
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
