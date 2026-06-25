<script lang="ts">
  // Systematische Farbauswahl statt nativem Farbwaehler: feste, gut unterscheidbare
  // Material-Design-Farben als anklickbare Swatches (eine Palette, keine Freiwahl).
  import { material } from './theme/palette'

  let {
    value = null,
    onWahl,
    mitKeine = true,
  }: {
    value?: string | null
    onWahl: (hex: string | null) => void
    mitKeine?: boolean
  } = $props()

  // Kuratierte, gut unterscheidbare Familien (Stufe 500) - bewusst begrenzt und ruhig.
  const FAMILIEN = [
    'red', 'pink', 'purple', 'deepPurple', 'indigo', 'blue', 'cyan', 'teal',
    'green', 'lightGreen', 'amber', 'orange', 'deepOrange', 'blueGrey',
  ] as const
  const FARBEN = FAMILIEN.map((f) => material[f][500] as string)

  const aktiv = $derived((value ?? '').toLowerCase())
</script>

<div class="palette" role="group" aria-label="Farbe waehlen">
  {#if mitKeine}
    <button
      type="button"
      class="swatch keine"
      class:an={!value}
      title="Keine Farbe"
      aria-label="Keine Farbe"
      onclick={() => onWahl(null)}
    ><i class="fa-solid fa-ban" aria-hidden="true"></i></button>
  {/if}
  {#each FARBEN as hex (hex)}
    <button
      type="button"
      class="swatch"
      class:an={aktiv === hex.toLowerCase()}
      style="background:{hex}"
      title={hex}
      aria-label={hex}
      onclick={() => onWahl(hex)}
    ></button>
  {/each}
</div>

<style>
  .palette {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }
  .swatch {
    width: 22px;
    height: 22px;
    border-radius: var(--r-s);
    border: 1px solid var(--border-2);
    padding: 0;
    cursor: pointer;
    box-sizing: border-box;
  }
  .swatch:hover {
    transform: scale(1.12);
  }
  .swatch.an {
    outline: 2px solid var(--hl-primary);
    outline-offset: 1px;
  }
  .keine {
    background: var(--surface-2);
    color: var(--text-3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
  }
</style>
