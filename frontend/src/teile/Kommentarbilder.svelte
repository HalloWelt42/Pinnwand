<script lang="ts">
  // Bilder an einem Kommentar (HELF-56): klein im Kommentar, ein Klick zeigt eines groß über der Seite, mit Pfeilen zum
  // nächsten. Die Dateien sind Anhänge der Karte in der Kellerwolke und kommen über die Inhaltsadresse der Pinnwand
  // (jedes Mitglied darf sie öffnen). Ein Bild, das inzwischen von der Karte genommen ist, fehlt still. Escape, ein
  // Klick daneben oder das X schließt die große Ansicht.
  import { dateiAdresse } from "../daten/anwendung/anhaenge.svelte";
  import type { Karte } from "../modell";

  let { karte, namen }: { karte: Karte; namen: string[] } = $props();

  const bilder = $derived(namen.map((n) => karte.anhaenge.find((a) => a.name === n && a.art === "bild"))
    .filter((a) => !!a).map((a) => ({ name: a.name, adresse: dateiAdresse(karte, a) })).filter((b) => b.adresse));
  let gross = $state<number | null>(null);

  /** die große Ansicht hängt am Ende der Seite, damit kein Rollfeld oder keine Schale sie beschneidet oder überdeckt */
  function anDieSeite(knoten: HTMLElement): { destroy: () => void } {
    document.body.append(knoten);
    return { destroy: () => knoten.remove() };
  }

  function taste(e: KeyboardEvent): void {
    if (gross === null) return;
    if (e.key === "Escape") gross = null;
    else if (e.key === "ArrowRight") gross = (gross + 1) % bilder.length;
    else if (e.key === "ArrowLeft") gross = (gross - 1 + bilder.length) % bilder.length;
    else return;
    e.preventDefault();
  }
</script>

<svelte:window onkeydown={taste} />

{#if bilder.length}
  <div class="pw-kommentarbilder">
    {#each bilder as b, i (b.name)}
      <button class="pw-kommentarbild" title="{b.name}: groß ansehen" onclick={() => (gross = i)}>
        <img src={b.adresse} alt={b.name} loading="lazy" /></button>
    {/each}
  </div>
{/if}

{#if gross !== null && bilder[gross]}
  {@const b = bilder[gross]}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="pw-bildansicht" use:anDieSeite role="dialog" aria-label="Bild {b.name}" tabindex="-1" onclick={(e) => { if (e.target === e.currentTarget) gross = null; }}>
    <figure>
      <img src={b.adresse} alt={b.name} />
      <figcaption>{b.name}{#if bilder.length > 1} · {gross + 1} von {bilder.length}{/if}</figcaption>
    </figure>
    <button class="knopf symbol pw-bildansicht-zu" aria-label="Schließen" title="Schließen (Escape)" onclick={() => (gross = null)}><i class="fa-solid fa-xmark"></i></button>
    {#if bilder.length > 1}
      <button class="knopf symbol pw-bildansicht-zurueck" aria-label="Voriges Bild" onclick={() => (gross = (gross! - 1 + bilder.length) % bilder.length)}><i class="fa-solid fa-chevron-left"></i></button>
      <button class="knopf symbol pw-bildansicht-weiter" aria-label="Nächstes Bild" onclick={() => (gross = (gross! + 1) % bilder.length)}><i class="fa-solid fa-chevron-right"></i></button>
    {/if}
  </div>
{/if}
