<script lang="ts" generics="T">
  // Kasten eines Vorschlags der KI (Modul KI an der Karte), gleich für Zusammenfassung, Checkliste, Labels und Karten
  // aus Text: Kopfzeile, solange die Leitstelle rechnet ein Hinweis mit Abbrechen, wenn es nicht ging der Grund mit
  // "Noch einmal", sonst der Inhalt und die Knöpfe der Stelle. Übernommen wird nur über diese Knöpfe; Verwerfen schließt.
  import type { Snippet } from "svelte";
  import type { Vorschlagslauf } from "../daten/anwendung/ki.svelte";

  let { titel, lauf, nochmal, children, knoepfe }: {
    titel: string;
    lauf: Vorschlagslauf<T>;
    /** dieselbe Frage noch einmal stellen */
    nochmal: () => void;
    /** der Vorschlag (nur, wenn einer da ist) */
    children: Snippet<[T]>;
    /** Knöpfe zum Übernehmen vor "Verwerfen" */
    knoepfe?: Snippet<[T]>;
  } = $props();
</script>

<div class="pw-vorschlag" role="region" aria-label={titel} aria-busy={lauf.laeuft}>
  <div class="kopf-zeile"><i class="fa-solid fa-wand-magic-sparkles"></i>{titel}</div>
  {#if lauf.laeuft}
    <div class="pw-vorschlag-text pw-vorschlag-warten"><i class="fa-solid fa-spinner fa-spin-pulse"></i>Die Leitstelle rechnet; das kann einen Moment dauern.</div>
    <div class="pw-vorschlag-knoepfe"><button class="knopf ohne klein" onclick={() => lauf.schliessen()}>Abbrechen</button></div>
  {:else if lauf.grund}
    <div class="pw-vorschlag-text">{lauf.grund}</div>
    <div class="pw-vorschlag-knoepfe">
      <button class="knopf klein" onclick={nochmal}><i class="fa-solid fa-rotate-right"></i>Noch einmal</button>
      <button class="knopf ohne klein" onclick={() => lauf.schliessen()}>Schließen</button>
    </div>
  {:else if lauf.wert !== null}
    {@render children(lauf.wert)}
    <div class="pw-vorschlag-knoepfe">
      {@render knoepfe?.(lauf.wert)}
      <button class="knopf ohne klein" onclick={() => lauf.schliessen()}>Verwerfen</button>
    </div>
  {/if}
</div>
