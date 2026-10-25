<script lang="ts">
  // Papierkorb der App: gelöschte Boards mit allem, was daran hing (Spalten, Karten, Verknüpfungen, Ordner), soweit du
  // sie wiederherstellen darfst (Recht "Board verwalten" im gelöschten Board). Wiederherstellen bringt das Board zurück,
  // auch in die Ordner, in denen es lag; endgültig entfernen fragt vorher in der Fläche und gibt sein Kürzel frei.
  // Karten und Spalten liegen im Papierkorb ihres Boards.
  import { boardsImPapierkorb } from "../../../daten/abfragen";
  import { entfernen, rechtZumWiederherstellen, wiederherstellen } from "../../../daten/anwendung/papierkorb.svelte";
  import { ICH } from "../../../daten/ich";
  import { wann } from "../../../daten/format";
  import { konto, stand } from "../../../daten/stand.svelte";
  import type { Geloescht } from "../../../modell";
  import { hatRecht } from "../../../regeln/board";

  function darf(e: Geloescht, recht: string): boolean {
    return !!e.inhalt && hatRecht(e.inhalt.board, recht, ICH, stand.moduleDa);
  }

  const liste = $derived(boardsImPapierkorb().filter((e) => darf(e, rechtZumWiederherstellen(e))));
  let frage = $state("");
  const karten = (n: number) => `${n} ${n === 1 ? "Karte" : "Karten"}`;
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
            <span class="klein leise">Kürzel <span class="pw-schluessel">{b.kuerzel}</span> · {karten(e.karten.length)},
              {b.spalten.length} {b.spalten.length === 1 ? "Spalte" : "Spalten"} · gelöscht von {konto(e.von).name}, {wann(e.am)}</span></div>
          <span class="rechts">
            <button class="knopf" onclick={() => wiederherstellen(e.id)}><i class="fa-solid fa-rotate-left"></i>Wiederherstellen</button>
            {#if darf(e, "papierkorb.leeren")}
              <button class="knopf ohne gefahr" onclick={() => (frage = e.id)}><i class="fa-solid fa-trash-can"></i>Endgültig entfernen</button>
            {/if}
          </span>
        </div>
        {#if frage === e.id}
          <div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
            <div><b>{b.name} endgültig entfernen?</b> Das Board mit {karten(e.karten.length)} ist danach weg und lässt sich nicht
              zurückholen; sein Kürzel {b.kuerzel} wird wieder frei.</div>
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
