<script lang="ts">
  // Schale der Pinnwand aus den Bausteinen des Leitstands: Kopf, Seitenleiste, Hauptbereich, Fußleiste. Die Seite rollt
  // nie; jede Ansicht bringt ihren festen Kopf und ihr eigenes Rollfeld mit.
  import type { Snippet } from "svelte";
  import Fuss from "./Fuss.svelte";
  import Kopf from "./Kopf.svelte";
  import Seite from "./Seite.svelte";

  let { aktiv, children }: { aktiv: string; children: Snippet } = $props();
</script>

<div class="schale pw-schale">
  <header class="kopf"><Kopf /></header>
  <nav class="seite" aria-label="Bereiche und Boards"><Seite {aktiv} /></nav>
  <main class="haupt rahmen">{@render children()}</main>
  <footer class="fuss"><Fuss /></footer>
</div>
