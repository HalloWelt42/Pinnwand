// Zentraler, getypter und fehlertoleranter Zugriff auf localStorage.
// localStorage kann im privaten Modus oder bei vollem Speicher werfen - deshalb
// ist jeder Zugriff gekapselt: Lesen liefert bei Fehlern den Standardwert,
// Schreiben/Loeschen tun bei Fehlern still nichts.

// Einen Textwert lesen (Standard, wenn nicht gesetzt oder nicht verfuegbar).
export function leseText(schluessel: string, standard = ''): string {
  try {
    return localStorage.getItem(schluessel) ?? standard
  } catch {
    return standard
  }
}

// Einen Textwert schreiben.
export function schreibeText(schluessel: string, wert: string): void {
  try {
    localStorage.setItem(schluessel, wert)
  } catch {
    /* localStorage nicht verfuegbar */
  }
}

// Einen Eintrag entfernen.
export function entferne(schluessel: string): void {
  try {
    localStorage.removeItem(schluessel)
  } catch {
    /* localStorage nicht verfuegbar */
  }
}

// Einen JSON-Wert lesen (Standard bei fehlendem Eintrag oder kaputtem JSON).
export function leseJson<T>(schluessel: string, standard: T): T {
  try {
    const roh = localStorage.getItem(schluessel)
    if (roh === null) return standard
    return JSON.parse(roh) as T
  } catch {
    return standard
  }
}

// Einen Wert als JSON schreiben.
export function schreibeJson(schluessel: string, wert: unknown): void {
  try {
    localStorage.setItem(schluessel, JSON.stringify(wert))
  } catch {
    /* localStorage nicht verfuegbar */
  }
}
