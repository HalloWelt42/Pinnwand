<script lang="ts">
  // Eigener Verwaltungsbereich für Labels: anlegen, umbenennen, Farbe aus der
  // Material-Palette zuweisen, entfernen. Die Farben gelten global überall, wo
  // das Label vorkommt. karte.labels bleibt freie Text-Liste - hier wird nur die
  // zugewiesene Farbe verwaltet; unbekannte Labels behalten ihre Fallback-Farbe.
  import { onMount } from 'svelte'
  import { ladeLabels, erstelleLabel, aktualisiereLabel, loescheLabel, type LabelDefinition } from '../../api'
  import { setzeLabelDefinitionen, labelFarbeFamilie, hexFuerFamilie, familieAusHex } from '../../labels'
  import { theme } from '../../theme/theme.svelte'
  import FarbWahl from '../../FarbWahl.svelte'

  let { boardId: _b = '' }: { boardId?: string } = $props()
  $effect(() => void _b)

  let labels = $state<LabelDefinition[]>([])
  let neuName = $state('')
  let neuFamilie = $state('blue')
  let fehler = $state('')
  let laedt = $state(true)

  const dunkel = $derived(theme.modus === 'dunkel')

  async function laden(): Promise<void> {
    laedt = true
    try {
      labels = await ladeLabels()
      setzeLabelDefinitionen(labels) // In-Memory-Farbquelle frisch halten.
    } catch {
      fehler = 'Labels konnten nicht geladen werden.'
    } finally {
      laedt = false
    }
  }
  onMount(laden)

  async function anlegen(): Promise<void> {
    const name = neuName.trim()
    if (!name) return
    fehler = ''
    try {
      await erstelleLabel(name, neuFamilie)
      neuName = ''
      await laden()
    } catch {
      fehler = `Ein Label "${name}" gibt es bereits.`
    }
  }

  async function umbenennen(def: LabelDefinition, wert: string): Promise<void> {
    const name = wert.trim()
    if (!name || name === def.name) return
    fehler = ''
    try {
      await aktualisiereLabel(def.id, { name })
      await laden()
    } catch {
      fehler = `Der Name "${name}" ist bereits vergeben.`
      await laden()
    }
  }

  async function faerben(def: LabelDefinition, hex: string | null): Promise<void> {
    if (!hex) return
    const familie = familieAusHex(hex)
    if (!familie || familie === def.familie) return
    await aktualisiereLabel(def.id, { familie })
    await laden()
  }

  async function entfernen(def: LabelDefinition): Promise<void> {
    await loescheLabel(def.id)
    await laden()
  }

  function neueFarbe(hex: string | null): void {
    const f = hex && familieAusHex(hex)
    if (f) neuFamilie = f
  }
</script>

<div class="labels">
  <p class="sec">Label-Verwaltung</p>
  <p class="hint">
    Lege eigene Labels an und weise ihnen eine Farbe aus der Palette zu. Die Farbe gilt
    überall, wo das Label an einer Karte vorkommt. Labels ohne eigene Farbe bekommen
    automatisch eine stabile Farbe. Beim Löschen wird nur die Farbzuweisung entfernt -
    der Text bleibt an den Karten erhalten (mit automatischer Farbe).
  </p>

  <div class="neu">
    <span class="vorschau" style="background:{labelFarbeFamilie(neuFamilie, dunkel).bg}; color:{labelFarbeFamilie(neuFamilie, dunkel).fg}">
      {neuName.trim() || 'Vorschau'}
    </span>
    <input
      class="feld"
      placeholder="Neues Label"
      bind:value={neuName}
      maxlength="40"
      aria-label="Name des neuen Labels"
      onkeydown={(e) => { if (e.key === 'Enter') anlegen() }}
    />
    <FarbWahl value={hexFuerFamilie(neuFamilie)} mitKeine={false} onWahl={neueFarbe} />
    <button class="btn primaer" onclick={anlegen} disabled={!neuName.trim()}>
      <i class="fa-solid fa-plus" aria-hidden="true"></i> Anlegen
    </button>
  </div>
  {#if fehler}<p class="fehler">{fehler}</p>{/if}

  {#if laedt}
    <p class="leer">Lade ...</p>
  {:else if !labels.length}
    <p class="leer">Noch keine Labels mit zugewiesener Farbe. Lege oben das erste an.</p>
  {:else}
    <div class="liste">
      {#each labels as def (def.id)}
        <div class="zeile">
          <span class="vorschau" style="background:{labelFarbeFamilie(def.familie, dunkel).bg}; color:{labelFarbeFamilie(def.familie, dunkel).fg}">
            {def.name}
          </span>
          <input
            class="feld name"
            value={def.name}
            maxlength="40"
            aria-label="Label umbenennen"
            onblur={(e) => umbenennen(def, e.currentTarget.value)}
            onkeydown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
          />
          <FarbWahl value={hexFuerFamilie(def.familie)} mitKeine={false} onWahl={(c) => faerben(def, c)} />
          <button class="ibtn gefahr" title="Label entfernen" aria-label="Label entfernen" onclick={() => entfernen(def)}>
            <i class="fa-solid fa-trash" aria-hidden="true"></i>
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .labels { height: 100%; overflow-y: auto; padding: 16px; max-width: 920px; }
  .sec { font-family: var(--font-display); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-3); margin: 0 0 8px; }
  .hint { font-size: 12px; color: var(--text-3); line-height: 1.55; margin: 0 0 14px; max-width: 72ch; }
  .neu { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 10px 12px; border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); }
  .feld { border: 1px solid var(--border-2); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-m); padding: 7px 10px; font-size: 12.5px; }
  .feld.name { flex: 1; min-width: 160px; }
  .btn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-m); padding: 8px 13px; font-size: 12.5px; display: inline-flex; align-items: center; gap: 7px; }
  .btn.primaer { background: var(--hl-primary); color: var(--hl-on-primary); border-color: transparent; font-weight: 500; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .fehler { margin: 9px 2px 0; font-size: 12px; color: var(--gefahr, #e5484d); }
  .leer { color: var(--text-3); font-size: 12.5px; margin-top: 14px; }
  .liste { margin-top: 14px; display: flex; flex-direction: column; gap: 6px; }
  .zeile { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 8px 12px; border: 1px solid var(--border); background: var(--surface-col); border-radius: var(--r-m); }
  .vorschau { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 999px; min-width: 64px; text-align: center; white-space: nowrap; }
  .ibtn { border: 1px solid var(--border); background: var(--surface-2); color: var(--text-2); border-radius: var(--r-s, 6px); width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; }
  .ibtn:hover { background: var(--surface-3); }
  .ibtn.gefahr:hover { color: var(--gefahr, #e5484d); }
</style>
