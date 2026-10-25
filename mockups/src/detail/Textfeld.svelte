<script lang="ts">
  // Markdown-Feld wie bisher: gerendert lesen, ein Klick bearbeitet an Ort und Stelle (Beschreibung) oder öffnet
  // gleich das Vollbild (Notizen); "Fertig" speichert erst, wenn der Server es bestätigt, nichts geht beim Schließen verloren.
  let { name, html = "", markdown = "", bearbeiten = false, nurVollbild = false, vorlesen = false }: {
    name: string; html?: string; markdown?: string; bearbeiten?: boolean; nurVollbild?: boolean; vorlesen?: boolean;
  } = $props();
  let offen = $state(false);
  $effect(() => { offen = bearbeiten; });
</script>

<section class="pw-abschnitt">
  <div class="etikett">{name}
    <span class="rechts">
      {#if vorlesen && html}<button class="knopf ohne symbol klein" title="Vorlesen"><i class="fa-solid fa-volume-high"></i></button>{/if}
      <button class="knopf ohne symbol klein" title="Vollbild"><i class="fa-solid fa-expand"></i></button>
    </span>
  </div>
  {#if offen}
    <div class="pw-text bearbeiten">
      <textarea>{markdown}</textarea>
    </div>
    <div style="display: flex; gap: var(--a2)">
      <button class="knopf haupt klein" onclick={() => (offen = false)}><i class="fa-solid fa-check"></i>Fertig</button>
      <button class="knopf ohne klein" onclick={() => (offen = false)}>Verwerfen</button>
      <span class="schwach" style="align-self: center; font-size: var(--marke)">Markdown; Escape verwirft</span>
    </div>
  {:else if html}
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="pw-text" onclick={() => { if (!nurVollbild) offen = true; }} title={nurVollbild ? "Klick öffnet das Vollbild" : "Klick zum Bearbeiten"}>{@html html}</div>
  {:else}
    <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
    <div class="pw-text noch-leer" onclick={() => (offen = true)}>Noch leer. Klicken zum Schreiben.</div>
  {/if}
</section>
