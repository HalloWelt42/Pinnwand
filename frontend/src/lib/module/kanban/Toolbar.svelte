<script lang="ts">
  import type { Prioritaet } from '../../types'
  import type { KiVorschlag } from '../../api'
  import KiAssistent from '../../ki/KiAssistent.svelte'

  let {
    suche = $bindable(),
    sortModus = $bindable(),
    filterPrio = $bindable(),
    filterLabels = $bindable(),
    alleLabels,
    mitglieder,
    reorderPausiert,
  }: {
    suche: string
    sortModus: 'manuell' | 'faellig' | 'prioritaet'
    filterPrio: Prioritaet | null
    filterLabels: string[]
    alleLabels: string[]
    mitglieder: string[]
    reorderPausiert: boolean
  } = $props()

  let filterOffen = $state(false)
  const aktiveFilter = $derived(filterLabels.length + (filterPrio ? 1 : 0))

  function labelUmschalten(l: string) {
    filterLabels = filterLabels.includes(l) ? filterLabels.filter((x) => x !== l) : [...filterLabels, l]
  }
  function zuruecksetzen() {
    suche = ''
    filterPrio = null
    filterLabels = []
    sortModus = 'manuell'
  }

  // KI schlaegt eine Filter-Kombination aus einem Wunsch vor; uebernommen wird nur,
  // was der Mensch in der Checkliste bestaetigt.
  function kiFilterKontext(): Record<string, unknown> {
    return {
      labels: alleLabels,
      prioritaeten: ['hoch', 'mittel', 'niedrig'],
      sortierungen: ['manuell', 'faellig', 'prioritaet'],
    }
  }
  function kiFilterUebernehmen(gewaehlt: KiVorschlag[]): void {
    for (const v of gewaehlt) {
      const [art, wert] = v.id.split(':')
      if (art === 'label' && alleLabels.includes(wert) && !filterLabels.includes(wert)) {
        filterLabels = [...filterLabels, wert]
      } else if (art === 'prioritaet' && ['hoch', 'mittel', 'niedrig'].includes(wert)) {
        filterPrio = wert as Prioritaet
      } else if (art === 'sortierung' && ['manuell', 'faellig', 'prioritaet'].includes(wert)) {
        sortModus = wert as 'manuell' | 'faellig' | 'prioritaet'
      }
    }
  }
</script>

<div class="tb">
  <label class="suche">
    <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
    <input placeholder="Suchen in Titel, Inhalt, Labels, Kommentaren ..." bind:value={suche} aria-label="Suche" />
    {#if suche}<button class="x" aria-label="Suche leeren" onclick={() => (suche = '')}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>{/if}
  </label>

  <div class="dd">
    <button class="chip" class:aktiv={aktiveFilter > 0} onclick={() => (filterOffen = !filterOffen)}>
      <i class="fa-solid fa-filter" aria-hidden="true"></i> Filter{#if aktiveFilter > 0}<span class="zahl">{aktiveFilter}</span>{/if}
    </button>
    {#if filterOffen}
      <div class="panel">
        <p class="ueber">Priorität</p>
        <div class="prios">
          {#each [['hoch', 'Hoch'], ['mittel', 'Mittel'], ['niedrig', 'Niedrig']] as [wert, text] (wert)}
            <button class="pchip" class:on={filterPrio === wert} onclick={() => (filterPrio = filterPrio === wert ? null : (wert as Prioritaet))}>{text}</button>
          {/each}
        </div>
        {#if alleLabels.length}
          <p class="ueber">Labels</p>
          <div class="labs">
            {#each alleLabels as l (l)}
              <button class="pchip" class:on={filterLabels.includes(l)} onclick={() => labelUmschalten(l)}>{l}</button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <div class="sort">
    <i class="fa-solid fa-arrow-down-wide-short" aria-hidden="true"></i>
    <select bind:value={sortModus} aria-label="Sortieren">
      <option value="manuell">Manuell</option>
      <option value="faellig">Fällig</option>
      <option value="prioritaet">Priorität</option>
    </select>
  </div>

  <KiAssistent typ="filter" titel="Filter vorschlagen" platzhalter="Was willst du sehen? z.B. dringende offene Bugs" uebernehmenText="Anwenden" kontext={kiFilterKontext} onUebernehmen={kiFilterUebernehmen} />

  {#if reorderPausiert}
    <button class="hinweis" onclick={zuruecksetzen} title="Filter und Sortierung zurücksetzen">
      <i class="fa-solid fa-lock" aria-hidden="true"></i> Verschieben pausiert
    </button>
  {/if}

  {#if mitglieder.length}
    <div class="avs" aria-label="Mitglieder">
      {#each mitglieder.slice(0, 5) as m (m)}<span class="av">{m}</span>{/each}
      {#if mitglieder.length > 5}<span class="av rest">+{mitglieder.length - 5}</span>{/if}
    </div>
  {/if}
</div>

<style>
  .tb {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    background: var(--surface-col);
  }
  .suche {
    flex: 1;
    min-width: 0;
    max-width: 360px;
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    padding: 0 10px;
    color: var(--text-3);
    height: 32px;
  }
  .suche input {
    flex: 1;
    min-width: 0;
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 12.5px;
    outline: none;
  }
  .suche .x {
    border: none;
    background: transparent;
    color: var(--text-3);
    font-size: 12px;
  }
  .dd {
    position: relative;
  }
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    height: 32px;
    padding: 0 11px;
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    background: var(--surface-2);
    color: var(--text-2);
    font-size: 12.5px;
  }
  .chip:hover {
    color: var(--text-1);
    border-color: var(--border-2);
  }
  .chip.aktiv {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .chip .zahl {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-radius: 8px;
    padding: 0 6px;
    font-size: 10px;
    font-weight: 600;
  }
  .panel {
    position: absolute;
    top: 38px;
    left: 0;
    z-index: 30;
    width: 240px;
    background: var(--surface-3);
    border: 1px solid var(--border-2);
    border-radius: var(--r-l);
    padding: 10px 11px;
    box-shadow: var(--schatten-pop);
  }
  .ueber {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 0 0 6px;
  }
  .prios,
  .labs {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 10px;
  }
  .labs {
    margin-bottom: 0;
  }
  .pchip {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: var(--r-m);
    border: 1px solid var(--border);
    background: var(--surface-1);
    color: var(--text-2);
  }
  .pchip.on {
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
  .sort {
    display: flex;
    align-items: center;
    gap: 7px;
    height: 32px;
    padding: 0 10px;
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    background: var(--surface-2);
    color: var(--text-3);
    font-size: 12.5px;
  }
  .sort select {
    border: none;
    background: transparent;
    color: var(--text-1);
    font-size: 12.5px;
    outline: none;
  }
  .hinweis {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    padding: 0 11px;
    border-radius: var(--r-m);
    border: 1px solid var(--prio-mittel);
    background: transparent;
    color: var(--prio-mittel);
    font-size: 12px;
  }
  .avs {
    margin-left: auto;
    display: flex;
  }
  .av {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--hl-primary-weich);
    color: var(--hl-primary-text);
    font-size: 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--surface-col);
    margin-left: -7px;
  }
  .av:first-child {
    margin-left: 0;
  }
  .av.rest {
    background: var(--surface-3);
    color: var(--text-2);
  }
</style>
