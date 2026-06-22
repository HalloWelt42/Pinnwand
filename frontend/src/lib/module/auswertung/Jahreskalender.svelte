<script lang="ts">
  import { ladeKalender, ladeAbwesenheitstypen, type KalenderAntwort, type AbwesenheitTyp } from '../../api'
  import type { Ebenen, TypMap } from './kalenderfarben'
  import JahresGitter from './JahresGitter.svelte'
  import TeamMatrix from './TeamMatrix.svelte'
  import TagModal from './TagModal.svelte'
  import KalenderLegende from './KalenderLegende.svelte'

  let { boardId }: { boardId: string } = $props()
  $effect(() => void boardId)

  interface UiStand { jahr: number; layout: 'gitter' | 'matrix'; ebenen: Ebenen }
  const STD: UiStand = {
    jahr: new Date().getFullYear(),
    layout: 'gitter',
    ebenen: { anwesenheit: true, feiertage: true, stunden: false, auslastung: false, frei: false },
  }
  function ladeUi(): UiStand {
    try {
      const r = JSON.parse(localStorage.getItem('pw_jahreskalender') || '{}')
      return { jahr: r.jahr ?? STD.jahr, layout: r.layout ?? STD.layout, ebenen: { ...STD.ebenen, ...(r.ebenen ?? {}) } }
    } catch {
      return STD
    }
  }
  const _ui = ladeUi()

  let jahr = $state(_ui.jahr)
  let layout = $state<'gitter' | 'matrix'>(_ui.layout)
  let ebenen = $state<Ebenen>(_ui.ebenen)
  let daten = $state<KalenderAntwort | null>(null)
  let typen = $state<AbwesenheitTyp[]>([])
  let laedt = $state(true)
  let modal = $state<{ person_id: string; von: string; bis: string } | null>(null)

  const typMap = $derived<TypMap>(Object.fromEntries(typen.map((t) => [t.code, t])))

  async function laden(): Promise<void> {
    laedt = true
    try {
      daten = await ladeKalender(jahr)
    } catch {
      daten = null
    } finally {
      laedt = false
    }
  }
  $effect(() => { void jahr; laden() })
  $effect(() => { ladeAbwesenheitstypen().then((t) => (typen = t)).catch(() => {}) })
  $effect(() => {
    localStorage.setItem('pw_jahreskalender', JSON.stringify({ jahr, layout, ebenen }))
  })

  const EBENEN: { key: keyof Ebenen; label: string; icon: string }[] = [
    { key: 'anwesenheit', label: 'Anwesenheit', icon: 'fa-users' },
    { key: 'feiertage', label: 'Feiertage', icon: 'fa-star' },
    { key: 'frei', label: 'Frei', icon: 'fa-umbrella-beach' },
    { key: 'stunden', label: 'Stunden', icon: 'fa-clock' },
    { key: 'auslastung', label: 'Auslastung', icon: 'fa-gauge' },
  ]

  function gespeichert(): void {
    modal = null
    laden()
  }
</script>

<div class="jk">
  <div class="topbar">
    <div class="jahrnav">
      <button class="ib" aria-label="Vorheriges Jahr" onclick={() => (jahr -= 1)}><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>
      <span class="jahr">{jahr}</span>
      <button class="ib" aria-label="Nächstes Jahr" onclick={() => (jahr += 1)}><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>
    </div>

    <div class="seg">
      <button class:an={layout === 'gitter'} onclick={() => (layout = 'gitter')}><i class="fa-solid fa-table-cells" aria-hidden="true"></i> Gitter</button>
      <button class:an={layout === 'matrix'} onclick={() => (layout = 'matrix')}><i class="fa-solid fa-bars-staggered" aria-hidden="true"></i> Matrix</button>
    </div>

    <div class="ebenen">
      {#each EBENEN as e (e.key)}
        <button class="chip" class:an={ebenen[e.key]} onclick={() => (ebenen = { ...ebenen, [e.key]: !ebenen[e.key] })}>
          <i class="fa-solid {e.icon}" aria-hidden="true"></i> {e.label}
        </button>
      {/each}
    </div>
  </div>

  <div class="flaeche">
    {#if laedt}
      <p class="hinweis">Kalender wird geladen ...</p>
    {:else if !daten || !daten.personen.length}
      <p class="hinweis">Keine Personen angelegt. Lege unter Planung Personen an.</p>
    {:else if layout === 'gitter'}
      <JahresGitter {daten} {ebenen} onTag={(iso) => (modal = { person_id: '', von: iso, bis: iso })} />
    {:else}
      <TeamMatrix {daten} {ebenen} typen={typMap} onBereich={(pid, von, bis) => (modal = { person_id: pid, von, bis })} />
    {/if}
  </div>

  <KalenderLegende {typen} {ebenen} />
</div>

{#if modal && daten}
  <TagModal
    personen={daten.personen}
    {typen}
    start={modal}
    onSchliessen={() => (modal = null)}
    onGespeichert={gespeichert}
  />
{/if}

<style>
  .jk { height: 100%; display: flex; flex-direction: column; }
  .topbar { flex: none; display: flex; align-items: center; gap: 16px; padding: 10px 14px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .jahrnav { display: flex; align-items: center; gap: 8px; }
  .jahr { font-family: var(--font-display); font-size: 15px; color: var(--text-1); min-width: 48px; text-align: center; }
  .ib { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); width: 30px; height: 30px; }
  .seg { display: inline-flex; border: 1px solid var(--border); border-radius: var(--r-m); overflow: hidden; }
  .seg button { background: var(--surface-2); color: var(--text-2); border: none; padding: 7px 12px; font-size: 12px; }
  .seg button.an { background: var(--hl-primary); color: var(--hl-on-primary); }
  .ebenen { display: inline-flex; gap: 6px; flex-wrap: wrap; }
  .chip { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-3); border-radius: 999px; padding: 6px 11px; font-size: 11.5px; }
  .chip.an { background: color-mix(in srgb, var(--hl-primary) 18%, transparent); color: var(--hl-primary-text); border-color: var(--hl-primary); }
  /* Scrollbereich: das Gitter scrollt vertikal, die Matrix bringt ihr eigenes Scrollen mit. */
  .flaeche { flex: 1; min-height: 0; overflow: auto; }
  .hinweis { color: var(--text-3); font-size: 12.5px; padding: 16px; }
</style>
