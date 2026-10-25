<script lang="ts">
  // Verweis auf eine Karte in den Zeit-Ansichten: Farbe des Boards, Schlüssel, Titel, Verweis ins Kartendetail. Der Name
  // kommt aus kartenName() und steht damit auch für Karten im Papierkorb oder entfernte (ohne Verweis, mit Zustand).
  import { kartenName, kartenNummer } from "../../beispiel/abfragen";
  import { board, karte } from "../../beispiel/stand.svelte";
  import { boardPfad } from "../../weg.svelte";

  let { id, zeilen = 1 }: { id: string; zeilen?: 1 | 2 } = $props();
  const name = $derived(kartenName(id));
  const k = $derived(karte(id));
  const b = $derived(k ? board(k.board) : undefined);
  const erledigt = $derived(!!(k && b?.spalten.find((s) => s.id === k.spalte)?.erledigt));
  const ZUSTAND = { da: "", papierkorb: "im Papierkorb", entfernt: "entfernt" };
</script>

<span class="pw-zeit-karte" class:zwei={zeilen === 2}
      title="{name.schluessel} {name.titel}{b ? `, Board ${b.name}` : ''}{erledigt ? ', erledigt' : ''}{ZUSTAND[name.zustand] ? `, ${ZUSTAND[name.zustand]}` : ''}">
  {#if b}<span class="pw-farbpunkt" data-farbe={b.farbe}></span>{/if}
  <span class="pw-schluessel">{name.schluessel}</span>
  {#if k && b}<a class="titel" href={boardPfad(b.kuerzel, kartenNummer(k))}>{name.titel}</a>{:else}<span class="titel">{name.titel}</span>{/if}
  {#if erledigt}<i class="fa-solid fa-check erledigt" title="Erledigt"></i>{/if}
  {#if ZUSTAND[name.zustand]}<span class="zustand">{ZUSTAND[name.zustand]}</span>{/if}
</span>
