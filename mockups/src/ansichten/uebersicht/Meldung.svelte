<script lang="ts">
  // Meldung unten rechts auf den Seiten dieses Bereichs (wie im Board): Ergebnis einer Aktion, erst nach der Antwort.
  import { stand } from "../../beispiel/stand.svelte";
</script>

{#if stand.meldung}
  <div class="pw-meldungen">
    <div class="pw-meldung"><i class="fa-solid fa-circle-info zeichen"></i><span>{stand.meldung}</span>
      <button class="knopf klein">Rückgängig</button>
      <button class="knopf ohne symbol klein" title="Schließen" onclick={() => (stand.meldung = "")}><i class="fa-solid fa-xmark"></i></button></div>
  </div>
{/if}
