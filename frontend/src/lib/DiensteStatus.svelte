<script lang="ts">
  import { ladeDienste, ttsStimmen, type Dienst, type Stimmen } from './api'
  import { tts, setzeStimme } from './tts.svelte'

  let dienste = $state<Dienst[]>([])
  let stimmen = $state<Stimmen>({})
  let offen = $state(false)

  async function laden(): Promise<void> {
    try {
      dienste = (await ladeDienste()).dienste
    } catch {
      dienste = []
    }
    try {
      const s = (await ttsStimmen()).stimmen
      stimmen = Array.isArray(s) ? {} : s
    } catch {
      stimmen = {}
    }
    // Standard: erste eigene Stimme, falls noch keine gewählt ist.
    if (!tts.stimme && stimmen.custom && stimmen.custom.length) {
      setzeStimme(stimmen.custom[0].name)
    }
  }

  $effect(() => {
    laden()
  })

  const ttsDienst = $derived(dienste.find((d) => d.schluessel === 'tts'))
  const stimmOptionen = $derived([...(stimmen.custom ?? []).map((c) => c.name), ...(stimmen.speakers ?? [])])

  function zustand(d: Dienst): 'an' | 'aus' | 'leer' {
    if (d.erreichbar) return 'an'
    if (d.konfiguriert) return 'aus'
    return 'leer'
  }
</script>

<div class="dienste">
  <button class="kopf" onclick={() => (offen = !offen)} aria-expanded={offen} title="Dienste-Status">
    <i class="fa-solid fa-circle-nodes" aria-hidden="true"></i>
    <span class="lbl">Dienste</span>
    <span class="ampeln">
      {#each dienste as d (d.schluessel)}
        <span class="dot {zustand(d)}" title="{d.name}: {d.erreichbar ? 'erreichbar' : d.konfiguriert ? 'nicht erreichbar' : 'aus'}"></span>
      {/each}
    </span>
    <i class="fa-solid {offen ? 'fa-chevron-up' : 'fa-chevron-down'} pf" aria-hidden="true"></i>
  </button>

  {#if offen}
    <div class="auf">
      {#each dienste as d (d.schluessel)}
        <div class="zeile">
          <span class="dot {zustand(d)}"></span>
          <span class="nm">{d.name}</span>
          <span class="st">{d.erreichbar ? 'erreichbar' : d.konfiguriert ? 'aus' : '-'}</span>
        </div>
      {/each}

      {#if ttsDienst?.erreichbar && stimmOptionen.length}
        <label class="stimme">
          <span class="slbl">Vorlese-Stimme</span>
          <select value={tts.stimme} onchange={(e) => setzeStimme(e.currentTarget.value)}>
            {#each stimmOptionen as o (o)}<option value={o}>{o}</option>{/each}
          </select>
        </label>
      {/if}

      <button class="neu" onclick={laden}><i class="fa-solid fa-rotate" aria-hidden="true"></i> Aktualisieren</button>
    </div>
  {/if}
</div>

<style>
  .dienste {
    border: 1px solid var(--border);
    border-radius: var(--r-m);
    background: var(--surface-2);
    margin-bottom: 8px;
  }
  .kopf {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    background: transparent;
    border: none;
    color: var(--text-2);
    padding: 8px 10px;
    font-size: 12px;
  }
  .lbl {
    font-family: var(--font-display);
  }
  .ampeln {
    margin-left: auto;
    display: flex;
    gap: 3px;
  }
  .pf {
    font-size: 9px;
    color: var(--text-3);
    margin-left: 4px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex: none;
  }
  .dot.an {
    background: var(--ok);
  }
  .dot.aus {
    background: var(--due-amber-fg);
  }
  .dot.leer {
    background: var(--text-3);
    opacity: 0.5;
  }
  .auf {
    padding: 4px 10px 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .zeile {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
    color: var(--text-2);
  }
  .zeile .nm {
    flex: 1;
  }
  .zeile .st {
    color: var(--text-3);
    font-size: 10.5px;
  }
  .stimme {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-top: 4px;
  }
  .slbl {
    font-size: 10.5px;
    color: var(--text-3);
  }
  .stimme select {
    background: var(--surface-1);
    color: var(--text-1);
    border: 1px solid var(--border-2);
    border-radius: var(--r-s);
    padding: 5px 7px;
    font-size: 12px;
  }
  .neu {
    margin-top: 4px;
    background: transparent;
    border: 1px solid var(--border-2);
    color: var(--text-2);
    border-radius: var(--r-s);
    padding: 5px 8px;
    font-size: 11px;
  }
  .neu:hover {
    color: var(--hl-primary-text);
    border-color: var(--hl-primary);
  }
</style>
