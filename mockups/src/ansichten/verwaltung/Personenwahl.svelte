<script lang="ts">
  // Person per Name finden: Textfeld mit Vorschlägen aus den Konten der Kellerwolke (ab zwei Buchstaben, höchstens
  // sechs), keine lange Auswahlliste. Wer schon in der Pinnwand ist, erscheint mit Kürzel und Farbe; wer noch kein Board
  // hat, mit Name und Kennung (Kürzel und Farbe bekommt er mit der Einladung).
  import { KONTEN } from "../../beispiel/daten";
  import Person from "../../board/Person.svelte";
  import type { Kennung } from "../../modell";
  import { KELLERWOLKE_NEU, KENNUNGEN, type Vorschlag } from "./daten";

  let { ausser = [], waehlen, text = $bindable(""), platzhalter = "Name einer Person mit Kellerwolke-Konto" }: {
    /** Konten, die schon dabei sind */
    ausser?: Kennung[];
    waehlen: (p: Vorschlag) => void;
    text?: string;
    platzhalter?: string;
  } = $props();

  const ALLE: Vorschlag[] = [
    ...KONTEN.map((k) => ({ kennung: KENNUNGEN[k.id], name: k.name, konto: k.id })),
    ...KELLERWOLKE_NEU,
  ];
  const suche = $derived(text.trim().toLowerCase());
  const treffer = $derived(suche.length < 2 ? [] : ALLE.filter((p) => !(p.konto && ausser.includes(p.konto)))
    .filter((p) => p.kennung.startsWith(suche) || p.name.toLowerCase().split(" ").some((w) => w.startsWith(suche))).slice(0, 6));

  function nehmen(p: Vorschlag): void {
    waehlen(p);
    text = "";
  }
</script>

<div class="pw-verwaltung-personenwahl">
  <label class="suche"><i class="fa-solid fa-user-plus"></i>
    <input bind:value={text} placeholder={platzhalter} aria-label="Person suchen" autocomplete="off"
           onkeydown={(e) => { if (e.key === "Enter" && treffer.length) nehmen(treffer[0]); if (e.key === "Escape") text = ""; }} /></label>
  {#if suche.length >= 2}
    <div class="pw-verwaltung-vorschlaege" role="listbox" aria-label="Vorschläge">
      {#each treffer as p (p.kennung)}
        <button type="button" role="option" aria-selected="false" onclick={() => nehmen(p)}>
          {#if p.konto}<Person id={p.konto} />{:else}<span class="pw-verwaltung-neuperson"><i class="fa-solid fa-user"></i></span>{/if}
          <span class="wer"><b>{p.name}</b><span class="pw-schluessel">{p.kennung}</span></span>
          <span class="woher">{p.konto ? "in der Pinnwand" : "Kellerwolke, noch ohne Board"}</span>
        </button>
      {:else}
        <div class="leer-zeile">Kein Konto der Kellerwolke passt zu "{text.trim()}".</div>
      {/each}
    </div>
  {/if}
</div>
