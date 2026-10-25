<script lang="ts">
  // Meldung unten rechts nach jeder Änderung der Zeit-Ansichten, mit Rückgängig (wie im Board).
  import { zeit } from "./stand.svelte";
</script>

{#if zeit.meldung}
  <div class="pw-meldungen" role="status">
    <div class="pw-meldung"><i class="fa-solid fa-circle-info zeichen"></i><span>{zeit.meldung.text}</span>
      {#if zeit.meldung.rueckgaengig}<button class="knopf klein" onclick={() => zeit.meldung?.rueckgaengig?.()}>Rückgängig</button>{/if}
      <button class="knopf ohne symbol klein" title="Schließen" onclick={() => (zeit.meldung = null)}><i class="fa-solid fa-xmark"></i></button></div>
  </div>
{/if}
