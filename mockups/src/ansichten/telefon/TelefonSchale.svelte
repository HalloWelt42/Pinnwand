<script lang="ts">
  // Schale der Telefonansicht, eigener Aufbau statt verkleinerter Rechnerschale: oben ein schmaler Kopf (Zurück, Titel,
  // Hinweise mit Zahl), darunter auf Wunsch eine feste Leiste der Ansicht (Spalten eines Boards), der Inhalt mit eigenem
  // Rollfeld, dann fest unten Knöpfe der Ansicht, die letzte Meldung mit Rückgängig, die Laufleiste des eigenen Timers
  // und die Fußleiste mit vier Reitern. Die sicheren Ränder halten oben die Statusleiste und unten die Wischleiste frei.
  import type { Snippet } from "svelte";
  import { HINWEISE } from "../../beispiel/daten";
  import { dauer } from "../../beispiel/format";
  import { stand } from "../../beispiel/stand.svelte";
  import { anhalten, kartenzeit, laufende, meldungSchliessen, pausierte, starten, telefon } from "./aktionen.svelte";
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
  const ungelesen = $derived(HINWEISE.filter((h) => !h.gelesen && !telefon.gelesen.includes(h.id)).length);
  const lauf = $derived(laufende());
  const pause = $derived(pausierte());
  const uhr = $derived(lauf ?? pause);
  const leisteZeigen = $derived(reiter !== "zeit" && uhr !== undefined && uhr.id !== karte);

  // Meldungen verschwinden nach 6 Sekunden, Rückgängig gilt so lange (M-104)
  $effect(() => {
    if (!stand.meldung) return;
    const uhr = setTimeout(meldungSchliessen, 6000);
    return () => clearTimeout(uhr);
  });
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
         aria-label="Hinweise, {ungelesen} neu"><i class="fa-solid fa-bell"></i>
        {#if ungelesen}<span class="zaehler pille gefahr">{ungelesen}</span>{/if}</a>
    {/if}
  </header>

  {#if leiste}<div class="pw-tel-leiste">{@render leiste()}</div>{/if}

  <main class="pw-tel-inhalt">{@render children()}</main>

  {#if unten}<div class="pw-tel-unten">{@render unten()}</div>{/if}

  {#if stand.meldung}
    <div class="pw-tel-meldung" role="status">
      <i class="fa-solid fa-circle-info"></i><span>{stand.meldung}</span>
      {#if telefon.rueckgaengig}<button class="knopf ohne" onclick={() => telefon.rueckgaengig?.()}>Rückgängig</button>{/if}
      <button class="knopf ohne symbol" title="Schließen" aria-label="Meldung schließen" onclick={meldungSchliessen}><i class="fa-solid fa-xmark"></i></button>
    </div>
  {/if}

  {#if leisteZeigen && lauf}
    <div class="pw-tel-laufleiste">
      <a class="was" href={telPfad("/zeiten")} title="Dein Timer: zur Zeit">
        <span class="stand"><span class="zustand laeuft"><i class="fa-solid fa-circle-play"></i>Läuft</span>
          <span class="zahl laufzeit">{dauer(kartenzeit(lauf), true)}</span></span>
        <span class="karte-titel"><span class="pw-schluessel">{lauf.schluessel}</span> {lauf.titel}</span>
      </a>
      <button class="knopf symbol" title="Anhalten und buchen" aria-label="Timer anhalten" onclick={anhalten}><i class="fa-solid fa-pause"></i></button>
    </div>
  {:else if leisteZeigen && pause}
    <div class="pw-tel-laufleiste pausiert">
      <a class="was" href={telPfad("/zeiten")} title="Dein Timer: zur Zeit">
        <span class="stand"><span class="zustand pausiert"><i class="fa-solid fa-circle-pause"></i>Angehalten</span>
          <span class="zahl">{dauer(kartenzeit(pause), true)}</span></span>
        <span class="karte-titel"><span class="pw-schluessel">{pause.schluessel}</span> {pause.titel}</span>
      </a>
      <button class="knopf symbol" title="Fortsetzen" aria-label="Timer fortsetzen" onclick={() => starten(pause.id)}><i class="fa-solid fa-play"></i></button>
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
