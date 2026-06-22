// Optionaler UI-Token-Schutz (greift nur, wenn das Backend PINNWAND_UI_TOKEN setzt).
// Ohne gesetztes Token kommt nie eine 401 und es wird nichts angezeigt.
const SCHLUESSEL = 'pw_ui_token'

export const uiAuth = $state<{ noetig: boolean }>({ noetig: false })

export function uiToken(): string {
  try {
    return localStorage.getItem(SCHLUESSEL) ?? ''
  } catch {
    return ''
  }
}

export function setzeUiToken(t: string): void {
  try {
    if (t) localStorage.setItem(SCHLUESSEL, t)
    else localStorage.removeItem(SCHLUESSEL)
  } catch {
    /* localStorage nicht verfuegbar */
  }
}
