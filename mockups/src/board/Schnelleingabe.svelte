<script lang="ts">
  // Schnelleingabe am Fuß einer Spalte: Titel tippen, Enter legt an und das Feld bleibt offen für die nächste Karte;
  // die zuständige Person ist vorbelegt (du, sonst die zuletzt gesetzte); Escape schließt und verwirft.
  import { ICH } from "../beispiel/daten";
  import type { Board, Spalte } from "../modell";
  import Person from "./Person.svelte";

  let { board, spalte, schliessen }: { board: Board; spalte: Spalte; schliessen: () => void } = $props();
</script>

<div class="pw-schnell">
  <!-- svelte-ignore a11y_autofocus -->
  <textarea class="eingabe" autofocus placeholder="Titel der neuen Karte, Enter legt an">Angebot Lochblechverkleidung</textarea>
  <div class="zeile-knoepfe">
    <span class="pw-umschalter"><button class="an"><i class="fa-solid fa-briefcase"></i>Arbeit</button><button><i class="fa-solid fa-lightbulb"></i>Idee</button></span>
    <Person id={ICH} />
    <button class="knopf ohne symbol klein" title="Fälligkeit"><i class="fa-regular fa-calendar"></i></button>
    <button class="knopf ohne symbol klein" title="Label"><i class="fa-solid fa-tag"></i></button>
    <button class="knopf ohne symbol klein" title="Per Sprache erfassen (Transkription)"><i class="fa-solid fa-microphone"></i></button>
  </div>
  <div class="zeile-knoepfe">
    <button class="knopf haupt klein">Anlegen</button>
    <button class="knopf ohne klein" onclick={schliessen}>Schließen</button>
    <span class="hinweistext">Enter legt an, das Feld bleibt offen · {board.kuerzel}-{board.laufnummer + 1} in {spalte.name}</span>
  </div>
</div>
