<script lang="ts">
  // Eigenstaendige Checkliste: abhaken, umbenennen (Klick auf Text), hinzufuegen, loeschen.
  // Reicht Einzeloperationen nach oben - der Aufrufer speichert sie atomar am Server.
  import type { ChecklistPunkt } from '../../types'

  let { punkte, onPunktNeu, onPunktAendern, onPunktEntfernen }: {
    punkte: ChecklistPunkt[]
    onPunktNeu: (text: string) => void
    onPunktAendern: (index: number, daten: { text?: string; erledigt?: boolean }) => void
    onPunktEntfernen: (index: number) => void
  } = $props()

  let neuerPunkt = $state('')
  let punktEdit = $state<number | null>(null)
  const erledigt = $derived(punkte.filter((c) => c.erledigt).length)

  function umschalten(i: number) {
    onPunktAendern(i, { erledigt: !punkte[i].erledigt })
  }
  function hinzufuegen() {
    const t = neuerPunkt.trim()
    if (!t) return
    onPunktNeu(t)
    neuerPunkt = ''
  }
  function entfernen(i: number) {
    onPunktEntfernen(i)
  }
  function textAendern(i: number, wert: string) {
    const t = wert.trim()
    punktEdit = null
    if (!t || t === punkte[i]?.text) return
    onPunktAendern(i, { text: t })
  }
</script>

<p class="sec">Checkliste {#if punkte.length}<span class="dezent">&middot; {erledigt} von {punkte.length}</span>{/if}</p>
{#if punkte.length}
  <div class="chkbar"><span style="width:{(erledigt / punkte.length) * 100}%"></span></div>
{/if}
{#each punkte as punkt, i (i)}
  <div class="chk" class:done={punkt.erledigt}>
    <button class="box" aria-label="Umschalten" onclick={() => umschalten(i)}>
      <i class="fa-{punkt.erledigt ? 'solid fa-square-check' : 'regular fa-square'}" aria-hidden="true"></i>
    </button>
    {#if punktEdit === i}
      <!-- svelte-ignore a11y_autofocus -->
      <input class="chkedit" value={punkt.text} autofocus aria-label="Punkt-Text"
        onblur={(e) => textAendern(i, e.currentTarget.value)}
        onkeydown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); else if (e.key === 'Escape') punktEdit = null }} />
    {:else}
      <button class="chktext" title="Zum Umbenennen klicken" onclick={() => (punktEdit = i)}>{punkt.text}</button>
    {/if}
    <button class="del" aria-label="Punkt entfernen" onclick={() => entfernen(i)}><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
  </div>
{/each}
<input class="feld" placeholder="+ Punkt hinzufügen" bind:value={neuerPunkt} onkeydown={(e) => { if (e.key === 'Enter') hinzufuegen() }} />

<style>
  .sec {
    font-family: var(--font-display);
    font-size: 10.5px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-3);
    margin: 18px 0 8px;
  }
  .dezent { color: var(--text-3); text-transform: none; letter-spacing: normal; }
  .chkbar { height: 4px; background: var(--surface-3); border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
  .chkbar span { display: block; height: 100%; background: var(--ok); }
  .chk { display: flex; align-items: center; gap: 9px; font-size: 12.5px; color: var(--text-1); padding: 4px 0; }
  .chk.done .chktext { color: var(--text-3); text-decoration: line-through; }
  .chk .box { border: none; background: transparent; color: var(--text-2); font-size: 15px; padding: 0; cursor: pointer; }
  .chk.done .box { color: var(--ok); }
  .chktext { flex: 1; cursor: text; border: none; background: transparent; color: inherit; font: inherit; text-align: left; padding: 0; }
  .chkedit { flex: 1; border: 1px solid var(--hl-primary); background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s); padding: 3px 6px; font-size: 12.5px; }
  .chk .del { border: none; background: transparent; color: var(--text-3); padding: 0; cursor: pointer; }
  .chk .del:hover { color: var(--gefahr); }
  .feld {
    width: 100%; box-sizing: border-box; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text-1); border-radius: var(--r-s);
    padding: 7px 9px; font-size: 12.5px; margin-top: 6px;
  }
</style>
