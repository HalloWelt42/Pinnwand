<script lang="ts">
  // Board einer Karte, eines Hinweises oder Termins außerhalb des Boards: Farbpunkt und Name.
  import type { Board } from "../../modell";

  let { board }: { board: Board } = $props();
</script>

<span class="pw-uebersicht-board" data-farbe={board.farbe}><span class="pw-farbpunkt"></span>{board.name}</span>
