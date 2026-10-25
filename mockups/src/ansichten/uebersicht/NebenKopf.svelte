<script lang="ts">
  // Kopf der Nebenseiten eines Boards (Archiv, Papierkorb): Titel, das Board mit Kürzel und Zurück zum Board; gebaut wie
  // der Kopf des Boards.
  import type { Snippet } from "svelte";
  import type { Board } from "../../modell";
  import { boardPfad } from "../../weg.svelte";

  let { board, titel, symbol, angabe, erklaerung, aktionen }: {
    board: Board; titel: string; symbol: string;
    /** kurze Angabe hinter dem Board (Zahl, Grenze) */
    angabe: string;
    erklaerung: string;
    aktionen?: Snippet;
  } = $props();
</script>

<div class="seitenkopf pw-boardkopf">
  <h1><i class="fa-solid {symbol} pw-uebersicht-kopfsymbol"></i>{titel}</h1>
  <div class="rechts">
    {@render aktionen?.()}
    <a class="knopf klein" href={boardPfad(board.kuerzel)}><i class="fa-solid fa-arrow-left"></i>Zurück zum Board</a>
  </div>
  <div class="pfad"><span class="pw-farbpunkt" data-farbe={board.farbe}></span>
    <a class="pw-uebersicht-boardverweis" href={boardPfad(board.kuerzel)}>{board.name}</a>
    <span class="pw-schluessel">Kürzel {board.kuerzel}</span><span>· {angabe}</span></div>
  <div class="unterzeile">{erklaerung}</div>
</div>
