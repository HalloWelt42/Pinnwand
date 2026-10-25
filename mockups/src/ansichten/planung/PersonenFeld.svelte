<script lang="ts">
  // Personen wählen als Textfeld mit Vorschlägen (keine lange Auswahlliste): gewählte als Chips mit Entfernen, darunter
  // beim Tippen die passenden Mitglieder des Boards. Wer nicht teilnehmen kann (etwa ohne Recht, Zeit zu buchen), steht
  // mit Grund da und ist nicht wählbar.
  import { konto } from "../../beispiel/stand.svelte";
  import Person from "../../board/Person.svelte";
  import type { Kennung } from "../../modell";

  let { konten = $bindable(), kandidaten, platzhalter = "Mitglied suchen und hinzufügen", vorschlagOffen = false }: {
    konten: Kennung[];
    kandidaten: { konto: Kennung; gesperrt?: string }[];
    platzhalter?: string;
    vorschlagOffen?: boolean;
  } = $props();

  let suche = $state("");
  let fokus = $state(false);
  const passend = $derived(kandidaten.filter((c) => !konten.includes(c.konto)
    && konto(c.konto).name.toLowerCase().includes(suche.trim().toLowerCase())));
  const zeigen = $derived((fokus || vorschlagOffen || suche !== "") && passend.length > 0);

  function waehlen(k: Kennung): void {
    konten = [...konten, k];
    suche = "";
  }
</script>

<div class="pw-planung-personen">
  {#if konten.length}
    <div class="gewaehlt">
      {#each konten as k (k)}
        <span class="chip"><Person id={k} />{konto(k).name}
          <button class="knopf ohne symbol klein" title="{konto(k).name} entfernen" onclick={() => (konten = konten.filter((x) => x !== k))}>
            <i class="fa-solid fa-xmark"></i></button></span>
      {/each}
    </div>
  {/if}
  <label class="suche"><i class="fa-solid fa-user-plus"></i>
    <input placeholder={platzhalter} bind:value={suche} onfocus={() => (fokus = true)} onblur={() => setTimeout(() => (fokus = false), 150)} /></label>
  {#if zeigen}
    <div class="vorschlaege" role="listbox" aria-label="Vorschläge">
      {#each passend as c (c.konto)}
        <button class="zeile" role="option" aria-selected="false" disabled={!!c.gesperrt} title={c.gesperrt ?? `${konto(c.konto).name} hinzufügen`}
                onclick={() => waehlen(c.konto)}>
          <Person id={c.konto} /><span class="name">{konto(c.konto).name}</span>
          {#if c.gesperrt}<span class="grund">{c.gesperrt}</span>{/if}
        </button>
      {/each}
    </div>
  {/if}
</div>
