<script lang="ts">
  import { sucheInhalte, sucheStatus, transkribiere, type SuchTreffer, type SuchStatus } from '../../api'
  import { oeffneKarte } from '../../navigation.svelte'

  // Suche ist global; boardId wird hier nicht benoetigt (Pflichtprop der Ansichts-Schnittstelle).
  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let frage = $state('')
  let treffer = $state<SuchTreffer[]>([])
  let modus = $state('stichwort')
  let laeuft = $state(false)
  let status = $state<SuchStatus | null>(null)

  let aufnahme = $state(false)
  let mikroFehler = $state('')
  let recorder: MediaRecorder | null = null
  let brocken: Blob[] = []

  let timer: ReturnType<typeof setTimeout> | null = null

  $effect(() => {
    sucheStatus().then((s) => (status = s)).catch(() => {})
  })

  // Reaktiv auf die Eingabe: entprellt suchen (liest frage zuverlaessig ueber das Binding).
  $effect(() => {
    const q = frage
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => starteSuche(q), 220)
  })

  async function starteSuche(q: string): Promise<void> {
    if (!q.trim()) {
      treffer = []
      return
    }
    laeuft = true
    try {
      const e = await sucheInhalte(q, 20)
      treffer = e.treffer
      modus = e.modus
    } catch {
      treffer = []
    } finally {
      laeuft = false
    }
  }

  async function mikrofon(): Promise<void> {
    mikroFehler = ''
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
            frage = text
            starteSuche(text)
          }
        } catch {
          mikroFehler = 'Spracheingabe nicht verfuegbar.'
        }
      }
      recorder.start()
      aufnahme = true
    } catch {
      mikroFehler = 'Kein Mikrofonzugriff.'
    }
  }

  function oeffne(t: SuchTreffer): void {
    if (t.board_id) oeffneKarte(t.board_id, t.karte_id)
  }
</script>

<div class="suche">
  <div class="kopf">
    <div class="feldreihe">
      <i class="fa-solid fa-magnifying-glass lupe" aria-hidden="true"></i>
      <input
        class="frage"
        placeholder="Frag nach allem - z.B. 'Qualitaet vor Auslieferung' oder 'R3-130'"
        bind:value={frage}
        aria-label="Suche"
      />
      {#if status?.mikrofon}
        <button class="mik" class:an={aufnahme} onclick={mikrofon} aria-label="Spracheingabe" title="Per Mikrofon suchen">
          <i class="fa-solid {aufnahme ? 'fa-stop' : 'fa-microphone'}" aria-hidden="true"></i>
        </button>
      {/if}
    </div>
    <div class="zeile-info">
      <span class="modus" title="Suchmodus">
        <i class="fa-solid {modus === 'hybrid' ? 'fa-wand-magic-sparkles' : 'fa-font'}" aria-hidden="true"></i>
        {modus === 'hybrid' ? 'Semantisch + Stichwort' : 'Stichwort'}
      </span>
      {#if laeuft}<span class="lade">sucht ...</span>{/if}
      {#if mikroFehler}<span class="fehler">{mikroFehler}</span>{/if}
    </div>
  </div>

  {#if frage.trim() && !treffer.length && !laeuft}
    <p class="leer">Keine Treffer.</p>
  {/if}

  <ul class="liste">
    {#each treffer as t (t.karte_id)}
      <li>
        <button class="treffer" onclick={() => oeffne(t)}>
          <span class="key">{t.schluessel ?? ''}</span>
          <span class="titel">{t.titel}</span>
          <span class="badges">
            {#if t.quelle === 'semantisch'}
              <span class="badge sem">semantisch{#if t.score} {Math.round(t.score * 100)}%{/if}</span>
            {:else}
              <span class="badge stw">Stichwort</span>
            {/if}
          </span>
        </button>
      </li>
    {/each}
  </ul>
</div>

<style>
  .suche {
    height: 100%;
    overflow-y: auto;
    padding: 18px;
    max-width: 820px;
    margin: 0 auto;
    width: 100%;
  }
  .kopf {
    margin-bottom: 14px;
  }
  .feldreihe {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l);
    padding: 4px 12px;
  }
  .feldreihe:focus-within {
    border-color: var(--hl-primary);
  }
  .lupe {
    color: var(--text-3);
    font-size: 15px;
  }
  .frage {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 16px;
    padding: 12px 0;
    outline: none;
  }
  .mik {
    width: 38px;
    height: 38px;
    border-radius: var(--r-m);
    border: 1px solid var(--border);
    background: var(--surface-2);
    color: var(--text-2);
    flex: none;
  }
  .mik:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .mik.an {
    background: var(--gefahr);
    color: #fff;
    border-color: transparent;
  }
  .zeile-info {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 8px 4px 0;
    font-size: 11.5px;
    color: var(--text-3);
  }
  .modus {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .fehler {
    color: var(--due-rot-fg);
  }
  .leer {
    color: var(--text-3);
    font-size: 13px;
    padding: 8px 4px;
  }
  .liste {
    list-style: none;
    margin: 6px 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .treffer {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    text-align: left;
    border: 1px solid var(--border);
    background: var(--surface-col);
    border-radius: var(--r-m);
    padding: 11px 13px;
    color: var(--text-1);
    cursor: pointer;
  }
  .treffer:hover {
    background: var(--surface-3);
    border-color: var(--border-2);
  }
  .key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
    flex: none;
    min-width: 56px;
  }
  .titel {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .badges {
    flex: none;
  }
  .badge {
    font-size: 10.5px;
    padding: 2px 8px;
    border-radius: 999px;
  }
  .badge.sem {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
  }
  .badge.stw {
    background: var(--surface-2);
    color: var(--text-3);
  }
</style>
