<script lang="ts">
  // Ein Termin in Heute (Modul Serien und Termine): Zeit, Titel, Board, Ort, Teilnehmer, deine Zusage.
  import { zusagen } from "../../daten/anwendung/termine.svelte";
  import { ICH } from "../../daten/ich";
  import { datum } from "../../daten/format";
  import { board } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Termin } from "../../modell";
  import BoardMarke from "./BoardMarke.svelte";

  let { termin, mitTag = false, gesperrt = false }: { termin: Termin; mitTag?: boolean; gesperrt?: boolean } = $props();
  const zugesagt = $derived(termin.zugesagt.includes(ICH));
</script>

<div class="pw-uebersicht-termin">
  <div class="inhalt">
    <span class="wann">{#if mitTag}<span>{datum(termin.datum, true)}</span>{/if}<b>{termin.von}-{termin.bis}</b></span>
    <a class="titel" href="/serien" title="Zu Serien und Termine">{termin.titel}</a>
    <div class="angaben">
      <BoardMarke board={board(termin.board)} />
      {#if termin.ort}<span class="pw-angabe"><i class="fa-solid fa-location-dot"></i>{termin.ort}</span>{/if}
      <span class="pw-personen" title="Teilnehmer">{#each termin.teilnehmer as p (p)}<Person id={p} />{/each}</span>
    </div>
  </div>
  {#if zugesagt}
    <span class="zustand fertig"><i class="fa-solid fa-check"></i>zugesagt</span>
  {:else}
    <button class="knopf klein" disabled={gesperrt} onclick={() => zusagen(termin.id)}>Zusagen</button>
  {/if}
</div>
