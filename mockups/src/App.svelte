<script lang="ts">
  // Entwürfe mit echten Pfaden wie in der App: / und /entwuerfe zeigen die Galerie, jeder andere Pfad die Ansicht aus
  // der Wegetabelle (routen.ts), in der Schale (Rechner) oder im Telefonrahmen (?geraet=telefon). Die Leiste unten
  // gehört nur zu den Entwürfen: Galerie, blättern, Thema, Schriftstufe (Vorgabe Klein).
  import { onMount, untrack } from "svelte";
  import Galerie from "./galerie/Galerie.svelte";
  import { zuruecksetzen } from "./beispiel/stand.svelte";
  import { finden } from "./routen";
  import Schale from "./schale/Schale.svelte";
  import { weg, wegStarten, wert } from "./weg.svelte";
  import { darstellung, darstellungAnwenden, darstellungSetzen, type Schrift } from "./darstellung.svelte";
  import { adresse, ZUSTAENDE } from "./zustaende";

  onMount(wegStarten);
  const galerie = $derived(weg.pfad === "/" || weg.pfad === "/entwuerfe");
  const geraet = $derived(wert("geraet") === "telefon" ? "telefon" : "rechner");
  const entwurf = $derived(wert("entwurf"));
  // die Wegesuche liest Boards und Karten, hängt aber nur am Pfad: Änderungen am Zustand richten die Ansicht nicht neu ein
  const treffer = $derived.by(() => { const p = weg.pfad, g = geraet, e = entwurf; return galerie ? null : untrack(() => finden(p, g, e)); });
  const hier = $derived(weg.pfad + weg.suche);
  const nr = $derived(ZUSTAENDE.findIndex((z) => adresse(z) === hier));
  const z = $derived(nr >= 0 ? ZUSTAENDE[nr] : undefined);
  const vorher = $derived(adresse(ZUSTAENDE[((nr < 0 ? 0 : nr) - 1 + ZUSTAENDE.length) % ZUSTAENDE.length]));
  const nachher = $derived(adresse(ZUSTAENDE[((nr < 0 ? -1 : nr) + 1) % ZUSTAENDE.length]));

  // Ein vorgeführter Zustand beginnt beim Ausgangsstand, wer ihn verlässt, kehrt dorthin zurück: so wirkt nichts aus
  // einem Entwurf in einen anderen. Vor dem Zeichnen, damit die Ansicht des Entwurfs sich danach einrichtet.
  let letzterEntwurf = wert("entwurf");
  $effect.pre(() => {
    if (entwurf !== letzterEntwurf) {
      letzterEntwurf = entwurf;
      zuruecksetzen();
    }
  });

  // Thema und Schriftstufe: eine Wahrheit mit der Einstellung Darstellung (darstellung.svelte.ts)
  onMount(darstellungAnwenden);
  const STUFEN_SCHRIFT: Schrift[] = ["klein", "mittel", "gross"];
  const NAME_SCHRIFT: Record<Schrift, string> = { klein: "Klein", mittel: "Mittel", gross: "Groß" };
  const dunkel = $derived(darstellung.thema === "dunkel" || (darstellung.thema === "system" && document.documentElement.dataset.theme === "dunkel"));
  // Am Telefon klappt die Leiste zu einem Griff am Rand ein, damit sie die Fußleiste der Ansicht nicht verdeckt
  let offen = $state(!matchMedia("(max-width: 600px)").matches);
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

<div class="pw-entwurfsleiste" class:zu={!offen} aria-label="Leiste der Entwürfe">
  {#if offen}
    <a class="knopf symbol" href="/entwuerfe" title="Alle Entwürfe"><i class="fa-solid fa-grip"></i></a>
    {#if !galerie}
      <a class="knopf symbol" href={vorher} title="Vorheriger Entwurf"><i class="fa-solid fa-chevron-left"></i></a>
      <span class="titel">{z ? `${nr + 1}/${ZUSTAENDE.length} ${z.titel}` : hier}</span>
      <a class="knopf symbol" href={nachher} title="Nächster Entwurf"><i class="fa-solid fa-chevron-right"></i></a>
    {/if}
    <button class="knopf symbol" title="Hell oder dunkel" onclick={() => darstellungSetzen({ thema: dunkel ? "hell" : "dunkel" })}>
      <i class="fa-solid {dunkel ? 'fa-sun' : 'fa-moon'}"></i></button>
    <button class="knopf" title="Schriftstufe" onclick={() => darstellungSetzen({ schrift: STUFEN_SCHRIFT[(STUFEN_SCHRIFT.indexOf(darstellung.schrift) + 1) % 3] })}>
      <i class="fa-solid fa-text-height"></i>{NAME_SCHRIFT[darstellung.schrift]}</button>
    <button class="knopf symbol einklappen" title="Leiste einklappen" onclick={() => (offen = false)}><i class="fa-solid fa-chevron-down"></i></button>
  {:else}
    <button class="knopf symbol" title="Leiste der Entwürfe zeigen" onclick={() => (offen = true)}><i class="fa-solid fa-grip"></i></button>
  {/if}
</div>
