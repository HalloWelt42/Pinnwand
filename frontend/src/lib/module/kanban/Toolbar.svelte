<script lang="ts">
  import type { Prioritaet } from '../../types'
  import type { KiVorschlag } from '../../api'
  import KiAssistent from '../../ki/KiAssistent.svelte'
  import { leseJson, schreibeJson } from '../../uiSpeicher'

  let {
    boardId,
    ansichtsModus = $bindable(),
    suche = $bindable(),
    sortModus = $bindable(),
    filterPrio = $bindable(),
    filterLabels = $bindable(),
    filterZustaendig = $bindable(),
    alleLabels,
    mitglieder,
    reorderPausiert,
  }: {
    boardId: string
    ansichtsModus: 'board' | 'liste'
    suche: string
    sortModus: 'manuell' | 'faellig' | 'prioritaet'
    filterPrio: Prioritaet | null
    filterLabels: string[]
    filterZustaendig: string[]
    alleLabels: string[]
    mitglieder: string[]
    reorderPausiert: boolean
  } = $props()

  let filterOffen = $state(false)
  const aktiveFilter = $derived(filterLabels.length + (filterPrio ? 1 : 0) + filterZustaendig.length)

  // Benannte, je Board gespeicherte Filter-Kombinationen (browser-lokal wie der
  // uebrige UI-Zustand). Ein Klick auf den Chip wendet den Satz an, ein zweiter
  // setzt zurueck; gespeichert wird die KOMPLETTE Sicht (Suche, Prio, Labels,
  // Personen, Sortierung).
  interface FilterSatz {
    name: string
    suche: string
    sortModus: 'manuell' | 'faellig' | 'prioritaet'
    filterPrio: Prioritaet | null
    filterLabels: string[]
    filterZustaendig: string[]
  }
  let gespeicherte = $state<FilterSatz[]>([])
  let neuName = $state('')
  $effect(() => {
    gespeicherte = leseJson('pw_filtersets_' + boardId, [])
  })
  function filterMerken(): void {
    const name = neuName.trim()
    if (!name) return
    const satz: FilterSatz = {
      name, suche, sortModus, filterPrio,
      filterLabels: [...filterLabels], filterZustaendig: [...filterZustaendig],
    }
    gespeicherte = [...gespeicherte.filter((s) => s.name !== name), satz]
    schreibeJson('pw_filtersets_' + boardId, $state.snapshot(gespeicherte))
    neuName = ''
  }
  function filterAnwenden(s: FilterSatz): void {
    suche = s.suche
    sortModus = s.sortModus
    filterPrio = s.filterPrio
    filterLabels = [...s.filterLabels]
    filterZustaendig = [...s.filterZustaendig]
    filterOffen = false
  }
  function filterEntfernen(name: string): void {
    gespeicherte = gespeicherte.filter((s) => s.name !== name)
    schreibeJson('pw_filtersets_' + boardId, $state.snapshot(gespeicherte))
  }
  function gleicheListe(a: string[], b: string[]): boolean {
    return a.length === b.length && a.every((x) => b.includes(x))
  }
  function satzAktiv(s: FilterSatz): boolean {
    return suche === s.suche && sortModus === s.sortModus && filterPrio === s.filterPrio
      && gleicheListe(filterLabels, s.filterLabels) && gleicheListe(filterZustaendig, s.filterZustaendig)
  }

  function labelUmschalten(l: string) {
    filterLabels = filterLabels.includes(l) ? filterLabels.filter((x) => x !== l) : [...filterLabels, l]
  }
  function zuruecksetzen() {
    suche = ''
    filterPrio = null
    filterLabels = []
    filterZustaendig = []
    sortModus = 'manuell'
  }
  function personUmschalten(m: string) {
    filterZustaendig = filterZustaendig.includes(m) ? filterZustaendig.filter((x) => x !== m) : [...filterZustaendig, m]
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
  <div class="modus" role="group" aria-label="Darstellung">
    <button class="mb" class:on={ansichtsModus === 'board'} title="Spalten-Ansicht" aria-label="Spalten-Ansicht" onclick={() => (ansichtsModus = 'board')}>
      <i class="fa-solid fa-table-columns" aria-hidden="true"></i>
    </button>
    <button class="mb" class:on={ansichtsModus === 'liste'} title="Listen-Ansicht" aria-label="Listen-Ansicht" onclick={() => (ansichtsModus = 'liste')}>
      <i class="fa-solid fa-table-list" aria-hidden="true"></i>
    </button>
  </div>
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
        <p class="ueber merken-ueber">Sicht speichern</p>
        <div class="merken">
          <input placeholder="Name der Sicht" bind:value={neuName} aria-label="Name der gespeicherten Sicht"
            onkeydown={(e) => { if (e.key === 'Enter') filterMerken() }} />
          <button class="pchip" disabled={!neuName.trim()} onclick={filterMerken}>Speichern</button>
        </div>
      </div>
    {/if}
  </div>

  {#each gespeicherte as s (s.name)}
    <span class="fsatz" class:on={satzAktiv(s)}>
      <button class="fname" title={satzAktiv(s) ? 'Sicht zurücksetzen' : 'Gespeicherte Sicht anwenden'}
        onclick={() => (satzAktiv(s) ? zuruecksetzen() : filterAnwenden(s))}>
        <i class="fa-solid fa-bookmark" aria-hidden="true"></i> {s.name}
      </button>
      <button class="fx" aria-label="Gespeicherte Sicht {s.name} entfernen" onclick={() => filterEntfernen(s.name)}>
        <i class="fa-solid fa-xmark" aria-hidden="true"></i>
      </button>
    </span>
  {/each}

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
    <!-- Avatare sind der Personen-Filter: Klick zeigt nur die Karten der Person(en). -->
    <div class="avs" aria-label="Nach Person filtern">
      {#each mitglieder.slice(0, 7) as m (m)}
        <button class="av klick" class:on={filterZustaendig.includes(m)} title="Nur Karten von {m}" onclick={() => personUmschalten(m)}>{m}</button>
      {/each}
      {#if mitglieder.length > 7}<span class="av rest">+{mitglieder.length - 7}</span>{/if}
    </div>
  {/if}
</div>

<style>
  .av.klick { cursor: pointer; border: 1px solid transparent; background: var(--surface-2); }
  .av.klick:hover { border-color: var(--hl-primary); }
  .av.klick.on { background: var(--hl-primary); color: var(--hl-on-primary); font-weight: 700; }
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
  .merken-ueber { margin-top: 10px; }
  .merken { display: flex; gap: 6px; }
  .merken input {
    flex: 1; min-width: 0; border: 1px solid var(--border); background: var(--surface-1);
    color: var(--text-1); border-radius: var(--r-m); padding: 4px 8px; font-size: 12px; outline: none;
  }
  .merken input:focus { border-color: var(--hl-primary); }
  .merken .pchip:disabled { opacity: 0.5; }
  .fsatz {
    display: inline-flex; align-items: center; height: 32px;
    border: 1px solid var(--border); border-radius: var(--r-m); background: var(--surface-2);
    color: var(--text-2); font-size: 12px; overflow: hidden;
  }
  .fsatz.on { border-color: var(--hl-primary); color: var(--hl-primary-text); background: var(--hl-primary-weich); }
  .fsatz .fname { display: inline-flex; align-items: center; gap: 6px; height: 100%; padding: 0 4px 0 10px; border: none; background: transparent; color: inherit; font-size: inherit; }
  .fsatz .fx { height: 100%; padding: 0 8px; border: none; background: transparent; color: var(--text-3); font-size: 11px; }
  .fsatz .fx:hover { color: var(--gefahr); }
  .modus { display: flex; border: 1px solid var(--border); border-radius: var(--r-m); overflow: hidden; }
  .mb { width: 34px; height: 30px; border: none; background: var(--surface-2); color: var(--text-3); font-size: 12px; }
  .mb:hover { color: var(--text-1); }
  .mb.on { background: var(--hl-primary-weich); color: var(--hl-primary-text); }
</style>
