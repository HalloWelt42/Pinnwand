<script lang="ts">
  // Schale der Telefonansicht, eigener Aufbau statt verkleinerter Rechnerschale: oben ein schmaler Kopf (Zurück, Titel,
  // Hinweise mit Zahl), darunter auf Wunsch eine feste Leiste der Ansicht (Spalten eines Boards), der Inhalt mit eigenem
  // Rollfeld, dann fest unten Knöpfe der Ansicht, die eine Meldung mit Rückgängig (teile/Meldung), die Laufleiste des Timers
  // und die Fußleiste mit vier Reitern. Die sicheren Ränder halten oben die Statusleiste und unten die Wischleiste frei.
  import type { Snippet } from "svelte";
  import { timerVon, ungelesen, zeitDerKarte } from "../../beispiel/abfragen";
  import { anhalten, fortsetzen } from "../../beispiel/anwendung/timer.svelte";
  import { ICH } from "../../beispiel/daten";
  import { dauer } from "../../beispiel/format";
  import { karte as holeKarte } from "../../beispiel/stand.svelte";
  import Meldung from "../../teile/Meldung.svelte";
  import { telPfad } from "./weg";

  type Reiter = "heute" | "boards" | "zeit" | "erfassen";
  let { titel, unter = "", reiter, zurueck = "", karte = "", glocke = true, leiste, unten, blatt, children }: {
    titel: string;
    unter?: string;
    /** aktiver Reiter der Fußleiste; ohne: keiner (Hinweise) */
    reiter?: Reiter;
    /** Pfad hinter dem Zurück-Pfeil */
    zurueck?: string;
    /** Karte im Detail: ihr Timer steht dort, die Laufleiste entfällt für sie */
    karte?: string;
    /** Hinweise im Kopf (nicht auf der Seite Hinweise selbst) */
    glocke?: boolean;
    /** feste Leiste unter dem Kopf */
    leiste?: Snippet;
    /** feste Knöpfe der Ansicht über der Fußleiste */
    unten?: Snippet;
    /** Blatt über allem (Auswahl von unten) */
    blatt?: Snippet;
    children: Snippet;
  } = $props();

  const REITER: [Reiter, string, string, string][] = [
    ["heute", "Heute", "fa-sun", "/heute"],
    ["boards", "Boards", "fa-table-columns", "/boards"],
    ["zeit", "Zeit", "fa-stopwatch", "/zeiten"],
    ["erfassen", "Erfassen", "fa-circle-plus", "/erfassen"],
  ];
  const neu = $derived(ungelesen());
  /** dein Timer (läuft oder angehalten) und seine Karte; die Laufleiste fehlt auf Zeit und auf der Karte selbst */
  const timer = $derived(timerVon(ICH));
  const timerKarte = $derived(timer ? holeKarte(timer.karte) : undefined);
  const leisteZeigen = $derived(reiter !== "zeit" && timer !== undefined && timer.karte !== karte);
</script>

<div class="pw-tel">
  <header class="pw-tel-kopf" class:mit-zurueck={!!zurueck}>
    {#if zurueck}
      <a class="pw-tel-knopf" href={zurueck} title="Zurück" aria-label="Zurück"><i class="fa-solid fa-chevron-left"></i></a>
    {/if}
    <div class="titel">
      <h1>{titel}</h1>
      {#if unter}<span class="unter">{unter}</span>{/if}
    </div>
    {#if glocke}
      <a class="pw-tel-knopf pw-tel-glocke" href={telPfad("/hinweise")} title="Hinweise: zugewiesen, fällig, erwähnt, Termine"
         aria-label="Hinweise, {neu} neu"><i class="fa-solid fa-bell"></i>
        {#if neu}<span class="zaehler pille gefahr">{neu}</span>{/if}</a>
    {/if}
  </header>

  {#if leiste}<div class="pw-tel-leiste">{@render leiste()}</div>{/if}

  <main class="pw-tel-inhalt">{@render children()}</main>

  {#if unten}<div class="pw-tel-unten">{@render unten()}</div>{/if}

  <Meldung ort="telefon" />

  {#if leisteZeigen && timer && timerKarte}
    <div class="pw-tel-laufleiste" class:pausiert={!timer.seit}>
      <a class="was" href={telPfad("/zeiten")} title="Dein Timer: zur Zeit">
        <span class="stand">
          {#if timer.seit}
            <span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft</span>
          {:else}
            <span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
          {/if}
          <span class="zahl" class:laufzeit={!!timer.seit}>{dauer(zeitDerKarte(timerKarte.id), true)}</span></span>
        <span class="karte-titel"><span class="pw-schluessel">{timerKarte.schluessel}</span> {timerKarte.titel}</span>
      </a>
      {#if timer.seit}
        <button class="knopf symbol" title="Anhalten: die Sitzung wird gebucht" aria-label="Timer anhalten" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
      {:else}
        <button class="knopf symbol" title="Fortsetzen" aria-label="Timer fortsetzen" onclick={fortsetzen}><i class="fa-solid fa-play"></i></button>
      {/if}
    </div>
  {/if}

  <nav class="pw-tel-fuss" aria-label="Bereiche">
    {#each REITER as [id, name, symbol, pfad] (id)}
      <a href={telPfad(pfad)} class:aktiv={reiter === id} aria-current={reiter === id ? "page" : undefined}>
        <span class="symbol"><i class="fa-solid {symbol}"></i></span>{name}</a>
    {/each}
  </nav>

  {#if blatt}{@render blatt()}{/if}
</div>
