<script lang="ts">
  // Die eine Meldung nach jeder Änderung, mit Rückgängig: am Rechner unten rechts über dem Fuß, am Telefon über der
  // Fußleiste. Sie geht nach sechs Sekunden von selbst (wie in der alten App), nicht solange der Zeiger darauf ruht; in
  // vorgeführten Zuständen bleibt sie stehen, damit man sie sieht. Jede Ansicht zeigt dieselbe, es gibt keine zweite.
  import { meldungSchliessen } from "../beispiel/anwendung/meldung.svelte";
  import { stand } from "../beispiel/stand.svelte";
  import { wert } from "../weg.svelte";

  let { ort = "rechner" }: { ort?: "rechner" | "telefon" } = $props();
  const STEHT_MS = 6000;
  const getrennt = $derived(stand.verbindung === "getrennt");
  let darauf = $state(false);

  $effect(() => {
    const m = stand.meldung;
    if (!m || darauf || wert("entwurf")) return;
    const uhr = setTimeout(() => { if (stand.meldung === m) meldungSchliessen(); }, STEHT_MS);
    return () => clearTimeout(uhr);
  });
</script>

{#if stand.meldung}
  <div class="pw-meldungen {ort}" role="status" onmouseenter={() => (darauf = true)} onmouseleave={() => (darauf = false)}>
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
