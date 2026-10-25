<script lang="ts">
  // Dein laufender Timer oben in Heute: Karte, Board, Zeit, Schätzung; Anhalten bucht die Sitzung (ein Timer je Person).
  import { dauer, laufendSek, uhrzeit } from "../../beispiel/format";
  import type { Board, Karte } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import { timerAnhalten } from "./aktionen.svelte";
  import BoardMarke from "./BoardMarke.svelte";

  let { karte, board, gesperrt = false }: { karte: Karte; board: Board; gesperrt?: boolean } = $props();
  const zeit = $derived(karte.erfasstSek + (karte.laeuft ? laufendSek(karte.laeuft.seit) : 0));
  const anteil = $derived(karte.schaetzungMin ? zeit / 60 / karte.schaetzungMin : 0);
</script>

<div class="pw-uebersicht-laeuft">
  <i class="fa-solid fa-circle-play symbol"></i>
  <div class="was">
    <span class="seit">Läuft seit {uhrzeit(karte.laeuft?.seit ?? "")}</span>
    <a class="titel" href={boardPfad(board.kuerzel, karte.schluessel.split("-")[1])}><span class="pw-schluessel">{karte.schluessel}</span> {karte.titel}</a>
  </div>
  <BoardMarke {board} />
  {#if karte.schaetzungMin}
    <span class="schaetzung" class:ueber={anteil > 1} title="Erfasst gegen die Schätzung der Karte">
      <span class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></span>
      {Math.round(anteil * 100)} % von {dauer(karte.schaetzungMin * 60)}{anteil > 1 ? ", überschritten" : ""}
    </span>
  {/if}
  <span class="zeit">{dauer(zeit, true)}</span>
  <button class="knopf haupt" disabled={gesperrt} title="Anhalten und die Sitzung buchen" onclick={() => timerAnhalten(karte.id)}>
    <i class="fa-solid fa-pause"></i>Anhalten</button>
</div>
