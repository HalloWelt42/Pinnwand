<script lang="ts">
  // Papierkorb der App: gelöschte Boards mit allem, was daran hing (Karten, Spalten, Serien, Termine, Ordner).
  // Wiederherstellen bringt das Board an seine alte Stelle; endgültig entfernen fragt vorher in der Fläche, die gebuchte
  // Zeit seiner Karten bleibt. Karten und Spalten liegen im Papierkorb ihres Boards.
  import { untrack } from "svelte";
  import { boardsImPapierkorb } from "../../../daten/abfragen";
  import { boardInPapierkorb } from "../../../daten/anwendung/papierkorb.svelte";
  import { meldungSchliessen } from "../../../daten/anwendung/meldung.svelte";
  import { entfernen, wiederherstellen } from "../../../daten/anwendung/papierkorb.svelte";
  import { ICH } from "../../../daten/ich";
  import { wann } from "../../../daten/format";
  import { konto, stand } from "../../../daten/stand.svelte";
  import type { Geloescht } from "../../../modell";
  import { hatRecht } from "../../../regeln/board";

  let { entwurf = "" }: { entwurf?: string } = $props();

  // vorgeführt: das Board Ideen liegt im Papierkorb (einmal je Entwurf, über den Anwendungsfall)
  $effect(() => {
    const e = entwurf;
    untrack(() => {
      if (e === "board") { boardInPapierkorb("b-ideen"); meldungSchliessen(); }
    });
  });

  const liste = $derived(boardsImPapierkorb());
  let frage = $state("");

  function darfEntfernen(e: Geloescht): boolean {
    return !!e.inhalt && hatRecht(e.inhalt.board, "papierkorb.leeren", ICH, stand.moduleDa);
  }
</script>

<div class="rollfeld">
  <div class="pw-verwaltung-flaeche">
    <section class="bereich">
      <h2 class="etikett">Gelöschte Boards</h2>
      {#each liste as e (e.id)}
        {@const b = e.inhalt!.board}
        <div class="pw-verwaltung-geloescht">
          <span class="pw-farbpunkt" data-farbe={b.farbe}></span>
          <div class="wer"><b>{b.name}</b>
            <span class="klein leise">Kürzel <span class="pw-schluessel">{b.kuerzel}</span> · {e.karten.length} {e.karten.length === 1 ? "Karte" : "Karten"},
              {e.inhalt!.serien.length} {e.inhalt!.serien.length === 1 ? "Serie" : "Serien"} · gelöscht von {konto(e.von).name}, {wann(e.am)}</span></div>
          <span class="rechts">
            <button class="knopf" onclick={() => wiederherstellen(e.id)}><i class="fa-solid fa-rotate-left"></i>Wiederherstellen</button>
            {#if darfEntfernen(e)}
              <button class="knopf ohne gefahr" onclick={() => (frage = e.id)}><i class="fa-solid fa-trash-can"></i>Endgültig entfernen</button>
            {/if}
          </span>
        </div>
        {#if frage === e.id}
          <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
            <div><b>{b.name} endgültig entfernen?</b> Das Board mit {e.karten.length} {e.karten.length === 1 ? "Karte" : "Karten"}, seinen Serien
              und Terminen ist danach weg und lässt sich nicht zurückholen. Die gebuchte Zeit seiner Karten bleibt in den Zeitkonten.</div>
            <span class="rechts"><button class="knopf klein" onclick={() => (frage = "")}>Behalten</button>
              <button class="knopf haupt gefahr klein" onclick={() => { entfernen([e.id]); frage = ""; }}>Endgültig entfernen</button></span>
          </div>
        {/if}
      {:else}
        <p class="leise">Der Papierkorb ist leer. Ein gelöschtes Board liegt hier mit allem, was daran hing, bis du es wiederherstellst
          oder endgültig entfernst.</p>
      {/each}
    </section>
  </div>
</div>
