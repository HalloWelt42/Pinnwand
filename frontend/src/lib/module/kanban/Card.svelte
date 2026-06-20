<script lang="ts">
  import type { Karte } from '../../types'
  import { labelFarbe } from '../../labels'
  import { theme } from '../../theme/theme.svelte'
  import { timer, timerStarten, timerPausieren, erfassteSekunden, formatDauer } from '../../timer.svelte'

  let { karte, onOeffnen, onLoeschen }: { karte: Karte; onOeffnen: (id: string) => void; onLoeschen: (id: string) => void } = $props()

  const dunkel = $derived(theme.modus === 'dunkel')
  const laeuft = $derived(!!karte.laeuft_seit)
  const sek = $derived(laeuft ? erfassteSekunden(karte, timer.jetzt) : (karte.erfasst_sek ?? 0))
  const zeitUeber = $derived(karte.schaetzung_min ? sek / 60 > karte.schaetzung_min : false)
  function zeitToggle() {
    if (laeuft) timerPausieren(karte.id)
    else timerStarten(karte.id)
  }

  function kurz(iso: string): string {
    const [, m, t] = iso.split('-')
    return `${t}.${m}.`
  }
  function tageBis(iso: string): number {
    const ziel = new Date(iso + 'T00:00:00').getTime()
    const heute = new Date()
    heute.setHours(0, 0, 0, 0)
    return Math.round((ziel - heute.getTime()) / 86400000)
  }
  const faelligKlasse = $derived.by(() => {
    if (!karte.faellig) return ''
    const d = tageBis(karte.faellig)
    return d < 0 ? 'rot' : d <= 2 ? 'amber' : 'neutral'
  })
  const erledigt = $derived(karte.checkliste.filter((c) => c.erledigt).length)
  const liegtTage = $derived.by(() => {
    if (!karte.bewegt_am) return null
    const t = new Date(karte.bewegt_am).getTime()
    if (Number.isNaN(t)) return null
    return Math.floor((Date.now() - t) / 86400000)
  })
  const aging = $derived(liegtTage != null && liegtTage >= 4 ? (liegtTage >= 8 ? 'rot' : 'amber') : null)
  const prioFarbe: Record<string, string> = {
    hoch: 'var(--prio-hoch)',
    mittel: 'var(--prio-mittel)',
    niedrig: 'var(--prio-niedrig)',
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<article
  class="card"
  role="listitem"
  tabindex="0"
  onclick={() => onOeffnen(karte.id)}
  onkeydown={(e) => {
    if (e.target !== e.currentTarget) return
    if (e.key === 'Enter') {
      e.preventDefault()
      onOeffnen(karte.id)
    }
  }}
>
  <button
    class="aktion"
    aria-label="Karte löschen"
    title="Löschen"
    onclick={(e) => { e.stopPropagation(); onLoeschen(karte.id) }}
  >
    <i class="fa-solid fa-trash" aria-hidden="true"></i>
  </button>
  {#if karte.cover}
    <div class="cover" style="background:{karte.cover}"></div>
  {/if}
  {#if karte.labels.length}
    <div class="labels">
      {#each karte.labels as label (label)}
        {@const f = labelFarbe(label, dunkel)}
        <span class="lab" style="background:{f.bg};color:{f.fg}">{label}</span>
      {/each}
    </div>
  {/if}
  <p class="titel">{karte.titel}</p>
  {#if karte.beschreibung}
    <p class="desc">{karte.beschreibung}</p>
  {/if}
  <div class="foot">
    <button class="zeit" class:laeuft class:ueber={zeitUeber} title={laeuft ? 'Pausieren' : 'Starten'} onclick={(e) => { e.stopPropagation(); zeitToggle() }}>
      <i class="fa-solid {laeuft ? 'fa-pause' : 'fa-play'}" aria-hidden="true"></i>
      {#if laeuft || sek > 0}<span>{formatDauer(sek)}</span>{/if}
    </button>
    {#if karte.schluessel}<span class="key">{karte.schluessel}</span>{/if}
    {#if karte.faellig}
      <span class="due {faelligKlasse}"><i class="fa-regular fa-clock" aria-hidden="true"></i> {kurz(karte.faellig)}</span>
    {/if}
    {#if karte.checkliste.length}
      <span class="chk" class:voll={erledigt === karte.checkliste.length}><i class="fa-regular fa-square-check" aria-hidden="true"></i> {erledigt}/{karte.checkliste.length}</span>
    {/if}
    {#if karte.kommentare.length}
      <span class="badge"><i class="fa-regular fa-comment" aria-hidden="true"></i> {karte.kommentare.length}</span>
    {/if}
    {#if aging}
      <span class="alter {aging}" title="Liegt {liegtTage} Tage in dieser Spalte"><i class="fa-solid fa-hourglass-half" aria-hidden="true"></i> {liegtTage}</span>
    {/if}
    <span class="rechts">
      {#if karte.prioritaet}
        <span class="prio" style="background:{prioFarbe[karte.prioritaet]}" title="Priorität: {karte.prioritaet}"></span>
      {/if}
      {#if karte.zustaendig}
        <span class="av" title={karte.zustaendig}>{karte.zustaendig}</span>
      {/if}
    </span>
  </div>
</article>

<style>
  .card {
    position: relative;
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: var(--r-l);
    padding: 9px 10px;
    box-shadow: var(--schatten-karte);
    cursor: grab;
    transition: border-color 0.12s, background 0.12s;
  }
  .card:hover {
    border-color: var(--border-2);
    background: var(--surface-3);
  }
  .card:active {
    cursor: grabbing;
  }
  .aktion {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 24px;
    height: 24px;
    border-radius: var(--r-s);
    border: none;
    background: var(--surface-3);
    color: var(--text-3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    opacity: 0;
    transition: opacity 0.12s, color 0.12s;
  }
  .card:hover .aktion,
  .card:focus-within .aktion {
    opacity: 1;
  }
  .aktion:hover {
    color: var(--gefahr);
    background: var(--surface-1);
  }
  .cover {
    height: 6px;
    border-radius: 4px;
    margin-bottom: 8px;
  }
  .labels {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin-bottom: 6px;
  }
  .lab {
    font-size: 10.5px;
    padding: 1px 7px;
    border-radius: 5px;
    font-weight: 500;
  }
  .titel {
    font-size: 12.5px;
    font-weight: 500;
    line-height: 1.35;
    margin: 0;
    color: var(--text-1);
  }
  .desc {
    font-size: 11px;
    color: var(--text-3);
    margin: 5px 0 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .foot {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 9px;
    margin-top: 9px;
    font-size: 11px;
    color: var(--text-2);
  }
  .foot i {
    font-size: 12px;
  }
  .zeit {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: 1px solid var(--border-2);
    background: var(--surface-2);
    color: var(--text-2);
    border-radius: 5px;
    padding: 1px 7px;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }
  .zeit i {
    font-size: 10px;
  }
  .zeit:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .zeit.laeuft {
    border-color: var(--hl-primary);
    color: var(--hl-primary-text);
    background: var(--hl-primary-weich);
  }
  .zeit.ueber {
    border-color: var(--gefahr);
    color: var(--due-rot-fg);
    background: var(--due-rot-bg);
  }
  .key {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-3);
  }
  .due {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 1px 6px;
    border-radius: 5px;
  }
  .due.rot {
    background: var(--due-rot-bg);
    color: var(--due-rot-fg);
  }
  .due.amber {
    background: var(--due-amber-bg);
    color: var(--due-amber-fg);
  }
  .due.neutral {
    color: var(--text-3);
  }
  .alter {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 1px 6px;
    border-radius: 5px;
  }
  .alter.amber {
    background: var(--due-amber-bg);
    color: var(--due-amber-fg);
  }
  .alter.rot {
    background: var(--due-rot-bg);
    color: var(--due-rot-fg);
  }
  .chk {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .chk.voll {
    color: var(--ok);
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .rechts {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .prio {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .av {
    width: 21px;
    height: 21px;
    border-radius: 50%;
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    font-size: 9.5px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
