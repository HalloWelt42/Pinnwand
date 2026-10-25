<script lang="ts">
  // In ein anderes Board (etwa vom Ideenboard aufs Arbeitsboard): erst das Board, dann die Spalte; ein Klick auf die
  // Spalte zieht die Karte um, und das Detail folgt ihr an den neuen Pfad. Nummer, Kartenart, Labels und Felder gleicht
  // der Server an; angeboten werden nur Boards, in denen du Karten anlegen darfst.
  import { kartenNummer, umzugsziele } from "../daten/abfragen";
  import { umziehen } from "../daten/anwendung/karten.svelte";
  import { stand } from "../daten/stand.svelte";
  import type { Karte, Spalte } from "../modell";
  import { boardPfad, gehe } from "../weg.svelte";

  let { karte: k, schliessen }: { karte: Karte; schliessen: () => void } = $props();

  const ziele = $derived(umzugsziele(k));
  let gewaehlt = $state<string | null>(null);
  const ziel = $derived(ziele.find((b) => b.id === gewaehlt));
  let unterwegs = $state(false);

  async function nach(s: Spalte): Promise<void> {
    if (!ziel || unterwegs) return;
    unterwegs = true;
    const neu = await umziehen(k.id, ziel.id, s.id);
    unterwegs = false;
    const b = neu && stand.boards.find((x) => x.id === neu.board);
    if (neu && b) gehe(boardPfad(b.kuerzel, kartenNummer(neu)));
  }
</script>

<section class="pw-umzug" aria-label="In ein anderes Board">
  <div class="kopfzeile">
    <b><i class="fa-solid fa-arrow-right-arrow-left"></i>In ein anderes Board</b>
    <button class="knopf ohne symbol klein" title="Schließen" aria-label="Schließen" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </div>
  <p class="schwach">{k.schluessel} bekommt dort die nächste Nummer und die Kartenart des Boards; Labels und Felder mit
    gleichem Namen bleiben, Inhalt, Kommentare und Zeit ziehen mit.</p>
  <div class="wahl">
    {#each ziele as b (b.id)}
      <button class="knopf klein" class:haupt={b.id === gewaehlt} data-farbe={b.farbe} onclick={() => (gewaehlt = b.id)}>
        <span class="pw-farbpunkt"></span>{b.name}</button>
    {/each}
  </div>
  {#if ziel}
    <div class="etikett">Spalte in {ziel.name}</div>
    <div class="wahl">
      {#each ziel.spalten as s (s.id)}
        <button class="knopf klein" data-farbe={s.farbe} disabled={unterwegs} title="{k.schluessel} nach {ziel.name}, {s.name}"
                onclick={() => nach(s)}><span class="pw-farbpunkt"></span>{s.name}</button>
      {/each}
    </div>
  {/if}
</section>
