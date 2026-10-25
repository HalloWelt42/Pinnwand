<script lang="ts">
  // Schnelleingabe am Fuß einer Spalte: Titel tippen, Enter legt an und das Feld bleibt offen für die nächste Karte;
  // zuständig bist du; Escape schließt und verwirft. Arbeit oder Idee wählt man nur, wenn das Board Zeiterfassung hat,
  // sonst gilt die Kartenart des Boards. Das Feld leert sich sofort; lehnt der Server ab, steht der Titel wieder da.
  // Mit dem Modul KI an der Karte macht "Aus Text" aus einem Text (Notiz, Nachricht, Liste) einen Vorschlag mehrerer
  // Karten; angehakt und mit dem Titel, wie er im Feld steht, entstehen sie in einer Änderung (ein Rückgängig).
  import { kartenAusTextHolen, kiDa, Vorschlagslauf } from "../daten/anwendung/ki.svelte";
  import { anlegen, mehrereAnlegen } from "../daten/anwendung/karten.svelte";
  import { ICH } from "../daten/ich";
  import { laufnummer } from "../daten/stand.svelte";
  import Vorschlag from "../detail/Vorschlag.svelte";
  import type { Board, Kartenentwurf, Spalte } from "../modell";
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

  // ═══ Karten aus Text (Modul KI an der Karte) ════════════════════════════════════════════════════════════════════════

  let ausText = $state(false);
  let text = $state("");
  const vorschlag = new Vorschlagslauf<{ karten: Kartenentwurf[] }>();
  /** die vorgeschlagenen Karten, wie sie angelegt würden: angehakt und mit Titel aus dem Feld */
  let entwuerfe = $state<(Kartenentwurf & { an: boolean })[]>([]);
  const anzulegen = $derived(entwuerfe.filter((e) => e.an && e.titel.trim()));
  $effect(() => () => vorschlag.schliessen());

  async function vorschlagen(): Promise<void> {
    if (!text.trim()) return;
    if (await vorschlag.holen(kartenAusTextHolen(board.id, text))) entwuerfe = (vorschlag.wert?.karten ?? []).map((k) => ({ ...k, an: true }));
  }

  async function alleAnlegen(): Promise<void> {
    const karten = anzulegen.map((e) => ({ titel: e.titel.trim(), beschreibung: e.beschreibung, checkliste: e.checkliste }));
    if (karten.length && await mehrereAnlegen(board.id, spalte.id, art, karten)) einzeln();
  }

  /** zurück zur Eingabe einzelner Titel; der Text und der Vorschlag gehen */
  function einzeln(): void {
    vorschlag.schliessen();
    text = "";
    entwuerfe = [];
    ausText = false;
  }

  function textTaste(e: KeyboardEvent): void {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void vorschlagen(); }
    if (e.key === "Escape") einzeln();
  }

  function kurz(e: Kartenentwurf): string {
    const punkte = e.checkliste.length ? `${e.checkliste.length} ${e.checkliste.length === 1 ? "Punkt" : "Punkte"}` : "";
    return [e.beschreibung, punkte].filter(Boolean).join(" · ");
  }
</script>

<div class="pw-schnell">
  {#if ausText}
    <!-- svelte-ignore a11y_autofocus -->
    <textarea class="eingabe pw-schnell-text" autofocus placeholder="Text, aus dem Karten werden: Notiz, Nachricht oder Liste"
              aria-label="Text, aus dem Karten werden" bind:value={text} onkeydown={textTaste} disabled={vorschlag.laeuft}></textarea>
  {:else}
    <!-- svelte-ignore a11y_autofocus -->
    <textarea class="eingabe" autofocus placeholder="Titel der neuen Karte, Enter legt an" bind:value={titel} onkeydown={taste}></textarea>
  {/if}
  <div class="zeile-knoepfe">
    {#if board.module.zeiterfassung}
      <span class="pw-umschalter" title="Arbeit hat Zeiterfassung, eine Idee nicht">
        <button class:an={art === "arbeit"} onclick={() => (gewaehlt = "arbeit")}><i class="fa-solid fa-briefcase"></i>Arbeit</button>
        <button class="idee" class:an={art === "idee"} onclick={() => (gewaehlt = "idee")}><i class="fa-solid fa-lightbulb"></i>Idee</button>
      </span>
    {/if}
    <span title="Zuständig: du"><Person id={ICH} /></span>
  </div>
  {#if ausText && vorschlag.offen}
    <Vorschlag titel="Vorschlag: Karten aus dem Text" lauf={vorschlag} nochmal={vorschlagen}>
      {#snippet children()}
        {#each entwuerfe as e, i (i)}
          <div class="pw-entwurf" class:aus={!e.an}>
            <input type="checkbox" bind:checked={e.an} aria-label="Karte {e.titel} anlegen" />
            <div class="inhalt">
              <input class="eingabe" bind:value={e.titel} disabled={!e.an} aria-label="Titel der Karte" />
              {#if kurz(e)}<span class="hinweistext">{kurz(e)}</span>{/if}
            </div>
          </div>
        {:else}
          <div class="pw-vorschlag-text">In diesem Text steht nichts, woraus eine Karte würde.</div>
        {/each}
      {/snippet}
      {#snippet knoepfe()}
        {#if entwuerfe.length}<button class="knopf haupt klein" disabled={!anzulegen.length} onclick={alleAnlegen}>Anlegen</button>{/if}
      {/snippet}
    </Vorschlag>
  {/if}
  <div class="zeile-knoepfe">
    {#if ausText}
      {#if !vorschlag.offen}
        <button class="knopf haupt klein" disabled={!text.trim()} onclick={() => void vorschlagen()}><i class="fa-solid fa-wand-magic-sparkles"></i>Vorschlagen</button>
      {/if}
      <button class="knopf ohne klein" onclick={einzeln}>Einzeln anlegen</button>
      <span class="hinweistext">{#if anzulegen.length && vorschlag.wert}{anzulegen.length} {anzulegen.length === 1 ? "Karte" : "Karten"} in {spalte.name}{:else}Strg und Enter schlägt vor · in {spalte.name}{/if}</span>
    {:else}
      <button class="knopf haupt klein" disabled={!titel.trim()} onclick={() => void anlegenUndWeiter()}>Anlegen</button>
      <button class="knopf ohne klein" onclick={schliessen}>Schließen</button>
      {#if kiDa(board)}
        <button class="knopf ohne klein" title="Aus einem Text mehrere Karten machen (Vorschlag über die Leitstelle)" onclick={() => (ausText = true)}><i class="fa-solid fa-wand-magic-sparkles"></i>Aus Text</button>
      {/if}
      <span class="hinweistext">Enter legt an, das Feld bleibt offen · {board.kuerzel}-{laufnummer(board.id) + 1} in {spalte.name}</span>
    {/if}
  </div>
</div>
