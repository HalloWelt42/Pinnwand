<script lang="ts">
  // Dein Timer oben in Heute: Karte, Board, Zeit, Schätzung. Anhalten bucht die Sitzung und lässt den Timer auf der
  // Karte (fortsetzen geht später), Stoppen bucht und beendet ihn; ein Timer je Person.
  import { kartenNummer, sitzungSek, zeitDerKarte } from "../../daten/abfragen";
  import { anhalten, fortsetzen, stoppen } from "../../daten/anwendung/timer.svelte";
  import { dauer, uhrzeit } from "../../daten/format";
  import type { Board, Karte, Timer } from "../../modell";
  import { boardPfad } from "../../weg.svelte";
  import BoardMarke from "./BoardMarke.svelte";

  let { timer, karte, board, gesperrt = false }: { timer: Timer; karte: Karte; board: Board; gesperrt?: boolean } = $props();
  const zeit = $derived(zeitDerKarte(karte.id));
  const anteil = $derived(karte.schaetzungMin ? zeit / 60 / karte.schaetzungMin : 0);
</script>

<div class="pw-uebersicht-laeuft" class:angehalten={!timer.seit}>
  <i class="fa-solid {timer.seit ? 'fa-circle-play' : 'fa-circle-pause'} symbol"></i>
  <div class="was">
    <span class="seit">{timer.seit ? `Läuft seit ${uhrzeit(timer.seit)}` : "Angehalten, die Sitzungen sind gebucht"}</span>
    <a class="titel" href={boardPfad(board.kuerzel, kartenNummer(karte))}><span class="pw-schluessel">{karte.schluessel}</span> {karte.titel}</a>
  </div>
  <BoardMarke {board} />
  {#if karte.schaetzungMin}
    <span class="schaetzung" class:ueber={anteil > 1} title="Gebucht gegen die Schätzung der Karte">
      <span class="pw-fortschritt zeit" class:ueber={anteil > 1}><span style="width: {Math.min(100, anteil * 100)}%"></span></span>
      {Math.round(anteil * 100)} % von {dauer(karte.schaetzungMin * 60)}{anteil > 1 ? ", überschritten" : ""}
    </span>
  {/if}
  <span class="zeit">{dauer(zeit, true)}</span>
  <span class="knoepfe">
    {#if timer.seit}
      <button class="knopf haupt" disabled={gesperrt} title="Anhalten: die Sitzung wird gebucht, fortsetzen geht später" onclick={anhalten}>
        <i class="fa-solid fa-pause"></i>Anhalten</button>
    {:else}
      <button class="knopf haupt" disabled={gesperrt} onclick={fortsetzen}><i class="fa-solid fa-play"></i>Fortsetzen</button>
    {/if}
    <button class="knopf" disabled={gesperrt} title="Stoppen und buchen{timer.seit ? ` (${dauer(sitzungSek(timer))})` : ''}" onclick={stoppen}>
      <i class="fa-solid fa-stop"></i>Stoppen</button>
  </span>
</div>
