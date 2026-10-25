<script lang="ts">
  // Dateien aus deiner Kellerwolke an die Karte hängen (E-15): suchen, mehrere wählen, verknüpfen. Schon verknüpfte
  // stehen als solche da. Die Dateien bleiben, wo sie sind; Mitglieder sehen sie über die Rechte des Boards. Eine Fläche im
  // Detail, kein Browser-Dialog; Escape oder Abbrechen schließt sie.
  import { onMount } from "svelte";
  import { ausKellerwolke, KELLERWOLKE, type KellerwolkeDatei } from "../beispiel/anwendung/anhaenge.svelte";
  import type { Karte } from "../modell";
  import { verlassen, verwerfbar } from "../teile/verwerfen";
  import { SYMBOL } from "./anhang";
  import { inSicht } from "./sicht";

  let { karte, schliessen }: { karte: Karte; schliessen: () => void } = $props();

  let suche = $state("");
  let gewaehlt = $state<string[]>([]);
  let flaeche = $state<HTMLElement>();
  const kennung = (d: KellerwolkeDatei): string => `${d.pfad}/${d.name}`;
  const da = (d: KellerwolkeDatei): boolean => karte.anhaenge.some((a) => a.verknuepft && a.name === d.name);
  // beim Öffnen ganz in Sicht, auch wenn der Abschnitt unten im Detail steht
  onMount(() => inSicht(flaeche));
  const liste = $derived(KELLERWOLKE.filter((d) => kennung(d).toLowerCase().includes(suche.trim().toLowerCase())));

  function umschalten(d: KellerwolkeDatei): void {
    const k = kennung(d);
    gewaehlt = gewaehlt.includes(k) ? gewaehlt.filter((x) => x !== k) : [...gewaehlt, k];
  }

  function verknuepfen(): void {
    ausKellerwolke(karte.id, KELLERWOLKE.filter((d) => gewaehlt.includes(kennung(d))));
    zu();
  }

  function zu(): void {
    if (flaeche) verlassen(flaeche);
    schliessen();
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); zu(); }
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="pw-wolkenwahl" role="group" aria-label="Aus der Kellerwolke wählen" tabindex="-1" bind:this={flaeche} onkeydown={taste}>
  <div class="pw-wolkenwahl-kopf">
    <i class="fa-solid fa-cloud"></i><b>Deine Kellerwolke</b>
    <label class="suche"><i class="fa-solid fa-magnifying-glass"></i>
      <input bind:value={suche} use:verwerfbar placeholder="Datei oder Ordner suchen" aria-label="In der Kellerwolke suchen" autocomplete="off" /></label>
  </div>
  <div class="pw-wolkenwahl-liste">
    {#each liste as d (kennung(d))}
      {@const schon = da(d)}
      <label class="pw-wolkenwahl-datei" class:schon>
        <input type="checkbox" checked={schon || gewaehlt.includes(kennung(d))} disabled={schon} onchange={() => umschalten(d)} />
        <i class="fa-solid {SYMBOL[d.art]}"></i>
        <span class="wer"><span class="name">{d.name}</span><span class="pfad">{d.pfad}</span></span>
        <span class="meta">{schon ? "schon verknüpft" : d.groesse}</span>
      </label>
    {:else}
      <div class="leer-zeile">Keine Datei passt zu "{suche.trim()}".</div>
    {/each}
  </div>
  <div class="pw-wolkenwahl-fuss">
    <button class="knopf haupt klein" disabled={!gewaehlt.length} onclick={verknuepfen}><i class="fa-solid fa-link"></i>{gewaehlt.length > 1 ? `${gewaehlt.length} Dateien verknüpfen` : "Verknüpfen"}</button>
    <button class="knopf ohne klein" onclick={zu}>Abbrechen</button>
    <span class="schwach">Die Dateien bleiben in deiner Kellerwolke; Mitglieder sehen sie über die Rechte des Boards.</span>
  </div>
</div>
