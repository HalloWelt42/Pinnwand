<script lang="ts">
  // Schnelleingabe am Fuß einer Spalte: Titel tippen, Enter legt an und das Feld bleibt offen für die nächste Karte;
  // zuständig bist du; Escape schließt und verwirft. Arbeit oder Idee wählt man nur, wenn das Board Zeiterfassung hat,
  // sonst gilt die Kartenart des Boards. Das Feld leert sich sofort; lehnt der Server ab, steht der Titel wieder da.
  import { anlegen } from "../daten/anwendung/karten.svelte";
  import { ICH } from "../daten/ich";
  import { laufnummer } from "../daten/stand.svelte";
  import type { Board, Spalte } from "../modell";
  import Person from "./Person.svelte";

  let { board, spalte, schliessen }: { board: Board; spalte: Spalte; schliessen: () => void } = $props();
  let titel = $state("");
  let gewaehlt = $state<"arbeit" | "idee" | null>(null);
  const art = $derived(board.module.zeiterfassung ? gewaehlt ?? board.kartenart : board.kartenart);

  async function anlegenUndWeiter(): Promise<void> {
    const t = titel;
    if (!t.trim()) return;
    titel = "";
    if (!(await anlegen(board.id, spalte.id, { titel: t, art })) && !titel) titel = t;
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void anlegenUndWeiter(); }
    if (e.key === "Escape") { titel = ""; schliessen(); }
  }
</script>

<div class="pw-schnell">
  <!-- svelte-ignore a11y_autofocus -->
  <textarea class="eingabe" autofocus placeholder="Titel der neuen Karte, Enter legt an" bind:value={titel} onkeydown={taste}></textarea>
  <div class="zeile-knoepfe">
    {#if board.module.zeiterfassung}
      <span class="pw-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht">
        <button class:an={art === "arbeit"} onclick={() => (gewaehlt = "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
        <button class="idee" class:an={art === "idee"} onclick={() => (gewaehlt = "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
      </span>
    {/if}
    <span title="Zuständig: du"><Person id={ICH} /></span>
  </div>
  <div class="zeile-knoepfe">
    <button class="knopf haupt klein" disabled={!titel.trim()} onclick={() => void anlegenUndWeiter()}>Anlegen</button>
    <button class="knopf ohne klein" onclick={schliessen}>Schließen</button>
    <span class="hinweistext">Enter legt an, das Feld bleibt offen · {board.kuerzel}-{laufnummer(board.id) + 1} in {spalte.name}</span>
  </div>
</div>
