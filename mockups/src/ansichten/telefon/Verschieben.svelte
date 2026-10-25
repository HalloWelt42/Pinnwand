<script lang="ts">
  // Verschieben nach: Auswahl der Zielspalte als Blatt von unten. Ein Tippen auf eine offene Spalte verschiebt (derselbe
  // Weg wie das Ziehen im Board: ans Ende, Gruppe zieht mit, Alter beginnt neu); über der Grenze nur eine Warnung.
  // Erledigen ist folgenreich und geht nur per Halten: der eigene Timer hält dabei an und bucht.
  import { timerVon } from "../../beispiel/abfragen";
  import { verschieben } from "../../beispiel/anwendung/karten.svelte";
  import { ICH } from "../../beispiel/daten";
  import { board, gruppenmitglieder, kartenDerSpalte } from "../../beispiel/stand.svelte";
  import type { Karte, Spalte } from "../../modell";
  import HaltKnopf from "./HaltKnopf.svelte";

  let { karte: k, schliessen }: { karte: Karte; schliessen: () => void } = $props();

  const b = $derived(board(k.board));
  const mit = $derived(gruppenmitglieder(k).filter((m) => m.board === k.board));
  const zahl = (s: Spalte): number => kartenDerSpalte(s.id).length;
  const wirdUeber = (s: Spalte): boolean => s.grenze !== undefined && zahl(s) + 1 > s.grenze;

  function nach(s: Spalte): void {
    verschieben(k.id, s.id);
    schliessen();
  }
</script>

<button class="pw-tel-schleier" aria-label="Auswahl schließen" onclick={schliessen}></button>
<section class="pw-tel-blatt" aria-label="Verschieben nach">
  <div class="kopfzeile">
    <h2>Verschieben nach</h2>
    <button class="knopf ohne symbol" title="Schließen" aria-label="Schließen" onclick={schliessen}><i class="fa-solid fa-xmark"></i></button>
  </div>
  <p class="karte-zeile"><span class="pw-schluessel">{k.schluessel}</span> {k.titel}</p>
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
</section>
