<script lang="ts" module>
  import { aufnahmeEinrichten, aufnehmen } from "appkern-oberflaeche";

  /** Im Tippen aufrufen: richtet die Aufnahme auf das Board ein (dorthin gehen die Stücke) und startet sie. */
  export function sprechenStarten(boardId: string): void {
    aufnahmeEinrichten({ app: "pinnwand", hoeren: `/boards/${encodeURIComponent(boardId)}/sprache`, name: "Sprache" });
    void aufnehmen();
  }
</script>

<script lang="ts">
  // Erfassen per Sprache mit der Aufnahme des Appkerns: Zeit und Pegel zeigen, dass das Mikrofon hört; die
  // Live-Mitschrift schneidet an Sprechpausen und schickt jedes Stück über die Pinnwand an die Transkription, der Text
  // wächst beim Sprechen (Nutzer: "Ja, stückweise live"). "Stopp und übernehmen" wartet auf das letzte Stück: der erste
  // Satz wird Titel, der ganze Text Beschreibung; die Aufnahme selbst wird verworfen. Verwerfen bricht ohne Text ab.
  // Gestartet wird im Tippen auf "Sprechen" (`sprechenStarten`), sonst hält Safari am iPhone den Ton an.
  import {
    aufnahme, aufnahmeAbbrechen, aufnahmeBeenden, aufnahmeFortsetzen, aufnahmeVerwerfen, gespeicherteAufnahmen, mitschriftAbwarten,
  } from "appkern-oberflaeche";
  import { onDestroy, onMount } from "svelte";
  import type { Kennung } from "../../modell";

  let { boardId, uebernehmen, verwerfen }: {
    /** das Board, in dem die Karte entsteht (dorthin gehen die Stücke der Mitschrift) */
    boardId: Kennung;
    uebernehmen: (text: string) => void;
    verwerfen: () => void;
  } = $props();

  /** so viele Balken zeigt der Pegel (die neuesten rechts) */
  const BALKEN = 28;

  let umsetzen = $state(false);
  let grund = $state("");
  const text = $derived(aufnahme.mitschrift.map((s) => s.text).join(" "));
  const sek = $derived(Math.floor(aufnahme.dauer_ms / 1000));
  const pegel = $derived(aufnahme.pegel.slice(-BALKEN));
  const fehler = $derived(grund || aufnahme.fehler);
  let feld = $state<HTMLElement>();
  // die neueste Zeile bleibt in Sicht
  $effect(() => {
    void text;
    if (feld) feld.scrollTop = feld.scrollHeight;
  });

  // Aufnahmen früherer Spracheingaben, die ein Absturz liegen ließ, braucht niemand mehr
  onMount(async () => {
    for (const a of await gespeicherteAufnahmen()) void aufnahmeVerwerfen(a.id);
  });
  onDestroy(() => {
    if (aufnahme.laeuft) void aufnahmeAbbrechen();
  });

  async function stopp(): Promise<void> {
    umsetzen = true;
    const datei = await aufnahmeBeenden("Sprache");
    await mitschriftAbwarten();
    if (datei) await aufnahmeVerwerfen(datei.info.id);
    umsetzen = false;
    const fertig = text.trim();
    if (fertig) uebernehmen(fertig);
    else grund = aufnahme.liveStand || "In der Aufnahme war nichts zu verstehen";
  }

  async function ende(): Promise<void> {
    if (aufnahme.laeuft) await aufnahmeAbbrechen();
    verwerfen();
  }

  /** im Tippen: eine neue Aufnahme */
  function nochmal(): void {
    grund = "";
    sprechenStarten(boardId);
  }
</script>


<section class="pw-tel-sprache" aria-label="Aufnahme">
  <div class="kopfzeile">
    {#if fehler}
      <span class="zustand"><i class="fa-solid fa-microphone-slash"></i>Geht nicht</span>
    {:else if umsetzen}
      <span class="zustand"><i class="fa-solid fa-spinner fa-spin-pulse"></i>Letztes Stück</span>
    {:else if aufnahme.laeuft}
      <span class="zustand laeuft"><i class="fa-solid fa-microphone"></i>Aufnahme läuft</span>
    {:else}
      <span class="zustand"><i class="fa-solid fa-microphone"></i>Mikrofon wird geöffnet</span>
    {/if}
    <span class="zahl dauer">{Math.floor(sek / 60)}:{String(sek % 60).padStart(2, "0")}</span>
  </div>
  <div class="pegel" aria-hidden="true">
    {#each pegel as p, i (i)}<span style="--h: {Math.max(0.04, p / 100)}"></span>{/each}
  </div>
  <div class="mitschrift" aria-live="polite" bind:this={feld}>
    {#if fehler}{fehler}
    {:else if text}{text}{#if aufnahme.liveStand}{" "}<span class="vorlaeufig">{aufnahme.liveStand}</span>{/if}
    {:else}<span class="vorlaeufig">{aufnahme.liveStand || "Sprich einfach los; der Text erscheint an jeder Sprechpause."}</span>{/if}
  </div>
  {#if aufnahme.signal === "angehalten" && aufnahme.laeuft}
    <button class="knopf" onclick={() => aufnahmeFortsetzen()}><i class="fa-solid fa-play"></i>Ton fortsetzen</button>
  {:else}
    <span class="quelle"><i class="fa-solid fa-wave-square"></i>{aufnahme.signal === "still" && aufnahme.laeuft
      ? "Vom Mikrofon kommt gerade nichts an."
      : "Die Transkription schreibt mit; der erste Satz wird Titel, alles Beschreibung."}</span>
  {/if}
  <div class="knoepfe">
    <button class="knopf ohne" onclick={ende}><i class="fa-solid fa-xmark"></i>Verwerfen</button>
    {#if fehler}
      <button class="knopf haupt" onclick={nochmal}><i class="fa-solid fa-rotate-right"></i>Noch einmal</button>
    {:else}
      <button class="knopf haupt" disabled={!aufnahme.laeuft || umsetzen} onclick={stopp}><i class="fa-solid fa-stop"></i>Stopp und übernehmen</button>
    {/if}
  </div>
</section>
