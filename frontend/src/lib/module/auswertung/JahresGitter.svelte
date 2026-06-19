<script lang="ts">
  import type { KalenderAntwort, KalenderZelle } from '../../api'
  import { tagAggregat, type Ebenen } from './kalenderfarben'

  let { daten, ebenen, onTag }: { daten: KalenderAntwort; ebenen: Ebenen; onTag: (iso: string) => void } = $props()

  const MONATE = ['Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
  const WD = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
  const heuteD = new Date()
  const HEUTE = `${heuteD.getFullYear()}-${String(heuteD.getMonth() + 1).padStart(2, '0')}-${String(heuteD.getDate()).padStart(2, '0')}`

  // iso -> Zellen aller Personen
  const proTag = $derived.by(() => {
    const m: Record<string, KalenderZelle[]> = {}
    for (const iso of daten.tage) {
      m[iso] = daten.personen.map((p) => daten.zellen[p.id]?.[iso]).filter(Boolean) as KalenderZelle[]
    }
    return m
  })

  function zelleen(monat: number): { iso: string | null }[] {
    // monat 0..11; baut Zellen inkl. fuehrender Leerfelder (Mo-Start)
    const erster = new Date(daten.jahr, monat, 1)
    const start = (erster.getDay() + 6) % 7 // Mo=0
    const tage = new Date(daten.jahr, monat + 1, 0).getDate()
    const out: { iso: string | null }[] = []
    for (let i = 0; i < start; i++) out.push({ iso: null })
    for (let t = 1; t <= tage; t++) {
      const iso = `${daten.jahr}-${String(monat + 1).padStart(2, '0')}-${String(t).padStart(2, '0')}`
      out.push({ iso })
    }
    return out
  }
</script>

<div class="gitter">
  {#each MONATE as name, m (m)}
    <div class="monat">
      <div class="mkopf">{name}</div>
      <div class="wdzeile">{#each WD as w (w)}<span>{w}</span>{/each}</div>
      <div class="tage">
        {#each zelleen(m) as z, i (z.iso ?? `lk-${m}-${i}`)}
          {#if z.iso}
            {@const agg = tagAggregat(proTag[z.iso] ?? [], ebenen)}
            {@const tag = Number(z.iso.slice(8, 10))}
            <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
            <div class="tag" class:heute={z.iso === HEUTE} style="background:{agg.bg}" role="button" tabindex="-1" title={z.iso + ' - ' + agg.titel} onclick={() => onTag(z.iso!)}>
              <span class="nr">{tag}</span>
              {#if agg.zahl}<span class="zahl">{agg.zahl}</span>{/if}
            </div>
          {:else}
            <div class="leer"></div>
          {/if}
        {/each}
      </div>
    </div>
  {/each}
</div>

<style>
  .gitter { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; padding: 14px; }
  .monat { border: 1px solid var(--border); border-radius: var(--r-l); background: var(--surface-col); padding: 10px; }
  .mkopf { font-family: var(--font-display); font-size: 12.5px; color: var(--text-1); margin-bottom: 6px; }
  .wdzeile { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; margin-bottom: 3px; }
  .wdzeile span { text-align: center; font-size: 9.5px; color: var(--text-3); }
  .tage { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
  .tag { position: relative; aspect-ratio: 1; border-radius: var(--r-s, 5px); border: 1px solid var(--border); display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; overflow: hidden; }
  .tag:hover { outline: 1px solid var(--hl-primary); }
  .tag.heute { outline: 2px solid var(--ok); outline-offset: -2px; z-index: 1; }
  .nr { font-size: 9px; color: var(--text-3); position: absolute; top: 1px; left: 3px; }
  .zahl { font-size: 10px; color: var(--text-1); font-weight: 500; }
  .leer { aspect-ratio: 1; }
</style>
