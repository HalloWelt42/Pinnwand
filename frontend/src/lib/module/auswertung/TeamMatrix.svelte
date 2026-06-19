<script lang="ts">
  import type { KalenderAntwort } from '../../api'
  import { zellHintergrund, zellMarker, zellHalb, type Ebenen, type TypMap } from './kalenderfarben'

  let {
    daten,
    ebenen,
    typen,
    onBereich,
  }: {
    daten: KalenderAntwort
    ebenen: Ebenen
    typen: TypMap
    onBereich: (personId: string, von: string, bis: string) => void
  } = $props()

  const CW = 18
  const NAME_B = 150
  const MONATE = ['Jan', 'Feb', 'Maer', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
  const monate = $derived(
    MONATE.map((name, m) => ({ name, tage: new Date(daten.jahr, m + 1, 0).getDate() })),
  )
  const heuteD = new Date()
  const HEUTE = `${heuteD.getFullYear()}-${String(heuteD.getMonth() + 1).padStart(2, '0')}-${String(heuteD.getDate()).padStart(2, '0')}`

  function istWE(iso: string): boolean {
    return (new Date(iso + 'T00:00:00').getDay() + 6) % 7 >= 5
  }

  // Beim Oeffnen den heutigen Tag in den sichtbaren Bereich ruecken (einmalig je Jahr).
  let wrapEl: HTMLDivElement | undefined = $state()
  let zentriertesJahr = $state<number | null>(null)
  $effect(() => {
    if (!wrapEl || zentriertesJahr === daten.jahr) return
    const idx = daten.tage.indexOf(HEUTE)
    if (idx < 0) { zentriertesJahr = daten.jahr; return }
    wrapEl.scrollLeft = Math.max(0, NAME_B + idx * CW - wrapEl.clientWidth / 2)
    zentriertesJahr = daten.jahr
  })

  // Auswahl per Ziehen
  let ziehPerson = $state<string | null>(null)
  let ziehStart = $state<string | null>(null)
  let ziehEnde = $state<string | null>(null)

  function start(personId: string, iso: string): void {
    ziehPerson = personId
    ziehStart = iso
    ziehEnde = iso
  }
  function ueber(personId: string, iso: string): void {
    if (ziehPerson === personId) ziehEnde = iso
  }
  function fertig(): void {
    if (ziehPerson && ziehStart && ziehEnde) {
      const von = ziehStart < ziehEnde ? ziehStart : ziehEnde
      const bis = ziehStart < ziehEnde ? ziehEnde : ziehStart
      const p = ziehPerson
      ziehPerson = ziehStart = ziehEnde = null
      onBereich(p, von, bis)
    }
  }
  function imBereich(personId: string, iso: string): boolean {
    if (ziehPerson !== personId || !ziehStart || !ziehEnde) return false
    const a = ziehStart < ziehEnde ? ziehStart : ziehEnde
    const b = ziehStart < ziehEnde ? ziehEnde : ziehStart
    return iso >= a && iso <= b
  }
</script>

<svelte:window onpointerup={fertig} />
<div class="wrap" bind:this={wrapEl}>
  <div class="inhalt" style="--cw:{CW}px">
    <div class="kopf">
      <div class="namensp eck"></div>
      <div class="monate">
        {#each monate as mo (mo.name)}<div class="mo" style="width:calc({mo.tage} * var(--cw))">{mo.name}</div>{/each}
      </div>
    </div>
    {#each daten.personen as p (p.id)}
      <div class="zeile">
        <div class="namensp name" title={p.name}><b>{p.kuerzel ?? ''}</b> {p.name}</div>
        <div class="zellen">
          {#each daten.tage as iso (iso)}
            {@const z = daten.zellen[p.id]?.[iso]}
            {#if z}
              {@const mark = zellMarker(z, ebenen, typen)}
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <div
                class="z"
                role="gridcell"
                tabindex="-1"
                class:we={istWE(iso)}
                class:sel={imBereich(p.id, iso)}
                class:halb={zellHalb(z)}
                class:heute={iso === HEUTE}
                style="background:{zellHintergrund(z, ebenen, typen)}; {mark ? `box-shadow: inset 0 0 0 2px ${mark}` : ''}"
                title={`${p.name} ${iso}: ${z.status}${z.abw ? ' (' + z.abw.typ + ')' : ''}${z.feiertag ? ' - ' + z.feiertag : ''}`}
                onpointerdown={() => start(p.id, iso)}
                onpointerenter={() => ueber(p.id, iso)}
              ></div>
            {:else}
              <div class="z"></div>
            {/if}
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .wrap { height: 100%; overflow: auto; }
  .inhalt { display: inline-block; min-width: 100%; }
  .kopf { display: flex; position: sticky; top: 0; z-index: 3; background: var(--surface-col); border-bottom: 1px solid var(--border); }
  .namensp { width: 150px; min-width: 150px; position: sticky; left: 0; z-index: 2; background: var(--surface-col); border-right: 1px solid var(--border); }
  .eck { z-index: 4; }
  .monate { display: flex; }
  .mo { font-size: 10.5px; color: var(--text-3); padding: 4px 0 4px 3px; border-left: 1px solid var(--border); box-sizing: border-box; }
  .zeile { display: flex; border-bottom: 1px solid var(--border); }
  .name { font-size: 12px; color: var(--text-1); padding: 4px 8px; display: flex; align-items: center; gap: 5px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .name b { color: var(--text-3); font-family: var(--font-mono); font-size: 10px; }
  .zellen { display: flex; }
  .z { width: var(--cw); height: 26px; border-right: 1px solid var(--border); box-sizing: border-box; cursor: pointer; }
  .z.we { filter: brightness(0.8); }
  .z.sel { outline: 2px solid var(--hl-primary); outline-offset: -2px; }
  .z.heute { box-shadow: inset 1px 0 0 var(--ok), inset -1px 0 0 var(--ok); }
  .z.halb { background-image: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.28) 50%); }
</style>
