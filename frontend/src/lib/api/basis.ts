// Querschnitts-Helfer des HTTP-Clients: Basis-URL, Auth-Kopfzeilen, hole()
// und der Datei-Download. Alle bereichsbezogenen Module bauen hierauf auf.

import { uiAuth, uiToken } from '../uiAuth.svelte'
import { auth, authToken } from '../auth.svelte'

export const BASIS = import.meta.env.VITE_API ?? 'http://localhost:8420'

export async function hole<T>(pfad: string, init?: RequestInit): Promise<T> {
  const t = uiToken()
  const s = authToken()
  let antwort: Response
  try {
    antwort = await fetch(`${BASIS}${pfad}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(t ? { 'X-Pinnwand-Token': t } : {}),
        ...(s ? { 'X-Pinnwand-Sitzung': s } : {}),
      },
      ...init,
    })
  } catch {
    // Netzfehler verstaendlich machen ("Failed to fetch" hilft niemandem).
    throw new Error('Server nicht erreichbar')
  }
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

// Auth-Kopfzeilen fuer Aufrufe abseits von hole() (FormData, Blob, Downloads):
// ohne sie brechen diese Pfade bei aktivem Login mit 401.
export function authKopf(): Record<string, string> {
  const t = uiToken()
  const s = authToken()
  return { ...(t ? { 'X-Pinnwand-Token': t } : {}), ...(s ? { 'X-Pinnwand-Sitzung': s } : {}) }
}

// Download mit Auth-Kopfzeilen: ein nacktes <a href> sendet nie die Sitzung.
export async function ladeDateiHerunter(pfad: string, fallbackName: string): Promise<void> {
  const r = await fetch(`${BASIS}${pfad}`, { headers: authKopf() })
  if (!r.ok) throw new Error('Download fehlgeschlagen')
  const cd = r.headers.get('Content-Disposition') || ''
  const m = cd.match(/filename="(.+?)"/)
  const url = URL.createObjectURL(await r.blob())
  const a = document.createElement('a')
  a.href = url
  a.download = m ? m[1] : fallbackName
  a.click()
  URL.revokeObjectURL(url)
}
