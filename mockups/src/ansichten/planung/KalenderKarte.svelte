<script lang="ts">
  // Eine Karte im Kalender: Spaltenfarbe, Schlüssel, Titel; erledigt mit Haken und durchgestrichen, überfällig mit
  // Warnzeichen (Wort im Hinweis). Klick öffnet die Karte, Ziehen auf einen anderen Tag ändert die Fälligkeit.
  import { HEUTE } from "../../beispiel/daten";
  import type { Board, Karte } from "../../modell";
  import { hatRecht, istErledigt, kartenPfad } from "./plan.svelte";

  let { board, karte, ziehen }: { board: Board; karte: Karte; ziehen: (id: string | null) => void } = $props();

  const spalte = $derived(board.spalten.find((s) => s.id === karte.spalte));
  const erledigt = $derived(istErledigt(board, karte));
  const ueberfaellig = $derived(!erledigt && !!karte.faellig && karte.faellig < HEUTE);
  const darf = $derived(hatRecht(board, "karten.bearbeiten"));
  const hinweis = $derived(`${karte.schluessel} ${karte.titel} (${spalte?.name}${ueberfaellig ? ", überfällig" : ""}${erledigt ? ", erledigt" : ""})`
    + (darf ? ": auf einen anderen Tag ziehen ändert die Fälligkeit" : ""));

  function beginnen(e: DragEvent): void {
    e.dataTransfer?.setData("text/plain", karte.id);
    if (e.dataTransfer) e.dataTransfer.effectAllowed = "move";
    ziehen(karte.id);
  }
</script>

<a class="pw-kalender-eintrag ist-karte" class:erledigt class:ueberfaellig href={kartenPfad(board, karte)} draggable={darf} data-farbe={spalte?.farbe}
   title={hinweis} ondragstart={beginnen} ondragend={() => ziehen(null)}>
  {#if erledigt}<i class="fa-solid fa-check zeichen"></i>
  {:else if ueberfaellig}<i class="fa-solid fa-triangle-exclamation zeichen"></i>
  {:else}<span class="pw-farbpunkt"></span>{/if}
  <span class="schluessel">{karte.schluessel}</span><span class="titel">{karte.titel}</span>
</a>
