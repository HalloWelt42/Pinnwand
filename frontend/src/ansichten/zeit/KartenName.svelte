<script lang="ts">
  // Verweis auf eine Karte in den Zeit-Ansichten: Farbe des Boards, Schlüssel, Titel, Verweis ins Kartendetail. Der Name
  // kommt aus kartenName() und steht damit auch für Karten im Papierkorb, entfernte (ohne Verweis, mit Zustand) und
  // solche außerhalb des Stands: archiviert in einem deiner Boards (Verweis über ihren Pfad, der jede Karte öffnet, M-09)
  // oder in einem Board, das du verlassen hast (ohne Verweis).
  import { kartenName, kartenNummer } from "../../daten/abfragen";
  import { karte, stand } from "../../daten/stand.svelte";
  import { boardPfad } from "../../weg.svelte";

  let { id, zeilen = 1 }: { id: string; zeilen?: 1 | 2 } = $props();
  const name = $derived(kartenName(id));
  const k = $derived(karte(id));
  const b = $derived(stand.boards.find((x) => x.id === name.board));
  /** nicht im Stand, aber in einem deiner Boards: dann liegt sie im Archiv */
  const archiviert = $derived(!k && name.zustand === "da" && !!b);
  const erledigt = $derived(archiviert || !!(k && b?.spalten.find((s) => s.id === k.spalte)?.erledigt));
  const pfad = $derived(name.zustand === "da" && b ? boardPfad(b.kuerzel, kartenNummer(name)) : "");
  const ZUSTAND = { da: "", papierkorb: "im Papierkorb", entfernt: "entfernt" };
</script>

<span class="pw-zeit-karte" class:zwei={zeilen === 2}
      title="{name.schluessel} {name.titel}{b ? `, Board ${b.name}` : ''}{erledigt ? ', erledigt' : ''}{archiviert ? ', im Archiv' : ''}{ZUSTAND[name.zustand] ? `, ${ZUSTAND[name.zustand]}` : ''}">
  {#if b}<span class="pw-farbpunkt" data-farbe={b.farbe}></span>{/if}
  <span class="pw-schluessel">{name.schluessel}</span>
  {#if pfad}<a class="titel" href={pfad}>{name.titel}</a>{:else}<span class="titel">{name.titel}</span>{/if}
  {#if erledigt}<i class="fa-solid fa-check erledigt" title="Erledigt"></i>{/if}
  {#if ZUSTAND[name.zustand]}<span class="zustand">{ZUSTAND[name.zustand]}</span>{/if}
</span>
