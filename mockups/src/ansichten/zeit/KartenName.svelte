<script lang="ts">
  // Verweis auf eine Karte in Listen der Zeit-Ansichten: Farbe des Boards, Schlüssel, Titel; führt ins Kartendetail.
  import { board, karte as imBoard } from "../../beispiel/stand.svelte";
  import type { Karte } from "../../modell";
  import { boardPfad } from "../../weg.svelte";

  let { karte, zeilen = 1 }: { karte: Karte; zeilen?: 1 | 2 } = $props();
  const b = $derived(board(karte.board));
  const pfad = $derived(imBoard(karte.id) ? boardPfad(b.kuerzel, karte.schluessel.split("-")[1]) : "");
  const erledigt = $derived(!!b.spalten.find((s) => s.id === karte.spalte)?.erledigt);
</script>

<span class="pw-zeit-karte" class:zwei={zeilen === 2} title="{karte.schluessel} {karte.titel}, Board {b.name}{erledigt ? ', erledigt' : ''}">
  <span class="pw-farbpunkt" data-farbe={b.farbe}></span>
  <span class="pw-schluessel">{karte.schluessel}</span>
  {#if pfad}<a class="titel" href={pfad}>{karte.titel}</a>{:else}<span class="titel">{karte.titel}</span>{/if}
  {#if erledigt}<i class="fa-solid fa-check erledigt" title="Erledigt"></i>{/if}
</span>
