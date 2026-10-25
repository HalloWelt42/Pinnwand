<script lang="ts">
  // Platzhalter: diese Ansicht eines Boards entsteht im Bereich ihres Moduls. Sie bekommt das Board und den Entwurf.
  import type { Board } from "../../modell";

  let { board, entwurf = "" }: { board: Board; entwurf?: string } = $props();
</script>

<div class="rollfeld"><div class="leer">{board.name}: Ansicht entsteht {entwurf}</div></div>
