<script lang="ts">
  // Folgetag-Nachfrage fuer wiederkehrende Aufgaben: zeigt vergangene Serien-Karten,
  // die nicht erfasst und nicht erledigt wurden, und bietet an, die Stunden
  // nachzutragen (Soll vorgeschlagen, anpassbar) oder die Karte zu verwerfen.
  import { onMount } from 'svelte'
  import { ladeSerienNachtraege, serieNachtragen, loescheKarte, type SerienNachtrag } from './api'
  import { timer } from './timer.svelte'
  import { isoLang } from './zeit'

  let offen = $state<SerienNachtrag[]>([])
  let sichtbar = $state(false)
  let stunden = $state<Record<string, number>>({})

  const SCHLUESSEL = 'pw_serien_nachtrag_check'

  function heuteIso(): string {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  async function offeneLaden(): Promise<void> {
    offen = (await ladeSerienNachtraege()) ?? []
  }

  onMount(async () => {
    let zuletzt = ''
    try { zuletzt = localStorage.getItem(SCHLUESSEL) ?? '' } catch { /* ignorieren */ }
    if (zuletzt === heuteIso()) return // heute schon gefragt
    try {
      await offeneLaden()
    } catch { return }
    try { localStorage.setItem(SCHLUESSEL, heuteIso()) } catch { /* ignorieren */ }
    if (offen.length) sichtbar = true
  })

  function stundenVon(n: SerienNachtrag): number {
    return stunden[n.karte_id] ?? Math.round(((n.soll_min ?? 60) / 60) * 100) / 100
  }
  async function nachtragen(n: SerienNachtrag): Promise<void> {
    await serieNachtragen(n.karte_id, Math.max(0, Math.round(stundenVon(n) * 60)))
    timer.stand++ // Stunden-Leiste/Board aktualisieren
    await offeneLaden()
    if (!offen.length) sichtbar = false
  }
  async function verwerfen(n: SerienNachtrag): Promise<void> {
    await loescheKarte(n.karte_id)
    timer.stand++
    await offeneLaden()
    if (!offen.length) sichtbar = false
  }
  function spaeter(): void {
    sichtbar = false
  }
</script>

<svelte:window onkeydown={(e) => { if (sichtbar && e.key === 'Escape') spaeter() }} />
{#if sichtbar}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="overlay" role="presentation" onclick={spaeter}></div>
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="modal" role="dialog" aria-label="Stunden nachtragen" tabindex="-1" onclick={(e) => e.stopPropagation()}>
    <h2><i class="fa-solid fa-clock-rotate-left" aria-hidden="true"></i> Stunden nachtragen</h2>
    <p class="hint">Diese wiederkehrenden Aufgaben sind vorbei und wurden nicht erfasst. Stunden bei Bedarf anpassen und nachtragen - oder verwerfen, wenn nicht erledigt.</p>
    <div class="liste">
      {#each offen as n (n.karte_id)}
        <div class="zeile">
          <span class="dat">{isoLang(n.datum)}</span>
          <span class="tit">{n.titel}</span>
          <input class="std" type="number" min="0" step="0.25" value={stundenVon(n)}
            onchange={(e) => (stunden[n.karte_id] = parseFloat(e.currentTarget.value) || 0)} />
          <span class="me">Std</span>
          <button class="mini" onclick={() => nachtragen(n)}>Nachtragen</button>
          <button class="mini geist" onclick={() => verwerfen(n)}>Verwerfen</button>
        </div>
      {/each}
    </div>
    <div class="fuss">
      <button class="text" onclick={spaeter}>Später</button>
    </div>
  </div>
{/if}

<style>
  .overlay { position: fixed; inset: 0; z-index: 80; background: rgba(0, 0, 0, 0.5); }
  .modal {
    position: fixed; z-index: 81; top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 560px; max-width: 94vw; max-height: 86vh; overflow-y: auto;
    background: var(--surface-col); border: 1px solid var(--border-2); border-radius: var(--r-xl);
    padding: 20px; box-shadow: var(--schatten-pop);
  }
  h2 { margin: 0 0 6px; font-family: var(--font-display); font-size: 17px; color: var(--text-1); display: flex; align-items: center; gap: 9px; }
  .hint { margin: 0 0 14px; font-size: 12.5px; color: var(--text-2); line-height: 1.5; }
  .liste { display: flex; flex-direction: column; gap: 4px; }
  .zeile { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12.5px; }
  .zeile:last-child { border-bottom: none; }
  .dat { flex: 0 0 92px; color: var(--text-2); font-variant-numeric: tabular-nums; }
  .tit { flex: 1; min-width: 0; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .std { width: 64px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 4px 6px; font-size: 12px; }
  .me { color: var(--text-3); font-size: 11px; }
  .mini { border: 1px solid var(--hl-primary); background: var(--hl-primary); color: var(--hl-on-primary); border-radius: var(--r-s); padding: 4px 9px; font-size: 11.5px; white-space: nowrap; }
  .mini.geist { background: transparent; color: var(--text-2); border-color: var(--border-2); }
  .fuss { display: flex; align-items: center; justify-content: flex-end; margin-top: 16px; }
  .text { border: none; background: transparent; color: var(--text-3); font-size: 12.5px; padding: 8px 10px; }
</style>
