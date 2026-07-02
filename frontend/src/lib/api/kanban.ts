// HTTP-Aufrufe rund um das Kanban-Brett: Mappen/Projekte, Boards, Spalten,
// Karten, Zeiterfassung, Labels, Dokumente, Heute/Fällig, Anhänge und
// Aktivitäten.

import type {
  Aktivitaet,
  Anhang,
  Board,
  FaelligEintrag,
  BoardDetail,
  KartenSeite,
  KanbanEinstellungen,
  Karte,
  Projektmappe,
  ProjektAufwand,
  ProjektDetail,
  Spalte,
  Zeiteintrag,
  LabelDefinition,
  Dokument,
  DokumentKontext,
  ErfassenErgebnis,
  HeuteUebersicht,
  KarteEingabe,
  KarteAenderung,
} from '../types'
import { BASIS, hole, authKopf, ladeDateiHerunter } from './basis'

export const ladeMappen = (): Promise<Projektmappe[]> => hole('/api/kanban/mappen')
export const ladeBoards = (mappeId: string): Promise<Board[]> => hole(`/api/kanban/mappen/${mappeId}/boards`)

// Projekt-Mitglieder (wer sieht das Projekt). Pflege: Admins und Mitglieder der Mappe.
export const ladeMappenMitglieder = (mappeId: string): Promise<string[]> =>
  hole(`/api/kanban/mappen/${mappeId}/mitglieder`)
export const setzeMappenMitglied = (mappeId: string, personId: string): Promise<void> =>
  hole(`/api/kanban/mappen/${mappeId}/mitglieder/${personId}`, { method: 'PUT' })
export const entferneMappenMitglied = (mappeId: string, personId: string): Promise<void> =>
  hole(`/api/kanban/mappen/${mappeId}/mitglieder/${personId}`, { method: 'DELETE' })

export const erstelleMappe = (titel: string, beschreibung?: string): Promise<Projektmappe> =>
  hole('/api/kanban/mappen', { method: 'POST', body: JSON.stringify({ titel, beschreibung }) })

export const benenneMappe = (mappeId: string, titel: string): Promise<Projektmappe> =>
  hole(`/api/kanban/mappen/${mappeId}`, { method: 'PATCH', body: JSON.stringify({ titel }) })

// Allgemeines Aendern der Projektfelder (Titel, Owner, Budget, Status).
export const aktualisiereMappe = (
  mappeId: string,
  patch: Partial<Pick<Projektmappe, 'titel' | 'beschreibung' | 'owner' | 'budget_min' | 'status'>>,
): Promise<Projektmappe> =>
  hole(`/api/kanban/mappen/${mappeId}`, { method: 'PATCH', body: JSON.stringify(patch) })

export const loescheMappe = (mappeId: string): Promise<void> =>
  hole(`/api/kanban/mappen/${mappeId}`, { method: 'DELETE' })

// Projekt-Aufwand (Mappe = Projekt): Ist/Soll/Budget je Projekt bzw. je Board/Person.
export const ladeProjekte = (): Promise<ProjektAufwand[]> => hole('/api/kanban/projekte')
export const ladeProjektDetail = (mappeId: string): Promise<ProjektDetail> =>
  hole(`/api/kanban/projekte/${mappeId}`)

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

// Eine einzelne Karte (Fallback, wenn eine fertige Karte nicht im gefensterten Board liegt).
export const ladeKarte = (id: string): Promise<Karte> => hole(`/api/kanban/karten/${id}`)

// Gefensterte Seite fertiger Karten EINER Erledigt-Spalte (Zeitfenster + Deckel + Nachladen).
export const ladeFertige = (
  spalteId: string,
  opts: { zeitraum?: string; offset?: number; limit?: number; q?: string; labels?: string[]; prioritaet?: string | null; zustaendig?: string[] } = {},
): Promise<KartenSeite> => {
  const p = new URLSearchParams()
  if (opts.zeitraum) p.set('zeitraum', opts.zeitraum)
  if (opts.offset) p.set('offset', String(opts.offset))
  if (opts.limit != null) p.set('limit', String(opts.limit))
  if (opts.q && opts.q.trim()) p.set('q', opts.q.trim())
  if (opts.labels && opts.labels.length) p.set('labels', opts.labels.join(','))
  if (opts.prioritaet) p.set('prioritaet', opts.prioritaet)
  if (opts.zustaendig && opts.zustaendig.length) p.set('zustaendig', opts.zustaendig.join(','))
  const qs = p.toString()
  return hole(`/api/kanban/spalten/${spalteId}/fertige${qs ? '?' + qs : ''}`)
}

