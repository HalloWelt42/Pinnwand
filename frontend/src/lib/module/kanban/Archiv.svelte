<script lang="ts">
  import type { Karte } from '../../types'
  import { ladeKartenArchiv } from '../../api'
  import { labelFarbe } from '../../labels'
  import { theme } from '../../theme/theme.svelte'

  const dunkel = $derived(theme.modus === 'dunkel')

  let { boardId, titel, onSchliessen, onOeffneKarte }: {
    boardId: string
    titel: string
    onSchliessen: () => void
    onOeffneKarte: (karte: Karte) => void
  } = $props()

  let karten = $state<Karte[]>([])
  let gesamt = $state(0)
  let hatMehr = $state(false)
  let laden = $state(false)
  let suche = $state('')
  let sucheTimer: ReturnType<typeof setTimeout> | null = null

  async function seite(reset: boolean): Promise<void> {
    if (laden) return
    laden = true
    try {
      const offset = reset ? 0 : karten.length
      const s = await ladeKartenArchiv(boardId, { offset, q: suche || undefined })
      karten = reset ? s.karten : [...karten, ...s.karten]
      gesamt = s.gesamt
      hatMehr = s.hat_mehr
    } finally {
      laden = false
    }
  }

  function beiSuche(): void {
    if (sucheTimer) clearTimeout(sucheTimer)
    sucheTimer = setTimeout(() => seite(true), 250)
  }

  function beiScroll(e: Event): void {
    if (!hatMehr || laden) return
    const el = e.currentTarget as HTMLElement
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) seite(false)
  }

  $effect(() => {
    void boardId
    seite(true)
  })
</script>

<div class="huelle" role="button" tabindex="-1" onclick={onSchliessen} onkeydown={(e) => { if (e.key === 'Escape') onSchliessen() }}>
  <div class="fenster" role="dialog" aria-label="Archiv" tabindex="-1" onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>
    <header>
      <div class="kopf">
        <i class="fa-solid fa-box-archive" aria-hidden="true"></i>
        <span class="t">Archiv - {titel}</span>
        <span class="zahl">{gesamt}</span>
      </div>
      <button class="x" aria-label="Schliessen" onclick={onSchliessen}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
    </header>
    <div class="suchzeile">
      <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
      <input class="feld" placeholder="Im Archiv suchen ..." bind:value={suche} oninput={beiSuche} aria-label="Archiv durchsuchen" />
    </div>
    <div class="liste" onscroll={beiScroll}>
      {#each karten as k (k.id)}
        <button class="eintrag" onclick={() => onOeffneKarte(k)}>
          <div class="zeile1">
            {#if k.schluessel}<span class="schl">{k.schluessel}</span>{/if}
            <span class="titel">{k.titel}</span>
          </div>
          <div class="zeile2">
            {#if k.abschluss_am}<span class="datum"><i class="fa-solid fa-flag-checkered" aria-hidden="true"></i> {k.abschluss_am}</span>{/if}
            {#if k.zustaendig}<span class="wer">{k.zustaendig}</span>{/if}
            {#each (k.labels ?? []) as l}{@const f = labelFarbe(l, dunkel)}<span class="label" style="background:{f.bg};color:{f.fg}">{l}</span>{/each}
          </div>
        </button>
      {/each}
      {#if !laden && karten.length === 0}
        <div class="leer">Keine archivierten Karten{suche ? ' fuer diese Suche' : ''}.</div>
      {/if}
      {#if hatMehr}
        <button class="mehr" onclick={() => seite(false)} disabled={laden}>{laden ? 'Lädt ...' : 'Mehr laden'}</button>
      {/if}
    </div>
  </div>
</div>

<style>
  .huelle {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 60;
    padding: 24px;
  }
  .fenster {
    width: min(680px, 100%);
    max-height: min(80vh, 720px);
    background: var(--surface-1, #1b1b1f);
    border: 1px solid var(--border);
    border-radius: var(--r-xl, 14px);
    box-shadow: var(--schatten-lift, 0 12px 40px rgba(0, 0, 0, 0.4));
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-1);
    font-weight: 600;
  }
  .kopf .zahl {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-3);
    background: var(--surface-col, transparent);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 1px 9px;
  }
  .x {
    border: none;
    background: transparent;
    color: var(--text-3);
    cursor: pointer;
    font-size: 16px;
    padding: 4px 6px;
  }
  .x:hover {
    color: var(--text-1);
  }
  .suchzeile {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-3);
  }
  .suchzeile .feld {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text-1);
    font: inherit;
    outline: none;
  }
  .liste {
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .eintrag {
    text-align: left;
    background: var(--surface-col, transparent);
    border: 1px solid var(--border);
    border-radius: var(--r-l, 10px);
    padding: 8px 10px;
    cursor: pointer;
    color: var(--text-1);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .eintrag:hover {
    border-color: var(--hl-primary);
  }
  .zeile1 {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .zeile1 .schl {
    font-size: 11px;
    color: var(--text-3);
    font-variant-numeric: tabular-nums;
  }
  .zeile1 .titel {
    font-weight: 500;
  }
  .zeile2 {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 11px;
    color: var(--text-3);
  }
  .zeile2 .label {
    color: #10151c;
    border-radius: 999px;
    padding: 0 8px;
    font-size: 10px;
    line-height: 16px;
  }
  .leer {
    text-align: center;
    color: var(--text-3);
    padding: 24px 8px;
    font-size: 13px;
  }
  .mehr {
    align-self: center;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-2);
    border-radius: var(--r-m, 6px);
    padding: 5px 14px;
    font: inherit;
    cursor: pointer;
    margin: 6px 0;
  }
  .mehr:hover:not(:disabled) {
    border-color: var(--hl-primary);
    color: var(--hl-primary-text);
  }
</style>
