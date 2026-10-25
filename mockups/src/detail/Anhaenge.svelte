<script lang="ts">
  // Anhänge der Karte (M-63, E-15): hochladen über die Dateiwahl oder durch Ziehen auf den Abschnitt, aus der eigenen
  // Kellerwolke verknüpfen, öffnen (die Datei aus der Kellerwolke in einem neuen Reiter) und entfernen mit Rückgängig.
  // Hochgeladenes liegt in der Kellerwolke im Ordner des Boards. Ändern nur mit dem Recht, die Karte zu bearbeiten.
  import { untrack } from "svelte";
  import { ablageOrt, dateiAdresse, entfernen, GRENZE_MB, hochladen } from "../beispiel/anwendung/anhaenge.svelte";
  import type { Anhang, Board, Karte } from "../modell";
  import { SYMBOL } from "./anhang";
  import Kellerwolkewahl from "./Kellerwolkewahl.svelte";

  let { karte, board, schreiben, wolke = false }: { karte: Karte; board: Board; schreiben: boolean; wolke?: boolean } = $props();

  let wahl = $state<HTMLInputElement>();
  let wolkeOffen = $state(false);
  let darueber = $state(false);
  $effect(() => { const w = wolke; untrack(() => { wolkeOffen = w; }); });

  function gewaehlt(e: Event & { currentTarget: HTMLInputElement }): void {
    const dateien = Array.from(e.currentTarget.files ?? []);
    e.currentTarget.value = "";
    hochladen(karte.id, dateien);
  }

  function mitDateien(e: DragEvent): boolean {
    return schreiben && !!e.dataTransfer?.types.includes("Files");
  }

  function ueber(e: DragEvent): void {
    if (!mitDateien(e)) return;
    e.preventDefault();
    darueber = true;
  }

  function weg(e: DragEvent & { currentTarget: HTMLElement }): void {
    if (!e.currentTarget.contains(e.relatedTarget as Node | null)) darueber = false;
  }

  function ablegen(e: DragEvent): void {
    if (!mitDateien(e)) return;
    e.preventDefault();
    darueber = false;
    hochladen(karte.id, Array.from(e.dataTransfer?.files ?? []));
  }

  function oeffnen(a: Anhang): void {
    window.open(dateiAdresse(karte, a), "_blank", "noopener");
  }
</script>

<section class="pw-abschnitt pw-anhaenge" class:darueber aria-label="Anhänge" ondragover={ueber} ondragleave={weg} ondrop={ablegen}>
  <div class="etikett">Anhänge {#if karte.anhaenge.length}<span class="zaehler">{karte.anhaenge.length}</span>{/if}
    {#if schreiben}
      <span class="rechts">
        <button class="knopf ohne klein" title="Dateien von diesem Gerät, bis {GRENZE_MB} MB je Datei" onclick={() => wahl?.click()}><i class="fa-solid fa-upload"></i>Hochladen</button>
        <button class="knopf klein" class:ohne={!wolkeOffen} class:aktiv={wolkeOffen} aria-expanded={wolkeOffen} onclick={() => (wolkeOffen = !wolkeOffen)}><i class="fa-solid fa-cloud"></i>Aus der Kellerwolke</button>
      </span>
      <input type="file" multiple hidden bind:this={wahl} onchange={gewaehlt} />
    {/if}
  </div>
  {#if wolkeOffen && schreiben}
    <Kellerwolkewahl {karte} schliessen={() => (wolkeOffen = false)} />
  {/if}
  {#each karte.anhaenge as a (a.name)}
    <div class="pw-anhang">
      <i class="fa-solid {SYMBOL[a.art]}"></i>
      <button class="name pw-anhang-name" title="{a.name} öffnen" onclick={() => oeffnen(a)}>{a.name}</button>
      <span class="meta">{a.verknuepft ? "verknüpft aus deiner Kellerwolke" : `${a.groesse} · Kellerwolke, ${ablageOrt(board)}`}</span>
      <button class="knopf ohne symbol klein" title="Öffnen" onclick={() => oeffnen(a)}><i class="fa-solid fa-arrow-up-right-from-square"></i></button>
      {#if schreiben}
        <button class="knopf ohne symbol klein" title={a.verknuepft ? "Verknüpfung lösen (Rückgängig möglich)" : "Entfernen (Rückgängig möglich)"}
                onclick={() => entfernen(karte.id, a.name)}><i class="fa-solid fa-xmark"></i></button>
      {/if}
    </div>
  {:else}
    <div class="schwach pw-detail-leer">{schreiben ? "Dateien hierher ziehen oder hochladen; sie liegen in der Kellerwolke im Ordner dieses Boards." : "Keine Anhänge."}</div>
  {/each}
  {#if darueber}<div class="pw-anhang-ablage"><i class="fa-solid fa-file-arrow-up"></i>Loslassen hängt die Dateien an</div>{/if}
</section>
