<script lang="ts">
  // Dateien aus deiner Kellerwolke an die Karte hängen (E-15): durch die Ordner gehen wie in der Kellerwolke, im gezeigten
  // Ordner suchen, mehrere wählen (auch aus verschiedenen Ordnern), verknüpfen. Schon angehängte stehen als solche da. Die
  // Pinnwand sieht dabei mit deiner Anmeldung nur Namen und Größen; die Dateien bleiben, wo sie sind. Eine Fläche im
  // Detail, kein Browser-Dialog; Escape oder Abbrechen schließt sie.
  import { Suchfeld } from "appkern-oberflaeche";
  import { seitenFehler } from "appkern-oberflaeche";
  import { onMount, tick } from "svelte";
  import { kellerwolkeDateien } from "../daten/abfragen";
  import { AUF_EINMAL, ausKellerwolke } from "../daten/anwendung/anhaenge.svelte";
  import type { Karte, KellerwolkeDatei, KellerwolkeOrdner } from "../modell";
  import { verlassen, verwerfen } from "../teile/verwerfen";
  import { SYMBOL } from "./anhang";
  import { inSicht } from "./sicht";

  let { karte, schliessen }: { karte: Karte; schliessen: () => void } = $props();

  let suche = $state("");
  let gewaehlt = $state<KellerwolkeDatei[]>([]);
  let ordner = $state<KellerwolkeOrdner | null>(null);
  let fehler = $state("");
  let flaeche = $state<HTMLElement>();
  let laufend: AbortController | null = null;

  const schon = (d: KellerwolkeDatei) => karte.anhaenge.find((a) => a.datei === d.id);
  const istGewaehlt = (d: KellerwolkeDatei): boolean => gewaehlt.some((x) => x.id === d.id);
  const liste = $derived((ordner?.eintraege ?? []).filter((d) => d.name.toLowerCase().includes(suche.trim().toLowerCase())));
  const weg = $derived(ordner && ordner.kette.length > 1 ? ordner.kette : []);

  /** Einen Ordner zeigen (null: Meine Dateien); eine noch laufende Anfrage gilt dann nicht mehr */
  async function zeigen(id: string | null): Promise<void> {
    laufend?.abort();
    const halt = (laufend = new AbortController());
    fehler = "";
    try {
      const neu = await kellerwolkeDateien(id, halt.signal);
      if (halt.signal.aborted) return;
      ordner = neu;
      suche = "";
      await tick();
      inSicht(flaeche);
    } catch (f) {
      if (!halt.signal.aborted) fehler = seitenFehler(f);
    }
  }

  // beim Öffnen ganz in Sicht, auch wenn der Abschnitt unten im Detail steht
  onMount(() => {
    inSicht(flaeche);
    void zeigen(null);
    return () => laufend?.abort();
  });

  function umschalten(d: KellerwolkeDatei): void {
    gewaehlt = istGewaehlt(d) ? gewaehlt.filter((x) => x.id !== d.id) : [...gewaehlt, d];
  }

  function verknuepfen(): void {
    ausKellerwolke(karte.id, gewaehlt);
    zu();
  }

  function zu(): void {
    laufend?.abort();
    if (flaeche) verlassen(flaeche);
    schliessen();
  }

  function taste(e: KeyboardEvent): void {
    if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); zu(); }
  }

  function hinein(e: KeyboardEvent, d: KellerwolkeDatei): void {
    if (e.key === "Enter") { e.preventDefault(); void zeigen(d.id); }
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="pw-wolkenwahl" role="group" aria-label="Aus der Kellerwolke wählen" tabindex="-1" bind:this={flaeche} onkeydown={taste}>
  <div class="pw-wolkenwahl-kopf">
    <i class="fa-solid fa-cloud"></i><b>Deine Kellerwolke</b>
    <Suchfeld bind:wert={suche} {@attach verwerfen} placeholder="Datei oder Ordner suchen" aria-label="In diesem Ordner suchen" autocomplete="off" />
  </div>
  {#if weg.length}
    <nav class="pw-wolkenwahl-kopf" aria-label="Weg in deiner Kellerwolke">
      {#each weg as g, i (g.id ?? "")}
        {#if i}<i class="fa-solid fa-chevron-right"></i>{/if}
        {#if i < weg.length - 1}
          <button class="knopf ohne klein" onclick={() => zeigen(g.id)}>{#if !i}<i class="fa-solid fa-house"></i>{/if}{g.name}</button>
        {:else}
          <b aria-current="location">{g.name}</b>
        {/if}
      {/each}
    </nav>
  {/if}
  <div class="pw-wolkenwahl-liste">
    {#if fehler}<div class="leer-zeile">{fehler}</div>{/if}
    {#each liste as d (d.id)}
      {#if d.typ === "ordner"}
        <div class="pw-wolkenwahl-datei" role="button" tabindex="0" onclick={() => zeigen(d.id)} onkeydown={(e) => hinein(e, d)}>
          <i class="fa-solid fa-folder"></i>
          <span class="wer"><span class="name">{d.name}</span></span>
          <i class="fa-solid fa-chevron-right"></i>
        </div>
      {:else}
        {@const da = schon(d)}
        <label class="pw-wolkenwahl-datei" class:schon={!!da}>
          <input type="checkbox" checked={!!da || istGewaehlt(d)} disabled={!!da || (!istGewaehlt(d) && gewaehlt.length >= AUF_EINMAL)}
                 onchange={() => umschalten(d)} />
          <i class="fa-solid {SYMBOL[d.art]}"></i>
          <span class="wer"><span class="name">{d.name}</span></span>
          <span class="meta">{da ? (da.verknuepft ? "schon verknüpft" : "schon angehängt") : d.groesse}</span>
        </label>
      {/if}
    {:else}
      {#if !fehler}
        <div class="leer-zeile">{!ordner ? "Lädt ..." : suche.trim() ? `Keine Datei passt zu "${suche.trim()}".` : "Dieser Ordner ist leer."}</div>
      {/if}
    {/each}
  </div>
  <div class="pw-wolkenwahl-fuss">
    <button class="knopf haupt klein" disabled={!gewaehlt.length} onclick={verknuepfen}><i class="fa-solid fa-link"></i>{gewaehlt.length > 1 ? `${gewaehlt.length} Dateien verknüpfen` : "Verknüpfen"}</button>
    <button class="knopf ohne klein" onclick={zu}>Abbrechen</button>
    <span class="schwach">Die Dateien bleiben in deiner Kellerwolke; an der Karte sehen alle Mitglieder Name und Größe.</span>
  </div>
</div>
