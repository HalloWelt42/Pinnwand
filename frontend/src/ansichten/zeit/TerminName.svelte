<script lang="ts">
  // Verweis auf einen Termin in den Zeit-Ansichten, wie KartenName für Karten: Farbe des Boards, das Wort Termin, Titel
  // mit Verweis zu Serien und Termine (solange das Board das Modul an hat). Ein Termin, der nicht im Stand ist (Board
  // verlassen), heißt nur "Termin", ohne Verweis; seine bestätigte Zeit bleibt deine.
  import { datum } from "../../daten/format";
  import { stand } from "../../daten/stand.svelte";
  import { modulAn } from "../../regeln/board";

  let { id, zeilen = 1 }: { id: string; zeilen?: 1 | 2 } = $props();
  const t = $derived(stand.termine.find((x) => x.id === id));
  const b = $derived(t ? stand.boards.find((x) => x.id === t.board) : undefined);
  const verweis = $derived(!!b && modulAn(b, "serien", stand.moduleDa));
</script>

<span class="pw-zeit-karte" class:zwei={zeilen === 2}
      title={t ? `Termin ${t.titel}, ${datum(t.datum, true)} ${t.von} bis ${t.bis}${b ? `, Board ${b.name}` : ""}` : "Termin, den du nicht mehr siehst"}>
  {#if b}<span class="pw-farbpunkt" data-farbe={b.farbe}></span>{/if}
  <span class="pw-schluessel"><i class="fa-solid fa-handshake"></i> Termin</span>
  {#if t && verweis}<a class="titel" href="/serien">{t.titel}</a>{:else}<span class="titel">{t?.titel ?? "nicht mehr sichtbar"}</span>{/if}
</span>