// Archivierte fertige Karten eines Boards (aelter als die Archiv-Schwelle), paginiert.
export const ladeKartenArchiv = (
  boardId: string,
  opts: { offset?: number; limit?: number; q?: string } = {},
): Promise<KartenSeite> => {
  const p = new URLSearchParams()
  if (opts.offset) p.set('offset', String(opts.offset))
  if (opts.limit != null) p.set('limit', String(opts.limit))
  if (opts.q && opts.q.trim()) p.set('q', opts.q.trim())
  const qs = p.toString()
  return hole(`/api/kanban/boards/${boardId}/archiv${qs ? '?' + qs : ''}`)
}

export const ladeKanbanEinstellungen = (): Promise<KanbanEinstellungen> => hole('/api/kanban/einstellungen')
export const setzeKanbanEinstellungen = (e: KanbanEinstellungen): Promise<KanbanEinstellungen> =>
  hole('/api/kanban/einstellungen', { method: 'PUT', body: JSON.stringify(e) })

export const ladeHeute = (): Promise<HeuteUebersicht> => hole('/api/kanban/heute')

export const ladeFaellige = (von: string, bis: string): Promise<FaelligEintrag[]> =>
  hole(`/api/kanban/faellig?von=${von}&bis=${bis}`)

// --- Datei-Anhaenge an Karten ---

export const ladeAnhaenge = (karteId: string): Promise<Anhang[]> =>
  hole(`/api/kanban/karten/${karteId}/anhaenge`)

export async function anhangHochladen(karteId: string, datei: File): Promise<Anhang> {
  const form = new FormData()
  form.append('datei', datei)
  const r = await fetch(`${BASIS}/api/kanban/karten/${karteId}/anhaenge`, {
    method: 'POST',
    headers: authKopf(),
    body: form,
  })
  if (!r.ok) {
    const detail = await r.json().then((d) => d.detail).catch(() => null)
    throw new Error(typeof detail === 'string' ? detail : 'Hochladen fehlgeschlagen')
  }
  return r.json()
}

export const anhangLoeschen = (anhangId: string): Promise<void> =>
  hole(`/api/kanban/anhaenge/${anhangId}`, { method: 'DELETE' })

export const anhangHerunterladen = (a: Anhang): Promise<void> =>
  ladeDateiHerunter(`/api/kanban/anhaenge/${a.id}`, a.name)

// --- Aktivitaetsprotokoll (Verlauf je Karte + Benachrichtigungs-Glocke) ---

export const ladeKartenAktivitaet = (karteId: string): Promise<Aktivitaet[]> =>
  hole(`/api/kanban/karten/${karteId}/aktivitaet`)

export const ladeGlocke = (kuerzel: string, seit?: string | null): Promise<Aktivitaet[]> => {
  const p = new URLSearchParams({ kuerzel })
  if (seit) p.set('seit', seit)
  return hole(`/api/kanban/aktivitaet?${p.toString()}`)
}

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

// Checkliste als Einzeloperationen (atomar im Backend - kein Ganz-Listen-Ersatz,
// zwei gleichzeitige Bearbeiter ueberschreiben sich nicht mehr).
export const checklistePunktNeu = (karteId: string, text: string): Promise<Karte> =>
  hole(`/api/kanban/karten/${karteId}/checkliste`, { method: 'POST', body: JSON.stringify({ text }) })

export const checklistePunktAendern = (
  karteId: string,
  index: number,
  daten: { text?: string; erledigt?: boolean },
): Promise<Karte> =>
  hole(`/api/kanban/karten/${karteId}/checkliste/${index}`, { method: 'PATCH', body: JSON.stringify(daten) })

export const checklistePunktLoeschen = (karteId: string, index: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${karteId}/checkliste/${index}`, { method: 'DELETE' })

export const loescheKarte = (id: string): Promise<void> =>
  hole(`/api/kanban/karten/${id}`, { method: 'DELETE' })

// --- Zeiterfassung ---

export const ladeLaufend = (kuerzel?: string | null): Promise<Karte | null> =>
  hole(`/api/kanban/laufend${kuerzel ? `?kuerzel=${encodeURIComponent(kuerzel)}` : ''}`)

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

// Gesamt-Ticketzeit atomar setzen (Korrektur in EINER Transaktion serverseitig).
export const setzeTicketzeit = (karteId: string, sekunden: number): Promise<Karte> =>
  hole(`/api/kanban/karten/${karteId}/ticketzeit`, { method: 'POST', body: JSON.stringify({ sekunden }) })

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
