// Optionaler UI-Token-Schutz (greift nur, wenn das Backend PINNWAND_UI_TOKEN setzt).
// Ohne gesetztes Token kommt nie eine 401 und es wird nichts angezeigt.
import { leseText, schreibeText, entferne } from './uiSpeicher'

const SCHLUESSEL = 'pw_ui_token'

export const uiAuth = $state<{ noetig: boolean }>({ noetig: false })

export function uiToken(): string {
  return leseText(SCHLUESSEL)
}

export function setzeUiToken(t: string): void {
  if (t) schreibeText(SCHLUESSEL, t)
  else entferne(SCHLUESSEL)
}
