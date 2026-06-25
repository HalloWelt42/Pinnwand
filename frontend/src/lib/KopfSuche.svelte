<script lang="ts">
  // Zentrale Suche im Kopfbereich: ein Feld + Spracheingabe (Mikrofon), global ueber
  // allen Ansichten. Schreibt in den kopfSuche-Store und fuehrt in die Suche-Ansicht.
  import { sucheStatus, transkribiere, type SuchStatus } from './api'
  import { kopfSuche, sucheSetzen } from './suchkopf.svelte'

  let { onSuche }: { onSuche?: () => void } = $props()

  let q = $state(kopfSuche.q)
  let status = $state<SuchStatus | null>(null)
  let aufnahme = $state(false)
  let recorder: MediaRecorder | null = null
  let brocken: Blob[] = []
  let timer: ReturnType<typeof setTimeout> | null = null

  $effect(() => {
    sucheStatus().then((s) => (status = s)).catch(() => {})
  })

  function ausloesen(q2: string): void {
    sucheSetzen(q2)
    if (q2.trim()) onSuche?.()
  }
  function tippen(): void {
    if (timer) clearTimeout(timer)
    const w = q
    timer = setTimeout(() => ausloesen(w), 250)
  }
  function absenden(): void {
    if (timer) clearTimeout(timer)
    ausloesen(q)
  }

  async function mikrofon(): Promise<void> {
    if (aufnahme) {
      recorder?.stop()
      return
    }
    try {
      const strom = await navigator.mediaDevices.getUserMedia({ audio: true })
      recorder = new MediaRecorder(strom)
      brocken = []
      recorder.ondataavailable = (e) => brocken.push(e.data)
      recorder.onstop = async () => {
        strom.getTracks().forEach((t) => t.stop())
        aufnahme = false
        const blob = new Blob(brocken, { type: recorder?.mimeType || 'audio/webm' })
        try {
          const { text } = await transkribiere(blob)
          if (text) {
            q = text
            ausloesen(text)
          }
        } catch {
          /* Spracheingabe nicht verfuegbar - still bleiben, Tippen geht weiter */
        }
      }
      recorder.start()
      aufnahme = true
    } catch {
      /* kein Mikrofonzugriff */
    }
  }
</script>

<div class="ksuche" class:auf={aufnahme}>
  <i class="fa-solid fa-magnifying-glass lupe" aria-hidden="true"></i>
  <input
    class="kfeld"
    placeholder="Suchen ... (Karten, Inhalte)"
    bind:value={q}
    oninput={tippen}
    onkeydown={(e) => { if (e.key === 'Enter') absenden() }}
    aria-label="Suche"
  />
  {#if q}
    <button class="kx" aria-label="Suche leeren" onclick={() => { q = ''; ausloesen('') }}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
  {/if}
  {#if status?.mikrofon}
    <button class="kmik" class:an={aufnahme} onclick={mikrofon} aria-label="Spracheingabe" title="Per Mikrofon suchen">
      <i class="fa-solid {aufnahme ? 'fa-stop' : 'fa-microphone'}" aria-hidden="true"></i>
    </button>
  {/if}
</div>

<style>
  .ksuche {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l);
    padding: 4px 10px;
    width: 100%;
    max-width: 460px;
  }
  .ksuche:focus-within {
    border-color: var(--hl-primary);
  }
  .ksuche.auf {
    border-color: var(--gefahr);
  }
  .lupe {
    color: var(--text-3);
    font-size: 13px;
  }
  .kfeld {
    flex: 1;
    min-width: 0;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 13px;
    padding: 6px 0;
    outline: none;
  }
  .kx {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 12px;
    padding: 2px 4px;
    flex: none;
  }
  .kx:hover {
    color: var(--text-1);
  }
  .kmik {
    width: 28px;
    height: 28px;
    border-radius: var(--r-s);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    flex: none;
  }
  .kmik:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .kmik.an {
    background: var(--gefahr);
    color: #fff;
    border-color: transparent;
  }
</style>
