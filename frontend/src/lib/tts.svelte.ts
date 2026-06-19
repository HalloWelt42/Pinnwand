// Vorlese-Adapter: nutzt den lokalen TTS-Dienst (ueber das Backend) und faellt
// auf die Browser-Sprachausgabe zurueck. Vorlesen ist optional - ohne Dienst
// und ohne Browser-Unterstuetzung passiert nichts.

import { vorleseAudio } from './api'

export const tts = $state<{ laeuft: boolean }>({ laeuft: false })

let audio: HTMLAudioElement | null = null

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

export async function vorlesen(text: string, opts?: { tempo?: number; stimme?: string }): Promise<void> {
  stoppeVorlesen()
  const sauber = nurText(text)
  if (!sauber) return
  try {
    const blob = await vorleseAudio(sauber, opts?.stimme)
    audio = new Audio(URL.createObjectURL(blob))
    audio.playbackRate = opts?.tempo ?? 1
    audio.onended = () => (tts.laeuft = false)
    tts.laeuft = true
    await audio.play()
  } catch {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(sauber)
      u.lang = 'de-DE'
      u.rate = opts?.tempo ?? 1
      u.onend = () => (tts.laeuft = false)
      tts.laeuft = true
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(u)
    } else {
      tts.laeuft = false
    }
  }
}

export function stoppeVorlesen(): void {
  if (audio) {
    audio.pause()
    audio = null
  }
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  tts.laeuft = false
}
