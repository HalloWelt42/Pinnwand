<script lang="ts">
  // Die eine Meldung nach jeder Änderung, mit Rückgängig, solange sie steht: am Rechner unten rechts über dem Fuß, am
  // Telefon über der Fußleiste. Jede Ansicht zeigt dieselbe; es gibt keine zweite Meldung.
  import { meldungSchliessen } from "../beispiel/anwendung/meldung.svelte";
  import { stand } from "../beispiel/stand.svelte";

  let { ort = "rechner" }: { ort?: "rechner" | "telefon" } = $props();
  const getrennt = $derived(stand.verbindung === "getrennt");
</script>

{#if stand.meldung}
  <div class="pw-meldungen {ort}" role="status">
    <div class="pw-meldung" class:gefahr={getrennt}>
      <i class="fa-solid {getrennt ? 'fa-plug-circle-xmark' : 'fa-circle-info'} zeichen"></i>
      <span>{stand.meldung.text}</span>
      {#if stand.meldung.rueckgaengig}
        <button class="knopf klein" onclick={stand.meldung.rueckgaengig}><i class="fa-solid fa-rotate-left"></i>Rückgängig</button>
      {/if}
      <button class="knopf ohne symbol klein" title="Schließen" onclick={meldungSchliessen}><i class="fa-solid fa-xmark"></i></button>
    </div>
  </div>
{/if}
