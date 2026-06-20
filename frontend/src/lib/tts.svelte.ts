// Vorlese-Adapter: liest satzweise ueber den lokalen TTS-Dienst (via Backend) und
// faellt auf die Browser-Sprachausgabe zurueck. Satzweises Lesen erlaubt
// Satz-Hervorhebung, Pause/Weiter und ein live veraenderbares Tempo. Vorlesen ist
// optional - ohne Dienst und ohne Browser-Unterstuetzung passiert nichts.

import { vorleseAudio } from './api'

export const tts = $state<{
  laeuft: boolean
  pausiert: boolean
  stimme: string
  tempo: number
  satz: string
  index: number
  anzahl: number
}>({ laeuft: false, pausiert: false, stimme: '', tempo: 1, satz: '', index: 0, anzahl: 0 })

try {
  tts.stimme = localStorage.getItem('pw_tts_stimme') ?? ''
  const t = parseFloat(localStorage.getItem('pw_tts_tempo') ?? '')
  if (Number.isFinite(t) && t > 0) tts.tempo = t
} catch {
  /* localStorage nicht verfuegbar */
}

export function setzeStimme(stimme: string): void {
  tts.stimme = stimme
  try { localStorage.setItem('pw_tts_stimme', stimme) } catch { /* ignorieren */ }
}

export function setzeTempo(tempo: number): void {
  tts.tempo = tempo
  try { localStorage.setItem('pw_tts_tempo', String(tempo)) } catch { /* ignorieren */ }
  if (audio) audio.playbackRate = tempo // Audio-Tempo greift sofort.
}

let audio: HTMLAudioElement | null = null
let saetze: string[] = []
let lauf = 0 // Generationszaehler: entwertet Rueckrufe nach Stopp/Neustart.
let browserModus = false
let aktiveStimme: string | undefined

/** Entfernt grobe Markdown-Syntax, damit nur der Lesetext gesprochen wird. */
export function nurText(md: string): string {
  return (md || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_~|]/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

/** Zerlegt Text in vorlesbare Saetze (Satzzeichen oder Zeilenumbruch). */
function inSaetze(text: string): string[] {
  return text
    .split(/(?<=[.!?:])\s+|\n+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export async function vorlesen(text: string, opts?: { tempo?: number; stimme?: string }): Promise<void> {
  stoppeVorlesen()
  const sauber = nurText(text)
  if (!sauber) return
  saetze = inSaetze(sauber)
  if (!saetze.length) return
  if (opts?.tempo) tts.tempo = opts.tempo
  aktiveStimme = opts?.stimme ?? (tts.stimme || undefined)
  browserModus = false
  const meine = ++lauf
  tts.laeuft = true
  tts.pausiert = false
  tts.anzahl = saetze.length
  await spieleAb(0, meine)
}

async function spieleAb(index: number, meine: number): Promise<void> {
  if (meine !== lauf) return
  if (index >= saetze.length) { stoppeVorlesen(); return }
  tts.index = index
  tts.satz = saetze[index]
  const weiter = () => { if (meine === lauf) void spieleAb(index + 1, meine) }

  if (!browserModus) {
    try {
      const blob = await vorleseAudio(saetze[index], aktiveStimme)
      if (meine !== lauf) return
      audio = new Audio(URL.createObjectURL(blob))
      audio.playbackRate = tts.tempo
      audio.onended = weiter
      await audio.play()
      return
    } catch {
      browserModus = true // einmal scheitern -> ab jetzt Browser-Stimme
    }
  }

  if ('speechSynthesis' in window) {
    const u = new SpeechSynthesisUtterance(saetze[index])
    u.lang = 'de-DE'
    u.rate = tts.tempo
    u.onend = weiter
    window.speechSynthesis.speak(u)
  } else {
    stoppeVorlesen()
  }
}

export function pauseVorlesen(): void {
  if (!tts.laeuft) return
  tts.pausiert = true
  if (audio) audio.pause()
  if (browserModus && 'speechSynthesis' in window) window.speechSynthesis.pause()
}

export function weiterVorlesen(): void {
  if (!tts.laeuft || !tts.pausiert) return
  tts.pausiert = false
  if (audio) void audio.play()
  if (browserModus && 'speechSynthesis' in window) window.speechSynthesis.resume()
}

export function stoppeVorlesen(): void {
  lauf++
  if (audio) { audio.pause(); audio = null }
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  tts.laeuft = false
  tts.pausiert = false
  tts.satz = ''
  tts.index = 0
  tts.anzahl = 0
}
