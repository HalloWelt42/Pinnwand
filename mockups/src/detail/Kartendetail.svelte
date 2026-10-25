<script lang="ts">
  // Kartendetail als Leiste rechts über dem Board (M-44, M-125): beim Öffnen liegt der Fokus im Detail; es schließt mit
  // X, Escape oder einem Klick daneben ins Board (ein Klick auf eine andere Karte öffnet diese). Steckt der Fokus in einem
  // Feld, gilt das erste Escape dem Feld (es verwirft dessen Eingabe), das zweite schließt das Detail. Ein Kartenwechsel
  // richtet den Inhalt neu ein (Suche, Reiter, Editoren leer); offene Editoren speichern dabei an ihrer Karte. Ebenso ein
  // neuer vorgeführter Zustand: er beginnt beim Ausgangsstand.
  import { untrack } from "svelte";
  import { karte as holeKarte } from "../beispiel/stand.svelte";
  import type { Board } from "../modell";
  import { verlassen } from "../teile/verwerfen";
  import { DETAIL_ENTWUERFE, type DetailZustand } from "./entwuerfe";
  import Karteninhalt from "./Karteninhalt.svelte";

  let { kartenId, board, voll = false, entwurf = "", schliessen }: {
    kartenId: string; board: Board; voll?: boolean;
    /** Entwurfszusatz des Weges (?entwurf=...), vom Board durchgereicht */
    entwurf?: string;
    schliessen: () => void;
  } = $props();

  const k = $derived(holeKarte(kartenId));
  /** vorgeführter Zustand des Details zum Entwurfszusatz */
  const vorgefuehrt = $derived<DetailZustand>(DETAIL_ENTWUERFE[entwurf] ?? {});
  let vollbild = $state(false);
  $effect(() => { vollbild = voll; });
  let flaeche = $state<HTMLElement>();

  // Fokus ins Detail beim Öffnen und bei jedem Kartenwechsel, außer er steckt schon darin (etwa in einem offenen Editor)
  $effect(() => {
    void kartenId;
    untrack(() => { if (flaeche && !flaeche.contains(document.activeElement)) flaeche.focus({ preventScroll: true }); });
  });

  const FELD = "input, textarea, select, [contenteditable]";

  function taste(e: KeyboardEvent): void {
    if (e.key !== "Escape" || e.defaultPrevented || !flaeche) return;
    const ziel = e.target instanceof HTMLElement ? e.target : null;
    if (ziel?.matches(FELD)) {
      // Felder außerhalb (etwa die Suche im Board) haben ihr eigenes Escape; im Detail verlässt das erste Escape das Feld
      if (flaeche.contains(ziel)) verlassen(ziel);
      return;
    }
    schliessen();
  }

  /** Klick daneben: im Raum des Boards, nicht im Detail und nicht auf etwas, das selbst etwas tut (Karte, Knopf, Feld) */
  function daneben(ziel: EventTarget | null): boolean {
    const raum = flaeche?.parentElement;
    if (!(ziel instanceof Element) || !raum || !flaeche) return false;
    return raum.contains(ziel) && !flaeche.contains(ziel) && !ziel.closest("a, button, input, select, textarea, label, [role='button'], [tabindex]");
  }

  // beginnt der Druck im Detail (etwa beim Markieren von Text) und endet daneben, bleibt es offen
  let druckDaneben = false;
</script>

<svelte:window onkeydown={taste} />
<svelte:document onpointerdown={(e) => (druckDaneben = daneben(e.target))}
                 onclick={(e) => { if (druckDaneben && daneben(e.target)) schliessen(); druckDaneben = false; }} />

<aside class="pw-detail" class:voll={vollbild} tabindex="-1" bind:this={flaeche} aria-label="Karte {k?.schluessel ?? ''}">
  {#key `${kartenId} ${entwurf}`}
    <!-- fehlt die Karte (Anlegen rückgängig gemacht, in den Papierkorb gelegt), schließt das Board das Detail -->
    {#if k}<Karteninhalt karte={k} {board} {vorgefuehrt} konflikt={!!vorgefuehrt.konflikt} bind:vollbild {schliessen} />{/if}
  {/key}
</aside>
