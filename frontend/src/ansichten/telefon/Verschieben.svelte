<script lang="ts">
  // Verschieben nach: Auswahl der Zielspalte als Blatt von unten. Ein Tippen auf eine offene Spalte verschiebt (derselbe
  // Weg wie das Ziehen im Board: ans Ende, Gruppe zieht mit, Alter beginnt neu); über der Grenze nur eine Warnung.
  // Erledigen ist folgenreich und geht nur per Halten: der eigene Timer hält dabei an und bucht. Darunter die anderen
  // Boards (etwa vom Ideenboard aufs Arbeitsboard): ein Board öffnet seine offenen Spalten, ein Tippen zieht die Karte
  // um, und das Detail folgt ihr an den neuen Pfad.
  import { kartenNummer, timerVon, umzugsziele } from "../../daten/abfragen";
  import { umziehen, verschieben } from "../../daten/anwendung/karten.svelte";
  import { ICH } from "../../daten/ich";
  import { board, gruppenmitglieder, kartenDerSpalte, stand } from "../../daten/stand.svelte";
  import type { Board, Karte, Spalte } from "../../modell";
  import { boardPfad, gehe } from "../../weg.svelte";
  import HaltKnopf from "./HaltKnopf.svelte";

  let { karte: k, schliessen }: { karte: Karte; schliessen: () => void } = $props();

  const b = $derived(board(k.board));
  const mit = $derived(gruppenmitglieder(k).filter((m) => m.board === k.board));
  const ziele = $derived(umzugsziele(k));
  /** gewähltes anderes Board; leer: die Spalten des eigenen */
  let fremd = $state<Board | null>(null);
  let unterwegs = $state(false);
  const zahl = (s: Spalte): number => kartenDerSpalte(s.id).length;
  const wirdUeber = (s: Spalte): boolean => s.grenze !== undefined && zahl(s) + 1 > s.grenze;

  function nach(s: Spalte): void {
    verschieben(k.id, s.id);
    schliessen();
  }

  async function umziehenNach(ziel: Board, s: Spalte): Promise<void> {
    if (unterwegs) return;
    unterwegs = true;
    const neu = await umziehen(k.id, ziel.id, s.id);
    unterwegs = false;
    const nb = neu && stand.boards.find((x) => x.id === neu.board);
    if (!neu || !nb) return;
    schliessen();
    gehe(boardPfad(nb.kuerzel, kartenNummer(neu)));
  }
</script>

<button class="pw-tel-schleier" aria-label="Auswahl schließen" onclick={schliessen}></button>
<section class="pw-tel-blatt" aria-label="Verschieben nach">
  <div class="kopfzeile">
    {#if fremd}
      <button class="knopf ohne symbol" title="Zurück zu den Spalten von {b.name}" aria-label="Zurück" onclick={() => (fremd = null)}><i class="fa-solid fa-chevron-left"></i></button>
    {/if}
    <h2>{fremd ? `Nach ${fremd.name}` : "Verschieben nach"}</h2>
    <button class="knopf ohne symbol" title="Schließen" aria-label="Schließen" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </div>
  <p class="karte-zeile"><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</p>
  {#if fremd}
    <p class="hinweis"><i class="fa-solid fa-arrow-right-arrow-left"></i><span>Dort bekommt sie die nächste Nummer und die Kartenart
      des Boards; Labels und Felder mit gleichem Namen bleiben, Inhalt und Zeit ziehen mit.</span></p>
    <div class="pw-tel-ziele">
      {#each fremd.spalten.filter((s) => !s.erledigt) as s (s.id)}
        <button class="pw-tel-ziel" data-farbe={s.farbe} disabled={unterwegs} onclick={() => umziehenNach(fremd!, s)}>
          <span class="pw-farbpunkt"></span><span class="text"><span class="name">{s.name}</span></span>
          <span class="zaehler">{zahl(s)}{s.grenze !== undefined ? `/${s.grenze}` : ""}</span>
          <i class="fa-solid fa-chevron-right"></i>
        </button>
      {/each}
    </div>
  {:else}
    {#if mit.length}
      <p class="hinweis"><i class="fa-solid fa-link"></i><span>Verknüpft: {mit.map((m) => m.schluessel).join(", ")} {mit.length === 1 ? "zieht" : "ziehen"} mit.</span></p>
    {/if}
    <div class="pw-tel-ziele">
      {#each b.spalten as s (s.id)}
        {#if s.id === k.spalte}
          <div class="pw-tel-ziel jetzt" data-farbe={s.farbe}>
            <span class="pw-farbpunkt"></span><span class="name">{s.name}</span><span class="zustand">Jetzt hier</span>
          </div>
        {:else if s.erledigt}
          <div class="pw-tel-ziel erledigen" data-farbe={s.farbe}>
            <HaltKnopf beschriftung="{k.schluessel} erledigen" aktion={() => nach(s)} />
            <span class="text"><span class="name">{s.name}</span>
              <span class="erklaerung">Ring halten zum Erledigen{timerVon(ICH)?.karte === k.id ? "; dein Timer endet und bucht" : ""}</span></span>
          </div>
        {:else}
          <button class="pw-tel-ziel" data-farbe={s.farbe} onclick={() => nach(s)}>
            <span class="pw-farbpunkt"></span>
            <span class="text"><span class="name">{s.name}</span>
              {#if wirdUeber(s)}<span class="erklaerung warnung"><i class="fa-solid fa-triangle-exclamation"></i>Danach über der Grenze ({zahl(s) + 1}/{s.grenze})</span>{/if}</span>
            <span class="zaehler">{zahl(s)}{s.grenze !== undefined ? `/${s.grenze}` : ""}</span>
            <i class="fa-solid fa-chevron-right"></i>
          </button>
        {/if}
      {/each}
    </div>
    {#if ziele.length}
      <div class="etikett">In ein anderes Board</div>
      <div class="pw-tel-ziele">
        {#each ziele as z (z.id)}
          <button class="pw-tel-ziel" data-farbe={z.farbe} onclick={() => (fremd = z)}>
            <span class="pw-farbpunkt"></span><span class="text"><span class="name">{z.name}</span>
              <span class="erklaerung">{z.kuerzel}, {z.kartenart === "idee" ? "neue Karten sind Ideen" : "neue Karten sind Arbeit"}</span></span>
            <i class="fa-solid fa-chevron-right"></i>
          </button>
        {/each}
      </div>
    {/if}
  {/if}
</section>
