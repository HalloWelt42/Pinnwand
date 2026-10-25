<script lang="ts">
  // Farbe aus der Palette des Appkerns wählen, als Knöpfe (kein nativer Farbwähler); das Wort steht immer dabei.
  // Kompakt zeigt nur die gewählte Farbe und klappt die Palette erst auf Klick auf (für Zeilen in Listen).
  import type { Farbe } from "../../modell";
  import { FARBEN, FARBNAMEN } from "./daten";

  let { wert, waehlen, kompakt = false, wofuer = "Farbe" }: {
    wert: Farbe; waehlen: (f: Farbe) => void; kompakt?: boolean;
    /** wofür die Farbe gilt, für Hinweise und Vorlesen */
    wofuer?: string;
  } = $props();
  let offen = $state(false);
</script>

{#snippet palette()}
  <span class="pw-cover-wahl pw-verwaltung-palette" role="radiogroup" aria-label={wofuer}>
    {#each FARBEN as f (f)}
      <button type="button" role="radio" aria-checked={wert === f} data-farbe={f} class:gewaehlt={wert === f} title={FARBNAMEN[f]}
              aria-label="{wofuer}: {FARBNAMEN[f]}" onclick={() => { waehlen(f); offen = false; }}></button>
    {/each}
  </span>
{/snippet}

{#if kompakt}
  <span class="pw-verwaltung-farbe">
    <button type="button" class="chip" data-farbe={wert} aria-expanded={offen} title="{wofuer} ändern" onclick={() => (offen = !offen)}>
      <span class="pw-farbpunkt"></span>{FARBNAMEN[wert]}<i class="fa-solid fa-chevron-{offen ? 'up' : 'down'}"></i></button>
    {#if offen}{@render palette()}{/if}
  </span>
{:else}
  <span class="pw-verwaltung-farbe">{@render palette()}<span class="pw-verwaltung-farbname" data-farbe={wert}><span class="pw-farbpunkt"></span>{FARBNAMEN[wert]}</span></span>
{/if}
