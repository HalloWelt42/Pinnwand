<script lang="ts">
  // Die Pinnwand nach der Anmeldung: Zustand aus dem Server und Ereignisstrom, Uhr, Weg, Verbindungen des Gerüsts. Jeder Pfad zeigt die Ansicht aus
  // der Wegetabelle (routen.ts), am Rechner in der Schale, am Telefon in der eigenen Ansicht. "/" führt zu Heute.
  import { geraet, verbindungenVerfolgen } from "appkern-oberflaeche";
  import { onMount, untrack } from "svelte";
  import { stand, verbinden } from "./daten/stand.svelte";
  import { uhrStarten } from "./daten/uhr.svelte";
  import { finden } from "./routen";
  import Schale from "./schale/Schale.svelte";
  import { gehe, weg, wegStarten } from "./weg.svelte";

  onMount(() => {
    const enden = [verbinden(), uhrStarten(), wegStarten(), verbindungenVerfolgen()];
    return () => enden.forEach((ende) => ende());
  });

  // "/" führt zu Heute; das Kürzel eines Boards steht im Pfad klein (/board/HAUS/12 wird /board/haus/12)
  $effect(() => {
    if (weg.pfad === "/") gehe("/heute", true);
    const gross = weg.pfad.match(/^\/board\/([^/]*[A-Z][^/]*)(.*)$/);
    if (gross) gehe(`/board/${gross[1].toLowerCase()}${gross[2]}${weg.suche}`, true);
  });

  const geraetArt = $derived(geraet.mobil ? "telefon" : "rechner");
  // die Wegesuche liest Boards und Karten, hängt aber nur am Pfad, am Gerät und an der Menge der Boards: Änderungen an
  // Karten richten die Ansicht nicht neu ein
  const treffer = $derived.by(() => {
    const p = weg.pfad, g = geraetArt, n = stand.boards.length;
    return stand.geladen && n >= 0 ? untrack(() => finden(p, g)) : null;
  });
</script>

{#if !stand.geladen}
  <div class="anmeldung pw-laedt"><span>Lädt die Boards ...</span></div>
{:else if treffer && geraetArt === "telefon"}
  <treffer.komponente {...treffer.werte} />
{:else if treffer}
  <Schale aktiv={treffer.navi}><treffer.komponente {...treffer.werte} /></Schale>
{:else}
  <Schale aktiv=""><div class="rollfeld"><div class="hinweis warnung"><i class="fa-solid fa-triangle-exclamation"></i>
    <div>Diesen Weg gibt es nicht: {weg.pfad}. <a href="/heute">Zu Heute</a></div></div></div></Schale>
{/if}
