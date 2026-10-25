<script lang="ts">
  // Leiste neben Kalender und Zeitachse: Karten des Boards ohne Datum, zum Hineinziehen auf einen Tag. Wer eine Karte
  // darauf ablegt, entfernt ihr Datum (nur wo die Ansicht das anbietet). Einklappbar wie eine Spalte; in schmalen
  // Fenstern beginnt sie eingeklappt.
  import { onMount } from "svelte";
  import Person from "../../board/Person.svelte";
  import type { Board, Karte } from "../../modell";
  import { darf as darfIm } from "../../beispiel/abfragen";
  import { farbeDerSpalte, kartenPfad } from "./lesen";

  let { board, karten, titel, erklaerung, gezogen = $bindable(null), ablegen, gesperrt = false }: {
    board: Board;
    karten: Karte[];
    titel: string;
    erklaerung: string;
    /** Kennung der Karte, die gerade gezogen wird (geteilt mit der Ansicht) */
    gezogen?: string | null;
    /** Ablegen auf der Leiste: Datum entfernen */
    ablegen?: (id: string) => void;
    /** Ziehen gesperrt (Suche oder Filter aktiv) */
    gesperrt?: boolean;
  } = $props();
  const ziehbar = $derived(darfIm(board, "karten.bearbeiten") && !gesperrt);

  let eingeklappt = $state(false);
  let ziel = $state(false);
  // mit schmaler Seitenleiste (unter 1240 Pixeln, wie der Leitstand) beginnt die Leiste eingeklappt
  onMount(() => { if (innerWidth < 1240) eingeklappt = true; });

  function ziehenBeginnt(e: DragEvent, k: Karte): void {
    e.dataTransfer?.setData("text/plain", k.id);
    if (e.dataTransfer) e.dataTransfer.effectAllowed = "move";
    gezogen = k.id;
  }
  function ueber(e: DragEvent): void {
    if (!ablegen || !gezogen || !ziehbar || karten.some((k) => k.id === gezogen)) return;
    e.preventDefault();
    ziel = true;
  }
  function fallen(e: DragEvent): void {
    e.preventDefault();
    const id = e.dataTransfer?.getData("text/plain") || gezogen;
    ziel = false;
    gezogen = null;
    if (id && ablegen) ablegen(id);
  }
</script>

<aside class="pw-planung-leiste" class:eingeklappt class:ziel aria-label={titel}
       ondragover={ueber} ondragleave={() => (ziel = false)} ondrop={fallen}>
  {#if eingeklappt}
    <div class="leistenkopf">
      <button class="knopf ohne symbol klein" title="Aufklappen: {titel}" onclick={() => (eingeklappt = false)}><i class="fa-solid fa-angles-left"></i></button>
      <span class="zaehler">{karten.length}</span>
      <span class="senkrecht">{titel}</span>
    </div>
  {:else}
    <div class="leistenkopf">
      <i class="fa-solid fa-inbox schwach"></i><b>{titel}</b><span class="zaehler">{karten.length}</span>
      <button class="knopf ohne symbol klein" title="Einklappen" onclick={() => (eingeklappt = true)}><i class="fa-solid fa-angles-right"></i></button>
    </div>
    <div class="erklaerung">{erklaerung}</div>
    <div class="liste">
      {#each karten as k (k.id)}
        <a class="pw-planung-mini" class:gezogen={gezogen === k.id} href={kartenPfad(board, k)} draggable={ziehbar} data-farbe={farbeDerSpalte(board, k)}
           title="{k.schluessel} {k.titel}{ziehbar ? ': auf einen Tag ziehen' : ''}" ondragstart={(e) => ziehenBeginnt(e, k)} ondragend={() => (gezogen = null)}>
          <span class="oben"><span class="pw-farbpunkt"></span><span class="pw-schluessel">{k.schluessel}</span>
            <span class="rechts pw-personen">{#each k.zustaendig.slice(0, 2) as p (p)}<Person id={p} />{/each}</span></span>
          <span class="titel">{k.titel}</span>
        </a>
      {:else}
        <div class="leer"><i class="fa-regular fa-calendar-check"></i><p>Alle Karten haben ein Datum.</p></div>
      {/each}
    </div>
  {/if}
</aside>
