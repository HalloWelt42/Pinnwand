<script lang="ts">
  // Teilnehmer einer Serie oder eines Termins wählen: die gewählten als Chips mit Entfernen, dazu die gemeinsame
  // Personenwahl mit den Mitgliedern des Boards, die sich schon angemeldet haben. Erfasst das Board Zeit, nur wer Zeit
  // buchen darf (die Zeit wird vorgebucht und von jedem selbst bestätigt); wer das nicht darf (etwa als Leser), steht als
  // Hinweis darunter. Die Liste ist der Formularstand des Aufrufers, gespeichert wird über seinen Anwendungsfall.
  import { konto, mitKonto, stand } from "../../daten/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Board, KellerwolkePerson, Kennung } from "../../modell";
  import { hatRecht, modulAn } from "../../regeln/board";
  import Personenwahl from "../../teile/Personenwahl.svelte";

  let { board, konten = $bindable() }: { board: Board; konten: Kennung[] } = $props();

  const mitZeit = $derived(modulAn(board, "zeiterfassung", stand.moduleDa));
  const waehlbar = (k: Kennung): boolean => !mitZeit || hatRecht(board, "zeit.buchen", k, stand.moduleDa);
  const kandidaten = $derived(mitKonto(board).filter((m) => waehlbar(m.konto))
    .map((m): KellerwolkePerson => { const k = konto(m.konto); return { kennung: k.kellerwolke, name: k.name, konto: k.id }; }));
  const ohneRecht = $derived(mitKonto(board).filter((m) => !waehlbar(m.konto)).map((m) => konto(m.konto).name));
</script>

<div class="pw-planung-teilnehmer">
  {#if konten.length}
    <div class="gewaehlt">
      {#each konten as k (k)}
        <span class="chip"><Person id={k} />{konto(k).name}
          <button class="knopf ohne symbol klein" title="{konto(k).name} entfernen" onclick={() => (konten = konten.filter((x) => x !== k))}>
            <i class="fa-solid fa-xmark"></i></button></span>
      {/each}
    </div>
  {/if}
  <Personenwahl {kandidaten} ausser={konten} platzhalter="Mitglied des Boards suchen und hinzufügen"
                waehlen={(p) => { if (p.konto && !konten.includes(p.konto)) konten = [...konten, p.konto]; }} />
  {#if ohneRecht.length}<span class="schwach klein">{ohneRecht.join(", ")}: ohne Recht, Zeit zu buchen, nicht wählbar</span>{/if}
</div>
