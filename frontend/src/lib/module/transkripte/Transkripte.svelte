<script lang="ts">
  import {
    transkripteStatus,
    transkripteSuche,
    transkriptDetail,
    type TranskriptTreffer,
    type TranskriptDetail,
  } from '../../api'
  import { tts, vorlesen, stoppeVorlesen } from '../../tts.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  let frage = $state('')
  let treffer = $state<TranskriptTreffer[]>([])
  let aktiv = $state<TranskriptDetail | null>(null)
  let status = $state<{ erreichbar: boolean; konfiguriert: boolean } | null>(null)
  let laeuft = $state(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  $effect(() => {
    transkripteStatus().then((s) => (status = s)).catch(() => (status = { erreichbar: false, konfiguriert: false }))
  })

  // Erstbefuellung (leere Suche zeigt die neuesten) und entprellte Suche.
  $effect(() => {
    const q = frage
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => suchen(q), 220)
  })

  async function suchen(q: string): Promise<void> {
    if (status && !status.erreichbar) return
    laeuft = true
    try {
      treffer = (await transkripteSuche(q, 40)).treffer
    } catch {
      treffer = []
    } finally {
      laeuft = false
    }
  }

  async function oeffne(t: TranskriptTreffer): Promise<void> {
    stoppeVorlesen()
    try {
      aktiv = await transkriptDetail(t.id)
    } catch {
      aktiv = null
    }
  }

  function vorlesenUmschalten(): void {
    if (tts.laeuft) stoppeVorlesen()
    else if (aktiv) vorlesen(aktiv.full_text)
  }

  function hervor(text: string, q: string): string {
    // Einfache Hervorhebung des Suchbegriffs (HTML-sicher).
    const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c] as string)
    if (!q.trim()) return esc(text)
    const re = new RegExp(`(${q.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    return esc(text).replace(re, '<mark>$1</mark>')
  }
</script>

<div class="trans">
  {#if status && !status.konfiguriert}
    <p class="hinweis">Kein Transkriptions-Dienst konfiguriert.</p>
  {:else if status && !status.erreichbar}
    <p class="hinweis">Transkriptions-Dienst nicht erreichbar. Laeuft er?</p>
  {:else}
    <div class="spalten">
      <aside class="liste">
        <div class="feldreihe">
          <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
          <input class="frage" placeholder="Transkripte durchsuchen ..." bind:value={frage} aria-label="Transkripte suchen" />
        </div>
        {#if laeuft}<p class="lade">sucht ...</p>{/if}
        <ul>
          {#each treffer as t (t.id)}
            <li>
              <button class="eintrag" class:on={aktiv?.id === t.id} onclick={() => oeffne(t)}>
                <span class="nm">{t.name}</span>
                {#if t.snippet}<span class="snip">{@html hervor(t.snippet, frage)}</span>{/if}
                {#if t.speaker_names.length}<span class="spk">{t.speaker_names.length} Sprecher</span>{/if}
              </button>
            </li>
          {/each}
          {#if !treffer.length && !laeuft}<li class="leer">Keine Transkripte.</li>{/if}
        </ul>
      </aside>

      <section class="detail">
        {#if aktiv}
          <header class="dkopf">
            <h2>{aktiv.name}</h2>
            <div class="meta">
              {#if aktiv.language}<span>{aktiv.language}</span>{/if}
              {#if aktiv.speaker_names.length}<span>{aktiv.speaker_names.join(', ')}</span>{/if}
              {#if aktiv.segment_count}<span>{aktiv.segment_count} Segmente</span>{/if}
            </div>
            <div class="aktionen">
              <button class="btn" onclick={vorlesenUmschalten}>
                <i class="fa-solid {tts.laeuft ? 'fa-stop' : 'fa-volume-high'}" aria-hidden="true"></i>
                {tts.laeuft ? 'Stopp' : 'Vorlesen'}
              </button>
            </div>
            {#if aktiv.audio_url}
              <audio class="player" controls src={aktiv.audio_url}></audio>
            {/if}
          </header>
          <div class="text">{@html hervor(aktiv.full_text, frage)}</div>
        {:else}
          <p class="leer-d">Links ein Transkript waehlen.</p>
        {/if}
      </section>
    </div>
  {/if}
</div>

<style>
  .trans {
    height: 100%;
    overflow: hidden;
    padding: 16px;
  }
  .hinweis {
    color: var(--text-3);
    font-size: 13px;
  }
  .spalten {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 16px;
    height: 100%;
    min-height: 0;
  }
  .liste {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  .feldreihe {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-m);
    padding: 2px 10px;
    color: var(--text-3);
  }
  .feldreihe:focus-within {
    border-color: var(--hl-primary);
  }
  .frage {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 13px;
    padding: 9px 0;
    outline: none;
  }
  .lade {
    font-size: 11px;
    color: var(--text-3);
    margin: 6px 2px;
  }
  .liste ul {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .eintrag {
    width: 100%;
    text-align: left;
    background: var(--surface-col);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 9px 11px;
    color: var(--text-1);
    display: flex;
    flex-direction: column;
    gap: 3px;
    cursor: pointer;
  }
  .eintrag:hover {
    background: var(--surface-3);
  }
  .eintrag.on {
    border-color: var(--hl-primary);
    background: var(--hl-primary-weich);
  }
  .nm {
    font-size: 12.5px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .snip {
    font-size: 11px;
    color: var(--text-3);
    line-height: 1.4;
    max-height: 2.8em;
    overflow: hidden;
  }
  .spk {
    font-size: 10px;
    color: var(--text-3);
  }
  .leer,
  .leer-d {
    color: var(--text-3);
    font-size: 12.5px;
    padding: 8px 2px;
  }
  .detail {
    min-width: 0;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
    border-radius: var(--r-l);
    background: var(--surface-col);
    overflow: hidden;
  }
  .dkopf {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .dkopf h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 15px;
    color: var(--text-1);
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 11px;
    color: var(--text-3);
  }
  .btn {
    align-self: flex-start;
    border: 1px solid var(--hl-primary);
    background: var(--hl-primary);
    color: var(--hl-on-primary);
    border-radius: var(--r-m);
    padding: 7px 12px;
    font-size: 12.5px;
    font-weight: 500;
  }
  .player {
    width: 100%;
    height: 34px;
  }
  .text {
    padding: 14px 16px;
    overflow-y: auto;
    font-size: 13.5px;
    line-height: 1.7;
    color: var(--text-1);
    white-space: pre-wrap;
  }
  .text :global(mark),
  .snip :global(mark) {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-radius: 2px;
  }
</style>
