<script lang="ts">
  // Farbe aus der Palette des Appkerns wählen, als Knöpfe (kein nativer Farbwähler); das Wort steht immer dabei.
  // Kompakt zeigt nur die gewählte Farbe und klappt die Palette erst auf Klick auf (für Zeilen in Listen).
  import { FARBEN, FARBNAMEN } from "../anzeige";
  import type { Farbe } from "../modell";

  let { wert, waehlen, kompakt = false, keine = false, wofuer = "Farbe" }: {
    /** leer: keine Farbe (nur mit keine) */
    wert: Farbe | undefined; waehlen: (f: Farbe | undefined) => void; kompakt?: boolean;
    /** auch "keine Farbe" anbieten (etwa beim Cover einer Karte) */
    keine?: boolean;
    /** wofür die Farbe gilt, für Hinweise und Vorlesen */
    wofuer?: string;
  } = $props();
  let offen = $state(false);
</script>

{#snippet palette()}
  <span class="pw-farbwahl-palette" role="radiogroup" aria-label={wofuer}>
    {#if keine}
      <button type="button" role="radio" aria-checked={!wert} class="kein" class:gewaehlt={!wert} title="Keine" aria-label="{wofuer}: keine"
              onclick={() => { waehlen(undefined); offen = false; }}></button>
    {/if}
    {#each FARBEN as f (f)}
      <button type="button" role="radio" aria-checked={wert === f} data-farbe={f} class:gewaehlt={wert === f} title={FARBNAMEN[f]}
              aria-label="{wofuer}: {FARBNAMEN[f]}" onclick={() => { waehlen(f); offen = false; }}></button>
    {/each}
  </span>
{/snippet}

{#if kompakt}
  <span class="pw-farbwahl">
    <button type="button" class="chip" data-farbe={wert} aria-expanded={offen} title="{wofuer} ändern" onclick={() => (offen = !offen)}>
      <span class="pw-farbpunkt"></span>{wert ? FARBNAMEN[wert] : "Keine"}<i class="fa-solid fa-chevron-{offen ? 'up' : 'down'}"></i></button>
    {#if offen}{@render palette()}{/if}
  </span>
{:else}
  <span class="pw-farbwahl">{@render palette()}<span class="pw-farbwahl-name" data-farbe={wert}><span class="pw-farbpunkt"></span>{wert ? FARBNAMEN[wert] : "Keine"}</span></span>
{/if}
