<script lang="ts">
  // Eine Karte, die der Pfad nennt, die aber nicht im Zustand liegt (archiviert, in ein anderes Board gezogen): einzeln
  // vom Server holen (M-09). Liegt sie danach im Zustand, zeigt der Weg ihr Detail von selbst; ist sie umgezogen, folgt
  // die Ansicht ihr an den neuen Pfad; gibt es sie nicht, geht es mit Meldung zum Board.
  import { untrack } from "svelte";
  import { kartenNummer } from "../../daten/abfragen";
  import { melden } from "../../daten/anwendung/meldung.svelte";
  import { karteHolen, stand } from "../../daten/stand.svelte";
  import { boardPfad, gehe } from "../../weg.svelte";
  import { telPfad } from "./weg";

  let { boardId, schluessel }: { boardId: string; schluessel: string } = $props();

  $effect(() => {
    const brett = boardId, s = schluessel;
    void untrack(async () => {
      const k = await karteHolen(s);
      const neu = k && k.board !== brett ? stand.boards.find((b) => b.id === k.board) : undefined;
      if (k && neu) {
        gehe(telPfad(boardPfad(neu.kuerzel, kartenNummer(k))), true);
      } else if (!k) {
        melden(`Die Karte ${s} gibt es nicht (mehr)`);
        const b = stand.boards.find((x) => x.id === brett);
        gehe(telPfad(b ? boardPfad(b.kuerzel) : "/boards"), true);
      }
    });
  });
</script>

<p class="schwach"><i class="fa-solid fa-spinner fa-spin"></i> {schluessel} wird geladen</p>
