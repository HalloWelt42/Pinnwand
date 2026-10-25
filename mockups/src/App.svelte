<script lang="ts">
  // Entwürfe mit echten Pfaden wie in der App: / und /entwuerfe zeigen die Galerie, jeder andere Pfad die Ansicht aus
  // der Wegetabelle (routen.ts), in der Schale (Rechner) oder im Telefonrahmen (?geraet=telefon). Die Leiste unten
  // gehört nur zu den Entwürfen: Galerie, blättern, Thema, Schriftstufe (Vorgabe Klein).
  import { onMount } from "svelte";
  import Galerie from "./galerie/Galerie.svelte";
  import { finden } from "./routen";
  import Schale from "./schale/Schale.svelte";
  import { weg, wegStarten, wert } from "./weg.svelte";
  import { adresse, ZUSTAENDE } from "./zustaende";

  onMount(wegStarten);
  const galerie = $derived(weg.pfad === "/" || weg.pfad === "/entwuerfe");
  const geraet = $derived(wert("geraet") === "telefon" ? "telefon" : "rechner");
  const entwurf = $derived(wert("entwurf"));
  const treffer = $derived(galerie ? null : finden(weg.pfad, geraet, entwurf));
  const hier = $derived(weg.pfad + weg.suche);
  const nr = $derived(ZUSTAENDE.findIndex((z) => adresse(z) === hier));
  const z = $derived(nr >= 0 ? ZUSTAENDE[nr] : undefined);
  const vorher = $derived(adresse(ZUSTAENDE[((nr < 0 ? 0 : nr) - 1 + ZUSTAENDE.length) % ZUSTAENDE.length]));
  const nachher = $derived(adresse(ZUSTAENDE[((nr < 0 ? -1 : nr) + 1) % ZUSTAENDE.length]));

  // Thema wie in den Apps aus appkern_anzeige (setzt auch die Ansichtsprüfung), sonst aus der Startseite
  function gemerktesThema(): string {
    try { return JSON.parse(localStorage.getItem("appkern_anzeige") ?? "{}").thema ?? ""; } catch { return ""; }
  }
  let thema = $state(gemerktesThema() || (document.documentElement.dataset.theme ?? "dunkel"));
  let schrift = $state(document.documentElement.dataset.schrift ?? "klein");
  $effect(() => { document.documentElement.dataset.theme = thema; });
  $effect(() => { document.documentElement.dataset.schrift = schrift; });
  const STUFEN_SCHRIFT = ["klein", "mittel", "gross"];
  const NAME_SCHRIFT: Record<string, string> = { klein: "Klein", mittel: "Mittel", gross: "Groß" };
</script>

{#if galerie}
  <Galerie />
{:else if treffer && geraet === "telefon"}
  <div class="pw-buehne">
    <div class="pw-telefon"><treffer.komponente {...treffer.werte} /></div>
    {#if z}<div class="erklaerung"><h2>{z.titel}</h2><p>{z.text}</p></div>{/if}
  </div>
{:else if treffer}
  <Schale aktiv={treffer.navi}><treffer.komponente {...treffer.werte} /></Schale>
{:else}
  <Schale aktiv=""><div class="rollfeld"><div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
    <div>Diesen Weg gibt es nicht: {weg.pfad}. <a href="/entwuerfe">Zu den Entwürfen</a></div></div></div></Schale>
{/if}

<div class="pw-entwurfsleiste" aria-label="Leiste der Entwürfe">
  <a class="knopf symbol" href="/entwuerfe" title="Alle Entwürfe"><i class="fa-solid fa-grip"></i></a>
  {#if !galerie}
    <a class="knopf symbol" href={vorher} title="Vorheriger Entwurf"><i class="fa-solid fa-chevron-left"></i></a>
    <span class="titel">{z ? `${nr + 1}/${ZUSTAENDE.length} ${z.titel}` : hier}</span>
    <a class="knopf symbol" href={nachher} title="Nächster Entwurf"><i class="fa-solid fa-chevron-right"></i></a>
  {/if}
  <button class="knopf symbol" title="Hell oder dunkel" onclick={() => (thema = thema === "dunkel" ? "hell" : "dunkel")}>
    <i class="fa-solid {thema === 'dunkel' ? 'fa-sun' : 'fa-moon'}"></i></button>
  <button class="knopf" title="Schriftstufe" onclick={() => (schrift = STUFEN_SCHRIFT[(STUFEN_SCHRIFT.indexOf(schrift) + 1) % 3])}>
    <i class="fa-solid fa-text-height"></i>{NAME_SCHRIFT[schrift]}</button>
</div>
