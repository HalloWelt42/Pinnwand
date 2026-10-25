<script lang="ts">
  // Kommentare und Verlauf der Karte (M-61, M-64). Kommentare in einfachem Markdown, Erwähnungen mit @ hervorgehoben (der
  // volle Name im Hinweis). Enter sendet, Umschalt und Enter macht eine neue Zeile; das Feld leert sich erst, wenn der
  // Kommentar gespeichert ist. Der Verlauf zeigt, was die Anwendungsfälle vermerkt haben, neueste zuerst.
  import { tick, untrack } from "svelte";
  import { darf } from "../beispiel/abfragen";
  import { kommentieren } from "../beispiel/anwendung/karten.svelte";
  import { ICH } from "../beispiel/daten";
  import { wann } from "../beispiel/format";
  import { konto } from "../beispiel/stand.svelte";
  import type { Board, Karte } from "../modell";
  import Person from "../board/Person.svelte";
  import { markdownHtml, type MarkdownOptionen } from "../teile/markdown";
  import { verwerfbar } from "../teile/verwerfen";
  import { inSicht } from "./sicht";

  let { karte, board, optionen, reiter: vorgabe = "kommentare" }: {
    karte: Karte; board: Board; optionen: MarkdownOptionen; reiter?: "kommentare" | "verlauf";
  } = $props();

  let reiter = $state<"kommentare" | "verlauf">("kommentare");
  let abschnitt = $state<HTMLElement>();
  // vorgeführter Reiter: gewählt und in Sicht
  $effect(() => {
    const r = vorgabe;
    untrack(async () => {
      reiter = r;
      if (r === "kommentare") return;
      await tick();
      inSicht(abschnitt, "anfang");
    });
  });
  let text = $state("");
  /** neueste zuerst; was im selben Augenblick geschah, in der Folge, in der es geschah, von hinten */
  const verlauf = $derived([...karte.verlauf].reverse().sort((a, b) => b.zeit.localeCompare(a.zeit)));

  function senden(): void {
    if (kommentieren(karte.id, text)) text = "";
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      senden();
    }
  }
</script>

<section class="pw-abschnitt" bind:this={abschnitt}>
  <div class="reiter pw-detail-reiter">
    <button class:aktiv={reiter === "kommentare"} onclick={() => (reiter = "kommentare")}><i class="fa-regular fa-comment"></i>Kommentare<span class="zaehler">{karte.kommentare.length}</span></button>
    <button class:aktiv={reiter === "verlauf"} onclick={() => (reiter = "verlauf")}><i class="fa-solid fa-clock-rotate-left"></i>Verlauf<span class="zaehler">{karte.verlauf.length}</span></button>
  </div>
  {#if reiter === "kommentare"}
    {#each karte.kommentare as c, i (i)}
      <div class="pw-kommentar"><Person id={c.von} />
        <div class="blase"><div class="kopf-zeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span></div>
          <div class="pw-md">{@html markdownHtml(c.text, optionen)}</div></div></div>
    {:else}
      <div class="schwach pw-detail-leer">Noch keine Kommentare.</div>
    {/each}
    {#if darf(board, "kommentieren")}
      <div class="pw-kommentar"><Person id={ICH} />
        <div class="pw-kommentar-neu">
          <textarea class="eingabe" rows="2" bind:value={text} use:verwerfbar onkeydown={taste} aria-label="Kommentar"
                    placeholder="Kommentar schreiben, @ erwähnt eine Person"
                    title="Enter sendet, Umschalt und Enter macht eine neue Zeile; Markdown wie **fett**, *kursiv* und - Liste"></textarea>
          <div><button class="knopf klein" disabled={!text.trim()} onclick={senden}><i class="fa-solid fa-paper-plane"></i>Senden</button></div>
        </div>
      </div>
    {/if}
  {:else}
    <div class="pw-verlauf">
      {#each verlauf as e, i (i)}
        <div class="pw-verlauf-zeile"><span class="zeit">{wann(e.zeit)}</span><span><b title={konto(e.von).name}>{konto(e.von).kuerzel}</b> {e.text}</span></div>
      {:else}
        <div class="schwach pw-detail-leer">Noch kein Verlauf.</div>
      {/each}
    </div>
  {/if}
</section>
