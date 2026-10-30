<script lang="ts">
  // Kommentare und Verlauf der Karte (M-61, M-64). Kommentare in einfachem Markdown, Erwähnungen mit @ hervorgehoben (der
  // volle Name im Hinweis). Enter sendet, Umschalt und Enter macht eine neue Zeile; das Feld leert sich erst, wenn der
  // Kommentar gespeichert ist. Neueste zuerst (HELF-50: nach unten in die Vergangenheit): das Feld für einen neuen
  // Kommentar steht oben, darunter der jüngste. Der Verlauf zeigt, was die Anwendungsfälle vermerkt haben, ebenso.
  import { darf } from "../daten/abfragen";
  import { kommentieren } from "../daten/anwendung/karten.svelte";
  import { liest, vorlesen, vorlesenDa } from "../daten/anwendung/vorlesen.svelte";
  import { ICH } from "../daten/ich";
  import { wann } from "../daten/format";
  import { konto } from "../daten/stand.svelte";
  import type { Board, Karte } from "../modell";
  import Person from "../board/Person.svelte";
  import { markdownHtml, markdownText, type MarkdownOptionen } from "../teile/markdown";
  import { verwerfbar } from "../teile/verwerfen";
  import { enter } from "../teile/taste";

  let { karte, board, optionen }: { karte: Karte; board: Board; optionen: MarkdownOptionen } = $props();

  let reiter = $state<"kommentare" | "verlauf">("kommentare");
  let text = $state("");
  /** neueste zuerst; was im selben Augenblick geschah, in der Folge, in der es geschah, von hinten */
  const verlauf = $derived([...karte.verlauf].reverse().sort((a, b) => b.zeit.localeCompare(a.zeit)));
  /** Kommentare neueste zuerst, mit ihrer Stelle an der Karte (die Kennung des Vorlesens hängt daran) */
  const kommentare = $derived(karte.kommentare.map((c, i) => ({ c, i })).reverse());

  /** das Feld leert sich sofort; lehnt der Server ab, steht der Text wieder da */
  async function senden(): Promise<void> {
    const t = text;
    text = "";
    if (!(await kommentieren(karte.id, t)) && !text) text = t;
  }

  function taste(e: KeyboardEvent): void {
    if (enter(e) && !e.shiftKey) {
      e.preventDefault();
      void senden();
    }
  }
</script>

<section class="pw-abschnitt">
  <div class="reiter pw-detail-reiter">
    <button class:aktiv={reiter === "kommentare"} onclick={() => (reiter = "kommentare")}><i class="fa-regular fa-comment"></i>Kommentare<span class="zaehler">{karte.kommentare.length}</span></button>
    <button class:aktiv={reiter === "verlauf"} onclick={() => (reiter = "verlauf")}><i class="fa-solid fa-clock-rotate-left"></i>Verlauf<span class="zaehler">{karte.verlauf.length}</span></button>
  </div>
  {#if reiter === "kommentare"}
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
    {#each kommentare as { c, i } (i)}
      <div class="pw-kommentar"><Person id={c.von} />
        <div class="blase"><div class="kopf-zeile"><b>{konto(c.von).name}</b><span>{wann(c.zeit)}</span>
          {#if vorlesenDa(board)}
            {@const kennung = `kommentar-${karte.id}-${i}`}
            <button class="knopf ohne symbol klein pw-kommentar-vorlesen" title={liest(kennung) ? "Vorlesen anhalten" : "Kommentar vorlesen"}
                    aria-pressed={liest(kennung)} onclick={() => vorlesen(kennung, `${konto(c.von).name} schrieb: ${markdownText(c.text)}`, board.id)}>
              <i class="fa-solid {liest(kennung) ? 'fa-stop' : 'fa-volume-high'}"></i></button>
          {/if}</div>
          <div class="pw-md">{@html markdownHtml(c.text, optionen)}</div></div></div>
    {:else}
      <div class="schwach pw-detail-leer">Noch keine Kommentare.</div>
    {/each}
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
