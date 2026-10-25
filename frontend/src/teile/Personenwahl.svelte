<script lang="ts">
  // Person per Name finden: Textfeld mit Vorschlägen (ab zwei Buchstaben, höchstens sechs), keine lange Auswahlliste.
  // Die Kandidaten gibt der Aufrufer: Mitglieder eines Boards (zuweisen) oder Konten der Kellerwolke (einladen). Wer
  // schon in der Pinnwand ist, erscheint mit Kürzel und Farbe, wer noch kein Board hat, mit Name und Kennung.
  import Person from "../board/Person.svelte";
  import type { KellerwolkePerson, Kennung } from "../modell";

  let { kandidaten, ausser = [], waehlen, text = $bindable(""), platzhalter = "Name einer Person mit Kellerwolke-Konto", schwebend = false }: {
    kandidaten: KellerwolkePerson[];
    /** Vorschläge schweben über dem Inhalt darunter (in Leisten), statt ihn zu schieben */
    schwebend?: boolean;
    /** Konten, die schon dabei sind */
    ausser?: Kennung[];
    waehlen: (p: KellerwolkePerson) => void;
    text?: string;
    platzhalter?: string;
  } = $props();

  const suche = $derived(text.trim().toLowerCase());
  const treffer = $derived(suche.length < 2 ? [] : kandidaten.filter((p) => !(p.konto && ausser.includes(p.konto)))
    .filter((p) => p.kennung.startsWith(suche) || p.name.toLowerCase().split(" ").some((w) => w.startsWith(suche))).slice(0, 6));

  function nehmen(p: KellerwolkePerson): void {
    waehlen(p);
    text = "";
  }
</script>

<div class="pw-personenwahl" class:schwebend>
  <label class="suche"><i class="fa-solid fa-user-plus"></i>
    <input bind:value={text} placeholder={platzhalter} aria-label="Person suchen" autocomplete="off"
           onkeydown={(e) => { if (e.key === "Enter" && treffer.length) nehmen(treffer[0]); if (e.key === "Escape") text = ""; }} /></label>
  {#if suche.length >= 2}
    <div class="pw-personenwahl-vorschlaege" role="listbox" aria-label="Vorschläge">
      {#each treffer as p (p.kennung)}
        <button type="button" role="option" aria-selected="false" onclick={() => nehmen(p)}>
          {#if p.konto}<Person id={p.konto} />{:else}<span class="pw-personenwahl-neu"><i class="fa-solid fa-user"></i></span>{/if}
          <span class="wer"><b>{p.name}</b><span class="pw-schluessel">{p.kennung}</span></span>
          <span class="woher">{p.konto ? "in der Pinnwand" : "Kellerwolke, noch ohne Board"}</span>
        </button>
      {:else}
        <div class="leer-zeile">Niemand passt zu "{text.trim()}".</div>
      {/each}
    </div>
  {/if}
</div>
