<script lang="ts">
  // Datum als Textfeld in deutscher Schreibweise (keine nativen Datumsfelder, die der Browsersprache folgen): liest
  // nachsichtig "3.11.", "03.11.26", "03112026" und zeigt darunter, was verstanden wurde. Gespeichert bleibt ISO.
  import { untrack } from "svelte";
  import { HEUTE } from "../../beispiel/daten";
  import { datumJahr } from "./anzeige";
  import { datumLesen } from "./regeln";

  let { tag, ontag, titel = "", breite = "" }: { tag: string; ontag: (tag: string) => void; titel?: string; breite?: string } = $props();

  function zeigen(t: string): string {
    return t ? `${t.slice(8, 10)}.${t.slice(5, 7)}.${t.slice(0, 4)}` : "";
  }
  let text = $state("");
  let fokus = $state(false);
  $effect(() => { const t = tag; untrack(() => { if (!fokus) text = zeigen(t); }); });
  const gelesen = $derived(datumLesen(text, Number(HEUTE.slice(0, 4))));
  const falsch = $derived(text.trim() !== "" && !gelesen);

  function uebernehmen(): void {
    if (gelesen && gelesen !== tag) ontag(gelesen);
    if (gelesen) text = zeigen(gelesen);
  }
</script>

<span class="pw-zeit-datum" style={breite ? `width: ${breite}` : ""}>
  <input class="eingabe zahl" class:falsch bind:value={text} placeholder="TT.MM.JJJJ" title={titel || "Datum wie 16.11.2026, 16.11. oder 16112026"}
         aria-invalid={falsch} onfocus={() => (fokus = true)} onblur={() => { fokus = false; uebernehmen(); }}
         onkeydown={(e) => { if (e.key === "Enter") (e.currentTarget as HTMLInputElement).blur(); if (e.key === "Escape") { text = zeigen(tag); (e.currentTarget as HTMLInputElement).blur(); } }} />
  <small class:falsch>{falsch ? "Datum nicht lesbar" : gelesen ? datumJahr(gelesen, true) : ""}</small>
</span>
