<script lang="ts">
  // Verknüpfte Aufgaben (M-73 bis M-77): die anderen Mitglieder der Gruppe als Verweise auf ihre Karte, Lösen, der
  // Schalter "Zeit teilen" und die Suche zum Verknüpfen. Gesucht wird in den offenen Arbeitskarten dieses Boards nach
  // Titel oder Schlüssel, ohne die bisherigen Mitglieder, höchstens 8 Treffer; Pfeile wählen, Enter oder Klick
  // verknüpft über verknuepfen (hat der Treffer schon eine Gruppe, tritt diese Karte bei).
  import { Hilfepunkt, Suchfeld } from "appkern-oberflaeche";
  import { kartenNummer, verknuepfTreffer } from "../daten/abfragen";
  import { gruppeLoesen, verknuepfen, zeitTeilen } from "../daten/anwendung/karten.svelte";
  import { board as boardVon, gruppenmitglieder, stand } from "../daten/stand.svelte";
  import type { Board, Karte } from "../modell";
  import { verwerfen } from "../teile/verwerfen";
  import { boardPfad } from "../weg.svelte";
  import { enter } from "../teile/taste";

  let { karte, board, schreiben }: { karte: Karte; board: Board; schreiben: boolean } = $props();

  const HOECHSTENS = 8;
  const gruppe = $derived(gruppenmitglieder(karte));
  const teilen = $derived(stand.gruppen.find((g) => g.id === karte.gruppe)?.zeitTeilen ?? false);
  let suche = $state("");
  let gewaehlt = $state(0);

  /** Treffer der Suche (eine Abfrage, in der App der Schnittstelle) */
  const treffer = $derived(verknuepfTreffer(karte, suche, HOECHSTENS));
  $effect(() => { void treffer; gewaehlt = 0; });

  function spalteVon(x: Karte): string {
    return board.spalten.find((s) => s.id === x.spalte)?.name ?? "";
  }

  /** verknüpfen; das Feld leert sich erst, wenn beide in einer Gruppe sind (getrennt bleibt die Suche stehen) */
  function nehmen(x: Karte): void {
    verknuepfen(karte.id, x.id);
    if (karte.gruppe && stand.karten.find((y) => y.id === x.id)?.gruppe === karte.gruppe) suche = "";
  }

  function taste(e: KeyboardEvent): void {
    if (!treffer.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); gewaehlt = (gewaehlt + 1) % treffer.length; }
    if (e.key === "ArrowUp") { e.preventDefault(); gewaehlt = (gewaehlt - 1 + treffer.length) % treffer.length; }
    if (enter(e)) { e.preventDefault(); nehmen(treffer[gewaehlt]); }
  }
</script>

<section class="pw-abschnitt">
  <div class="etikett">Verknüpfte Aufgaben<Hilfepunkt thema="kartendetail" abschnitt="verknuepft" /> {#if gruppe.length}<span class="zaehler">{gruppe.length + 1}</span>{/if}
    {#if gruppe.length && karte.gruppe}{@const g = karte.gruppe}<span class="rechts"><button class="knopf ohne klein" disabled={!schreiben}
      title="Die Gruppe zeigt ihre gemeinsame Zeit; gebucht wird je Karte" onclick={() => zeitTeilen(g, !teilen)}><span class="schalter" class:an={teilen}></span>Zeit teilen</button></span>{/if}
  </div>
  {#each gruppe as m (m.id)}
    {@const mb = boardVon(m.board)}
    <div class="pw-anhang">
      <i class="fa-solid fa-link pw-akzent"></i>
      <a class="name pw-detail-verweis" href={boardPfad(mb.kuerzel, kartenNummer(m))} title="{m.schluessel} öffnen">
        <span class="pw-schluessel">{m.schluessel}</span> {m.titel}</a>
      {#if m.board !== karte.board}<span class="meta">{mb.name}</span>{/if}
      {#if schreiben}<button class="knopf ohne klein" title="{m.schluessel} aus der Gruppe lösen" onclick={() => gruppeLoesen(m.id)}>Lösen</button>{/if}
    </div>
  {/each}
  {#if schreiben}
    <div class="pw-detail-suchfeld">
      <Suchfeld klasse="pw-detail-suche" symbol="fa-link" bind:wert={suche} {@attach verwerfen} onkeydown={taste} autocomplete="off"
                aria-label="Karte suchen und verknüpfen" placeholder="Karte suchen und verknüpfen (zieht mit, Zeit geteilt)" />
      {#if suche.trim()}
        <div class="pw-detail-treffer" role="listbox" aria-label="Treffer">
          {#each treffer as x, n (x.id)}
            <button type="button" role="option" aria-selected={n === gewaehlt} onclick={() => nehmen(x)} onmouseenter={() => (gewaehlt = n)}>
              <span class="pw-schluessel">{x.schluessel}</span><span class="titel">{x.titel}</span>
              <span class="woher">{spalteVon(x)}{x.gruppe ? ", schon in einer Gruppe" : ""}</span>
            </button>
          {:else}
            <div class="leer-zeile">Keine offene Arbeitskarte in diesem Board passt zu "{suche.trim()}".</div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</section>
