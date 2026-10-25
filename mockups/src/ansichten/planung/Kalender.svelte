<script lang="ts">
  // Kalender eines Boards (/board/<kürzel>/kalender) unter Kopf und Werkzeugleiste des Boards: Monat oder Woche mit
  // Karten nach Fälligkeit, Terminen, Serientagen, Abwesenheiten der Mitglieder (Modul Arbeitszeit, mit Recht) und
  // Feiertagen ihrer Bundesländer. Karte auf einen anderen Tag ziehen ändert die Fälligkeit (M-51), Klick öffnet sie
  // (M-122); daneben die Karten ohne Fälligkeit zum Hineinziehen. Erledigte zählen mit, durchgestrichen (M-121).
  import { HEUTE } from "../../beispiel/daten";
  import { datum } from "../../beispiel/format";
  import type { Board } from "../../modell";
  import { tageInhalt, type Zeigen } from "./kalender";
  import KalenderMonat from "./KalenderMonat.svelte";
  import KalenderWoche from "./KalenderWoche.svelte";
  import OhneDatum from "./OhneDatum.svelte";
  import { abwesenheitenSichtbar, faelligEntfernen, faelligSetzen, istErledigt, kartenDesBoards } from "./plan.svelte";
  import { kalenderwoche, monatsanfang, monatsname, montagVon, plusMonate, plusTage, tageVon } from "./tage";

  let { board, entwurf = "" }: { board: Board; entwurf?: string } = $props();

  let ansicht = $state<"monat" | "woche">("monat");
  let bezug = $state(HEUTE);
  $effect(() => { ansicht = entwurf === "woche" ? "woche" : "monat"; bezug = HEUTE; });
  let zeigen = $state<Zeigen>({ karten: true, termine: true, serien: true, abwesenheiten: true });
  let gezogen = $state<string | null>(null);

  const karten = $derived(kartenDesBoards(board.id));
  const ohneFaelligkeit = $derived(karten.filter((k) => !k.faellig && !istErledigt(board, k)));
  const erster = $derived(ansicht === "monat" ? montagVon(monatsanfang(bezug)) : montagVon(bezug));
  const letzter = $derived(ansicht === "monat" ? plusTage(montagVon(plusTage(plusMonate(bezug, 1), -1)), 6) : plusTage(erster, 6));
  const tage = $derived(tageVon(erster, letzter));
  const inhalt = $derived(tageInhalt(board, tage, karten, zeigen));
  const titel = $derived(ansicht === "monat" ? monatsname(bezug)
    : `Woche ${kalenderwoche(erster)}: ${datum(erster)} bis ${datum(plusTage(erster, 6))}${plusTage(erster, 6).slice(0, 4)}`);
  const ARTEN = $derived([
    ["karten", "Karten", "fa-note-sticky", true],
    ["termine", "Termine", "fa-handshake", board.module.serien],
    ["serien", "Serien", "fa-repeat", board.module.serien],
    ["abwesenheiten", "Abwesenheiten", "fa-umbrella-beach", abwesenheitenSichtbar(board)],
  ] as const);

  function blaettern(n: number): void {
    bezug = ansicht === "monat" ? plusMonate(bezug, n) : plusTage(bezug, 7 * n);
  }
  function ablegen(id: string, tag: string): void {
    const k = karten.find((x) => x.id === id);
    if (k) faelligSetzen(k, tag);
    gezogen = null;
  }
  function entfernen(id: string): void {
    const k = karten.find((x) => x.id === id);
    if (k) faelligEntfernen(k);
  }
</script>

<div class="pw-planung-raum pw-kalender">
  <div class="pw-planung-haupt">
    <div class="pw-planung-steuer">
      <button class="knopf symbol klein" title={ansicht === "monat" ? "Voriger Monat" : "Vorige Woche"} onclick={() => blaettern(-1)}><i class="fa-solid fa-chevron-left"></i></button>
      <button class="knopf klein" onclick={() => (bezug = HEUTE)}>Heute</button>
      <button class="knopf symbol klein" title={ansicht === "monat" ? "Nächster Monat" : "Nächste Woche"} onclick={() => blaettern(1)}><i class="fa-solid fa-chevron-right"></i></button>
      <h2>{titel}</h2>
      <span class="pw-umschalter" role="group" aria-label="Zeitraum">
        <button class:an={ansicht === "monat"} onclick={() => (ansicht = "monat")}><i class="fa-solid fa-calendar-days"></i>Monat</button>
        <button class:an={ansicht === "woche"} onclick={() => (ansicht = "woche")}><i class="fa-solid fa-calendar-week"></i>Woche</button>
      </span>
      <div class="rechts">
        {#each ARTEN.filter((a) => a[3]) as [id, name, symbol] (id)}
          <button class="chip pw-kalender-zeigen" class:aus={!zeigen[id]} onclick={() => (zeigen[id] = !zeigen[id])} aria-pressed={zeigen[id]}
                  title="{name} {zeigen[id] ? 'ausblenden' : 'zeigen'}"><i class="fa-regular {zeigen[id] ? 'fa-square-check' : 'fa-square'}"></i>
            <i class="fa-solid {symbol} art"></i>{name}</button>
        {/each}
      </div>
    </div>
    {#if ansicht === "monat"}
      <KalenderMonat {board} {tage} {inhalt} monat={bezug.slice(0, 7)} bind:gezogen {ablegen}
                     zuTag={(t) => { ansicht = "woche"; bezug = t; }} />
    {:else}
      <KalenderWoche {board} {tage} {inhalt} bind:gezogen {ablegen} />
    {/if}
  </div>
  <OhneDatum {board} karten={ohneFaelligkeit} titel="Ohne Fälligkeit" bind:gezogen ablegen={entfernen}
             erklaerung="Auf einen Tag ziehen setzt die Fälligkeit; eine Karte hierher ziehen entfernt sie." />
</div>
